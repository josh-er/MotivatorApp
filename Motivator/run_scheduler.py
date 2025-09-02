# Motivator/run_scheduler.py
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from send_quotes import send_quotes  # your main SMS + logging function
import pytz

# --- Setup ---
logging.basicConfig(level=logging.INFO)
scheduler = BlockingScheduler(timezone=pytz.timezone("US/Eastern"))

# --- Scheduler Job ---
@scheduler.scheduled_job("interval", minutes=1)  # for testing locally
def daily_job():
    logging.info("⏱ Running scheduled send_quotes()")
    send_quotes()

# --- Entry Point ---
if __name__ == "__main__":
    logging.info("🌀 Motivator scheduler started (Ctrl+C to stop)")
    scheduler.start()
