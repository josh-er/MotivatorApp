from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
from Motivator.utils.tokens import generate_settings_token, hash_token
from Motivator.utils.phone import normalize_phone
from .services import get_all_users, get_message_logs
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, SettingsToken
from datetime import datetime, date, timedelta, timezone
from functools import wraps
import math
from zoneinfo import ZoneInfo
from Motivator.send_quotes import send_compliance
from Motivator.event_logger import log_event
from Motivator.models import EventLog
from sqlalchemy import desc

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
settings_bp = Blueprint("settings", __name__)

US_TIMEZONES = [
    ("America/New_York",             "Eastern (New York)"),
    ("America/Chicago",              "Central (Chicago)"),
    ("America/Denver",               "Mountain (Denver)"),
    ("America/Phoenix",              "Mountain – no DST (Phoenix)"),
    ("America/Los_Angeles",          "Pacific (Los Angeles)"),
    ("America/Anchorage",            "Alaska (Anchorage)"),
    ("America/Nome",                 "Alaska (Nome)"),
    ("America/Juneau",               "Alaska (Juneau)"),
    ("Pacific/Honolulu",             "Hawaii – no DST (Honolulu)"),
    ("America/Adak",                 "Hawaii-Aleutian (Adak)"),
    ("America/Indiana/Indianapolis", "Eastern – no DST (Indianapolis)"),
    ("America/Boise",                "Mountain (Boise)"),
]

def require_admin_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin login required", "danger")
            return redirect(url_for("admin_login"))  # redirect to login page
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/users")
@require_admin_login
def users():
    users = get_all_users()
    return render_template("admin/users.html", users=users, timezones=US_TIMEZONES)

@admin_bp.route("/logs")
@require_admin_login
def logs():
    from Motivator.db import engine
    print("ADMIN DB URL:", engine.url)

    status = request.args.get("status")
    phone = request.args.get("phone")
    limit = int(request.args.get("limit", 100))
    since_date = request.args.get("since_date")

    logs = get_message_logs(
        status=status,
        phone=phone,
        since_date=since_date,
        limit=limit
    )
    return render_template("admin/logs.html", logs=logs)

@admin_bp.route("/quotes")
@require_admin_login
def quotes():
    db = SessionLocal()
    try:
        all_quotes = db.query(Quote).order_by(Quote.id.asc()).all()
        return render_template("admin/quotes.html", quotes=all_quotes)
    finally:
        db.close()

@admin_bp.route("/users/add", methods=["POST"])
@require_admin_login
def add_user():
    phone = request.form.get("phone")
    local_time = request.form.get("local_time")  # HH:MM from <input type="time">
    timezone = request.form.get("timezone") or "America/New_York"

    if not phone or not local_time:
        flash("Phone and time are required", "danger")
        return redirect(url_for("admin.users"))

    try:
        phone = normalize_phone(phone)
    except ValueError:
        flash("Invalid phone number — use 10-digit US number or E.164 format", "danger")
        return redirect(url_for("admin.users"))

    db = SessionLocal()
    try:
        if db.query(User).filter_by(phone=phone).first():
            flash("User already exists", "warning")
            return redirect(url_for("admin.users"))

        try:
            tz = ZoneInfo(timezone)
            today_local = datetime.now(tz).date()
        except Exception as e:
            flash(f"Invalid time or timezone: {e}", "danger")
            return redirect(url_for("admin.users"))

        user = User(
            phone=phone,
            local_time=local_time,
            timezone=timezone,
            opted_in=True,
            received_compliance=False,
        )

        db.add(user)
        db.commit()
        send_compliance(db, user)
        flash(f"User {phone} added", "success")

    except Exception as e:
        db.rollback()
        flash(f"Error adding user: {e}", "danger")

    finally:
        db.close()

    return redirect(url_for("admin.users"))

@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@require_admin_login
def delete_user(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        if user:
            db.delete(user)
            try:
                db.commit()
                flash(f"User {user.phone} deleted. All associated sent quotes removed.", "success")
            except Exception as e:
                db.rollback()
                print("DELETE FAILED:", e)
                flash(f"Error deleting user: {e}", "danger")
        else:
            flash("User not found", "warning")
    finally:
        db.close()
    return redirect(url_for("admin.users"))

@admin_bp.route("/quotes/add", methods=["POST"])
@require_admin_login
def add_quote():
    text = request.form.get("text")
    if not text:
        flash("Quote text required", "danger")
        return redirect(url_for("admin.quotes"))

    db = SessionLocal()
    try:
        db.add(Quote(text=text))
        try:
            db.commit()
            flash("Quote added", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error adding quote: {e}", "danger")
    finally:
        db.close()
    return redirect(url_for("admin.quotes"))

@admin_bp.route("/quotes/delete/<int:quote_id>", methods=["POST"])
@require_admin_login
def delete_quote(quote_id):
    db = SessionLocal()
    try:
        quote = db.query(Quote).get(quote_id)
        if quote:
            db.delete(quote)
            try:
                db.commit()
                flash(f"Quote deleted. All associated sent quote records removed.", "success")
            except Exception as e:
                db.rollback()
                flash(f"Error deleting quote: {e}", "danger")
        else:
            flash("Quote not found", "warning")
    finally:
        db.close()
    return redirect(url_for("admin.quotes"))

@admin_bp.route("/events")
@require_admin_login
def event_logs():
    db = SessionLocal()
    try:
        events = (
            db.query(EventLog)
            .order_by(desc(EventLog.created_at))
            .limit(200)
            .all()
        )
        return render_template("admin/events.html", events=events)
    finally:
        db.close()

@settings_bp.route("/request-settings-link", methods=["POST"])
def request_settings_link():
    data = request.get_json()
    phone = data.get("phone")
    if not phone:
        abort(400, "Missing phone")

    try:
        phone = normalize_phone(phone)
    except ValueError:
        abort(400, "Invalid phone number")

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(phone=phone).first()
        if not user:
            abort(404, "User not found")

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Rate limit: at most one settings link per phone number per 30-minute
        # window, measured from when the most recent link was issued.
        # NOTE: no row-level locking here — two truly concurrent requests for
        # the same phone number could both pass this check and each create a
        # token. Acceptable for this low-traffic, user-triggered flow; revisit
        # with SELECT ... FOR UPDATE if that changes.
        most_recent = (
            db.query(SettingsToken)
            .filter_by(user_id=user.id)
            .order_by(desc(SettingsToken.created_at))
            .first()
        )
        if most_recent:
            window_end = most_recent.created_at + timedelta(minutes=30)
            if now < window_end:
                wait_minutes = math.ceil((window_end - now).total_seconds() / 60)
                return jsonify({
                    "error": f"Please wait {wait_minutes} minute(s) before requesting another settings link."
                }), 429

        # Window has passed (or no prior token) — invalidate any unexpired,
        # unused tokens for this user before issuing a new one.
        db.query(SettingsToken).filter(
            SettingsToken.user_id == user.id,
            SettingsToken.used.is_(False),
            SettingsToken.expires_at > now,
        ).update({"used": True})
        db.commit()

        token = generate_settings_token(user.id)

        log_event(
            db,
            user_id=user.id,
            event_type="settings_link_requested",
            source="settings_link",
        )
        db.commit()

        link = f"https://motivatorapp.onrender.com/settings?token={token}"

        return jsonify({"settings_link": link}), 200
    finally:
        db.close()

# ---------- SETTINGS HTML ----------
@settings_bp.route("/settings", methods=["GET"])
def settings_page():
    token_value = request.args.get("token")
    if not token_value:
        return render_template("settings.html", token=None, error="Missing or invalid link.")

    db = SessionLocal()
    try:
        token = db.query(SettingsToken).filter_by(token=hash_token(token_value)).first()
        if not token:
            return render_template("settings.html", token=None, error="This link is invalid.")
        if token.used:
            return render_template("settings.html", token=None, error="This link has already been used.")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if token.expires_at < now:
            return render_template("settings.html", token=None, error="This link has expired.")

        user = db.query(User).get(token.user_id)
        if not user:
            return render_template("settings.html", token=None, error="User not found.")

        return render_template(
            "settings.html",
            token=token_value,
            error=None,
            prefill_time=user.local_time,
            prefill_timezone=user.timezone,
            timezones=US_TIMEZONES,
        )
    finally:
        db.close()

# ---------- SETTINGS API (PREFILL) ----------
@settings_bp.route("/api/settings", methods=["GET"])
def get_settings():
    token_value = request.args.get("token")
    if not token_value:
        abort(400, "Missing token")

    db = SessionLocal()
    try:
        token = db.query(SettingsToken).filter_by(token=hash_token(token_value)).first()
        if not token:
            abort(404, "Invalid token")
        if token.used:
            abort(403, "Token already used")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if token.expires_at < now:
            abort(403, "Token expired")

        user = db.query(User).get(token.user_id)
        if not user:
            abort(404, "User not found")

        return jsonify({
            "user_id": user.id,
            "local_time": user.local_time,
            "timezone": user.timezone,
            "opted_in": user.opted_in
        })
    finally:
        db.close()

# ---------- SETTINGS UPDATE ----------
@settings_bp.route("/settings", methods=["POST"])
def update_settings():
    data = request.get_json()
    token_value = data.get("token")

    if not token_value:
        abort(400, "Missing token")

    db = SessionLocal()
    try:
        token = db.query(SettingsToken).filter_by(token=hash_token(token_value)).first()
        if not token:
            abort(404, "Invalid token")
        if token.used:
            abort(403, "Token already used")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if token.expires_at < now:
            abort(403, "Token expired")

        user = db.query(User).get(token.user_id)
        if not user:
            abort(404, "User not found")

        previous_opted_in = user.opted_in

        local_time = data.get("local_time")
        timezone_str = data.get("timezone") or user.timezone
        opted_in = data.get("opted_in")

        if local_time:
            tz = ZoneInfo(timezone_str)
            today_local = datetime.now(tz).date()
            user.local_time = local_time
            user.timezone = timezone_str

        token.used = True

        log_event(
            db,
            user_id=user.id,
            event_type="settings_updated",
            source="settings_link",
        )

        db.commit()

        return jsonify({
            "status": "settings updated",
            "user_id": user.id,
            "local_time": user.local_time,
            "timezone": user.timezone,
            "opted_in": user.opted_in
        })
    finally:
        db.close()