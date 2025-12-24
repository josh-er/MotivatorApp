# legacy, do not use
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
log_handler = RotatingFileHandler(
    "scheduler.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
log_handler.setFormatter(formatter)

logger = logging.getLogger("motivator")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(logging.StreamHandler())

# ----------------------------------------------------------------------
# Main send loop
# ----------------------------------------------------------------------
def send_now():
    db = SessionLocal()
    logger.info("---- Starting Motivator send cycle ----")

    try:
        users = db.query(User).all()
        quotes = db.query(Quote).all()

        if not users:
            logger.warning("No users found in DB.")
            return

        if not quotes:
            logger.warning("No quotes found in DB.")
            return

        for user in users:
            try:
                # Skip if already sent today
                if user.last_sent == date.today():
                    logger.info(f"Skipping {user.phone}, already sent today.")
                    continue

                sent_quote_ids = {
                    sq.quote_id for sq in db.query(SentQuote)
                    .filter_by(user_id=user.id, cycle=user.cycle)
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

                # Send SMS with retry logic
                for attempt in range(2):
                    try:
                        send_sms(user.phone, quote_text)
                        break
                    except Exception as e:
                        if attempt == 0:
                            logger.warning(f"Attempt 1 failed for {user.phone}: {e}. Retrying...")
                            time.sleep(5)
                        else:
                            status = "failed"
                            error_text = str(e)
                            logger.error(f"Attempt 2 failed for {user.phone}: {error_text}")

                # Log results
                log_entry = MessageLog(
                    phone=user.phone,
                    quote=quote_text,
                    status=status,
                    error=error_text,
                    timestamp=datetime.now()
                )
                db.add(log_entry)

                if status == "success":
                    db.add(SentQuote(user_id=user.id, quote_id=quote_obj.id, cycle=user.cycle))
                    user.last_quote_id = quote_obj.id
                    user.last_sent = date.today()

                db.commit()

            except Exception as inner_e:
                logger.exception(f"Error processing user {user.phone}: {inner_e}")
                db.rollback()

        logger.info("---- Finished Motivator send cycle ----")

    except Exception as e:
        logger.exception(f"Critical failure in send_now(): {e}")
    finally:
        db.close()


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    send_now()
