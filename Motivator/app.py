import os
import logging
from flask import Flask, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.exc import IntegrityError
from twilio.twiml.messaging_response import MessagingResponse
from Motivator.db import SessionLocal, engine
from Motivator.user_service import create_user
from Motivator.models import User
from Motivator.admin.routes import admin_bp, settings_bp
from Motivator.send_quotes import send_quote_to_user
from dotenv import load_dotenv

load_dotenv()

ADMIN_KEY = os.getenv("ADMIN_KEY")
ENV = os.getenv("ENV", "development")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
app.register_blueprint(admin_bp)
app.register_blueprint(settings_bp)

def require_admin(req):
    if not ADMIN_KEY:
        return False
    return req.headers.get("X-Admin-Key") == ADMIN_KEY

# --- Public routes ---
@app.route("/")
def home():
    return "Motivator is running!"


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/submit", methods=["POST"])
def submit():
    data = request.json or {}
    phone = data.get("phone")
    time_str = data.get("time")
    tz_str = data.get("timezone") or "America/New_York"

    if not phone or not time_str:
        return jsonify({"error": "Phone and time are required"}), 400

    try:
        ZoneInfo(tz_str)
    except Exception:
        return jsonify({"error": "Invalid timezone"}), 400

    db = SessionLocal()
    try:
        user = create_user(
            phone=phone,
            local_time=time_str,
            timezone=tz_str
        )
        db.add(user)
        db.commit()
        return jsonify({
            "status": "success",
            "timezone": user.timezone
        }), 201

    except IntegrityError:
        db.rollback()
        return jsonify({"error": "User already exists"}), 400

    finally:
        db.close()


@app.route("/sms/inbound", methods=["POST"])
def sms_inbound():
    logging.info("SMS INBOUND HIT")
    db = SessionLocal()
    from_number = request.form.get("From")
    body = request.form.get("Body", "").strip().upper()

    user = db.query(User).filter(User.phone == from_number).first()
    resp = MessagingResponse()

    if not user:
        resp.message("You're not signed up for Motivator. Download the app to join.")
        return str(resp)

    if body == "STOP":
        if user.opted_in:
            user.opted_in = False
            db.commit()
        return str(resp)

    if body == "START":
        if not user.opted_in:
            user.opted_in = True
            user.received_compliance = False
            db.commit()

            from Motivator.send_quotes import send_compliance
            send_compliance(db, user)
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

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "testpass")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Logged in as admin", "success")
            return redirect(url_for("admin.users"))
        else:
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
if ENV != "production":

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
