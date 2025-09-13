import random
import logging
from datetime import datetime, date
from .send_sms import send_sms
from .db import SessionLocal
from .models import User, Quote, MessageLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_quotes():
    """Scheduled sending: send one random quote to each user whose schedule matches current time."""
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

            quote = random.choice(db.query(Quote).all()).text
            try:
                send_sms(user.phone, quote)
                logger.info(f"Sent to {user.phone}: {quote}")

                # Update last_sent
                user.last_sent = today

                # Log message
                log = MessageLog(
                    phone=user.phone,
                    quote=quote,
                    status="success"
                )
                db.add(log)

            except Exception as e:
                logger.error(f"Failed to send to {user.phone}: {e}")
                log = MessageLog(
                    phone=user.phone,
                    quote=quote,
                    status="failed",
                    error=str(e)
                )
                db.add(log)

        db.commit()
    finally:
        db.close()


def send_now(phone: str):
    """Send one random quote immediately to a specific phone (ignores schedule)."""
    today = date.today()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()

        quotes = db.query(Quote).all()
        if not quotes:
            logger.warning("No quotes found in database")
            return

        quote = random.choice(quotes).text

        try:
            send_sms(phone, quote)
            logger.info(f"[send_now] Sent to {phone}: {quote}")

            if user:
                user.last_sent = today

            log = MessageLog(
                phone=phone,
                quote=quote,
                status="success"
            )
            db.add(log)

        except Exception as e:
            logger.error(f"[send_now] Failed to send to {phone}: {e}")
            log = MessageLog(
                phone=phone,
                quote=quote,
                status="failed",
                error=str(e)
            )
            db.add(log)

        db.commit()
    finally:
        db.close()
