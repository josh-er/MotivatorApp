from apscheduler.schedulers.blocking import BlockingScheduler
from send_quotes import send_quotes  # Make sure your logic is inside a function
import logging

# Setup logging (optional)
logging.basicConfig()
scheduler = BlockingScheduler()

# Run once per minute
@scheduler.scheduled_job('interval', minutes=1)
def scheduled_job():
    print("⏱ Running scheduled send_quotes()")
    send_quotes()

if __name__ == "__main__":
    print("🌀 Motivator scheduler started (Ctrl+C to stop)")
    scheduler.start()
