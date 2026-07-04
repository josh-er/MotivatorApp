import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADMIN_PASSWORD = "test-admin-password"  # matches conftest.py's ADMIN_PASSWORD env var


def _login(client, password=ADMIN_PASSWORD):
    return client.post("/admin/login", data={"password": password})


def test_login_wrong_password_does_not_authenticate(client):
    resp = _login(client, password="not-the-password")
    assert resp.status_code == 200  # re-renders login form, no redirect

    # confirm session was never marked admin
    follow_up = client.get("/admin/users")
    assert follow_up.status_code == 302
    assert "/admin/login" in follow_up.headers["Location"]


def test_login_correct_password_authenticates(client):
    resp = _login(client)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/admin/users")

    follow_up = client.get("/admin/users")
    assert follow_up.status_code == 200


def test_sixth_login_attempt_is_rate_limited(client):
    for _ in range(5):
        resp = _login(client, password="wrong")
        assert resp.status_code == 200

    sixth = _login(client, password="wrong")
    assert sixth.status_code == 429

    # even the correct password is rejected once rate-limited
    still_limited = _login(client, password=ADMIN_PASSWORD)
    assert still_limited.status_code == 429


def _get_csrf_token(client):
    """Logs in and pulls the csrf_token the context processor stashed in
    session when /admin/users was rendered."""
    _login(client)
    client.get("/admin/users")
    with client.session_transaction() as sess:
        return sess["csrf_token"]


def test_csrf_rejected_without_token(client, make_user):
    user = make_user(phone="+15551234567")
    _login(client)

    resp = client.post(f"/admin/users/delete/{user.id}", data={})
    assert resp.status_code == 400
    assert "csrf" in resp.get_data(as_text=True).lower()


def test_csrf_rejected_with_wrong_token(client, make_user):
    user = make_user(phone="+15551234567")
    _login(client)

    resp = client.post(f"/admin/users/delete/{user.id}", data={"csrf_token": "bogus"})
    assert resp.status_code == 400


def test_csrf_accepted_with_valid_token(client, db, make_user):
    from Motivator.models import User

    user = make_user(phone="+15551234567")
    token = _get_csrf_token(client)

    resp = client.post(
        f"/admin/users/delete/{user.id}",
        data={"csrf_token": token},
    )
    assert resp.status_code == 302
    assert db.query(User).filter_by(id=user.id).first() is None


def _run_app_import_check(extra_env):
    env = os.environ.copy()
    env.update({
        "RENDER": "1",
        "DATABASE_URL": "postgresql://user:pass@localhost/nonexistent_db_for_route_check",
        "TWILIO_ACCOUNT_SID": "ACtest0000000000000000000000000",
        "TWILIO_AUTH_TOKEN": "test_auth_token",
        "TWILIO_PHONE_NUMBER": "+15005550006",
        "SMS_DISABLED": "1",
        "ADMIN_KEY": "test-admin-key",
        "ADMIN_PASSWORD": "test-admin-password",
        "FLASK_SECRET_KEY": "test-flask-secret",
        "BASE_URL": "http://localhost:5000",
    })
    env.update(extra_env)

    script = (
        "import Motivator.app as m\n"
        "rules = {r.rule for r in m.app.url_map.iter_rules()}\n"
        "assert '/debug/users' not in rules, rules\n"
        "assert '/init-db' not in rules, rules\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result


def test_debug_routes_blocked_in_production():
    result = _run_app_import_check({})
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    assert "OK" in result.stdout
