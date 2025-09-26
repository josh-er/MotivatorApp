import random
import logging
from datetime import datetime, date
from sqlalchemy.orm import joinedload
from .send_sms import send_sms
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, MessageLog, SentQuote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_unseen_quotes(db, user):
    """Return list of quotes this user hasn’t seen in the current cycle."""
    # All quotes
    all_quotes = db.query(Quote).all()

    # Quote IDs user has already seen this cycle
    seen_ids = {
        sq.quote_id
        for sq in db.query(SentQuote).filter(
            SentQuote.user_id == user.id,
            SentQuote.cycle == getattr(user, "cycle", 1)  # default cycle 1
        )
    }

    # Filter unseen
    unseen = [q for q in all_quotes if q.id not in seen_ids]
    return unseen


def send_quote_to_user(db, user, today):
    """Send one quote to a user, ensuring no repeats until reset."""
    # Default cycle = 1
    if not hasattr(user, "cycle") or user.cycle is None:
        user.cycle = 1

    unseen = get_unseen_quotes(db, user)

    if not unseen:
        # All quotes sent → soft reset
        user.cycle += 1
        db.commit()
        logger.info(f"Resetting {user.phone} to cycle {user.cycle}")
        unseen = get_unseen_quotes(db, user)

        if not unseen:
            logger.warning("No quotes exist in DB at all")
            return

    # Pick one unseen at random
    quote = random.choice(unseen)

    try:
        send_sms(user.phone, quote.text)
        logger.info(f"Sent to {user.phone}: {quote.text}")

        # Update user
        user.last_sent = today

        # Log in SentQuote
        sent = SentQuote(
            user_id=user.id,
            quote_id=quote.id,
            sent_date=datetime.utcnow(),
            cycle=user.cycle
        )
        db.add(sent)

        # Log in MessageLog
        log = MessageLog(
            phone=user.phone,
            quote=quote.text,
            status="success"
        )
        db.add(log)

    except Exception as e:
        logger.error(f"Failed to send to {user.phone}: {e}")
        log = MessageLog(
            phone=user.phone,
            quote=quote.text,
            status="failed",
            error=str(e)
        )
        db.add(log)


def send_quotes():
    """Scheduled sending: send one unseen quote to each user whose schedule matches current time."""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    today = date.today()
    logger.info(f"Running scheduled send_quotes() at {current_time}")

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.time == current_time).all()
        logger.info(f"Found {len(users)} user(s) scheduled for {current_time}")

        for user in users:
            if user.last_sent == today:
                logger.info(f"Skipping {user.phone}, already sent today")
                continue
            send_quote_to_user(db, user, today)

        db.commit()
    finally:
        db.close()


def send_now(phone: str):
    """Send one unseen quote immediately to a specific phone (ignores schedule)."""
    today = date.today()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()

        if not user:
            logger.warning(f"No user found with phone {phone}")
            return

        send_quote_to_user(db, user, today)
        db.commit()
    finally:
        db.close()
