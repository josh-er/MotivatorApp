from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from Motivator.models import SentQuote, User
from Motivator.scheduler import is_user_due
from Motivator.send_quotes import send_quote_to_user

# Fixed instant: 15:30 UTC on 2026-07-03 == 11:30 local in America/New_York (EDT, UTC-4).
NOW_UTC = datetime(2026, 7, 3, 15, 30, tzinfo=timezone.utc)
TODAY_NY = date(2026, 7, 3)


def test_is_user_due_when_scheduled_time_has_passed(make_user):
    user = make_user(local_time="09:00", timezone="America/New_York", last_sent=None)
    assert is_user_due(NOW_UTC, user) is True


def test_is_user_due_false_when_scheduled_time_not_reached(make_user):
    user = make_user(local_time="20:00", timezone="America/New_York", last_sent=None)
    assert is_user_due(NOW_UTC, user) is False


def test_is_user_due_false_when_already_sent_today(make_user):
    user = make_user(local_time="09:00", timezone="America/New_York", last_sent=TODAY_NY)
    assert is_user_due(NOW_UTC, user) is False


def test_correct_users_selected_at_delivery_time(db, make_user):
    due_user = make_user(phone="+15551110001", local_time="09:00",
                          timezone="America/New_York", opted_in=True, last_sent=None)
    not_due_user = make_user(phone="+15551110002", local_time="20:00",
                              timezone="America/New_York", opted_in=True, last_sent=None)
    opted_out_user = make_user(phone="+15551110003", local_time="09:00",
                                timezone="America/New_York", opted_in=False, last_sent=None)

    active_users = db.query(User).filter(User.opted_in.is_(True)).all()
    # opted-out user must never even reach the is_user_due check
    assert opted_out_user not in active_users

    due = [u for u in active_users if is_user_due(NOW_UTC, u)]

    assert [u.id for u in due] == [due_user.id]
    assert not_due_user not in due


def test_last_sent_prevents_duplicate_send(db, make_user, make_quote, sent_sms):
    user = make_user(local_time="09:00", timezone="America/New_York", last_sent=None)
    make_quote("Keep going.")

    result1 = send_quote_to_user(db, user)
    assert result1 == "sent"
    assert len(sent_sms) == 1

    db.refresh(user)
    assert user.last_sent == datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York")).date()

    result2 = send_quote_to_user(db, user)
    assert result2 == "already_sent"
    assert len(sent_sms) == 1  # no second SMS

    assert db.query(SentQuote).filter_by(user_id=user.id).count() == 1


def test_opted_out_users_excluded_from_active_query(db, make_user):
    make_user(phone="+15551110004", opted_in=False)
    make_user(phone="+15551110005", opted_in=True)

    active_users = db.query(User).filter(User.opted_in.is_(True)).all()

    assert len(active_users) == 1
    assert active_users[0].phone == "+15551110005"
