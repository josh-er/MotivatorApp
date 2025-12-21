from Motivator.models import User, MessageLog
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

def get_message_logs(limit=100):
    db = SessionLocal()
    try:
        return (
            db.query(MessageLog)
            .order_by(MessageLog.timestamp.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()
