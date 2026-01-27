from datetime import datetime, timezone
from Motivator.models import EventLog


def log_event(db, *, user_id, event_type, source):
    db.add(
        EventLog(
            user_id=user_id,
            event_type=event_type,
            source=source,
            created_at=datetime.now(timezone.utc),
        )
    )