# app.py
from flask import Flask, request, jsonify
from Motivator.db import SessionLocal, Base, engine
from Motivator.models import User
from Motivator.send_now import send_now as send_now_task
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

@app.route("/")
def home():
    return "Motivator is running!"

@app.route("/init-db")
def init_db():
    """Drop and recreate all tables for a fresh start."""
    from Motivator.db import Base, engine
    from Motivator import models  # ensure tables are visible

    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return jsonify({"message": "Database initialized successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/submit", methods=["POST"])
def submit():
    """Register a new user with phone + preferred time."""
    data = request.json
    phone = data.get("phone")
    time = data.get("time")

    db = SessionLocal()
    try:
        user = User(phone=phone, time=time, last_sent=None)
        db.add(user)
        db.commit()
        return jsonify({"status": "success"}), 201
    except IntegrityError:
        db.rollback()
        return jsonify({"status": "error", "message": "User already exists"}), 400
    finally:
        db.close()

@app.route("/send_now", methods=["GET"])
def send_now_route():
    """Trigger quote send for all users (manual test endpoint)."""
    try:
        send_now_task()
        return jsonify({"status": "success", "message": "Quotes sent"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
