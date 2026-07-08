# Motivator

Motivator is a phone-number–driven SMS service that sends users a daily motivational message at a time they configure.

## Structure

- `Motivator/` — Flask backend (API, SMS webhook, scheduler, admin panel)
- `MotivatorUI/` — iOS app (SwiftUI)

## Architecture

Flask + PostgreSQL (hosted on Render), Twilio for SMS, a cron job driving the scheduler, and a SwiftUI iOS app as the signup/settings-link trigger surface. See `SPEC.md` for the full design and `PROGRESS.md` for implementation status.

## Running the backend locally

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set up a `.env` file with:

```
DATABASE_URL=...          # optional locally; falls back to SQLite if unset
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
FLASK_SECRET_KEY=...
ADMIN_PASSWORD=...
ADMIN_KEY=...
BASE_URL=http://localhost:5000
```

Run the app:

```
python3 -m Motivator.app
```

## Tests

```
pip install -r requirements-dev.txt
pytest
```

## iOS app

`MotivatorUI/` is a standard Xcode project — open it in Xcode and run. Debug builds point at `http://127.0.0.1:5000`; release builds point at the deployed Render URL.
