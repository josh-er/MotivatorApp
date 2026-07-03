1. Purpose and Core Behavior
Motivator is a phone-number–driven SMS motivation service. Users receive scheduled motivational messages at a configured daily time. Configuration happens via a secure, time-limited web link delivered over SMS. The mobile app is a thin trigger surface only.

2. High-Level Architecture
	•	Frontend (App): iOS (SwiftUI)
	•	Backend API: Python (Flask)
	•	Database: PostgreSQL
	•	Messaging: SMS provider (e.g., Twilio)
	•	Scheduler: Cron (or equivalent scheduled job runner)
The app has no authentication, no sessions, no local persistence.

2.1 Database Configuration
	•	Production store: PostgreSQL, hosted on Render. `DATABASE_URL` is provided via the Render environment.
	•	Local dev store: SQLite (`Motivator/motivator.db`), used only when no `DATABASE_URL` is set and the process is not running in production.
	•	Production is detected via the `RENDER` env var (set automatically by Render) or `FLASK_ENV=production`.
	•	Fail-loud guarantee: in production, if `DATABASE_URL` is missing or is not a `postgresql://` URL, the app raises `RuntimeError` at startup instead of silently falling back to SQLite. This prevents the scheduler or web app from ever reading/writing the wrong database in production.

3. User Identity Model
	•	The only identifier is phone number, normalized to E.164 format.
	◦	Example: +14155552671
	•	Normalization rules:
	◦	Strip all non-numeric characters
	◦	Assume US numbers if 10 digits and no country code
	◦	Prefix with +1 if US
	◦	Reject invalid lengths
	•	All database lookups and writes use the normalized E.164 value.

4. User Flow (End-to-End)
Step 1: App — Signup
	•	User enters phone number, delivery time, and timezone, and checks an SMS consent checkbox.
	•	App posts to POST /submit with phone, local_time, timezone, and consent=true.
	•	Backend creates the user record and immediately sends a compliance SMS.
Step 2: SMS — Re-activation (existing opted-out users only)
	•	If a user previously texted STOP, they can re-activate by texting START.
	•	Backend webhook:
	◦	Looks up existing user by phone number
	◦	Sets opted_in = true
	◦	Sends a settings link so the user can update their delivery time
	•	Unknown number texts START → reply: “To sign up for Motivator, please download the app.” No user record is created.
Step 3: App — Change Preferences
	•	User taps “Update delivery time”.
	•	App calls POST /request-settings-link with their phone number.
	•	Backend generates a single-use, time-limited settings link and sends it back.
	•	User opens the link to update local_time and timezone.

5. Settings Link (Core Feature)
5.1 What the Link Is
	•	A single-use, time-limited HTTPS link to a backend-hosted web page.
	•	Example: https://api.motivator.app/settings?token=abc123
	•	
5.2 Token Generation
	•	Backend generates:
	◦	Cryptographically secure random token
	◦	Stores hashed token in DB
	•	Token metadata:
	◦	expires_at = now + 30 minutes
	◦	used = false
	◦	Associated with phone number (FK)
Expiry duration: 30 minutes (fixed, explicit).

5.3 Visiting the Link (GET)
Endpoint
GET /settings?token=...
Backend behavior
	•	Validate token:
	◦	Exists
	◦	Not expired
	◦	Not used
	•	If invalid → render error page (expired/invalid link)
	•	If valid → render minimal HTML form
Rendered page contains
	•	Delivery time selector (HH:MM)
	•	Timezone selector (IANA tz string, default inferred)
	•	Submit button

5.4 Submitting Settings (POST)
Endpoint
POST /settings
Payload
{
  "token": "abc123",
  "local_time": "08:30",
  "timezone": "America/Los_Angeles"
}
Backend behavior
	•	Re-validate token
	•	Write preferences to DB
	•	Mark token used = true
	•	Optionally redirect to confirmation page

6. Delivery Preferences Schema
Delivery preferences are stored directly on the users table (no separate table).
users table
	•	phone (E.164, unique)
	•	opted_in (boolean)
	•	created_at
	•	local_time (TEXT, "HH:MM" — user's chosen delivery time in their local timezone)
	•	timezone (TEXT, IANA tz string, e.g. America/New_York)
	•	last_sent (DATE, nullable — user's local calendar date of last send)
	•	cycle (INTEGER, default 1 — increments when all quotes have been seen once)
Non-goals (explicit):
	•	No multiple daily sends
	•	No custom days of week
	•	No snooze logic (MVP)

7. Scheduling / Cron Logic (Critical Path)
7.1 Job Frequency
	•	Cron runs every minute.
7.2 Job Query Logic
For each active user:
	1	Convert current UTC → user local time using timezone
	2	Compare local_now >= scheduled_local (fires at or after the scheduled minute; sends late rather than missing a send if the worker was briefly down)
	3	Ensure:
	◦	opted_in = true
	◦	last_sent < today (user's local date)
7.3 Send Flow
	•	Select motivational message (random or sequential)
	•	Send SMS
	•	Update last_sent = today (user's local date)
This prevents duplicate sends on cron retries.

8. STOP / Opt-Out Handling (Required)
Incoming SMS: STOP
Backend behavior:
	•	Normalize sender number
	•	Set opted_in = false
	•	Do not delete preferences
Note: Twilio handles the STOP reply (“You’ve been unsubscribed”) natively at the carrier level. No application-level confirmation SMS is needed or sent.
After STOP
	•	Cron job must exclude opted_in = false
	•	User may re-activate by texting START again

9. Frontend / Backend Contract
Frontend guarantees
	•	Sends raw phone number input
	•	Does not store activation or settings state
	•	Does not assume link validity or timing
Backend guarantees
	•	Authoritative phone normalization
	•	Idempotent START handling
	•	Hard expiry enforcement for settings links
	•	Timezone-safe scheduling

10. Design Intent
	•	SMS is the control surface
	•	Web link is the configuration surface
	•	App is a stateless trigger
	•	Cron is the source of truth for delivery timing
Every decision favors determinism and auditability over UX complexity.
