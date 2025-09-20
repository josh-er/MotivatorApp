# send_now.py
import logging
import random
from datetime import datetime, date
from .db import SessionLocal
from .models import User, Quote, SentQuote, MessageLog
from .send_sms import send_sms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            # Find which quotes user already got this cycle
            sent_quote_ids = {
                sq.quote_id for sq in db.query(SentQuote).filter_by(user_id=user.id, cycle=user.cycle)
            }

            available_quotes = [q for q in quotes if q.id not in sent_quote_ids]

            if not available_quotes:
                # Start new cycle if all quotes sent
                user.cycle += 1
                db.commit()
                available_quotes = quotes

            # Pick a random available quote
            quote_obj = random.choice(available_quotes)
            quote_text = quote_obj.text

            logger.info(f"Sending to {user.phone}: {quote_text}")

            status = "success"
            error_text = None

            try:
                send_sms(user.phone, quote_text)
            except Exception as e:
                status = "error"
                error_text = str(e)
                logger.error(f"Failed to send to {user.phone}: {error_text}")

            # Log in MessageLog
            log_entry = MessageLog(
                phone=user.phone,
                quote=quote_text,
                status=status,
                error=error_text,
                timestamp=datetime.now()
            )
            db.add(log_entry)

            # Track in SentQuote (only if success, to avoid "losing" quotes on failures)
            if status == "success":
                sent_entry = SentQuote(
                    user_id=user.id,
                    quote_id=quote_obj.id,
                    cycle=user.cycle
                )
                db.add(sent_entry)

                # Update last_sent
                user.last_sent = date.today()

            db.commit()

        logger.info("Done sending to all users.")
    finally:
        db.close()

if __name__ == "__main__":
    send_now()
