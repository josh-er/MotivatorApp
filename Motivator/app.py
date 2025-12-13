from flask import Flask, request, jsonify
from Motivator.db import SessionLocal, Base, engine
from Motivator.user_service import create_user
from Motivator.models import User, Quote
from Motivator.send_now import send_now as send_now_task
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from zoneinfo import ZoneInfo
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Motivator is running!"

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/init-db")
def init_db():
    """Initialize all database tables."""
    try:
        from Motivator import models  # Ensure models are registered
        print("Creating tables:", list(models.Base.metadata.tables.keys()))
        models.Base.metadata.create_all(bind=engine)
        return jsonify({"message": "Database initialized successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/submit", methods=["POST"])
def submit():
    """Register a new user with phone + preferred time + timezone."""
    data = request.json or {}
    phone = data.get("phone")
    time_str = data.get("time")         # "HH:MM"
    tz_str = data.get("timezone")       # e.g. "America/Los_Angeles"

    if not phone or not time_str:
        return jsonify({"status": "error", "message": "Phone and time are required"}), 400

    # Default timezone if mobile app didn't send one
    if not tz_str:
        tz_str = "America/New_York"

    # Validate timezone early
    try:
        ZoneInfo(tz_str)
    except Exception:
        return jsonify({"status": "error", "message": "Invalid timezone"}), 400

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
            "message": "User added",
            "utc_time": user.utc_time,
            "timezone": user.timezone
        }), 201

    except IntegrityError:
        db.rollback()
        return jsonify({"status": "error", "message": "User already exists"}), 400

    finally:
        db.close()


@app.route("/debug/users", methods=["GET"])
def debug_users():
    """Check all users currently in the database."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        result = [
            {
                "id": u.id,
                "phone": u.phone,
                "time": u.time,
                "last_sent": u.last_sent,
                "cycle": u.cycle,
                "local_time": u.local_time,
                "timezone": u.timezone,
                "utc_time": u.utc_time
            }
            for u in users
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route("/debug/add_user", methods=["POST"])
def debug_add_user():
    data = request.json or {}
    phone = data.get("phone")
    local_time = data.get("time", "09:00")
    timezone = data.get("timezone", "America/New_York")

    if not phone:
        return jsonify({"error": "Missing 'phone'"}), 400

    db = SessionLocal()
    try:
        user = create_user(phone, local_time, timezone)
        db.add(user)
        db.commit()
        return jsonify({
            "status": "success",
            "user": {
                "phone": phone,
                "local_time": local_time,
                "timezone": timezone,
                "utc_time": user.utc_time
            }
        }), 201
    except IntegrityError:
        db.rollback()
        return jsonify({"status": "error", "message": "User already exists"}), 400
    finally:
        db.close()


@app.route("/debug/delete_user", methods=["POST"])
def delete_user():
    """Delete a user by phone number (also removes their sent history)."""
    data = request.json or {}
    phone = data.get("phone")

    if not phone:
        return jsonify({"status": "error", "message": "Missing phone"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Delete related sent-quote history FIRST
        from Motivator.models import SentQuote
        db.query(SentQuote).filter(SentQuote.user_id == user.id).delete()

        # Now it's safe to delete the user
        db.delete(user)
        db.commit()

        return jsonify({"status": "success", "message": f"Deleted {phone}"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()


@app.route("/add_quote", methods=["POST"])
def add_quote():
    """Add a new motivational quote to the database."""
    data = request.json or {}
    text = data.get("text")

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400

    db = SessionLocal()
    try:
        quote = Quote(text=text)
        db.add(quote)
        db.commit()
        return jsonify({"status": "success", "quote": text}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()


@app.route("/send_now", methods=["GET"])
def send_now_route():
    """Manually trigger sending quotes."""
    try:
        print("Triggering send_now_task()")
        send_now_task()
        return jsonify({"status": "success", "message": "Quotes sent"})
    except Exception as e:
        print("Error during send_now:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


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

    # STOP — required by law
    if body == "STOP":
        user.opted_in = False
        db.commit()
        resp.message("You've been unsubscribed. Reply START to rejoin Motivator.")
        return str(resp)

    # START — re-enable messages
    if body == "START":
        user.opted_in = True
        db.commit()
        resp.message("You're now opted in to receive once daily motivational SMS messages from Motivator. Msg & data rates may apply. Visit the Motivator app to customize your preferences. Reply HELP for help. Reply STOP to cancel.")
        return str(resp)

    # HELP — legally required
    if body == "HELP":
        resp.message("For help, contact our support team at support@motivator.app. You receive 1 motivational SMS per day. Reply STOP to unsubscribe. Msg & data rates may apply.")
        return str(resp)

    # Fallback
    resp.message("Unknown command. Reply HELP for info.")
    return str(resp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)