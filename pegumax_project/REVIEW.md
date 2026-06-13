# Pegumax — what you need to do

The **entire site now uses the new Midnight Premium theme** — every page, not just the home page.
I verified locally that all routes render (public + login-gated admin) and all templates compile.

---

## To run it LOCALLY

1. Install dependencies (adds `stripe`):
   ```
   pip install -r requirements.txt
   ```
2. Run with debug on (so it doesn't force HTTPS and images serve from `assets/`):
   ```powershell
   $env:DJANGO_DEBUG = "True"
   py manage.py runserver
   ```
   Open http://127.0.0.1:8000/  (stop any old server already on :8000 first.)

Notes: locally, form emails print to the terminal (no mail creds locally) and donations show
"not configured" unless you set `STRIPE_DONATION_KEY`. Both work for real on the server.

---

## To go LIVE on your server

Confirm these env vars exist for the app, then deploy as usual (`pip install -r requirements.txt`
+ your normal `collectstatic`):

| Variable | Why |
|---|---|
| `EMAIL_HOST_USER` | Gmail address — sends + receives form emails |
| `EMAIL_HOST_PASSWORD` | Gmail app password (16 chars, no spaces) |
| `STRIPE_DONATION_KEY` | Stripe restricted/secret key — enables donations |
| `DJANGO_DEBUG` | must be `False` (or unset) in production |

That's everything you have to do.

---

## What changed (no action needed)

- **Single theme via `base.html`** + `static/css/pegumax.css` + `static/js/pegumax.js`. Every page
  extends `base.html`, so the nav, footer, donate/feedback/login modals, and animations are shared.
- **App cards & links now open real app pages.** Each card on Home/Software links to its detail page:
  Apex Studio, Student Suite, LucidCut (was Movie Word Scanner), Game Portal (Nancy Drew branding
  dropped), Scribe, **Contour** (new), **Inference** (new). All download links / the Game Portal PIN
  gate / Student Suite launch options are preserved and working.
- **New pages wired up:** `/lucidcut/`, `/scribe/`, `/contour/`, `/inference/` (views + URLs added).
- **Add or change an app in one place:** edit the `PRODUCTS` list in
  `main_site/context_processors.py` — the home cards, software grid, marquee, and stat counters all
  update automatically. (Set a `url_name`, image, and `status`/`free` flags.)
- **Auth, account, contact, policy, payment, 404/500, and the admin dashboards** are all re-themed;
  the admin dashboards keep all their original live polling/controls.
- App cards' **download buttons** point at your real GitHub/App Store/Play URLs (carried over from
  the old pages). The only placeholders are the "Notify me"/"Wishlist" buttons on the 3 coming-soon
  apps, which open the feedback form.
- Old templates (e.g. `software-center.html`, `movie-word-scanner.html`) are left in place unused as
  backups; nothing references them.
