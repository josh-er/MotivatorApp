from Motivator.models import User


def test_valid_signup(client, db, sent_sms):
    resp = client.post("/submit", json={
        "phone": "5551234567",
        "local_time": "08:30",
        "timezone": "America/Los_Angeles",
        "consent": True,
    })

    assert resp.status_code == 201
    assert resp.get_json() == {"status": "success", "timezone": "America/Los_Angeles"}

    user = db.query(User).filter_by(phone="+15551234567").first()
    assert user is not None
    assert user.local_time == "08:30"
    assert user.timezone == "America/Los_Angeles"
    assert user.opted_in is True
    assert user.received_compliance is True

    # compliance SMS sent immediately
    assert len(sent_sms) == 1
    to, message = sent_sms[0]
    assert to == "+15551234567"
    assert "subscribed" in message.lower()


def test_duplicate_phone(client, make_user):
    make_user(phone="+15551234567")

    resp = client.post("/submit", json={
        "phone": "5551234567",
        "local_time": "08:30",
        "timezone": "America/Los_Angeles",
        "consent": True,
    })

    assert resp.status_code == 400
    assert resp.get_json() == {"error": "user_exists"}


def test_missing_consent(client, db):
    resp = client.post("/submit", json={
        "phone": "5551234567",
        "local_time": "08:30",
        "timezone": "America/Los_Angeles",
        # no consent field
    })

    assert resp.status_code == 400
    assert resp.get_json() == {"error": "SMS consent is required"}
    assert db.query(User).count() == 0


def test_missing_consent_false(client, db):
    resp = client.post("/submit", json={
        "phone": "5551234567",
        "local_time": "08:30",
        "timezone": "America/Los_Angeles",
        "consent": False,
    })

    assert resp.status_code == 400
    assert resp.get_json() == {"error": "SMS consent is required"}
    assert db.query(User).count() == 0


def test_malformed_local_time(client, db):
    resp = client.post("/submit", json={
        "phone": "5551234567",
        "local_time": "25:99",
        "timezone": "America/Los_Angeles",
        "consent": True,
    })

    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Invalid local_time — expected HH:MM"}
    assert db.query(User).count() == 0


def test_invalid_phone_format(client, db):
    resp = client.post("/submit", json={
        "phone": "123",
        "local_time": "08:30",
        "timezone": "America/Los_Angeles",
        "consent": True,
    })

    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Invalid phone number"}
    assert db.query(User).count() == 0
