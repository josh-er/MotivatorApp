"""
Test env setup MUST happen before any `Motivator.*` module is imported.

`.env` in the repo root points DATABASE_URL at the real Postgres database and
has SMS_DISABLED=0 — both db.py and app.py call load_dotenv() at import time,
which by default does NOT override already-set environment variables. So by
setting these here, at module load (before any Motivator import below), we
guarantee the real DB and real Twilio are never touched, regardless of what's
in .env.
"""
import os
import tempfile

_TMP_DIR = tempfile.mkdtemp(prefix="motivator_test_")
_DB_PATH = os.path.join(_TMP_DIR, "test.db")

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ["TWILIO_ACCOUNT_SID"] = "ACtest0000000000000000000000000"
os.environ["TWILIO_AUTH_TOKEN"] = "test_auth_token"
os.environ["TWILIO_PHONE_NUMBER"] = "+15005550006"
os.environ["SMS_DISABLED"] = "1"
os.environ["SMS_DRY_RUN"] = "0"
os.environ["ADMIN_KEY"] = "test-admin-key"
os.environ["ADMIN_PASSWORD"] = "test-admin-password"
os.environ["FLASK_SECRET_KEY"] = "test-flask-secret"
os.environ["BASE_URL"] = "http://localhost:5000"
os.environ.pop("RENDER", None)
os.environ.pop("FLASK_ENV", None)

import pytest
from twilio.request_validator import RequestValidator

import Motivator.app as app_module
from Motivator.db import engine
from Motivator.models import Base, User, Quote, SettingsToken
from Motivator.db import SessionLocal

app_module.app.config["TESTING"] = True


@pytest.fixture(autouse=True)
def reset_db():
    """Fresh schema before every test — full isolation, no cross-test state."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def reset_login_rate_limit():
    """_login_attempts is an in-process module-level dict — clear it so one
    test's failed logins don't bleed into the next."""
    app_module._login_attempts.clear()
    yield
    app_module._login_attempts.clear()


@pytest.fixture(autouse=True)
def sent_sms(monkeypatch):
    """Replace every module-local `send_sms` reference with a recorder, so
    tests never attempt a real Twilio call and can assert on message content.
    Each of these modules did `from Motivator.send_sms import send_sms`, so
    each holds its own binding that must be patched separately."""
    import Motivator.admin.routes as admin_routes
    import Motivator.send_quotes as send_quotes

    calls = []

    def fake_send_sms(to_number, message):
        calls.append((to_number, message))
        return None

    monkeypatch.setattr(app_module, "send_sms", fake_send_sms)
    monkeypatch.setattr(admin_routes, "send_sms", fake_send_sms)
    monkeypatch.setattr(send_quotes, "send_sms", fake_send_sms)
    return calls


@pytest.fixture
def client():
    return app_module.app.test_client()


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_user(db):
    """Insert a user directly (bypassing /submit) and return it, already
    committed and refreshed."""

    def _make(phone="+15551234567", local_time="09:00", timezone="America/New_York",
              opted_in=True, received_compliance=True, last_sent=None, cycle=1):
        user = User(
            phone=phone,
            local_time=local_time,
            timezone=timezone,
            opted_in=opted_in,
            received_compliance=received_compliance,
            last_sent=last_sent,
            cycle=cycle,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture
def make_quote(db):
    def _make(text="Keep going."):
        quote = Quote(text=text)
        db.add(quote)
        db.commit()
        db.refresh(quote)
        return quote

    return _make


def sign_twilio_request(path: str, form: dict, auth_token: str = None) -> str:
    """Compute a valid X-Twilio-Signature for a POST to `path` with `form`
    as the body, matching how app.py's validate_twilio_request() rebuilds
    the URL (BASE_URL + request.path)."""
    auth_token = auth_token or os.environ["TWILIO_AUTH_TOKEN"]
    base_url = os.environ["BASE_URL"].rstrip("/")
    validator = RequestValidator(auth_token)
    return validator.compute_signature(base_url + path, form)


@pytest.fixture
def twilio_post(client):
    """POST to /sms/inbound with a valid Twilio signature attached."""

    def _post(form, path="/sms/inbound"):
        signature = sign_twilio_request(path, form)
        return client.post(path, data=form, headers={"X-Twilio-Signature": signature})

    return _post
