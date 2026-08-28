import os
import hmac
import logging
import threading
import time
from flask import Flask, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from Motivator.db import SessionLocal, engine, IS_PRODUCTION
from Motivator.user_service import create_user
from Motivator.models import User, SettingsToken
from Motivator.admin.routes import admin_bp, settings_bp
from Motivator.send_quotes import send_quote_to_user, send_compliance
from dotenv import load_dotenv
from Motivator.utils.tokens import generate_settings_token
from Motivator.utils.phone import normalize_phone
from Motivator.send_sms import send_sms
from Motivator.event_logger import log_event

load_dotenv()

ADMIN_KEY = os.getenv("ADMIN_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

logger = logging.getLogger(__name__)

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if IS_PRODUCTION:
    # Never fall back to a hardcoded secret/password in production — fail
    # loudly at startup instead of silently running with a known default
    # that would let anyone forge an admin session or log in outright.
    if not FLASK_SECRET_KEY:
        raise RuntimeError(
            "FLASK_SECRET_KEY is missing in production. Refusing to start "
            "with a hardcoded fallback secret key."
        )
    if not ADMIN_PASSWORD:
        raise RuntimeError(
            "ADMIN_PASSWORD is missing in production. Refusing to start "
            "with a hardcoded fallback admin password."
        )
else:
    FLASK_SECRET_KEY = FLASK_SECRET_KEY or "dev-secret"
    ADMIN_PASSWORD = ADMIN_PASSWORD or "testpass"

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.register_blueprint(admin_bp)
app.register_blueprint(settings_bp)

def require_admin(req):
    if not ADMIN_KEY:
        return False
    provided = req.headers.get("X-Admin-Key") or ""
    return hmac.compare_digest(provided, ADMIN_KEY)


# --- Admin login rate limiting ---
# In-process failed-attempt counter, keyed by client IP. Not persisted or
# shared across workers — Render's gunicorn config runs --workers=2, so each
# worker tracks independently, meaning the effective ceiling is up to
# LOGIN_MAX_ATTEMPTS per worker rather than a hard global cap. Accepted as a
# lightweight stopgap for a single shared admin password rather than adding a
# new DB table; revisit with a persisted counter if this needs to be airtight.
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutes

_login_attempts = {}
_login_attempts_lock = threading.Lock()


def _client_ip(req):
    forwarded = req.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return req.remote_addr or "unknown"


def _login_rate_limited(ip):
    now = time.time()
    with _login_attempts_lock:
        attempts = [t for t in _login_attempts.get(ip, []) if now - t < LOGIN_WINDOW_SECONDS]
        _login_attempts[ip] = attempts
        return len(attempts) >= LOGIN_MAX_ATTEMPTS


def _record_login_failure(ip):
    with _login_attempts_lock:
        _login_attempts.setdefault(ip, []).append(time.time())


def _clear_login_attempts(ip):
    with _login_attempts_lock:
        _login_attempts.pop(ip, None)


def validate_twilio_request(req):
    """Verify the request actually came from Twilio using the X-Twilio-Signature
    header. Fails closed: missing/misconfigured auth token or a bad/missing
    signature is treated as invalid."""
    if not TWILIO_AUTH_TOKEN:
        logger.error("TWILIO_AUTH_TOKEN not set — rejecting inbound SMS webhook")
        return False

    signature = req.headers.get("X-Twilio-Signature", "")
    if not signature:
        return False

    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    url = BASE_URL.rstrip("/") + req.path
    return validator.validate(url, req.form.to_dict(), signature)

# --- Public routes ---
@app.route("/")
def home():
    return "Motivator is running!"


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/submit", methods=["POST"])
def submit():
    # NOTE: no per-phone/per-IP rate limiting here. The `users.phone` unique
    # constraint permanently blocks a second signup for a number that already
    # has a user row, but an attacker can still submit many *distinct*
    # numbers, each triggering one real compliance SMS (an SMS-reflector /
    # cost-abuse risk). Accepted as residual risk for this pass — revisit
    # with IP-based throttling or a signup CAPTCHA post-launch.
    data = request.json or {}
    phone = data.get("phone")
    local_time = data.get("local_time")
    tz_str = data.get("timezone") or "America/New_York"
    consent = data.get("consent")

    if not phone:
        return jsonify({"error": "Phone is required"}), 400

    if not consent:
        return jsonify({"error": "SMS consent is required"}), 400

    try:
        phone = normalize_phone(phone)
    except ValueError:
        return jsonify({"error": "Invalid phone number"}), 400

    try:
        ZoneInfo(tz_str)
    except Exception:
        return jsonify({"error": "Invalid timezone"}), 400

    if local_time:
        try:
            datetime.strptime(local_time, "%H:%M")
        except ValueError:
            return jsonify({"error": "Invalid local_time — expected HH:MM"}), 400

    db = SessionLocal()
    try:
        user = create_user(
            phone=phone,
            local_time=local_time,
            timezone=tz_str
        )
        db.add(user)
        db.commit()

        send_compliance(db, user)
        log_event(db, user_id=user.id, event_type="user_signed_up_via_app", source="submit")
        db.commit()

        return jsonify({
            "status": "success",
            "timezone": user.timezone
        }), 201

    except IntegrityError:
        db.rollback()
        return jsonify({"error": "user_exists"}), 400

    finally:
        db.close()


@app.route("/sms/inbound", methods=["POST"])
def sms_inbound():
    if not validate_twilio_request(request):
        logger.warning("Rejected inbound SMS webhook with invalid Twilio signature")
        return jsonify({"error": "invalid signature"}), 403

    db = SessionLocal()
    from_number = request.form.get("From")
    body = request.form.get("Body", "").strip().upper()

    user = db.query(User).filter(User.phone == from_number).first()
    resp = MessagingResponse()

    if not user:
        if body == "START":
            resp.message("To sign up for Motivator, please download the app.")
        return str(resp)

    if body == "STOP":
        if user.opted_in:
            user.opted_in = False
            db.commit()
        return str(resp)

    if body == "START":
        if not user.opted_in:
            user.opted_in = True
            db.commit()

            # Rate limit settings-link issuance the same way
            # request_settings_link() does (SPEC §5.5): at most one link per
            # phone number per 30-minute window, measured from the most
            # recently issued token.
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            most_recent = (
                db.query(SettingsToken)
                .filter_by(user_id=user.id)
                .order_by(desc(SettingsToken.created_at))
                .first()
            )
            within_window = (
                most_recent is not None
                and now < most_recent.created_at + timedelta(minutes=30)
            )

            if not within_window:
                # Window has passed (or no prior token) — invalidate any
                # unexpired, unused tokens before issuing a new one.
                db.query(SettingsToken).filter(
                    SettingsToken.user_id == user.id,
                    SettingsToken.used.is_(False),
                    SettingsToken.expires_at > now,
                ).update({"used": True})
                db.commit()

                token = generate_settings_token(user.id)
                settings_link = f"{BASE_URL}/settings?token={token}"

                send_sms(
                    user.phone,
                    f"You're re-subscribed to Motivator! Update your delivery time: {settings_link}"
                )

            log_event(db, user_id=user.id, event_type="user_opt_in", source="sms_inbound")
            db.commit()
        return str(resp)


    if body == "HELP":
        resp.message("For help, contact our support team at support@motivator.app. You receive 1 motivational SMS per day. Reply STOP to unsubscribe. Msg & data rates may apply.")
        return str(resp)

    resp.message("Unknown command. Reply HELP for info.")
    return str(resp)


# --- Admin/test routes (JSON) ---
@app.route("/admin/test-send", methods=["POST"])
def admin_test_send():
    if not require_admin(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.json or {}
    phone = data.get("phone")
    if not phone:
        return jsonify({"error": "Missing phone"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        today = datetime.now(timezone.utc).date()
        if user.last_sent == today:
            return jsonify({
                "status": "skipped",
                "reason": "already sent today"
            }), 200

        send_quote_to_user(db, user)
        db.commit()

        return jsonify({
            "status": "sent",
            "phone": user.phone,
            "cycle": user.cycle,
            "last_sent": user.last_sent.isoformat() if user.last_sent else None
        }), 200

    finally:
        db.close()

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        ip = _client_ip(request)
        if _login_rate_limited(ip):
            flash("Too many login attempts. Please wait a few minutes and try again.", "danger")
            return "Too many login attempts. Please wait a few minutes and try again.", 429

        password = request.form.get("password") or ""
        if hmac.compare_digest(password, ADMIN_PASSWORD):
            _clear_login_attempts(ip)
            session["is_admin"] = True
            flash("Logged in as admin", "success")
            return redirect(url_for("admin.users"))
        else:
            _record_login_failure(ip)
            flash("Incorrect password", "danger")
    return """
        <form method="post">
            <input type="password" name="password" placeholder="Admin Password">
            <button type="submit">Login</button>
        </form>
    """


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out", "info")
    return redirect(url_for("admin_login"))
    

# --- Development only routes ---
if not IS_PRODUCTION:

    @app.route("/init-db")
    def init_db():
        if not require_admin(request):
            return jsonify({"error": "Unauthorized"}), 401

        from Motivator import models
        models.Base.metadata.create_all(bind=engine)
        return jsonify({"message": "Database initialized"})

    @app.route("/debug/users", methods=["GET"])
    def debug_users():
        if not require_admin(request):
            return jsonify({"error": "Unauthorized"}), 401

        db = SessionLocal()
        users = db.query(User).all()
        db.close()

        return jsonify([
            {
                "id": u.id,
                "phone": u.phone,
                "local_time": u.local_time,
                "timezone": u.timezone,
                "last_sent": u.last_sent
            }
            for u in users
        ])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
