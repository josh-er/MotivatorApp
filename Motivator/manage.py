# manage.py
import argparse
from .db import SessionLocal
from .models import User, Quote
from .send_quotes import send_now

def add_user(phone, schedule_time=None):
    db = SessionLocal()
    user = User(phone=phone, time=schedule_time)
    db.add(user)
    db.commit()
    db.close()
    print(f"Added user {phone} with schedule {schedule_time}")

def list_users():
    db = SessionLocal()
    users = db.query(User).all()
    if not users:
        print("No users found.")
    else:
        for u in users:
            print(f"- {u.phone} @ {u.time}")
    db.close()

def remove_user(phone):
    db = SessionLocal()
    user = db.query(User).filter_by(phone=phone).first()
    if not user:
        print(f"No user found with phone {phone}")
    else:
        db.delete(user)
        db.commit()
        print(f"Removed user {phone}")
    db.close()

def list_quotes():
    db = SessionLocal()
    quotes = db.query(Quote).all()
    if not quotes:
        print("No quotes found.")
    else:
        for q in quotes:
            print(f"- {q.text}")
    db.close()

def main():
    parser = argparse.ArgumentParser(description="Manage Motivator users and quotes")
    subparsers = parser.add_subparsers(dest="command")

    # user commands
    add_parser = subparsers.add_parser("add", help="Add a user")
    add_parser.add_argument("phone", type=str, help="Phone number")
    add_parser.add_argument("schedule_time", nargs="?", default=None, help="Optional schedule time")

    subparsers.add_parser("list", help="List all users")

    remove_parser = subparsers.add_parser("remove", help="Remove a user")
    remove_parser.add_argument("phone", type=str, help="Phone number")

    # quote commands
    subparsers.add_parser("list_quotes", help="List all quotes")

    # send_now command
    send_now_parser = subparsers.add_parser("send_now", help="Send a quote immediately to a specific user")
    send_now_parser.add_argument("phone", type=str, help="Phone number")

    args = parser.parse_args()

    if args.command == "add":
        add_user(args.phone, args.schedule_time)
    elif args.command == "list":
        list_users()
    elif args.command == "remove":
        remove_user(args.phone)
    elif args.command == "list_quotes":
        list_quotes()
    elif args.command == "send_now":
        send_now(args.phone)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
