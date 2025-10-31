import os
import time
import datetime
from Motivator.db import SessionLocal
from Motivator.models import User, Quote
from Motivator.send_sms import send_sms  # reuse your Twilio sender
from Motivator.log_sms import log_message as log_sms

CHECK_INTERVAL = 60  # seconds — run every 1 minute

def should_send(user):
    """Check if this user should get a quote right now."""
    now = datetime.datetime.now()
    if not user.time:
        return False

    # If user's preferred time matches current time (to the minute)
    user_hour, user_minute = map(int, user.time.split(":"))
    if now.hour != user_hour or now.minute != user_minute:
        return False

    # Ensure user hasn't received a message today
    if user.last_sent and user.last_sent.date() == now.date():
        return False

    return True

def get_next_quote(session, user):
    """Get the next quote for the user in rotation."""
    quotes = session.query(Quote).all()
    if not quotes:
        return None

    next_index = (user.last_quote_id or 0) % len(quotes)
    return quotes[next_index]

def send_quote_to_user(session, user):
    """Send a quote to one user and log it."""
    quote = get_next_quote(session, user)
    if not quote:
        print(f"[WARN] No quotes available for user {user.phone}")
        return

    # Send the message via Twilio
    sent_ok = send_sms(user.phone, quote.text)
    log_sms(user.phone, quote.text, "success" if sent_ok else "failure")

    if sent_ok:
        user.last_sent = datetime.datetime.now()
        user.last_quote_id = (user.last_quote_id or 0) + 1
        session.commit()
        print(f"[OK] Sent quote to {user.phone}: {quote.text[:40]}...")
    else:
        print(f"[FAIL] Failed to send to {user.phone}")

def run_scheduler():
    """Main loop that checks users and sends quotes."""
    print("[Scheduler] Starting Motivator scheduler...")
    while True:
        session = SessionLocal()
        try:
            users = session.query(User).all()
            for user in users:
                if should_send(user):
                    send_quote_to_user(session, user)
        except Exception as e:
            print(f"[ERROR] Scheduler loop failed: {e}")
        finally:
            session.close()

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_scheduler()
