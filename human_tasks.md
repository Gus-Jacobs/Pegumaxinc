# Academy — Phase 2 Human Tasks

Engineering for Phase 2 (pricing, dev tiers, gated merch, Printful sync, storefront
overhaul, smart promos) is code-complete. The items below require a human with
credentials/accounts and cannot be done from the codebase alone.

---

## Section 1 — Local Testing Tasks

1. **Pull latest & install deps**
   ```
   pip install -r pegumax_project/requirements.txt   # adds `requests`
   ```

2. **Apply migrations & re-seed** (from `pegumax_project/`)
   ```
   py manage.py migrate
   py manage.py seed_courses --fresh                  # courses now $12; tiered merch
   ```

3. **Add your Printful token to `.env`** (next to `manage.py`)
   - Printful → **Settings → API → Add private token** (scope: read products).
   - Paste it into `.env`:
     ```
     PRINTFUL_API_KEY=your_private_token
     # PRINTFUL_STORE_ID=12345    # only if your token spans multiple stores
     ```

4. **Create at least one test product in Printful**
   - Printful dashboard → **Product templates / Stores → Add product** (e.g. a tee).
   - Give it variants (sizes/colors) and a retail price so the sync has data.

5. **Run the sync and confirm it lands**
   ```
   py manage.py sync_printful --dry-run     # inspect, writes nothing
   py manage.py sync_printful               # upsert into MerchItem
   ```
   - Visit `/academy/` → **All Merch** tab; click a product → `/academy/merch/<slug>/`.

6. **Exercise the gamified gating**
   - New accounts start at Level 1 = **Dev Tier 1**. The seeded *Builder Tee* (Tier 2)
     and *Local-First Hoodie* (Tier 3) should show a locked "Unlock at Dev Tier…" button.
   - Pass courses to climb levels (L5 → Dev 2, L10 → Dev 3) and watch items unlock.

7. **Test the smart promo loop end-to-end**
   - Finish a course → a 50%-off reward code appears on `/academy/dashboard/`.
   - Click the code → routes to `/academy/?tag=<tag>&promo=<CODE>` with the banner shown.
   - Buy a matching merch item → the code is auto-attached to the Stripe Checkout session.
   - Use Stripe test card `4242 4242 4242 4242`, any future expiry/CVC.
   - After payment, confirm the code shows **redeemed** in Django admin (single-use).

8. **(Optional) Local webhook** for realistic fulfillment:
   ```
   stripe listen --forward-to localhost:8000/academy/webhook/stripe/
   ```
   Paste the printed `whsec_…` into `STRIPE_WEBHOOK_SECRET` in `.env`.

---

## Section 2 — Production Deployment (Render + Stripe + Printful)

### Render
- Set environment variables (Dashboard → service → **Environment**):
  - `PRINTFUL_API_KEY` (and `PRINTFUL_STORE_ID` if applicable)
  - Confirm existing: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`,
    `STRIPE_WEBHOOK_SECRET`, `DATABASE_URL`, `DJANGO_SECRET_KEY`,
    `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Deploy, then run on the instance / via a one-off job:
  ```
  python manage.py migrate
  python manage.py seed_courses          # if (re)seeding courses
  python manage.py sync_printful         # populate live merch
  ```
- `requests` ships in `requirements.txt`, so the build will install it.
- **Catalogue sync options:**
  - Local/manual: Django admin → **Merch items → "⟳ Sync from Printful"** button.
  - Production (automatic): add a **Render Cron Job** running
    `python manage.py sync_printful` (e.g. hourly/daily) so merch stays current
    without anyone clicking the admin button.
- **Dev-merch level gating:** name Printful products like `Developer 3 Hoodie`
  or `Developer 5 Tee` — `sync_printful` parses the number as the **required
  account level**, and the store grays-out / locks the item until the user
  reaches that level. Products without that prefix are available to everyone.
- **Reward codes:** the 50% completion code now discounts **one unit of one
  item** (chosen in the cart), computed at the line-item level — Stripe never
  discounts the whole order. No Stripe coupons are created for these.

### Stripe (LIVE mode)
- Use **live** keys in Render (`sk_live_…`, `pk_live_…`).
- **Webhooks** → add endpoint `https://<your-domain>/academy/webhook/stripe/`,
  event `checkout.session.completed`; copy the **live** signing secret into
  `STRIPE_WEBHOOK_SECRET`.
- Completion reward coupons are created server-side with **`max_redemptions=1`**;
  no manual coupon setup needed. (Verify your account allows API coupon creation.)
- Confirm your products/pricing tax & shipping settings if charging real cards.

### Printful (go-live)
- Move from sandbox/test product to real published products.
- Ensure billing / payment method is set in Printful so live orders can fulfill.
- **Auto-fulfillment is wired up.** On `checkout.session.completed`, the webhook
  submits a Printful order via `POST /orders`, mapping the Stripe shipping address
  to Printful's recipient and the cart's sync variants to order items.
- **Live vs. draft is environment-driven** (no code edit needed):
  - `PRINTFUL_CONFIRM_ORDERS` env var: `True` = confirm (real manufacturing +
    charges the Pegumax card), `False` = draft only.
  - If unset, it defaults to **confirmed in production** (`DEBUG=False`) and
    **draft locally** (`DEBUG=True`). So a normal Render deploy fulfills for real
    automatically — **make sure a payment method/billing is set in Printful** or
    confirmed orders will fail.
  - To do a safe live smoke-test first, set `PRINTFUL_CONFIRM_ORDERS=False` on
    Render, verify a draft appears, then remove it (or set `True`) to go live.
- A Printful API failure is logged and the webhook still returns 200, so Stripe
  never enters a retry loop.

### Local testing — physical fulfillment loop
1. `PRINTFUL_API_KEY` is set in `.env`. Run the Stripe CLI:
   `stripe listen --forward-to localhost:8000/academy/webhook/stripe/`
   and paste the printed `whsec_…` into `STRIPE_WEBHOOK_SECRET`.
2. Add merch to the cart and check out with test card `4242 4242 4242 4242`.
   Stripe will now prompt for a **shipping address** (and phone).
3. Watch the runserver console: you should see
   `Printful DRAFT order created (id=…)`. Confirm the draft in the Printful
   dashboard (Orders) — it should be in **Draft** status, not submitted.
