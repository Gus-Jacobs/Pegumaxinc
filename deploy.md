# Pegumax — Deploy & "Add a New Tool" Guide

How to add a new software tool/product to the site, and the general production
deploy steps. (For the Store/Academy + Stripe + Printful specifics, see
`human_tasks.md`.)

---

## A. Adding a new software tool (Apex Studio, LucidCut, Scribe, …)

Tools are **content/config only — no database changes**. A tool is driven by one
central catalogue entry + a dedicated page. The home cards, software grid,
marquee, and stat counters all read from the catalogue automatically.

### 1. Register it in the product catalogue
`pegumax_project/main_site/context_processors.py` → add a dict to `PRODUCTS`:

```python
{
    "key": "lucidcut",                      # unique slug
    "name": "LucidCut",                     # display name
    "cat": "tool",                          # "tool" | "suite" | "game"
    "status": "live",                       # "live" shows it as available; "soon" shows a teaser
    "free": True,                           # True / False
    "featured": True,                       # show in the home featured row
    "tagline": "High-precision media cleanup",
    "desc": "Short description used on cards / marquee.",
    "img_static": "img/lucidcut_hero.png",  # hero image (see step 2)
    "icon": "fa-scissors",                  # Font Awesome icon name
    "grad": "#f7b731,#fa8231",              # two-colour accent gradient
    "url_name": "main_site:lucidcut",       # route name from step 3
    "platforms": ["windows"],               # any of: windows web apple android linux
},
```

### 2. Add the hero image
Put the image in `pegumax_project/assets/img/` with the filename used in
`img_static`. It's published automatically by `collectstatic` on deploy.

### 3. Add route + view + nav highlight
- **`main_site/urls.py`** — `path('lucidcut/', views.lucidcut_view, name='lucidcut')`
- **`main_site/views.py`** — `def lucidcut_view(request): return render(request, 'lucidcut.html')`
- **`main_site/context_processors.py`** → `_SECTION_BY_URL` — add
  `"lucidcut": "software"` so the top-nav "Software" tab highlights on that page.

### 4. Create the tool page template
Copy an existing one (`templates/lucidcut.html` or `templates/apex_studio.html`)
to `templates/<tool>.html` and edit. Include: hero (icon/tagline/badges),
features list, a **Download** section, and the "unsigned Windows build" note.

### 5. Wire the download link (do this on every release)
Point the platform button at the GitHub **release asset** URL, in the form:
```
https://github.com/Gus-Jacobs/<Repo>/releases/download/v<X.Y.Z>/<Installer>.exe
```
Live example — LucidCut v1.0.0 (in `templates/lucidcut.html`):
```
https://github.com/Gus-Jacobs/LucidCut/releases/download/v1.0.0/LucidCut-Setup-1.0.0.exe
```
On each new version, bump **both** the version label and the URL in that tool's
template. Platforms not yet shipped stay as disabled "Soon" buttons.

### 6. (Optional) Footer "Products" link
`templates/base.html` → footer Products column → add
`<a class="fl" href="{% url 'main_site:<name>' %}">Tool</a>`.

### 7. "soon" → "live"
When a tool is ready, flip its `status` from `"soon"` to `"live"` in `PRODUCTS`.
`"soon"` items show a teaser/notify form instead of a download.

### 8. Ship
```
git add -A
git commit -m "Add <Tool> vX.Y.Z (live)"
git push
```
Render auto-builds. **No migration needed for a tool** (no DB models). After
deploy, verify: home page, `/software-center/`, the tool page, the download link,
and that the nav "Software" tab highlights.

#### Quick checklist
- [ ] `PRODUCTS` entry added (status correct)
- [ ] hero image in `assets/img/`
- [ ] route + view + `_SECTION_BY_URL` entry
- [ ] `templates/<tool>.html` created
- [ ] download URL points at the new GitHub release
- [ ] (optional) footer link
- [ ] commit + push + verify live

---

## B. General production deploy (Render)

1. **Branch:** Render builds the branch set in the service (usually `main`).
   Merge your work to that branch and push.
2. **Build command** (already configured):
   `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   — so static files + migrations are handled automatically on every deploy.
3. **Env vars** (Render → Environment): `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
   `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL` (+ `DJANGO_DB_SSL_REQUIRE=True`),
   live Stripe keys, `STRIPE_WEBHOOK_SECRET`, `PRINTFUL_API_KEY`, email creds.
   **Never set `DJANGO_DEBUG=True` in production.**
4. **One-off commands** (Render → Shell), only when relevant:
   - Store catalogue: `python manage.py sync_printful`
   - Courses (only if missing in the prod DB): `python manage.py seed_courses` (never `--fresh` in prod)
5. **Smoke test:** home, software pages + downloads, `/academy/`, a test checkout.

See `human_tasks.md` for the full Store/Academy + Stripe + Printful go-live detail.
