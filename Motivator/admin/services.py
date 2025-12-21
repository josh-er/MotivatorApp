from Motivator.models import User
from Motivator.db import SessionLocal

def get_all_users():
    db = SessionLocal()
    try:
        return (
            db.query(User)
            .order_by(User.phone.asc())
            .all()
        )
    finally:
        db.close()
