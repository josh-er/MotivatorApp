import csv
import random
import logging
from datetime import datetime
from send_sms import send_sms  # Twilio wrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
TESTING = True # Set False in production
TEST_NUMBER = "+18585313930"  # Your number for testing (set None to disable override)

def send_quotes():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    today = now.date()

    logger.info("Running scheduled send_quotes()")
    logger.info(f"Checking for users scheduled at {current_time}")

    with open("submissions.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        users = [row for row in reader if row["time"] == current_time]

    logger.info(f"Found {len(users)} user(s) to message.")

    if not users:
        return

    # Load quotes
    with open("quotes.txt") as f:
        quotes = [line.strip() for line in f if line.strip()]

    for user in users:
        phone = user["phone"]
        last_sent = user.get("last_sent", "").strip()

        # Testing override: only send to TEST_NUMBER
        if TEST_NUMBER and phone != TEST_NUMBER:
            logger.info(f"Skipping {phone}, not TEST_NUMBER override.")
            continue

        # Production safeguard: don't send more than once per day
        if not TESTING and last_sent:
            try:
                last_date = datetime.strptime(last_sent, "%Y-%m-%d").date()
                if last_date == today:
                    logger.info(f"Skipping {phone}, already sent today.")
                    continue
            except ValueError:
                pass

        # Pick and send a random quote
        quote = random.choice(quotes)
        send_sms(phone, quote)
        logger.info(f"Sent to {phone}: {quote}")

        # Update last_sent in CSV
        user["last_sent"] = today.strftime("%Y-%m-%d")

    # Write updates back to CSV
    fieldnames = ["phone", "time", "last_sent"]
    with open("submissions.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)
