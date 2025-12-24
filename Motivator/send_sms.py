# send_sms.py
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def send_sms(to_number: str, message: str):
    """Send an SMS using Twilio, safely initializing client inside the function."""
    ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

    if not ACCOUNT_SID or not AUTH_TOKEN or not FROM_NUMBER:
        raise ValueError(
            "Missing Twilio environment variables. "
            "Check your .env file for TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER."
        )

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    return client.messages.create(
        body=message,
        from_=FROM_NUMBER,
        to=to_number
    )