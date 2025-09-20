# seed_data.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User, Quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "motivator.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def add_user(phone: str, time: str):
    """
    Add a user to the database.
    :param phone: Phone number in E.164 format (e.g., +15555555555)
    :param time: Daily send time in "HH:MM" 24-hour format
    """
    session = SessionLocal()
    try:
        user = User(phone=phone, time=time)
        session.add(user)
        session.commit()
        print(f"Added user {phone} with time {time}")
    except Exception as e:
        session.rollback()
        print(f"Error adding user {phone}: {e}")
    finally:
        session.close()


def add_quote(text: str):
    """
    Add a motivational quote to the database.
    :param text: Quote text
    """
    session = SessionLocal()
    try:
        quote = Quote(text=text)
        session.add(quote)
        session.commit()
        print(f"Added quote: {text[:50]}...")
    except Exception as e:
        session.rollback()
        print(f"Error adding quote: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("Motivator Seeder")
    print("Options:")
    print("1. Add User")
    print("2. Add Quote")
    choice = input("Select option: ")

    if choice == "1":
        phone = input("Enter phone number (E.164, e.g. +15555555555): ")
        time = input("Enter time (HH:MM, 24h): ")
        add_user(phone, time)

    elif choice == "2":
        text = input("Enter quote text: ")
        add_quote(text)

    else:
        print("Invalid choice")
