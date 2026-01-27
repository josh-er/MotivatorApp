
## `docs/scheduler.md`

# Scheduler Invariants & Time Semantics
This document defines the scheduling rules.
These are invariants, not implementation details.

---

## Core Guarantees
- At most one quote per user per local calendar day
- No retries
- No backfill
- Late sends are allowed if the scheduler was down
- Scheduling is based on user-local time

---

## Time Semantics
- All system timestamps are stored in UTC
- All scheduling decisions are made using:
  - now_utc → converted to user’s timezone
- local_time is a wall-clock preference, not a timestamp

---

## Send Logic (Conceptual)
A user is due if:
- opted_in is true
- local_time and timezone are set
- last_sent != today (in user’s local date)
- local_now >= scheduled_local_time

If the scheduler was down:
- the message is sent late
- but still only once per local day

---

## last_sent Rules
- last_sent is stored as a DATE
- It represents the user’s local calendar day
- It is not a timestamp
- It prevents duplicate sends within the same local day

---

## Explicit Non-Guarantees
- No guarantee of exact delivery minute
- No compensation for downtime beyond same-day catch-up
- No ordering guarantees across users

---

## Logging Expectations
- Delivery events: UTC timestamps
- Audit events: UTC timestamps
- Local time is never used for logs or compliance records

This document must remain true even if the implementation changes.
