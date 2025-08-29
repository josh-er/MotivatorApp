import csv
from datetime import datetime
import os

LOG_FILE = "sent_log.csv"

def log_message(phone, quote, status, error=None):
    """Append SMS send attempt to CSV log."""
    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "phone", "quote", "status", "error"])

        timestamp = datetime.now().isoformat()
        writer.writerow([timestamp, phone, quote, status, error or ""])
