# Motivator/scheduler.py
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from Motivator.db import SessionLocal
from Motivator.models import User
from Motivator.send_quotes import send_users
from Motivator.db import engine


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
logger.warning(f"[SCHEDULER] ENGINE URL: {engine.url}")
# -------------------------------------------------
# Scheduling logic
# -------------------------------------------------
def is_user_due(now_utc: datetime, user: User) -> bool:
    if not user.local_time or not user.timezone:
        logger.debug(f"User {user.id} missing local_time or timezone")
        return False

    tz = ZoneInfo(user.timezone)
    local_now = now_utc.astimezone(tz)
    local_today = local_now.date()

    if user.last_sent == local_today:
        logger.debug(f"User {user.id} already sent today ({local_today})")
        return False

    send_hour, send_minute = map(int, user.local_time.split(":"))

    scheduled_local = local_now.replace(
        hour=send_hour,
        minute=send_minute,
        second=0,
        microsecond=0,
    )

    # If worker was down, send late but only once per local day
    return local_now >= scheduled_local

# -------------------------------------------------
# Scheduler loop
# -------------------------------------------------
def run_scheduler():
    logger.info("Motivator Scheduler started — checking every 60 seconds.")
    while True:
        try:
            db = SessionLocal()
            now_utc = datetime.now(timezone.utc)

            users = (
                db.query(User)
                .filter(User.opted_in.is_(True))
                .all()
            )

            due_users = [u for u in users if is_user_due(now_utc, u)]

            if due_users:
                logger.info(
                    f"{len(due_users)} user(s) due — sending quotes"
                )
                send_users(db, due_users)
            else:
                logger.debug("No users due this minute")

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
