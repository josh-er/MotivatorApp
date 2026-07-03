from datetime import datetime
from zoneinfo import ZoneInfo
from Motivator.models import User

def create_user(phone: str, local_time: str | None, timezone: str | None):
    """
    Canonical user creation.
    local_time: 'HH:MM'
    timezone: IANA tz string (e.g. America/New_York)
    """
    if not local_time:
        local_time = "09:00"

    if not timezone:
        timezone = "America/New_York"

    user_time_naive = datetime.strptime(local_time, "%H:%M")

    user_tz = ZoneInfo(timezone)
    utc = ZoneInfo("UTC")

    today_local = datetime.now(user_tz).date()
    dt_local = datetime.combine(today_local, user_time_naive.time(), tzinfo=user_tz)
    dt_utc = dt_local.astimezone(utc)

    return User(
        phone=phone,
        local_time=local_time,
        timezone=timezone,
        # time is a legacy field, noting for reference
        time=dt_utc.time().isoformat(),
        last_sent=None
    )
