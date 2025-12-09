from flask import Flask, request, jsonify
from Motivator.db import SessionLocal, Base, engine
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
    """Register a new user with phone + preferred time (stored in UTC)."""
    data = request.json or {}
    phone = data.get("phone")
    time_str = data.get("time")

    if not phone or not time_str:
        return jsonify({"status": "error", "message": "Phone and time are required"}), 400

    # Parse HH:MM input
    try:
        user_time_naive = datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return jsonify({"status": "error", "message": "Time must be HH:MM"}), 400

    # Convert ET → UTC
    et = ZoneInfo("America/New_York")
    utc = ZoneInfo("UTC")

    today = datetime.now(et).date()
    dt_et = datetime.combine(today, user_time_naive.time(), tzinfo=et)
    dt_utc = dt_et.astimezone(utc)

    # Store normalized UTC time as HH:MM string
    utc_string = dt_utc.strftime("%H:%M")

    db = SessionLocal()
    try:
        user = User(phone=phone, time=utc_string, last_sent=None)
        db.add(user)
        db.commit()
        return jsonify({"status": "success", "message": "User added", "stored_utc_time": utc_string}), 201
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
                "cycle": u.cycle
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
    """Quickly add a user for testing (bypasses front-end)."""
    data = request.json or {}
    phone = data.get("phone")
    time = data.get("time", "09:00")

    if not phone:
        return jsonify({"error": "Missing 'phone'"}), 400

    db = SessionLocal()
    try:
        user = User(phone=phone, time=time)
        db.add(user)
        db.commit()
        return jsonify({"status": "success", "user": {"phone": phone, "time": time}}), 201
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