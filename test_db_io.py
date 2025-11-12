# test_db_io.py
import sys
import os
from datetime import date
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Motivator.db import SessionLocal
from Motivator.models import User, Quote

def test_db_io():
    session = SessionLocal()

    try:
        print("\n[1] Creating test user...")
        user = User(phone="9999999999", time="12:00", last_sent=None, cycle=1)
        session.add(user)
        session.commit()
        print(f"User created with id={user.id}")

        print("\n[2] Reading test user...")
        found = session.query(User).filter_by(phone="9999999999").first()
        if found:
            print(f"Found user: id={found.id}, time={found.time}, cycle={found.cycle}")
        else:
            raise Exception("User not found after insert")

        print("\n[3] Updating test user...")
        found.last_sent = date.today()
        session.commit()
        print("Updated last_sent successfully")

        print("\n[4] Deleting test user...")
        session.delete(found)
        session.commit()
        print("User deleted successfully")

        print("\nAll DB I/O operations completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        session.rollback()

    finally:
        session.close()


if __name__ == "__main__":
    test_db_io()
