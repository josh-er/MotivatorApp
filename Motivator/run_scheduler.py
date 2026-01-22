import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from sqlalchemy.sql.expression import func
from Motivator.send_sms import send_sms
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, MessageLog
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO)
scheduler = BackgroundScheduler(timezone="UTC")
'''
def recalc_all_user_utc_times():
    """Recalculate utc_time for every user based on local_time + timezone.
    This handles DST transitions. Run once daily (00:05 UTC) or on demand.
    """
    logging.info("[Scheduler] Recalculating utc_time for all users...")
    db = SessionLocal()
    try:
        users = db.query(User).all()
        updated = 0
        for u in users:
            if not u.local_time or not u.timezone:
                continue
            try:
                tz = ZoneInfo(u.timezone)
                today_local = datetime.now(tz).date()
                local_dt = datetime.combine(today_local, datetime.strptime(u.local_time, "%H:%M").time(), tzinfo=tz)
                utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
                new_utc = utc_dt.strftime("%H:%M")
                if u.utc_time != new_utc:
                    u.utc_time = new_utc
                    updated += 1
            except Exception as e:
                logging.warning(f"Failed to recalc for {u.phone}: {e}")
        db.commit()
        logging.info(f"[Scheduler] Recalc complete — updated {updated} users.")
    finally:
        db.close()
'''
def send_quotes():
    logging.warning(
        "[Scheduler] send_quotes() in run_scheduler.py is disabled. "
        "All sending must go through Motivator.send_quotes.send_quote_to_user()."
    )
    return
    """
    now_utc = datetime.now(timezone.utc).strftime("%H:%M")
    today_utc = datetime.now(timezone.utc).date()
    logging.info(f"[Scheduler] Checking for users scheduled at {now_utc} UTC")

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.utc_time == now_utc).all()
        logging.info(f"[Scheduler] Found {len(users)} user(s) to message.")

        for user in users:
            if not user.opted_in:
                logging.info(f"[Scheduler] Skipping {user.phone} — user opted out.")
                continue

            if user.last_sent == today_utc:
                logging.info(f"[Scheduler] Skipping {user.phone}, already sent today.")
                continue

            # fetch a random quote
            quote = db.query(Quote).order_by(func.random()).first()
            if not quote:
                logging.warning("[Scheduler] No quotes available in DB.")
                continue

            # send the daily quote
            send_sms(user.phone, quote.text)

            # Update last_sent and log
            user.last_sent = today_utc
            log_entry = MessageLog(phone=user.phone, quote=quote.text, timestamp=datetime.now(timezone.utc))
            db.add(log_entry)
            db.commit()
            logging.info(f"[Scheduler] Sent quote to {user.phone}")

    except Exception as e:
        logging.exception(f"[Scheduler] Error in send_quotes: {e}")
    finally:
        db.close()
    """

# Run send job every minute
scheduler.add_job(send_quotes, "interval", minutes=1)

# Recalc utc_time once per day at 00:05 UTC to handle DST shifts
# scheduler.add_job(recalc_all_user_utc_times, "cron", hour=0, minute=5)

scheduler.start()

if __name__ == "__main__":
    import time
    logging.info("[Scheduler] Started (UTC).")
    while True:
        time.sleep(1)
