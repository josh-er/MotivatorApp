from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .services import get_all_users, get_message_logs
from Motivator.db import SessionLocal
from Motivator.models import User, Quote
from datetime import datetime, date
from functools import wraps

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

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
    if not phone:
        flash("Phone required", "danger")
        return redirect(url_for("admin.users"))

    db = SessionLocal()
    try:
        if db.query(User).filter_by(phone=phone).first():
            flash("User already exists", "warning")
            return redirect(url_for("admin.users"))

        # --- defaults ---
        local_time_str = "09:00"
        timezone = "America/New_York"

        # compute utc_time
        from zoneinfo import ZoneInfo
        local_dt = datetime.strptime(local_time_str, "%H:%M").replace(
            year=2000, month=1, day=1, tzinfo=ZoneInfo(timezone)
        )
        utc_time = local_dt.astimezone(ZoneInfo("UTC")).strftime("%H:%M")

        user = User(
            phone=phone,
            time=local_time_str,
            timezone=timezone,
            utc_time=utc_time,
            opted_in=True
        )

        db.add(user)
        db.commit()

        # --- compliance opt-in SMS ---
        from Motivator.sms import send_sms
        send_sms(
            phone,
            "You're now opted in to receive once daily motivational SMS messages from Motivator. Msg & data rates may apply. Visit the Motivator app to customize your preferences. Reply HELP for help. Reply STOP to cancel."
        )

        flash(f"User {phone} added and opt-in message sent", "success")

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
