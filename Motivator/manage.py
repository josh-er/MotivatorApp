# manage.py
import argparse
import re
from datetime import datetime
from db import SessionLocal, engine
from models import User
from db import engine
print("DB path:", engine.url)


def validate_phone(phone: str) -> str:
    """Ensure phone is in E.164 format (e.g., +15551234567)."""
    if not re.match(r"^\+\d{10,15}$", phone):
        raise ValueError("Phone must be in E.164 format (e.g., +15551234567).")
    return phone

def validate_time(time_str: str) -> str:
    """Ensure time is in HH:MM 24-hour format."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return time_str
    except ValueError:
        raise ValueError("Time must be in HH:MM (24-hour) format, e.g., 09:30 or 18:45.")

def add_user(phone, schedule_time):
    db = SessionLocal()
    try:
        phone = validate_phone(phone)
        schedule_time = validate_time(schedule_time)

        # check if exists
        existing = db.query(User).filter(User.phone == phone).first()
        if existing:
            print(f"⚠️ User with phone {phone} already exists.")
            return

        user = User(phone=phone, time=schedule_time)
        db.add(user)
        db.commit()
        print(f"Added user {phone} at {schedule_time}")
    except ValueError as e:
        print(f"{e}")
    finally:
        db.close()

def remove_user(phone):
    db = SessionLocal()
    try:
        phone = validate_phone(phone)
        user = db.query(User).filter(User.phone == phone).first()
        if user:
            db.delete(user)
            db.commit()
            print(f"Removed user {phone}")
        else:
            print(f"⚠️ No user found with phone {phone}")
    except ValueError as e:
        print(f"{e}")
    finally:
        db.close()

def list_users():
    session = SessionLocal()
    users = session.query(User).all()
    if not users:
        print("No users found.")
    else:
        print("Users:")
        for u in users:
            # Grab all attributes for inspection
            attrs = {c.name: getattr(u, c.name) for c in u.__table__.columns}
            print(attrs)
    session.close()

def main():
    parser = argparse.ArgumentParser(description="Manage users in Motivator DB")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add", help="Add a new user")
    add_parser.add_argument("phone", help="Phone number (E.164 format, e.g., +15551234567)")
    add_parser.add_argument("schedule_time", help="Time in HH:MM (24h format)")

    # remove
    remove_parser = subparsers.add_parser("remove", help="Remove a user")
    remove_parser.add_argument("phone", help="Phone number to remove")

    # list
    subparsers.add_parser("list", help="List all users")

    args = parser.parse_args()

    if args.command == "add":
        add_user(args.phone, args.schedule_time)
    elif args.command == "remove":
        remove_user(args.phone)
    elif args.command == "list":
        list_users()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
