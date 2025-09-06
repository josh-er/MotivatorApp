import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from send_sms import send_sms
from db import SessionLocal
from models import User

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
            continue  # already sent today

        # send SMS
        send_sms(user.phone, "Here’s your motivational quote for today!")

        # update last_sent
        user.last_sent = datetime.now().date()
        db.commit()

    db.close()

scheduler.add_job(send_quotes, "interval", minutes=1)
scheduler.start()

if __name__ == "__main__":
    import time
    while True:
        time.sleep(1)
