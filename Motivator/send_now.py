# send_now.py
import logging
import random
import time
from datetime import datetime, date
from logging.handlers import RotatingFileHandler
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, SentQuote, MessageLog
from .send_sms import send_sms

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
log_handler = RotatingFileHandler("motivator.log", maxBytes=1_000_000, backupCount=5)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[log_handler, logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Main send loop
# ----------------------------------------------------------------------
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
            # Skip if already sent today
            if user.last_sent == date.today():
                logger.info(f"Skipping {user.phone}, already sent today.")
                continue

            # Track which quotes user already got this cycle
            sent_quote_ids = {
                sq.quote_id for sq in db.query(SentQuote).filter_by(user_id=user.id, cycle=user.cycle)
            }

            available_quotes = [q for q in quotes if q.id not in sent_quote_ids]
            if not available_quotes:
                # Start new cycle if all quotes have been sent
                user.cycle += 1
                db.commit()
                available_quotes = quotes
                sent_quote_ids.clear()

            # Pick a random quote different from last sent
            filtered_quotes = [q for q in available_quotes if q.id != user.last_quote_id]
            quote_obj = random.choice(filtered_quotes or available_quotes)
            quote_text = quote_obj.text

            logger.info(f"Sending to {user.phone}: {quote_text}")
            status = "success"
            error_text = None

            # ------------------------------------------------------------------
            # Send SMS with retry logic
            # ------------------------------------------------------------------
            try:
                send_sms(user.phone, quote_text)
            except Exception as e:
                logger.warning(f"First attempt failed for {user.phone}: {e}. Retrying once...")
                time.sleep(10)
                try:
                    send_sms(user.phone, quote_text)
                except Exception as e2:
                    status = "error"
                    error_text = str(e2)
                    logger.error(f"Second attempt failed for {user.phone}: {error_text}")

            # ------------------------------------------------------------------
            # Logging + persistence
            # ------------------------------------------------------------------
            log_entry = MessageLog(
                phone=user.phone,
                quote=quote_text,
                status=status,
                error=error_text,
                timestamp=datetime.now()
            )
            db.add(log_entry)

            if status == "success":
                sent_entry = SentQuote(user_id=user.id, quote_id=quote_obj.id, cycle=user.cycle)
                db.add(sent_entry)
                user.last_quote_id = quote_obj.id
                user.last_sent = date.today()

            db.commit()

        logger.info("Done sending to all users.")

    except Exception as e:
        logger.exception(f"Critical failure in send_now(): {e}")
    finally:
        db.close()

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    send_now()
