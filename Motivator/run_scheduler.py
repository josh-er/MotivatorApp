# run_scheduler.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from send_sms import send_sms
from db import SessionLocal
from models import User, Quote, MessageLog

logging.basicConfig(level=logging.INFO)
scheduler = BackgroundScheduler()

def send_quotes():
    now = datetime.now().strftime("%H:%M")
    logging.info(f"Checking for users scheduled at {now}")
    db = SessionLocal()
    users = db.query(User).filter(User.time == now).all()

    logging.info(f"Found {len(users)} user(s) to message.")

    for user in users:
        if user.last_sent == datetime.now().date():
            logging.info(f"Skipping {user.phone}, already sent today.")
            continue

        # fetch a random quote
        quote = db.query(Quote).order_by(func.random()).first()
        if not quote:
            logging.warning("No quotes available in DB.")
            continue

        # send SMS
        send_sms(user.phone, quote.text)

        # update last_sent
        user.last_sent = datetime.now().date()

        # log the message
        log_entry = MessageLog(
            user_id=user.id,
            message=quote.text
        )
        db.add(log_entry)

        db.commit()
        logging.info(f"Sent to {user.phone}: {quote.text}")

    db.close()

# needed for func.random()
from sqlalchemy.sql.expression import func

scheduler.add_job(send_quotes, "interval", minutes=1)
scheduler.start()

if __name__ == "__main__":
    import time
    while True:
        time.sleep(1)
