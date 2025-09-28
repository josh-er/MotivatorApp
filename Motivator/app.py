from flask import Flask, request, jsonify
from Motivator.db import SessionLocal, Base, engine
from Motivator.models import User
from sqlalchemy.exc import IntegrityError

# import your existing send_now logic
from Motivator.send_now import send_now as send_now_task

app = Flask(__name__)

# Make sure DB tables exist (only needed once in dev; Render will handle migrations)
Base.metadata.create_all(bind=engine)

@app.route("/")
def home():
    return "Motivator is running!"

@app.route("/submit", methods=["POST"])
def submit():
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
    """Expose send_now via HTTP for testing"""
    try:
        send_now_task()
        return jsonify({"status": "success", "message": "Quotes sent"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
