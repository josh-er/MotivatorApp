# scripts/backfill_timezones.py
from datetime import datetime
from zoneinfo import ZoneInfo
from Motivator.db import SessionLocal
from Motivator.models import User

DEFAULT_TZ = "America/New_York"

'''
def compute_utc(local_time_str, tz_str):
    tz = ZoneInfo(tz_str)
    today_local = datetime.now(tz).date()
    dt_local = datetime.combine(today_local, datetime.strptime(local_time_str, "%H:%M").time(), tzinfo=tz)
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
    return dt_utc.strftime("%H:%M")
'''

def backfill():
    db = SessionLocal()
    users = db.query(User).all()
    updated = 0
    for u in users:
        # if timezone not set, assume DEFAULT_TZ and use legacy time column if present
        if not u.local_time:
            u.local_time = u.time or None
        if not u.timezone:
            u.timezone = DEFAULT_TZ
    db.commit()
    db.close()
    print(f"Backfill complete. Updated {updated} users.")

if __name__ == "__main__":
    backfill()
