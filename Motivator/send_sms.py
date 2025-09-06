# send_sms.py
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Grab credentials once at import time
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Fail fast if any are missing
if not ACCOUNT_SID or not AUTH_TOKEN or not FROM_NUMBER:
    raise ValueError(
        "Missing Twilio environment variables. "
        "Check your .env file for TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER."
    )

# Initialize Twilio client once
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_sms(to_number: str, message: str):
    """Send an SMS using Twilio."""
    return client.messages.create(
        body=message,
        from_=FROM_NUMBER,
        to=to_number
    )
