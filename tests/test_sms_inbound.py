from Motivator.models import User
from tests.conftest import sign_twilio_request


def test_start_unknown_number(client, db, twilio_post):
    resp = twilio_post({"From": "+15559998888", "Body": "START"})

    assert resp.status_code == 200
    assert "download the app" in resp.get_data(as_text=True)
    assert db.query(User).filter_by(phone="+15559998888").first() is None


def test_start_reactivates_opted_out_user(client, db, make_user, sent_sms, twilio_post):
    user = make_user(phone="+15551234567", opted_in=False)

    resp = twilio_post({"From": "+15551234567", "Body": "START"})

    assert resp.status_code == 200
    db.refresh(user)
    assert user.opted_in is True

    # a settings link should have been sent via SMS
    assert len(sent_sms) == 1
    to, message = sent_sms[0]
    assert to == "+15551234567"
    assert "/settings?token=" in message


def test_stop_opts_out_active_user(db, make_user, twilio_post):
    user = make_user(phone="+15551234567", opted_in=True)

    resp = twilio_post({"From": "+15551234567", "Body": "STOP"})

    assert resp.status_code == 200
    db.refresh(user)
    assert user.opted_in is False


def test_forged_request_without_signature_is_rejected(client, make_user):
    make_user(phone="+15551234567", opted_in=True)

    resp = client.post("/sms/inbound", data={"From": "+15551234567", "Body": "STOP"})

    assert resp.status_code == 403
    assert resp.get_json() == {"error": "invalid signature"}


def test_forged_request_with_bad_signature_is_rejected(client, make_user):
    make_user(phone="+15551234567", opted_in=True)

    resp = client.post(
        "/sms/inbound",
        data={"From": "+15551234567", "Body": "STOP"},
        headers={"X-Twilio-Signature": "not-a-real-signature"},
    )

    assert resp.status_code == 403


def test_forged_request_cannot_flip_opt_in_state(client, db, make_user):
    """A forged (unsigned) STOP must not actually change state."""
    user = make_user(phone="+15551234567", opted_in=True)

    client.post("/sms/inbound", data={"From": "+15551234567", "Body": "STOP"})

    db.refresh(user)
    assert user.opted_in is True


def test_unknown_number_arbitrary_body_is_noop(db, twilio_post):
    resp = twilio_post({"From": "+15559998888", "Body": "hello there"})

    assert resp.status_code == 200
    assert "<Message>" not in resp.get_data(as_text=True)
    assert db.query(User).filter_by(phone="+15559998888").first() is None
