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
    users = db.query(User).filter(User.time == now_utc).all()

    logging.info(f"[Scheduler] Found {len(users)} user(s) to message.")

    for user in users:

        # ---------------------------------------------------------
        # 1. Skip if user STOP'ed
        # ---------------------------------------------------------
        if not user.opted_in:
            logging.info(f"[Scheduler] Skipping {user.phone} — user opted out.")
            continue

        # ---------------------------------------------------------
        # 2. Skip if they already received today's message
        # ---------------------------------------------------------
        if user.last_sent == today_utc:
            logging.info(f"[Scheduler] Skipping {user.phone}, already sent today.")
            continue

        # ---------------------------------------------------------
        # 3. Get a quote
        # ---------------------------------------------------------
        quote = db.query(Quote).order_by(func.random()).first()
        if not quote:
            logging.warning("[Scheduler] No quotes in database.")
            continue

        # ---------------------------------------------------------
        # 4. FIRST MESSAGE — compliance text
        # (sent once, before their first motivational quote)
        # ---------------------------------------------------------
        if not user.received_compliance:
            send_sms(
                user.phone,
                "You're now opted in to receive once daily motivational SMS messages from Motivator. Msg & data rates may apply. Visit the Motivator app to customize your preferences. Reply HELP for help. Reply STOP to cancel."
            )
            user.received_compliance = True
            db.commit()
            logging.info(f"[Scheduler] Sent compliance message to {user.phone}")
            continue  # Do NOT send the quote yet

        # ---------------------------------------------------------
        # 5. Normal daily quote
        # ---------------------------------------------------------
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

        logging.info(f"[Scheduler] Sent quote to {user.phone}")

    db.close()


# Run the job every minute (Render supports this fine)
scheduler.add_job(send_quotes, "interval", minutes=1)
scheduler.start()

if __name__ == "__main__":
    import time
    while True:
        time.sleep(1)
