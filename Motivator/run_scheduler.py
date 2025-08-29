import logging
import pytz
from datetime import date
from apscheduler.schedulers.blocking import BlockingScheduler
from send_sms import send_sms  # your Twilio wrapper
from log_sms import log_message  # your CSV logger
import random

# --- Setup ---
logging.basicConfig(level=logging.INFO)
scheduler = BlockingScheduler(timezone=pytz.timezone("US/Eastern"))  # pick your TZ

# In-memory tracker to prevent duplicates (simple for MVP)
last_sent = {}

# --- Helpers ---
def get_users():
    """Return active user phone numbers. Later: swap to DB/CSV."""
    return ["+18585313930"]

def get_random_quote():
    """Return a random quote. Later: swap to DB/API."""
    quotes = [
        "Keep going, you're doing great!",
        "Discipline beats motivation.",
        "Small steps every day add up."
    ]
    return random.choice(quotes)

def send_quote(phone):
    """Send a single quote with error handling + logging."""
    # Prevent duplicates (1/day)
    today = date.today().isoformat()
    if last_sent.get(phone) == today:
        logging.info(f"Already sent to {phone} today, skipping.")
        return

    quote = get_random_quote()
    try:
        send_sms(phone, quote)
        log_message(phone, quote, "success")
        last_sent[phone] = today
        logging.info(f"✅ Sent to {phone}: {quote}")
    except Exception as e:
        log_message(phone, quote, "error", str(e))
        logging.error(f"❌ Failed to send to {phone}: {e}")

# --- Scheduler Job ---
@scheduler.scheduled_job("cron", hour=9, minute=0)
def daily_job():
    logging.info("⏱ Running daily job...")
    for phone in get_users():
        send_quote(phone)

# --- Entry Point ---
if __name__ == "__main__":
    logging.info("🌀 Motivator scheduler started (Ctrl+C to stop)")
    scheduler.start()
