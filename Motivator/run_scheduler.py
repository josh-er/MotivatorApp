# run_scheduler.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from sqlalchemy.sql.expression import func
from send_sms import send_sms
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, MessageLog

logging.basicConfig(level=logging.INFO)
scheduler = BackgroundScheduler(timezone="UTC")

def send_quotes():
    # Always compare in UTC — this is what DB stores
    now_utc = datetime.now(timezone.utc).strftime("%H:%M")
    today_utc = datetime.now(timezone.utc).date()

    logging.info(f"[Scheduler] Checking for users scheduled at {now_utc} UTC")

    db = SessionLocal()

    # Get users matching exact HH:MM UTC
    users = db.query(User).filter(User.time == now_utc).all()

    logging.info(f"[Scheduler] Found {len(users)} user(s) to message.")

    for user in users:

        # Skip if already sent today
        if user.last_sent == today_utc:
            logging.info(f"[Scheduler] Skipping {user.phone}, already sent today.")
            continue

        # Fetch random quote
        quote = db.query(Quote).order_by(func.random()).first()
        if not quote:
            logging.warning("[Scheduler] No quotes in database.")
            continue

        # Send SMS
        send_sms(user.phone, quote.text)

        # Update last_sent
        user.last_sent = today_utc

        # Log the message
        log_entry = MessageLog(
            user_id=user.id,
            message=quote.text
        )
        db.add(log_entry)

        db.commit()
        logging.info(f"[Scheduler] Sent to {user.phone}")

    db.close()

# needed for func.random()

scheduler.add_job(send_quotes, "interval", minutes=1)
scheduler.start()

if __name__ == "__main__":
    import time
    while True:
        time.sleep(1)
