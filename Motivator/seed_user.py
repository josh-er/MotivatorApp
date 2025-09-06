# Motivator/seed_user.py
from db import SessionLocal
from models import User

def seed():
    db = SessionLocal()
    try:
        # Replace with your own phone and preferred time
        test_user = User(
            phone="+18585313930",   # your number
            time="00:07",           # use a near-future HH:MM for testing
            last_sent=None
        )

        # Check if already exists
        existing = db.query(User).filter_by(phone=test_user.phone).first()
        if existing:
            print(f"User {test_user.phone} already exists. Updating time to {test_user.time}.")
            existing.time = test_user.time
            existing.last_sent = None
        else:
            db.add(test_user)

        db.commit()
        print("User seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
