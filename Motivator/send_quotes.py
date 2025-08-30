# Motivator/send_quotes.py
import csv
import random
import time
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv
import os
import sqlite3
import tempfile
import shutil
from pathlib import Path
from log_sms import log_message  # use your logger

SENT_LOG_FILE = "sent_log.csv"

def send_quotes():
    load_dotenv()
    TWILIO_SID = os.getenv("TWILIO_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")

    print(f"Checking for users scheduled at {current_time_str}")

    def already_sent_today(phone):
        """Check if we already sent to this phone today."""
        if not Path(SENT_LOG_FILE).exists():
            return False
        with open(SENT_LOG_FILE, newline="") as f:
            reader = csv.reader(f)
            return any(row and row[0].startswith(today_str) and row[1] == phone for row in reader)

    def mark_as_sent(phone, quote, status="success", error=None):
        """Mark a phone number as sent to today + log the result."""
        log_message(phone, quote, status, error)

    def send_quote_to_user(phone, quote):
        try:
            client.messages.create(
                body=quote,
                from_=TWILIO_PHONE_NUMBER,
                to=phone
            )
            print(f"Sent to {phone}: {quote}")
            mark_as_sent(phone, quote, "success")
        except Exception as e:
            print(f"Failed to send to {phone}: {e}")
            mark_as_sent(phone, quote, "error", str(e))

    scheduled_users = []
    with open("submissions.csv", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header row
        for row in reader:
            if len(row) < 2:
                continue

            phone = row[0]
            preferred_time = row[1]
            last_sent = row[2] if len(row) > 2 else ""

            if preferred_time == current_time_str and last_sent != today_str:
                scheduled_users.append((phone, preferred_time, last_sent))

    print(f"Found {len(scheduled_users)} user(s) to message.")

    # Safely update submissions.csv with new last_sent values
    with open("submissions.csv", newline="") as infile, tempfile.NamedTemporaryFile("w", delete=False, newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        header = next(reader, None)
        if header:
            writer.writerow(header)

        for row in reader:
            if len(row) < 2:
                writer.writerow(row)
                continue

            phone, preferred_time = row[0], row[1]
            last_sent = row[2] if len(row) > 2 else ""

            if preferred_time == current_time_str and not already_sent_today(phone):
                # Fetch random quote
                conn = sqlite3.connect("quotes.db")
                cursor = conn.cursor()
                cursor.execute("SELECT text FROM quotes ORDER BY RANDOM() LIMIT 1")
                result = cursor.fetchone()
                quote = result[0] if result else "Stay strong."
                conn.close()

                send_quote_to_user(phone, quote)
                row = [phone, preferred_time, today_str]  # update last_sent

            writer.writerow(row)

    shutil.move(outfile.name, "submissions.csv")
