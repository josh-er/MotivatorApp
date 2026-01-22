import random
import logging
from datetime import datetime, timezone
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, MessageLog, SentQuote
from .send_sms import send_sms
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def utc_today():
    return datetime.now(timezone.utc).date()

def send_compliance(db, user):
    user = db.get(User, user.id)
    
    if not user.phone:
        return

    if user.received_compliance or not user.opted_in:
        return

    text = (
        "You're now opted in to receive once daily motivational SMS messages from Motivator. Msg & data rates may apply. Visit the Motivator app to customize your preferences. Reply HELP for help. Reply STOP to cancel."
    )

    log = MessageLog(
        phone=user.phone,
        quote="[COMPLIANCE]",
        status="pending",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

    try:
        send_sms(user.phone, text)
        user.received_compliance = True
        log.status = "success"
    except Exception as e:
        log.status = "failed"
        log.error = str(e)

    db.commit()


def get_unseen_quotes(db, user):
    all_quotes = db.query(Quote).all()

    seen_ids = {
        sq.quote_id
        for sq in db.query(SentQuote).filter(
            SentQuote.user_id == user.id,
            SentQuote.cycle == (user.cycle or 1)
        )
    }

    return [q for q in all_quotes if q.id not in seen_ids]


def send_quote_to_user(db, user):
    # --- compute LOCAL today ---
    try:
        user_tz = ZoneInfo(user.timezone)
    except Exception:
        log = MessageLog(
            phone=user.phone,
            quote="",
            status="skipped",
            error="invalid timezone",
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        return


    
    # for testing DST now_utc = datetime(2025, 11, 2, 12, 0, tzinfo=timezone.utc)
    now_utc = datetime.now(timezone.utc)
    local_now = now_utc.astimezone(user_tz)
    local_today = local_now.date()
    # line below for testing
    # logger.info(f"LOCAL_NOW={local_now}, LOCAL_TODAY={local_today}")

    # --- create log immediately ---
    log = MessageLog(
        phone=user.phone,
        quote="",
        status="pending",
        timestamp=now_utc,
    )
    db.add(log)
    db.commit()

    # --- guards ---
    if not user.local_time or not user.timezone:
        log.status = "skipped"
        log.error = "invalid schedule (missing preferred_time or timezone)"
        db.commit()
        return

    if not user.opted_in:
        log.status = "skipped"
        log.error = "user opted out"
        db.commit()
        return

    if not user.received_compliance:
        log.status = "skipped"
        log.error = "compliance not sent"
        db.commit()
        return

    if user.last_sent == local_today:
        log.status = "skipped"
        log.error = "already sent today (local)"
        db.commit()
        # logger.info line is for testing
        # logger.info(f"Skipped {user.phone}: already sent today (local)")
        return

    # --- quote selection ---
    if not user.cycle:
        user.cycle = 1

    unseen = get_unseen_quotes(db, user)
    if not unseen:
        user.cycle += 1
        unseen = get_unseen_quotes(db, user)
        if not unseen:
            log.status = "failed"
            log.error = "no quotes available"
            db.commit()
            return

    quote = random.choice(unseen)
    log.quote = quote.text

    try:
        # mark sent BEFORE SMS to guarantee idempotency
        user.last_sent = local_today
        db.commit()

        send_sms(user.phone, quote.text)

        db.add(
            SentQuote(
                user_id=user.id,
                quote_id=quote.id,
                sent_date=now_utc,  # always UTC timestamp
                cycle=user.cycle,
            )
        )

        log.status = "success"

    except Exception as e:
        logger.exception(f"Failed to send to {user.phone}")
        log.status = "failed"
        log.error = str(e)

    db.commit()


def send_now(phone: str):
    import logging
    logging.error("### EXECUTING send_quotes.send_now ###")    
    db = SessionLocal()
    # print("SEND_NOW DB URL:", db.get_bind().url)
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            logger.warning(f"No user found for {phone}")
            return

        send_quote_to_user(db, user)

    finally:
        db.close()

def send_users(db, users):
    """
    Send quotes to a pre-selected list of users.
    Scheduler is responsible for time logic.
    """
    logger.info(f"Sending quotes to {len(users)} users")

    for user in users:
        send_quote_to_user(db, user)