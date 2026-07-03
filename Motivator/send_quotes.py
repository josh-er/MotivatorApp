import random
import logging
from datetime import datetime, timezone
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, SentQuote
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

    COMPLIANCE_MESSAGE = (
        "Motivator: You're subscribed to 1 motivational msg/day. "
        "Msg & data rates may apply. Reply STOP to cancel, HELP for help."
    )
    send_sms(user.phone, COMPLIANCE_MESSAGE)

    user.received_compliance = True

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

    if not user.phone or not user.opted_in:
        return "not_eligible"

    if not user.local_time or not user.timezone:
        return "invalid_schedule"

    try:
        user_tz = ZoneInfo(user.timezone)
    except Exception:
        return "invalid_timezone"

    local_today = now_utc.astimezone(user_tz).date()

    if user.last_sent == local_today:
        return "already_sent"

    unseen = get_unseen_quotes(db, user)
    if not unseen:
        user.cycle = (user.cycle or 1) + 1
        unseen = get_unseen_quotes(db, user)
        if not unseen:
            return "no_quotes"

    quote = random.choice(unseen)
    message_text = quote.text

    db.commit()

    try:
        user.last_sent = local_today
        db.commit()

        send_sms(user.phone, message_text)

        db.add(SentQuote(
            user_id=user.id,
            quote_id=quote.id,
            sent_date=now_utc,
            cycle=user.cycle or 1,
        ))

        log_event(db, user_id=user.id, event_type="quote_sent", source="scheduler")
        db.commit()
        return "sent"

    except Exception as e:
        db.commit()

        log_db = SessionLocal()
        try:
            log_event(
                log_db,
                user_id=user.id,
                event_type="quote_send_failed",
                source="scheduler",
                error_message=str(e),
            )
            log_db.commit()
        finally:
            log_db.close()

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