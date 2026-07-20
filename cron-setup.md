# Pegumax — Order-Retry Setup (QStash + once-daily safety-net sweep)

## What this is / why it matters
Pegumax has a worst-case order-recovery pipeline: if a customer pays but the
Printful order fails, the order is queued and **automatically retried**; if it
still can't be fulfilled within ~3 hours, the customer is granted a store credit.

There are **two** triggers for that retry loop:

1. **QStash (primary, event-driven).** The moment a Printful order fails, the
   Stripe webhook schedules a delayed retry through
   [Upstash QStash](https://upstash.com/docs/qstash). Each failed retry
   re-schedules itself with backoff (**5m → 15m → 45m → 2h15m**) until it either
   succeeds or the 3-hour window closes and a store credit is granted. Because
   this only fires when an order *actually* fails, the database stays asleep
   (letting Neon auto-suspend) instead of being polled every few minutes.

2. **A once-daily safety-net sweep (backstop).** A free external scheduler pings
   a token-protected URL **once a day** to catch anything the QStash chain
   missed — e.g. an order that failed while QStash was briefly unreachable.

> **Why the change?** We used to ping every 5 minutes, which kept the Neon
> database awake 24/7. QStash makes retries event-driven, so the scheduler is now
> just a daily backstop.

Both triggers hit the **same** endpoint and share the **same** per-order logic,
so an order can never be charged or manufactured twice.

---

## Part 1 — QStash setup (the primary trigger)

**In Upstash (https://console.upstash.com → QStash):**
1. Create a free account / open the QStash tab.
2. Copy these three values from the QStash dashboard:
   - **QSTASH_TOKEN** (under "Request Builder" / the token at the top)
   - **QSTASH_CURRENT_SIGNING_KEY**
   - **QSTASH_NEXT_SIGNING_KEY** (both under "Signing Keys")

**In Render → your service → Environment:** add all three as environment
variables with those exact names, then redeploy.

That's the entire QStash setup — no schedule to configure there. QStash posts
back to our retry endpoint, and we **verify its signature** with the two signing
keys, so no random request can trigger a retry.

**The exact URL QStash calls back (for reference / debugging):**

| Field | Value |
|-------|-------|
| **Destination URL** | `https://pegumax.com/academy/tasks/retry-orders/` |
| **Method** | `POST` (with header `Upstash-Signature`) |
| **Body** | `{"session_id": "cs_..."}` |
| **Auth** | QStash JWT signature, verified against the two signing keys (fail-closed → `401`) |

> This URL must match the site's `PEGUMAX_SITE_URL` env var exactly (it's what we
> both publish to and verify against). If the site ever moves off `pegumax.com`,
> update `PEGUMAX_SITE_URL` in Render.

If `QSTASH_TOKEN` is blank, retries simply aren't scheduled and the daily sweep
below becomes the only net — the app still runs, it just recovers failed orders
once a day instead of within minutes.

---

## Part 2 — The once-daily safety-net sweep

This is the backstop. QStash (Part 1) does the fast, event-driven retries; this
just sweeps once a day for stragglers. The endpoint is the same URL — when it's
called with the token (instead of a QStash signature) it processes any orders
still stuck in `printful_failed`.

### The endpoint (the thing that gets pinged)

| Field | Value |
|-------|-------|
| **URL** | `https://pegumax.com/academy/tasks/retry-orders/` |
| **Method** | `GET` |
| **Auth** | a secret token, sent **either** as a header `X-Task-Token: <TOKEN>` (preferred) **or** as a query param `?token=<TOKEN>` |
| **Token value** | the `TASK_RUNNER_TOKEN` environment variable set in Render (a long random string) |
| **How often** | **once a day** (e.g. at midnight) |
| **Success response** | HTTP `200` with JSON body like `{"ok": true, "output": "..."}` |
| **Auth failure** | HTTP `403` (wrong/missing token, or the token isn't configured on the server) |

> Prefer the **header** method. Query strings appear in server access logs, so
> `?token=...` would leak the secret into logs. `X-Task-Token` does not.

**Prerequisites (already done in Render):**
- `TASK_RUNNER_TOKEN` is set to a long random value.
- The site is deployed and reachable at `https://pegumax.com`.

---

## Quick manual test first (do this before scheduling)

Replace `YOUR_TOKEN` with the `TASK_RUNNER_TOKEN` value from Render.

**macOS / Linux / Git Bash:**
```
curl -i -H "X-Task-Token: YOUR_TOKEN" https://pegumax.com/academy/tasks/retry-orders/
```

**Windows PowerShell** — do NOT use plain `curl` here; in PowerShell `curl` is an
alias for `Invoke-WebRequest` and it will error with *"Missing an argument for
parameter 'InFile'"*. Use one of these instead:
```powershell
# Real curl (bundled with Windows 10/11):
curl.exe -i -H "X-Task-Token: YOUR_TOKEN" https://pegumax.com/academy/tasks/retry-orders/

# …or the native cmdlet:
Invoke-WebRequest -Uri "https://pegumax.com/academy/tasks/retry-orders/" -Headers @{ "X-Task-Token" = "YOUR_TOKEN" } | Select-Object StatusCode, Content
```

- Expect: HTTP `200` and a JSON body starting `{"ok": true`.
- If you get `403`: the token doesn't match what's in Render (or Render's
  `TASK_RUNNER_TOKEN` is blank). Fix that before continuing.

---

## Option A — cron-job.org (recommended: free, reliable)

1. Go to **https://cron-job.org** and create a free account.
2. Click **Create cronjob** (or "CREATE CRONJOB").
3. **Title:** `Pegumax retry orders (daily sweep)`
4. **Address (URL):** `https://pegumax.com/academy/tasks/retry-orders/`
5. **Schedule:** choose **Every day** at a quiet hour (e.g. `0 0 * * *` for
   midnight). This is only a backstop now — QStash handles prompt retries.
6. Open **Advanced settings** (or the "Advanced" tab):
   - **Request method:** `GET`
   - **Headers:** add a header:
     - Name: `X-Task-Token`
     - Value: `YOUR_TASK_RUNNER_TOKEN` (the exact value from Render)
   - **Treat as success:** HTTP status `200` (default is fine).
   - (Optional) enable **Save responses** so you can inspect results.
7. **Save / Create.**
8. Use **Run now** (or wait for the daily run), then open the cronjob's
   **History / Execution log**. You should see a `200` response. Click it to
   confirm the body is `{"ok": true, ...}`.

That's it — it now sweeps once a day forever.

---

## Option B — UptimeRobot (not ideal here)

UptimeRobot's minimum interval is 5 minutes and it can't be set to run once a
day, so it would ping our endpoint constantly — waking the Neon database every 5
minutes and defeating the auto-suspend savings that QStash gives us. **Prefer
cron-job.org (Option A) for the once-daily sweep.** Only use UptimeRobot if you
specifically want frequent monitoring and don't mind the database staying warm.

---

## Option C — GitHub Actions (fully in your repo, but less punctual)

Only if you'd rather keep it in the repo. Note: GitHub's scheduled workflows are
often **delayed 5–20 minutes** and can be auto-disabled on inactive repos, so
cron-job.org is more reliable for time-sensitive retries.

1. In the repo, create `.github/workflows/retry-orders.yml`:
   ```yaml
   name: Retry failed orders (daily sweep)
   on:
     schedule:
       - cron: "0 0 * * *"    # once a day at midnight UTC (GitHub may delay this)
     workflow_dispatch: {}      # lets you run it manually from the Actions tab
   jobs:
     ping:
       runs-on: ubuntu-latest
       steps:
         - name: Ping retry endpoint
           run: |
             curl -fsS -H "X-Task-Token: ${{ secrets.TASK_RUNNER_TOKEN }}" \
               https://pegumax.com/academy/tasks/retry-orders/
   ```
2. In GitHub: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `TASK_RUNNER_TOKEN`
   - Value: the same token as in Render.
3. Commit + push. Watch the **Actions** tab; use **Run workflow** to test on demand.

---

## How to know it's working (ongoing)

- **QStash side:** Upstash console → QStash → **Logs / Events** shows each
  scheduled retry, its delay, and the `200`/`401` our endpoint returned. A
  healthy failed-order recovery looks like a short chain of deliveries a few
  minutes apart, ending when the order is fulfilled or credited.
- **Scheduler side:** the daily cron-job.org history shows a `200` once a day.
- **App side:** when there ARE failed orders, the token-sweep response `output`
  field shows lines like `[ok] cs_... fulfilled` or `[!] cs_... credited`. When
  there's nothing to do it returns `{"ok": true, "output": "No failed orders to
  retry."}` — the normal, healthy state most of the time.
- **Admin:** Django admin → **Fulfilled orders** shows statuses; failed ones move
  to `processed` (retry succeeded) or `credited` (gave up → store credit granted).

---

## Security notes
- **Token sweep:** the endpoint does nothing unless the token matches
  `TASK_RUNNER_TOKEN`; a wrong or missing token returns `403`. If the env var is
  blank, the token path is fully disabled (always 403). Prefer the **header**
  method so the token stays out of access logs. Rotate by changing
  `TASK_RUNNER_TOKEN` in Render and updating the scheduler.
- **QStash callbacks:** a request that arrives with an `Upstash-Signature` header
  is verified against `QSTASH_CURRENT_SIGNING_KEY` / `QSTASH_NEXT_SIGNING_KEY`
  before anything runs. A bad/forged signature — or missing signing keys on the
  server — returns `401` (fail-closed). To rotate keys, update both env vars in
  Render (QStash gives you a "current" and "next" precisely so rotation is
  zero-downtime).

## Troubleshooting
- **403 every time:** token mismatch. Compare the scheduler's token to Render's
  `TASK_RUNNER_TOKEN` exactly (no extra spaces/quotes). Redeploy if you just changed it.
- **404:** wrong URL — it must be exactly `/academy/tasks/retry-orders/` (trailing slash included).
- **Timeouts / 502:** the app may be waking from sleep (free tiers) or Printful is
  slow; the next ping will pick up where it left off — the retry is safe to run
  repeatedly and never double-orders.
- **Nothing happening but you expected a retry:** confirm there's actually a
  `printful_failed` order in Django admin → Fulfilled orders. If everything is
  `processed`, there's simply nothing to retry (good).
- **QStash logs show `401`:** the signing keys in Render don't match Upstash, or
  they're blank. Re-copy `QSTASH_CURRENT_SIGNING_KEY` / `QSTASH_NEXT_SIGNING_KEY`
  and redeploy. (We fail closed on purpose, so a mismatch means retries stop
  until it's fixed — the daily sweep still covers you meanwhile.)
- **QStash never fires at all:** check `QSTASH_TOKEN` is set in Render and that
  `PEGUMAX_SITE_URL` matches the real site host — QStash posts to that URL.
