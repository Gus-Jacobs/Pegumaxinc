# Pegumax — External Cron Setup (retry-failed-orders pinger)

## What this is / why it matters
Pegumax has a worst-case order-recovery pipeline: if a customer pays but the
Printful order fails, the order is queued and **automatically retried**; if it
still can't be fulfilled, the customer is granted a store credit. That retry
loop is driven by one URL that must be **called every ~5 minutes**.

Render (our host) doesn't include free cron jobs, so we trigger the retry with a
**free external scheduler** that pings a token-protected URL on our site. This
document explains exactly how to set that up. If it isn't set up, failed orders
won't retry or escalate — so this matters.

---

## The endpoint (the thing that must be pinged)

| Field | Value |
|-------|-------|
| **URL** | `https://pegumax.com/academy/tasks/retry-orders/` |
| **Method** | `GET` |
| **Auth** | a secret token, sent **either** as a header `X-Task-Token: <TOKEN>` (preferred) **or** as a query param `?token=<TOKEN>` |
| **Token value** | the `TASK_RUNNER_TOKEN` environment variable set in Render (a long random string) |
| **How often** | every **5 minutes** |
| **Success response** | HTTP `200` with JSON body like `{"ok": true, "output": "..."}` |
| **Auth failure** | HTTP `403` (wrong/missing token, or the token isn't configured on the server) |

> Prefer the **header** method. Query strings appear in server access logs, so
> `?token=...` would leak the secret into logs. `X-Task-Token` does not.

**Prerequisites (already done in Render):**
- `TASK_RUNNER_TOKEN` is set to a long random value.
- The site is deployed and reachable at `https://pegumax.com`.

---

## Quick manual test first (do this before scheduling)

From a terminal (replace `YOUR_TOKEN`):
```
curl -i -H "X-Task-Token: YOUR_TOKEN" https://pegumax.com/academy/tasks/retry-orders/
```
- Expect: `HTTP/1.1 200 OK` and a JSON body starting `{"ok": true`.
- If you get `403`: the token doesn't match what's in Render (or Render's
  `TASK_RUNNER_TOKEN` is blank). Fix that before continuing.

---

## Option A — cron-job.org (recommended: free, reliable, 5-min friendly)

1. Go to **https://cron-job.org** and create a free account.
2. Click **Create cronjob** (or "CREATE CRONJOB").
3. **Title:** `Pegumax retry orders`
4. **Address (URL):** `https://pegumax.com/academy/tasks/retry-orders/`
5. **Schedule:** choose **Every 5 minutes** (in the "Common" schedule presets, or
   set the custom pattern so it runs at minutes `*/5`).
6. Open **Advanced settings** (or the "Advanced" tab):
   - **Request method:** `GET`
   - **Headers:** add a header:
     - Name: `X-Task-Token`
     - Value: `YOUR_TASK_RUNNER_TOKEN` (the exact value from Render)
   - **Treat as success:** HTTP status `200` (default is fine).
   - (Optional) enable **Save responses** so you can inspect results.
7. **Save / Create.**
8. Wait ~5 min, then open the cronjob's **History / Execution log**. You should
   see `200` responses. Click one to confirm the body is `{"ok": true, ...}`.

That's it — it now pings every 5 minutes forever.

---

## Option B — UptimeRobot (also free)

UptimeRobot is a uptime monitor, but a "monitor" is just a periodic HTTP request,
which is exactly what we need.

1. Sign up at **https://uptimerobot.com** (free plan).
2. **Add New Monitor.**
3. **Monitor Type:** `HTTP(s)`.
4. **Friendly Name:** `Pegumax retry orders`.
5. **URL:** `https://pegumax.com/academy/tasks/retry-orders/?token=YOUR_TASK_RUNNER_TOKEN`
   - (UptimeRobot's free plan can't send custom headers, so the token goes in the
     query string here. It works, but the token will appear in our access logs —
     acceptable, just less clean. Use cron-job.org if you want the header method.)
6. **Monitoring interval:** `5 minutes` (the free plan's minimum).
7. **Create Monitor.**
8. Check that it reports "Up" (200). You can view response details in the log.

---

## Option C — GitHub Actions (fully in your repo, but less punctual)

Only if you'd rather keep it in the repo. Note: GitHub's scheduled workflows are
often **delayed 5–20 minutes** and can be auto-disabled on inactive repos, so
cron-job.org is more reliable for time-sensitive retries.

1. In the repo, create `.github/workflows/retry-orders.yml`:
   ```yaml
   name: Retry failed orders
   on:
     schedule:
       - cron: "*/5 * * * *"   # every 5 minutes (GitHub may delay this)
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

- **Scheduler side:** the job/monitor history shows regular `200` responses.
- **App side:** when there ARE failed orders, the response `output` field will
  show lines like `[ok] cs_... fulfilled` or `[!] cs_... credited`. When there's
  nothing to do, it returns `{"ok": true, "output": "No failed orders to retry."}`
  — that's the normal, healthy state most of the time.
- **Admin:** Django admin → **Fulfilled orders** shows statuses; failed ones move
  to `processed` (retry succeeded) or `credited` (gave up → store credit granted).

---

## Security notes
- The endpoint does nothing unless the token matches `TASK_RUNNER_TOKEN`; a wrong
  or missing token returns `403`. If the env var is blank, the endpoint is fully
  disabled (always 403).
- Keep the token secret. Prefer the **header** method so it stays out of access logs.
- If the token is ever exposed, rotate it: change `TASK_RUNNER_TOKEN` in Render,
  then update the header/URL in your scheduler.

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
