# send_now.py
import logging
import random
from datetime import datetime, date
from db import SessionLocal
from models import User, Quote, MessageLog
from send_sms import send_sms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config: set to True to update user's last_sent to today after a successful send
UPDATE_LAST_SENT = False

def send_now():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        quotes = db.query(Quote).all()

        if not users:
            logger.info("No users found in DB.")
            return

        if not quotes:
            logger.warning("No quotes found in DB.")
            return

        for user in users:
            quote_obj = random.choice(quotes)
            quote_text = quote_obj.text if hasattr(quote_obj, "text") else str(quote_obj)

            logger.info(f"Sending to {user.phone}: {quote_text}")

            status = "success"
            error_text = None

            try:
                send_sms(user.phone, quote_text)
            except Exception as e:
                status = "error"
                error_text = str(e)
                logger.error(f"Failed to send to {user.phone}: {error_text}")

            # Try to create a MessageLog entry using common shapes
            log_entry = None
            try:
                # Try (user_id, message)
                log_entry = MessageLog(user_id=user.id, message=quote_text, timestamp=datetime.now())
            except TypeError:
                try:
                    # Try (phone, quote, status, error, timestamp)
                    log_entry = MessageLog(
                        phone=user.phone,
                        quote=quote_text,
                        status=status,
                        error=error_text,
                        timestamp=datetime.now()
                    )
                except TypeError:
                    try:
                        # Try (user_id, quote) fallback
                        log_entry = MessageLog(user_id=user.id, quote=quote_text)
                    except Exception:
                        log_entry = None

            if log_entry is not None:
                try:
                    db.add(log_entry)
                except Exception as e:
                    logger.error(f"Failed to add log entry for {user.phone}: {e}")

            if UPDATE_LAST_SENT and status == "success":
                try:
                    user.last_sent = date.today()
                except Exception as e:
                    logger.error(f"Failed to update last_sent for {user.phone}: {e}")

            db.commit()

        logger.info("Done sending to all users.")
    finally:
        db.close()

if __name__ == "__main__":
    send_now()
