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

def get_message_logs(status=None, phone=None, limit=100, since_date=None):
    db = SessionLocal()
    try:
        q = db.query(MessageLog)

        if status:
            q = q.filter(MessageLog.status == status)

        if phone:
            q = q.filter(MessageLog.phone.contains(phone))

        if since_date:
            q = q.filter(MessageLog.timestamp >= since_date)

        return (
            q.order_by(MessageLog.timestamp.desc())
             .limit(limit)
             .all()
        )
    finally:
        db.close()