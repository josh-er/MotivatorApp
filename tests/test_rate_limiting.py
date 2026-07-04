from datetime import datetime, timedelta, timezone

from Motivator.models import SettingsToken


def test_second_settings_link_request_within_30min_is_429(client, make_user, sent_sms):
    make_user(phone="+15551234567")

    first = client.post("/request-settings-link", json={"phone": "5551234567"})
    assert first.status_code == 200

    second = client.post("/request-settings-link", json={"phone": "5551234567"})
    assert second.status_code == 429
    assert "minute" in second.get_json()["error"].lower()

    # only the first SMS went out
    assert len(sent_sms) == 1


def test_settings_link_request_after_30min_window_succeeds_and_invalidates_prior(
    client, db, make_user, sent_sms
):
    make_user(phone="+15551234567")

    first = client.post("/request-settings-link", json={"phone": "5551234567"})
    assert first.status_code == 200

    old_token = db.query(SettingsToken).one()
    old_token.created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=31)
    db.commit()

    third = client.post("/request-settings-link", json={"phone": "5551234567"})
    assert third.status_code == 200
    assert len(sent_sms) == 2

    db.refresh(old_token)
    assert old_token.used is True  # invalidated by the new request

    tokens = db.query(SettingsToken).all()
    assert len(tokens) == 2
    new_token = [t for t in tokens if t.id != old_token.id][0]
    assert new_token.used is False


def test_second_start_reactivation_within_30min_is_rate_limited(
    client, db, make_user, sent_sms, twilio_post
):
    user = make_user(phone="+15551234567", opted_in=False)

    first = twilio_post({"From": "+15551234567", "Body": "START"})
    assert first.status_code == 200
    db.refresh(user)
    assert user.opted_in is True
    assert len(sent_sms) == 1  # settings link sent once

    # opt back out (simulating STOP) so the guard `if not user.opted_in`
    # is reachable again for a second START within the same window
    user.opted_in = False
    db.commit()

    second = twilio_post({"From": "+15551234567", "Body": "START"})
    assert second.status_code == 200
    db.refresh(user)
    assert user.opted_in is True  # still re-activates...

    # ...but no second settings-link SMS, and no second token
    assert len(sent_sms) == 1
    assert db.query(SettingsToken).count() == 1
