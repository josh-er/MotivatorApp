import random
import logging
from datetime import datetime, timezone
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, MessageLog, SentQuote
from .send_sms import send_sms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def utc_today():
    return datetime.now(timezone.utc).date()


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

    today = utc_today()

    if user.last_sent == today:
        logger.info(f"Skipping {user.phone}, already sent today")
        return

    # Initialize cycle if needed
    if not user.cycle:
        user.cycle = 1

    # Mark as sent first
    user.last_sent = today
    db.flush()

    unseen = get_unseen_quotes(db, user)
    if not unseen:
        user.cycle += 1
        unseen = get_unseen_quotes(db, user)
        if not unseen:
            logger.warning("No quotes available")
            return

    quote = random.choice(unseen)

    try:
        # FORCE FAILURE FOR TESTING
        raise RuntimeError("FORCED TEST FAILURE")

        send_sms(user.phone, quote.text)

        db.add(SentQuote(
            user_id=user.id,
            quote_id=quote.id,
            sent_date=datetime.now(timezone.utc),
            cycle=user.cycle
        ))

        db.add(MessageLog(
            phone=user.phone,
            quote=quote.text,
            status="success",
            timestamp=datetime.now(timezone.utc)
        ))

    except Exception as e:
        logger.exception(f"Failed to send to {user.phone}")

        db.add(MessageLog(
            phone=user.phone,
            quote=quote.text,
            status="failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc)
        ))

    db.commit()


def send_quotes():
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%H:%M")
    today = utc_today()

    logger.info(f"Running send_quotes at {current_time}")

    db = SessionLocal()
    try:
        users = (
            db.query(User)
            .filter(User.utc_time == current_time)
            .filter((User.last_sent.is_(None)) | (User.last_sent != today))
            .all()
        )

        logger.info(f"Found {len(users)} eligible users")

        for user in users:
            send_quote_to_user(db, user)

    finally:
        db.close()


def send_now(phone: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            logger.warning(f"No user found for {phone}")
            return

        send_quote_to_user(db, user)

    finally:
        db.close()
