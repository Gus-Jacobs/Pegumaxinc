# Security & Prod-Readiness Report

_Scan date: 2026-06-12. Ran `manage.py check --deploy` (clean), audited views/templates/settings,
and tested fixes with the Django test client._

## ✅ Fixed in this pass
- **CSRF on account endpoints (was account-takeover risk).** `edit_profile` and `change_password`
  were `@login_required` **and** `@csrf_exempt` — a forged cross-site POST could have changed a
  logged-in user's password/email. Removed `@csrf_exempt`; the forms already send the token, so it
  still works. Verified: forged POST → **403**, legitimate POST → **200**.
- **Entire bot API was unauthenticated.** Anyone could read bot earnings/logs/status, mark logs
  acknowledged, send the bot start/stop commands, or inject log entries. Now fully locked down
  (the bot isn't currently hooked up, so there was no risk in securing it):
  - `dashboard-data`, `get-logs`, `live-bot-status`, `acknowledge-logs` → **admin only** (`IsAdminUser`).
  - `receive-logs` and `bot-command` POST (heartbeat) → require the **bot API key** (`X-Bot-API-Key`).
  - `bot-command` PUT (admin sends start/stop) → **admin session + CSRF** (the dashboard already sends both).
  - Verified: anonymous → **403** everywhere; admin reads → **200**; API-key heartbeat → **200**;
    admin command with CSRF → **200**, forged command → **403**.
- **Public message endpoint hardened.** `/api/message/` now clamps name/email/message lengths to stop
  oversized-payload abuse. (Header injection isn't possible — Django rejects newlines in subjects.)
- **Account page bugs fixed.** Login history now loads **real** data from the server (it was showing
  hard-coded sample rows); profile-edit now updates the page correctly on success.

## ✅ Already solid (verified, no action needed)
- `manage.py check --deploy` passes: with `DEBUG=False` the app enables HSTS, SSL redirect, secure
  session/CSRF cookies, and X-Frame-Options.
- Templates auto-escape output; the only `|json_script` uses are XSS-safe; no secrets are committed
  (Stripe **secret** key and email creds come from env; the Stripe **publishable** key is public).
- Donation amounts are server-validated and clamped ($1–$10,000).

## ⚠️ You MUST set these env vars before production
| Variable | Why it matters |
|---|---|
| `DJANGO_SECRET_KEY` | Without it, Django falls back to an insecure built-in key. **Critical.** |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated domain(s), e.g. `pegumax.com,www.pegumax.com`. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | e.g. `https://pegumax.com` — **required** or login/signup/contact POSTs fail on HTTPS. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Gmail address + 16-char app password (form emails). |
| `STRIPE_DONATION_KEY` | Stripe restricted/secret key (donations). |
| `DJANGO_BOT_REMOTE_LOG_API_KEY` | Real bot API key (defaults to a dev fallback otherwise). |

## When you DO hook the bot back up
- The bot's logging/heartbeat client must send the header `X-Bot-API-Key: <DJANGO_BOT_REMOTE_LOG_API_KEY>`
  (set that env var to a strong secret in prod). Without it, `receive-logs` / `bot-command` POST return 403.
- The admin dashboard's start/stop buttons keep working as-is (session + CSRF, already wired).

## ⚠️ Recommended — optional
- **Pre-existing bug:** `LogReceiverView.post` calls `request.data.get(...)` before checking the payload is
  a list, so a JSON-list payload 500s. Harmless until the bot is live; worth tidying when you wire it up.
- Optional: add rate-limiting (e.g. `django-ratelimit`) to `/api/message/` and `/donate/create-session/`
  to further limit spam/abuse.
