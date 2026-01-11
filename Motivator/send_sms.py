# send_sms.py
import os
from twilio.rest import Client
from dotenv import load_dotenv
from datetime import datetime, timezone
from Motivator.db import SessionLocal
from Motivator.models import MessageLog

# Load environment variables from .env
load_dotenv()

FROM_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
if not FROM_NUMBER:
    raise ValueError("Missing TWILIO_PHONE_NUMBER in .env")

def send_sms(to_number: str, message: str):
    """Send an SMS using Twilio. Logs any failure to the database."""
    ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

    if not ACCOUNT_SID or not AUTH_TOKEN:
        raise ValueError(
            "Missing Twilio environment variables. "
            "Check your .env file for TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
        )

    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    try:
        return client.messages.create(
            body=message,
            from_=FROM_NUMBER,
            to=to_number
        )
    except Exception as e:
        # Log the failure in MessageLog
        db = SessionLocal()
        try:
            log = MessageLog(
                phone=to_number,
                quote=message,
                status="failed",
                error=str(e),
                timestamp=datetime.now(timezone.utc)
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
        # Re-raise so the caller knows it failed
        raise
