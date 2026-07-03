# Motivator — Implementation Progress

Last updated: 2026-06-29

---

## What this document is

A snapshot of where the codebase stands against SPEC.md. Written after a full audit and a round of fixes. Items are grouped by status, not by discovery order.

---

## Completed

### Signup flow overhaul (§4)
The original code created users via SMS START. The flow is now:
- **New users sign up through `POST /submit`** — sends phone, `local_time`, timezone, and `consent=true`. Backend creates the user and immediately sends the TCPA compliance SMS.
- **SMS START is re-activation only** — if a known user's `opted_in` is false, START re-enables them and sends a settings link. Unknown numbers texting START receive: "To sign up for Motivator, please download the app." No user record is created.
- **Settings link is change-preferences flow** — not initial setup.

### Consent validation (§4, TCPA)
`POST /submit` requires `consent=true`. Returns HTTP 400 if absent. The compliance SMS is sent immediately after user creation.

Disclosure text shown on the iOS form (must accompany an unchecked checkbox):
> "By checking this box, you agree to receive approximately 1 automated motivational SMS per day from Motivator at the phone number provided above. Consent is not required to use any service. Msg & data rates may apply. Reply STOP to cancel at any time, HELP for help."

### Compliance SMS crash fixed (send_quotes.py)
`send_compliance` was calling `send_sms(user.phone)` with no message argument — a guaranteed `TypeError` at runtime. Fixed to pass the approved compliance message text.

### Schema — `created_at` added (§6)
Column added to the `User` model. Migration written at `migrations/versions/add_created_at_to_users.py`. Applied to the database on 2026-06-25.

### SPEC.md brought in sync with code
The following spec errors were corrected to reflect intentional implementation choices:
- **Token expiry**: 15 min → 30 min (§5.2)
- **Scheduler comparison**: `==` → `>=` with a note on late-fire behavior (§7.2)
- **STOP reply**: spec no longer requires app-level confirmation SMS — Twilio handles it natively (§8)
- **Schema**: merged `delivery_preferences` into `users` table; removed `status`, `frequency`, `updated_at`; corrected `last_sent` type to DATE; corrected field name to `local_time` (§5.4, §6, §7)
- **User flow**: §4 rewritten to match current app signup model

### #1 — Phone normalization (§3, §9)
`normalize_phone()` added in `utils/phone.py`. Strips non-digits, accepts 10-digit US numbers (prefixes `+1`) or 11-digit numbers starting with `1`; rejects anything else with HTTP 400. Applied to `POST /submit`, `POST /request-settings-link`, and the admin add-user form. The inbound SMS path was already safe (Twilio normalizes to E.164). §9's "Authoritative phone normalization" guarantee is now true.

### #7 — Token hashing (§5.2)
`hash_token()` added in `utils/tokens.py` (`sha256(raw).hexdigest()`). `generate_settings_token()` now stores the hash; all three lookup sites (`GET /settings`, `GET /api/settings`, `POST /settings`) hash the incoming value before querying. The raw token still travels in the SMS link — only the stored value changed. Existing plaintext tokens were invalidated on deploy (30-min expiry makes this a non-issue).

### #9 — Server-side token validation on GET /settings (§5.3)
`settings_page()` now validates the token in the GET handler before rendering anything. Invalid/expired/used tokens render an inline error message; the form is never shown. Valid tokens prefill `local_time` and `timezone` server-side via Jinja2 — the client-side `loadSettings()` fetch to `/api/settings` has been removed.

### #10 — Timezone selector expanded (§5.3)
`US_TIMEZONES` constant defined in `admin/routes.py` with 12 entries covering all major US zones including Phoenix (MT no DST), Honolulu (Hawaii no DST), Anchorage/Nome/Juneau (Alaska), Adak (Hawaii-Aleutian), Indianapolis (Eastern no DST), and Boise (Mountain). Passed server-side to both `settings.html` and `admin/users.html`; both now render options with Jinja2. The admin add-user form also upgraded from a hidden `America/New_York` input to a full select.

### iOS signup form — consent, local_time, timezone (§4, TCPA)
`PhoneEntryView` and `PhoneEntryViewModel` updated to match the backend contract:
- **Consent checkbox**: custom checkbox control (SF Symbols `checkmark.square.fill` / `square`) with the approved TCPA disclosure text. Tapping anywhere on the row (icon or text) toggles the state.
- **Timezone picker**: sorted `Picker` over the same 12-zone list as the backend's `US_TIMEZONES` constant in `admin/routes.py`. Defaults to nil ("Select timezone") — a real selection is required.
- **Delivery time**: `DatePicker` (hour and minute only, `.compact` style).
- **Payload**: `POST /submit` now sends `phone`, `local_time` (formatted `HH:mm`), `timezone`, and `consent: true`.
- **Submit guard**: button disabled until both consent is checked and a timezone is selected. `signUp()` also guards on `canSubmit` as a belt-and-suspenders check.

Backend and frontend are now aligned on the `/submit` contract. Ready for end-to-end testing.

---

## Spec sections that still describe unimplemented behavior

None — all known gaps are resolved.
