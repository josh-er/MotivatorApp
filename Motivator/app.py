#testing sending logic
from Motivator.send_quotes import send_quote_to_user
from datetime import timezone
#testing sending logic
import os
from flask import Flask, request, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.exc import IntegrityError
from twilio.twiml.messaging_response import MessagingResponse

from Motivator.db import SessionLocal, engine
from Motivator.user_service import create_user
from Motivator.models import User, Quote

ADMIN_KEY = os.getenv("ADMIN_KEY")
ENV = os.getenv("ENV", "development")

app = Flask(__name__)

def require_admin(req):
    if not ADMIN_KEY:
        return False
    return req.headers.get("X-Admin-Key") == ADMIN_KEY

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
            "utc_time": user.utc_time,
            "timezone": user.timezone
        }), 201

    except IntegrityError:
        db.rollback()
        return jsonify({"error": "User already exists"}), 400

    finally:
        db.close()


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
                "utc_time": u.utc_time,
                "last_sent": u.last_sent
            }
            for u in users
        ])


    @app.route("/debug/add_user", methods=["POST"])
    def debug_add_user():
        if not require_admin(request):
            return jsonify({"error": "Unauthorized"}), 401

        data = request.json or {}
        phone = data.get("phone")
        local_time = data.get("time", "09:00")
        timezone = data.get("timezone", "America/New_York")

        if not phone:
            return jsonify({"error": "Missing phone"}), 400

        db = SessionLocal()
        try:
            user = create_user(phone, local_time, timezone)
            db.add(user)
            db.commit()
            return jsonify({"status": "ok", "utc_time": user.utc_time})
        finally:
            db.close()


    @app.route("/debug/delete_user", methods=["POST"])
    def delete_user():
        if not require_admin(request):
            return jsonify({"error": "Unauthorized"}), 401

        data = request.json or {}
        phone = data.get("phone")

        if not phone:
            return jsonify({"error": "Missing phone"}), 400

        db = SessionLocal()
        user = db.query(User).filter(User.phone == phone).first()

        if not user:
            db.close()
            return jsonify({"error": "User not found"}), 404

        from Motivator.models import SentQuote
        db.query(SentQuote).filter(SentQuote.user_id == user.id).delete()
        db.delete(user)
        db.commit()
        db.close()

        return jsonify({"status": "deleted"})


    @app.route("/add_quote", methods=["POST"])
    def add_quote():
        if not require_admin(request):
            return jsonify({"error": "Unauthorized"}), 401

        data = request.json or {}
        text = data.get("text")

        if not text:
            return jsonify({"error": "Missing text"}), 400

        db = SessionLocal()
        db.add(Quote(text=text))
        db.commit()
        db.close()

        return jsonify({"status": "added"})


@app.route("/sms/inbound", methods=["POST"])
def sms_inbound():
    db = SessionLocal()

    from_number = request.form.get("From")
    body = request.form.get("Body", "").strip().upper()

    user = db.query(User).filter(User.phone == from_number).first()
    resp = MessagingResponse()

    if not user:
        resp.message("You're not signed up for Motivator. Download the app to join.")
        return str(resp)

    if body == "STOP":
        user.opted_in = False
        db.commit()
        resp.message("You've been unsubscribed. Reply START to rejoin Motivator.")
        return str(resp)

    if body == "START":
        user.opted_in = True
        db.commit()
        resp.message("You're now opted in to receive once daily motivational SMS messages from Motivator. Msg & data rates may apply. Visit the Motivator app to customize your preferences. Reply HELP for help. Reply STOP to cancel.")
        return str(resp)

    if body == "HELP":
        resp.message("For help, contact our support team at support@motivator.app. You receive 1 motivational SMS per day. Reply STOP to unsubscribe. Msg & data rates may apply.")
        return str(resp)

    resp.message("Unknown command. Reply HELP for info.")
    return str(resp)

@app.route("/admin/users", methods=["GET"])
def admin_users():
    if not require_admin(request):
        return jsonify({"error": "unauthorized"}), 401

    db = SessionLocal()
    try:
        users = db.query(User).all()
        return jsonify([
            {
                "phone": u.phone,
                "local_time": u.local_time,
                "timezone": u.timezone,
                "utc_time": u.utc_time,
                "last_sent": u.last_sent.isoformat() if u.last_sent else None,
                "opted_in": u.opted_in,
            }
            for u in users
        ])
    finally:
        db.close()

# admin test send
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

        # IMPORTANT: same logic scheduler uses

        send_quote_to_user(db, user, today)
        db.commit()

        return jsonify({
            "status": "sent",
            "phone": user.phone,
            "cycle": user.cycle,
            "last_sent": user.last_sent.isoformat() if user.last_sent else None
        }), 200

    finally:
        db.close()

# admin add quote
@app.route("/admin/add-quote", methods=["POST"])
def admin_add_quote():
    if not require_admin(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    text = data.get("text")

    if not text:
        return jsonify({"error": "Missing text"}), 400

    db = SessionLocal()
    db.add(Quote(text=text))
    db.commit()
    db.close()

    return jsonify({"status": "added"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
