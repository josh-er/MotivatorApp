# Motivator — Implementation Progress

Last updated: 2026-07-07

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

### Admin log gap closed — swallowed errors now reach EventLog (§11.2)
Investigation found a root-cause bug: `log_event()` is keyword-only (`db, *, user_id, event_type, source`) but `send_quotes.py` called it positionally, raising `TypeError` on every successful quote send and masking the failure inside a silent `except Exception` block — the SMS still went out, but `EventLog` never got the `"quote_sent"` row. Fixes:
- Corrected the `log_event` call site in `send_quotes.py`.
- Added a nullable `error_message` column to `EventLog` (migration `add_error_message_to_event_logs`, applied to the Render Postgres DB).
- `send_quotes.py`'s per-user send failure path and `scheduler.py`'s top-level loop failure path now both write an `EventLog` row (`quote_send_failed`, `scheduler_loop_failed`) with `error_message` populated, using a dedicated DB session so a broken primary session can't block the log write. Neither re-raises, since both run inside loops that must keep processing remaining users/ticks.
- All six previously flash-only admin panel exception handlers (`add_user` ×3, `delete_user`, `add_quote`, `delete_quote`) now also write an `EventLog` row (`source="admin"`, `error_message` populated) via a shared `_log_admin_failure()` helper, alongside the existing `flash()` messages.

Admins can now see every error case above in `/admin/events` — no more scenarios that require checking Render's raw logs directly.

### Rate limiting on settings link requests (§5.5)
`POST /request-settings-link` now enforces one link per phone number per 30-minute window (measured from the most recently issued token's `created_at`). Requesting within the window returns HTTP 429 with the remaining wait time. Requesting after the window invalidates any prior unexpired, unused token for that phone before issuing a new one. Known limitation (documented in code): no row-level locking, so two truly concurrent requests could both pass the check — acceptable for this low-traffic, user-triggered flow.

### Security audit — COMPLETE (2026-07-03)
Full-codebase review for SQL injection, token predictability, webhook auth, and rate limiting. No SQL injection found (ORM parameterized everywhere); tokens already `secrets.token_urlsafe` + sha256-hashed at rest. Fixes applied:

- **Twilio webhook signature verification** — `POST /sms/inbound` had zero authentication; anyone could forge `From`/`Body` to opt any user in or out. Now validated via `twilio.request_validator.RequestValidator` against `X-Twilio-Signature`, fails closed (403) if the signature is missing/invalid or `TWILIO_AUTH_TOKEN` isn't configured.
- **Hardcoded fallback secrets in production** — `FLASK_SECRET_KEY` (session signing) and `ADMIN_PASSWORD` defaulted to `"dev-secret"`/`"testpass"` if unset, and `render.yaml` never declared either for the web service. `app.py` now raises `RuntimeError` at startup if either is missing while `IS_PRODUCTION` (reusing `db.py`'s existing `RENDER`/`FLASK_ENV` detection) — dev keeps the convenience defaults.
- **Inconsistent production detection** — `app.py` gated `/init-db` and `/debug/users` on its own `ENV` var, which `render.yaml` never set (only `FLASK_ENV`), so those debug routes were reachable in production. Now gated on the same `IS_PRODUCTION` flag as `db.py`.
- **`log_event()` positional-args bug, second occurrence** — same shape as the `send_quotes.py` bug fixed above, found in two more call sites: `POST /submit` (app.py) and the SMS `START` re-activation handler (app.py). Both now use keyword args; signup and re-activation no longer 500 after already succeeding.
- **`/submit` `local_time` validation** — malformed `local_time` reached `datetime.strptime` unvalidated and threw an unhandled 500. Now validated against `HH:MM` up front, returns 400.
- **Settings-link re-activation rate limiting** — the `START` handler minted settings-link tokens with no rate limit or prior-token invalidation, unlike `POST /request-settings-link`. Now mirrors the same 30-minute-window + invalidate-prior-token logic.
- **Non-constant-time secret comparisons** — `admin_login` password check and both `X-Admin-Key` checks (`app.py`, `admin/auth.py`) now use `hmac.compare_digest`.
- **CSRF protection on admin panel** — the 4 state-changing admin forms (add/delete user, add/delete quote) had no CSRF protection. Added a per-session token (`secrets.token_urlsafe`) via a `context_processor` + `before_request` hook scoped to `admin_bp`, validated with `hmac.compare_digest`. No new dependency.
- **Admin login rate limiting** — no brute-force protection on `/admin/login`. Added an in-process, IP-keyed lockout (5 attempts / 5 minutes). Documented limitation: not persisted or shared across gunicorn's `--workers=2`, so the effective ceiling is up to 2× the stated limit — accepted tradeoff for a single shared admin password rather than a new DB table.
- **`POST /request-settings-link` account-takeover bug** — this endpoint never sent the settings link via SMS at all (`send_sms` wasn't even imported); it returned the raw, usable link directly in the JSON response. Anyone who knew a user's phone number could fetch and use a valid settings-change link without any SMS interception, defeating the "SMS is the control surface" design (§10). Now sends the link via `send_sms` (matching the `START` handler) and always returns an identical generic `{"status": "ok", ...}` body whether or not the phone is registered — this also closes a phone-number-enumeration side channel the same bug created. Also fixed a hardcoded `https://motivatorapp.onrender.com` domain in the link — now uses the `BASE_URL` env var like the rest of the app. **The link is no longer present in the response body under any circumstance** (SPEC.md §4 updated accordingly).

**Residual risk (accepted, deferred to post-launch)**: `POST /submit` has no per-phone or per-IP rate limiting. The `users.phone` unique constraint permanently blocks a second signup for a number that already has a user, but an attacker can still submit many *distinct* numbers, each triggering one real compliance SMS (an SMS-reflector / cost-abuse risk). Deferred until proper IP-based throttling (or a signup CAPTCHA) can be added post-launch.

**Audit status: all identified findings fixed except the one residual risk above, which is a deliberate, accepted tradeoff — not an oversight.**

### iOS — `POST /request-settings-link` response handling (2026-07-05)
`PhoneEntryViewModel.requestSettingsLink()` already didn't read `settings_link` from the response — `APIClient.postJSON` doesn't even decode a response body, and the view model just shows a generic message on success. The only leftover was an unused `SettingsLinkResponse` struct (with a `settings_link` field) in `APIModels.swift`, which has been deleted. No behavioral change; item closed.

### Testing pass — COMPLETE (2026-07-03)
Added an automated `pytest` suite (`tests/`, `pytest.ini`, `requirements-dev.txt`) covering every flow below via Flask's test client plus direct DB manipulation for time-based states (token expiry, rate-limit windows). 35 tests, all passing:
- `test_submit.py` — valid signup, duplicate phone, missing consent (absent + `false`), malformed `local_time`, invalid phone format
- `test_sms_inbound.py` — unknown-number START, opted-out START re-activation, STOP, forged/unsigned webhook requests (403), unknown-number no-op
- `test_settings_flow.py` — request link, GET valid/expired/used token, POST valid, POST replayed token (403)
- `test_rate_limiting.py` — settings-link 429 within the 30-min window + success after the window with prior-token invalidation, START re-activation rate limiting
- `test_scheduler.py` — `is_user_due` correctness, correct user selection at delivery time, `last_sent` dedup, opted-out exclusion
- `test_admin.py` — wrong password, correct password, 6th-attempt login lockout, CSRF rejected/accepted, `/debug/users` and `/init-db` confirmed unregistered when `RENDER=1`

Test env safety: `tests/conftest.py` sets sqlite/dummy-Twilio env vars before any `Motivator` module is imported, so the real Postgres `DATABASE_URL` and live Twilio credentials in `.env` are never touched.

Also fixed while writing tests: four `SQLAlchemy 2.0` `Query.get()` deprecation warnings surfaced by the suite, in `admin/routes.py` (`delete_user`, `settings_page`, `update_settings`, `get_settings`) — replaced with `db.get(Model, id)`.

### MotivatorUI added to the repo, Xcode cruft cleaned up (2026-07-07)
`MotivatorUI/` moved into the repo as a subfolder. `.gitignore` gained the missing Xcode entries (`DerivedData/`, `.build/`, `*.xcuserstate`, `xcuserdata/`, `.swiftpm/`); a stray `.DS_Store` and committed `xcuserdata/` directories were removed. No `DerivedData`/`.build` were present.

### iOS — returning-user flow and post-signup screen rework (2026-07-07)
- `PhoneEntryViewModel` now takes an `onSignUpSuccess` closure; a successful `POST /submit` sets `UserDefaults["hasSignedUp"] = true` and invokes it with the phone number instead of just showing a message.
- `ContentView` routes at launch based on `@AppStorage("hasSignedUp")`: fresh signup → `PostSignupInfoView`, returning user → new `ReturningUserView` (phone field + "Get settings link" button only), otherwise the normal signup form.
- New shared `SettingsLinkViewModel` backs the phone field + settings-link request on both `ReturningUserView` and `PostSignupInfoView`.
- `PostSignupInfoView` rewritten: confirmation message ("You're signed up. Check your phone for a confirmation text.") plus a visually distinct card (background + rounded corners) with the phone pre-filled and a "Get settings link" button.
- All "START" references removed from the app's UI text.
- The "Get settings link" button and its handler were subsequently removed from `PhoneEntryView`/`PhoneEntryViewModel` (dead code) since that functionality now lives only on `PostSignupInfoView`/`ReturningUserView`.

### iOS — configurable API base URL (2026-07-07)
`APIEndpoints.baseURL` now resolves via `#if DEBUG`/`#else`: `http://127.0.0.1:5000` for debug builds, `https://motivatorapp.onrender.com` for release builds. Uses Xcode's default `DEBUG` compilation condition on the Debug configuration — no project-settings changes needed. Both configurations verified to build clean.

### iOS — 429 rate-limit message on settings-link request (2026-07-07)
`SettingsLinkViewModel.requestSettingsLink()` now shows a user-friendly message on HTTP 429 instead of a generic failure: "A settings link was recently sent to your phone. Please wait 30 minutes before requesting another."

Fixing this surfaced a latent bug: `APIClient.postJSON` never inspected the HTTP response status code at all — any non-2xx response (429 included) was reported to callers as `.success`. Added `APIError.httpStatus(Int)`; `postJSON` now checks the status code and surfaces non-2xx responses as `.failure(APIError.httpStatus(code))`. `SettingsLinkViewModel` matches on 429 specifically; `PhoneEntryViewModel`'s generic `.failure` handling is unaffected (previously-silent non-2xx failures on `/submit` are now correctly reported as "Sign up failed.").

### iOS — `PhoneEntryViewModel` split into narrow view models (2026-08-25)
Performance refactor: `PhoneEntryViewModel`'s 6 `@Published` properties (each edit re-rendering the entire signup form) were split into five focused `ObservableObject`s, each with its own `@Published` state:
- `PhoneNumberViewModel` (`phone`)
- `DeliveryTimeViewModel` (`selectedTime`, plus `formattedLocalTime` for the `HH:mm` payload string)
- `TimezoneViewModel` (`timezone`)
- `ConsentViewModel` (`consentChecked`)
- `SubmissionStatusViewModel` (`message`, `isLoading`)

`PhoneEntryViewModel` is now a coordinator: it owns one instance of each, exposes `canSubmit`/`signUp()`, and no longer declares any `@Published` properties of its own. `PhoneEntryView` was split to match — `PhoneNumberField`, `DeliveryTimePicker`, `TimezonePicker`, `ConsentCheckboxRow`, `SubmitButton`, and `SubmissionStatusView` are private child views, each `@ObservedObject`-bound to only the view model(s) it needs. `SubmitButton` observes `ConsentViewModel` + `TimezoneViewModel` directly (the only two that gate `canSubmit`) so the button's disabled state stays live without the parent view re-rendering. Net effect: typing in the phone field, moving the time picker, etc. now only re-renders the one field touched, not the whole form. Build verified via `xcodebuild ... build` (BUILD SUCCEEDED).

### render.yaml audit and requirements.txt cleanup (2026-07-07)
Audited `render.yaml` against the actual repo: every `buildCommand`/`startCommand` file reference and the `databases:`/`fromDatabase` name pairing were checked for existence and consistency.

- **Scheduler `startCommand` fixed** — was `python Motivator/run_scheduler.py`, a file that doesn't exist anywhere in the repo (the module is `Motivator/scheduler.py`, which has an `if __name__ == "__main__":` block and is already imported elsewhere as `Motivator.scheduler`). This would have made the `motivator-scheduler` worker fail to start on every deploy. Now `python -m Motivator.scheduler`.
- Web service's `gunicorn Motivator.app:app` target confirmed valid (`app = Flask(__name__)` at `app.py:53`).
- **`requirements.txt` — removed `APScheduler` and `PyJWT`**, both unused: grepped clean across `Motivator/`, `tests/`, `scripts/`, `migrations/`. `scheduler.py` implements its own polling loop rather than using APScheduler; settings tokens (`utils/tokens.py`) use `hashlib`/`secrets`, not JWT.

---

## Remaining pre-launch items

- **Admin add-user removal** — per SPEC.md §11.1, add-user functionality must be removed from the admin panel before launch (delete, quotes management, and log viewing remain in scope).

---

## Post-launch cleanup

- **`POST /submit` rate limiting** — accepted residual risk from the security audit (see above); revisit post-launch with IP-based throttling or a signup CAPTCHA.
- **Remove legacy `User.time` column** — write-only field set in `user_service.py::create_user()`; nothing in the codebase reads it back. Predates `local_time`/`timezone` and was only kept "for compatibility during migration" (see `models.py`). Drop the column and the assignment once confirmed nothing external depends on it.
- **Rate limiting on inbound SMS webhook (`POST /sms/inbound`)** — no explicit per-number throttle on the handler itself, so rapid START/STOP cycling isn't blocked at that layer. Current mitigation: the 30-minute settings-link token window blocks settings-link spam specifically, and Twilio rate limits webhook calls generally, but neither constrains STOP/START toggling directly. Add a per-number throttle post-launch.
