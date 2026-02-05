import random
import logging
from datetime import datetime, timezone
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, MessageLog, SentQuote
from .send_sms import send_sms
from zoneinfo import ZoneInfo
from Motivator.event_logger import log_event

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

    log_event(
        db,
        user_id=user.id,
        event_type="compliance_sent",
        source="system",
    )

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
    now_utc = datetime.now(timezone.utc)

    # ---- guards: NO LOGGING ----
    if not user.phone:
        return "no_phone"

    if not user.local_time or not user.timezone:
        return "invalid_schedule"

    if not user.opted_in:
        return "not_opted_in"

    try:
        user_tz = ZoneInfo(user.timezone)
    except Exception:
        return "invalid_timezone"

    local_today = now_utc.astimezone(user_tz).date()

    if user.last_sent == local_today:
        return "already_sent"

    # ---- quote selection ----
    if not user.cycle:
        user.cycle = 1

    unseen = get_unseen_quotes(db, user)
    if not unseen:
        user.cycle += 1
        unseen = get_unseen_quotes(db, user)
        if not unseen:
            return "no_quotes"

    quote = random.choice(unseen)

    # ---- log ONLY now ----
    log = MessageLog(
        phone=user.phone,
        quote=quote.text,
        status="pending",
        timestamp=now_utc,
    )
    db.add(log)
    db.commit()

    try:
        # idempotency lock
        user.last_sent = local_today
        db.commit()

        send_sms(user.phone, quote.text)

        db.add(
            SentQuote(
                user_id=user.id,
                quote_id=quote.id,
                sent_date=now_utc,
                cycle=user.cycle,
            )
        )

        log.status = "success"

        log_event(
            db,
            user_id=user.id,
            event_type="quote_sent",
            source="scheduler",
        )

        db.commit()
        return "sent"

    except Exception as e:
        log.status = "failed"
        log.error = str(e)
        db.commit()
        return "failed"


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