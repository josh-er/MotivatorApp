## `docs/contracts.md`

# API & Integration Contracts
This document defines the external-facing backend contracts.

---

## Core Product Assumptions
- No passwords
- No accounts
- Authentication is SMS-based via single-use magic links
- Phone number is the primary user identifier
- Backend is the source of truth

---

## User Model (Relevant Fields)
- phone (string, E.164, unique)
- local_time (string, HH:MM, user’s preferred send time)
- timezone (IANA timezone string, e.g. America/New_York)
- opted_in (boolean)
- last_sent (date, local to user)

---

## Routes
### POST /signup
Creates or updates a user and sends compliance SMS.

Request body:
{
  "phone": "+15551234567",
  "local_time": "09:00",
  "timezone": "America/New_York",
  "agreed_to_terms": true
}

Responses:
- 200: signup successful
- 400: invalid input or missing consent
- 429: rate limited

### POST /request-settings-link
Generates a single-use settings link and sends it via SMS.
Request body:
{
  "phone": "+15551234567"
}

Responses:
- 200: link generated
- 404: user not found
- 429: rate limited

Notes:
- At most one active token per user
- Token has an expiration

### GET /settings
Server-rendered HTML page.

Query params:
- token (string)

Behavior:
- Renders settings UI if token is valid
- Errors on invalid, expired, or used tokens

### GET /api/settings
Prefill endpoint for settings UI.

Query params:
- token (string)

Response:
{
  "user_id": 123,
  "local_time": "09:00",
  "timezone": "America/New_York",
  "opted_in": true
}

Errors:
- 403: expired or used token
- 404: invalid token or user not found

### POST /settings 
Updates user preferences using a settings token.
Request body:
{
  "token": "abc123",
  "local_time": "10:00",
  "timezone": "America/New_York",
  "opted_in": false
}

Responses:
- 200: settings updated
- 403: token expired or used
- 404: invalid token or user

Side effects:
- Token is marked as used
- User preferences updated

---

## Twilio Webhooks
Incoming SMS
- STOP → opted_in = false
- START → opted_in = true

---

## Non-Goals
- No retries
- No backfill
- No message history editing
- No multi-device state
- No user-authenticated sessions