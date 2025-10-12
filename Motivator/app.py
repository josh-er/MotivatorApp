from flask import Flask, request, jsonify
from Motivator.db import SessionLocal, Base, engine
from Motivator.models import User, Quote
from Motivator.send_now import send_now as send_now_task
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Motivator is running!"

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
    """Register a new user with phone + preferred time."""
    data = request.json or {}
    phone = data.get("phone")
    time = data.get("time")

    if not phone or not time:
        return jsonify({"status": "error", "message": "Phone and time are required"}), 400

    db = SessionLocal()
    try:
        user = User(phone=phone, time=time, last_sent=None)
        db.add(user)
        db.commit()
        return jsonify({"status": "success", "message": "User added"}), 201
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
