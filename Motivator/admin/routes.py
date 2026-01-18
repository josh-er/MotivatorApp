from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
from Motivator.utils.tokens import generate_settings_token
from .services import get_all_users, get_message_logs
from Motivator.db import SessionLocal
from Motivator.models import User, Quote, SettingsToken
from datetime import datetime, date, timezone
from functools import wraps
from zoneinfo import ZoneInfo
from Motivator.send_quotes import send_compliance

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
settings_bp = Blueprint("settings", __name__)

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
    return render_template("admin/users.html", users=users)

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

    db = SessionLocal()
    try:
        if db.query(User).filter_by(phone=phone).first():
            flash("User already exists", "warning")
            return redirect(url_for("admin.users"))

        # compute utc_time immediately
        try:
            tz = ZoneInfo(timezone)
            today_local = datetime.now(tz).date()
            local_dt = datetime.combine(
                today_local,
                datetime.strptime(local_time, "%H:%M").time(),
                tzinfo=tz,
            )
            utc_time = local_dt.astimezone(ZoneInfo("UTC")).strftime("%H:%M")
        except Exception as e:
            flash(f"Invalid time or timezone: {e}", "danger")
            return redirect(url_for("admin.users"))

        user = User(
            phone=phone,
            local_time=local_time,
            timezone=timezone,
            utc_time=utc_time,
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

@settings_bp.route("/request-settings-link", methods=["POST"])
def request_settings_link():
    user_id = 7  # temp

    token = generate_settings_token(user_id)

    link = f"http://localhost:5000/settings?token={token}"

    return jsonify({"settings_link": link}), 200

@settings_bp.route("/settings", methods=["GET"])
def settings_page():
    token_value = request.args.get("token")
    if not token_value:
        abort(400, "Missing token")

    db = SessionLocal()
    try:
        token = (
            db.query(SettingsToken)
            .filter_by(token=token_value)
            .first()
        )

        if not token:
            abort(404, "Invalid token")

        if token.used:
            abort(403, "Token already used")

        # Convert aware -> naive UTC to match DB column
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if token.expires_at < now:
            abort(403, "Token expired")

        return jsonify({
            "status": "token valid",
            "user_id": token.user_id
        })

    finally:
        db.close()

@settings_bp.route("/settings", methods=["POST"])
def update_settings():
    data = request.get_json()
    token_value = data.get("token")
    local_time = data.get("local_time")
    timezone_str = data.get("timezone")
    opted_in = data.get("opted_in")

    if not token_value:
        abort(400, "Missing token")

    db = SessionLocal()
    try:
        token = db.query(SettingsToken).filter_by(token=token_value).first()
        if not token:
            abort(404, "Invalid token")
        if token.used:
            abort(403, "Token already used")
        
        # Convert aware -> naive UTC to match DB column
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if token.expires_at < now:
            abort(403, "Token expired")

        # Mark token as used
        db.query(SettingsToken).filter_by(id=token.id).update({"used": True})

        # Update user settings
        user = db.query(User).get(token.user_id)
        if not user:
            abort(404, "User not found")

        if local_time:
            user.local_time = local_time
            if timezone_str:
                user.timezone = timezone_str
            else:
                timezone_str = user.timezone or "UTC"

            # recalc UTC time
            try:
                tz = ZoneInfo(timezone_str)
                today_local = datetime.now(tz).date()
                local_dt = datetime.combine(
                    today_local,
                    datetime.strptime(local_time, "%H:%M").time(),
                    tzinfo=tz
                )
                user.utc_time = local_dt.astimezone(ZoneInfo("UTC")).strftime("%H:%M")
            except Exception as e:
                abort(400, f"Invalid local_time or timezone: {e}")

        if opted_in is not None:
            user.opted_in = bool(opted_in)

        db.commit()
        return jsonify({
            "status": "settings updated",
            "user_id": user.id,
            "local_time": user.local_time,
            "timezone": user.timezone,
            "utc_time": user.utc_time,
            "opted_in": user.opted_in
        })
    finally:
        db.close()
