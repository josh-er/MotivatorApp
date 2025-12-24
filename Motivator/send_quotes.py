import random
import logging
from datetime import datetime, date, timezone
from sqlalchemy.orm import joinedload
from .send_sms import send_sms
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, MessageLog, SentQuote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_unseen_quotes(db, user):
    """Return list of quotes this user hasn’t seen in the current cycle."""
    all_quotes = db.query(Quote).all()

    seen_ids = {
        sq.quote_id
        for sq in db.query(SentQuote).filter(
            SentQuote.user_id == user.id,
            SentQuote.cycle == getattr(user, "cycle", 1)
        )
    }

    return [q for q in all_quotes if q.id not in seen_ids]


def send_quote_to_user(db, user, today):
    """Send one quote to a user, ensuring no repeats until reset and always logging."""

    if not hasattr(user, "cycle") or user.cycle is None:
        user.cycle = 1

    unseen = get_unseen_quotes(db, user)

    if not unseen:
        user.cycle += 1
        logger.info(f"Resetting {user.phone} to cycle {user.cycle}")
        unseen = get_unseen_quotes(db, user)

        if not unseen:
            logger.warning("No quotes exist in DB at all")
            return

    quote = random.choice(unseen)

    # Create log entry first
    log = MessageLog(
        phone=user.phone,
        quote=quote.text,
        status="pending",
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()  # ensure the log exists even if send_sms fails

    try:
        send_sms(user.phone, quote.text)
        logger.info(f"Sent to {user.phone}: {quote.text}")
        log.status = "success"

        user.last_sent = today
        sent = SentQuote(
            user_id=user.id,
            quote_id=quote.id,
            sent_date=datetime.utcnow(),
            cycle=user.cycle
        )
        db.add(sent)

    except Exception as e:
        logger.exception(f"Failed to send to {user.phone}")
        log.status = "failed"
        log.error = str(e)

    finally:
        db.commit()  # update log and user/sent quote info


def send_quotes():
    """Scheduled sending: send one unseen quote to each user whose schedule matches current time."""
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%H:%M")
    today = now.date()
    logger.info(f"Running scheduled send_quotes() at {current_time}")

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.utc_time == current_time).all()
        logger.info(f"Found {len(users)} user(s) scheduled for {current_time}")

        for user in users:
            try:
                if user.last_sent == today:
                    logger.info(f"Skipping {user.phone}, already sent today")
                    continue
                send_quote_to_user(db, user, today)
            except Exception:
                db.rollback()  # rollback only if something unexpected happens

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
        try:
            send_quote_to_user(db, user, today)
        except Exception:
            db.rollback()
    finally:
        db.close()
