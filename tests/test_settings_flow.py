import re
from datetime import datetime, timedelta, timezone

from Motivator.models import SettingsToken
from Motivator.utils.tokens import hash_token

TOKEN_RE = re.compile(r"/settings\?token=([\w\-]+)")


def _extract_token(message):
    m = TOKEN_RE.search(message)
    assert m, f"no settings token link found in message: {message!r}"
    return m.group(1)


def test_request_settings_link(client, db, make_user, sent_sms):
    make_user(phone="+15551234567")

    resp = client.post("/request-settings-link", json={"phone": "5551234567"})

    assert resp.status_code == 200
    assert resp.get_json() == {
        "status": "ok",
        "message": "If that phone number is registered, a settings link has been sent via SMS.",
    }
    # link is never in the response body
    assert "token" not in resp.get_data(as_text=True)

    assert len(sent_sms) == 1
    to, message = sent_sms[0]
    assert to == "+15551234567"
    raw_token = _extract_token(message)

    # stored hashed, not in plaintext
    stored = db.query(SettingsToken).one()
    assert stored.token == hash_token(raw_token)
    assert stored.token != raw_token
    assert stored.used is False


def test_get_settings_valid_token(client, make_user, sent_sms):
    make_user(phone="+15551234567", local_time="07:15", timezone="America/Denver")
    client.post("/request-settings-link", json={"phone": "5551234567"})
    raw_token = _extract_token(sent_sms[0][1])

    resp = client.get(f"/settings?token={raw_token}")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "07:15" in body
    assert 'value="America/Denver" selected' in body


def test_get_settings_expired_token(client, db, make_user, sent_sms):
    make_user(phone="+15551234567")
    client.post("/request-settings-link", json={"phone": "5551234567"})
    raw_token = _extract_token(sent_sms[0][1])

    token_row = db.query(SettingsToken).one()
    token_row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db.commit()

    resp = client.get(f"/settings?token={raw_token}")

    assert resp.status_code == 200
    assert "expired" in resp.get_data(as_text=True).lower()


def test_get_settings_used_token(client, db, make_user, sent_sms):
    make_user(phone="+15551234567")
    client.post("/request-settings-link", json={"phone": "5551234567"})
    raw_token = _extract_token(sent_sms[0][1])

    token_row = db.query(SettingsToken).one()
    token_row.used = True
    db.commit()

    resp = client.get(f"/settings?token={raw_token}")

    assert resp.status_code == 200
    assert "already been used" in resp.get_data(as_text=True).lower()


def test_post_settings_valid_payload(client, db, make_user, sent_sms):
    user = make_user(phone="+15551234567", local_time="07:15", timezone="America/Denver")
    client.post("/request-settings-link", json={"phone": "5551234567"})
    raw_token = _extract_token(sent_sms[0][1])

    resp = client.post("/settings", json={
        "token": raw_token,
        "local_time": "18:00",
        "timezone": "America/Chicago",
    })

    assert resp.status_code == 200
    assert resp.get_json()["local_time"] == "18:00"
    assert resp.get_json()["timezone"] == "America/Chicago"

    db.refresh(user)
    assert user.local_time == "18:00"
    assert user.timezone == "America/Chicago"

    token_row = db.query(SettingsToken).one()
    assert token_row.used is True


def test_post_settings_replayed_token(client, make_user, sent_sms):
    make_user(phone="+15551234567")
    client.post("/request-settings-link", json={"phone": "5551234567"})
    raw_token = _extract_token(sent_sms[0][1])

    first = client.post("/settings", json={
        "token": raw_token,
        "local_time": "18:00",
        "timezone": "America/Chicago",
    })
    assert first.status_code == 200

    replay = client.post("/settings", json={
        "token": raw_token,
        "local_time": "19:00",
        "timezone": "America/Chicago",
    })
    assert replay.status_code == 403
