# Motivator/scheduler.py
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from Motivator.db import SessionLocal
from Motivator.models import User
from Motivator.send_now import send_now

CHECK_INTERVAL = 60  # seconds — check every minute

# -------------------------------------------------
# Logging setup
# -------------------------------------------------
log_handler = RotatingFileHandler("scheduler.log", maxBytes=1_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[log_handler, logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Scheduler loop
# -------------------------------------------------
def run_scheduler():
    logger.info("Motivator Scheduler started — checking every 60 seconds.")
    while True:
        try:
            db = SessionLocal()
            now = datetime.now().strftime("%H:%M")
            due_users = db.query(User).filter(User.time == now).all()

            if due_users:
                logger.info(f"{len(due_users)} user(s) scheduled for {now}, triggering send_now()...")
                send_now()
            else:
                logger.debug(f"No users scheduled for {now}")

        except Exception as e:
            logger.exception(f"Scheduler loop failed: {e}")
        finally:
            db.close()

        time.sleep(CHECK_INTERVAL)

# -------------------------------------------------
# Entry point
# -------------------------------------------------
if __name__ == "__main__":
    run_scheduler()
