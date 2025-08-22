# Motivator

Motivator is a simple SMS app that sends daily motivational (sometimes meme) quotes to users.

## Features
- Stores quotes in a SQLite database
- Sends SMS messages via Twilio
- Scheduler to send one message per day
- Logs sent messages in a csv

## Getting Started
1. Clone the repo
2. Install dependencies:
   pip install -r requirements.txt
3. Set up environment variables in a .env file:
    TWILIO_ACCOUNT_SID=your_sid
    TWILIO_AUTH_TOKEN=your_token
    TWILIO_PHONE=+1234567890
4. Initialize the database:
    python init_db.py
5. Run the scheduler:
    python run_scheduler.py
6. Deployment (Render)
    Push this repo to GitHub
    Connect it to Render as a new Web Service
    Add environment variables in Render’s dashboard
    Render will install from requirements.txt and run your app