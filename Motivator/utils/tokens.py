import secrets
from datetime import datetime, timedelta, timezone
from Motivator.db import SessionLocal
from Motivator.models import SettingsToken

def generate_settings_token(user_id, expires_in_minutes=30):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

    db = SessionLocal()
    try:
        settings_token = SettingsToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(settings_token)
        db.commit()
        return token
    finally:
        db.close()
