# send_sms.py
import os
import logging
from twilio.rest import Client
from datetime import datetime, timezone, timedelta
from Motivator.db import SessionLocal
from Motivator.models import MessageLog

FROM_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
if not FROM_NUMBER:
    raise ValueError("Missing TWILIO_PHONE_NUMBER")

SMS_DISABLED = os.getenv("SMS_DISABLED") == "1"
SMS_DRY_RUN = os.getenv("SMS_DRY_RUN") == "1"
MAX_DAILY_SMS = int(os.getenv("MAX_DAILY_SMS", "3"))

logger = logging.getLogger(__name__)


def _start_of_utc_day():
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc)


def _daily_send_count(db, phone: str) -> int:
    return (
        db.query(MessageLog)
        .filter(
            MessageLog.phone == phone,
            MessageLog.status == "success",
            MessageLog.timestamp >= _start_of_utc_day(),
        )
        .count()
    )


def send_sms(to_number: str, message: str):
    """
    Central SMS send with safety controls.
    """

    # --- Kill switch ---
    if SMS_DISABLED:
        logger.warning("SMS DISABLED — skipping send to %s", to_number)
        return None

    db = SessionLocal()
    try:
        # --- Daily cap ---
        sent_today = _daily_send_count(db, to_number)
        if sent_today >= MAX_DAILY_SMS:
            logger.warning(
                "Daily SMS cap hit for %s (%s/%s)",
                to_number,
                sent_today,
                MAX_DAILY_SMS,
            )
            return None

        # --- Dry run ---
        if SMS_DRY_RUN:
            logger.info("DRY RUN SMS to %s: %s", to_number, message)
            return None

    finally:
        db.close()

    ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

    if not ACCOUNT_SID or not AUTH_TOKEN:
        raise ValueError("Missing Twilio credentials")

    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    try:
        return client.messages.create(
            body=message,
            from_=FROM_NUMBER,
            to=to_number,
        )

    except Exception as e:
        # Log failure
        db = SessionLocal()
        try:
            log = MessageLog(
                phone=to_number,
                quote=message,
                status="failed",
                error=str(e),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
        raise
