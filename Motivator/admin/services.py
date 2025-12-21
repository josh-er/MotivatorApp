from Motivator.models import User
from Motivator.db import db

def get_all_users():
    return (
        db.session.query(User)
        .order_by(User.phone.asc())
        .all()
    )
