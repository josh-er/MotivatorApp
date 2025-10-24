# Motivator/test.py

import os
from sqlalchemy import text
from Motivator.db import SessionLocal
from Motivator.models import User, Quote
from Motivator.send_sms import send_sms # assuming your Twilio send function is here

def test_db_connection():
    print("Testing database connection...")
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
        print("Database connection successful!")
    except Exception as e:
        print("Database connection failed:", e)
    finally:
        session.close()


def list_users_and_quotes():
    session = SessionLocal()
    try:
        users = session.query(User).all()
        quotes = session.query(Quote).limit(3).all()
        print(f"\nFound {len(users)} users and {len(quotes)} quotes.")
        for u in users:
            print(f" - User phone: {u.phone}")
        for q in quotes:
            print(f" - Quote: {q.text[:60]}...")
    finally:
        session.close()


def test_twilio_send():
    print("\nTesting Twilio SMS send...")
    to_number = input("Enter your test phone number (in +1xxxxxxxxxx format): ").strip()
    message = "Test message from Motivator"
    try:
        send_sms(to_number, message)
        print("SMS sent successfully!")
    except Exception as e:
        print("SMS failed:", e)


if __name__ == "__main__":
    test_db_connection()
    list_users_and_quotes()
    test_twilio_send()
