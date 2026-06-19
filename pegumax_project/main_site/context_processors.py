"""Site-wide template context: the product catalogue + Stripe key + active nav.

Add or edit an app in PRODUCTS and every page (home cards, software grid,
marquee, stat counters, footer) updates automatically.
"""
from django.conf import settings

PRODUCTS = [
    {
        "key": "apex", "name": "Apex Studio", "cat": "tool",
        "status": "live", "free": True, "featured": True,
        "tagline": "Media downloader & converter",
        "desc": "Download and convert media across 20+ formats with a fast, fully-local backend.",
        "img_static": "img/apex-hero.webp", "icon": "fa-film",
        "grad": "#7c5cff,#22d3ee", "url_name": "main_site:apex_studio",
        "platforms": ["windows"],
    },
    {
        "key": "student", "name": "Student Suite", "cat": "suite",
        "status": "live", "free": False, "featured": True,
        "tagline": "Your all-in-one study companion",
        "desc": "Courses, flashcards, AI tutors, resume & interview tools — everywhere you study.",
        "img_static": "img/studentsuite_hero.png", "icon": "fa-graduation-cap",
        "grad": "#22d3ee,#36e0a0", "url_name": "main_site:student_suite_launch",
        "platforms": ["web", "apple", "android"],
    },
    {
        "key": "lucidcut", "name": "LucidCut", "cat": "tool",
        "status": "live", "free": True, "featured": True,
        "tagline": "High-precision media cleanup",
        "desc": "Pinpoint word detection plus beta imagery detection — the go-to for cleaning up movies and videos.",
        "img_static": "img/lucidcut_hero.png", "icon": "fa-scissors",
        "grad": "#f7b731,#fa8231", "url_name": "main_site:lucidcut",
        "platforms": ["windows"],
    },
    {
        "key": "gameportal", "name": "Game Portal", "cat": "game",
        "status": "live", "free": True, "featured": False,
        "tagline": "One launcher for every game",
        "desc": "A single secure launcher for your game collection — auto-updates and progress tracking built in.",
        "img_static": "img/nancy-drew-hero.webp", "icon": "fa-puzzle-piece",
        "grad": "#22d3ee,#7c5cff", "url_name": "main_site:game_portal",
        "platforms": ["windows"],
    },
    {
        "key": "scribe", "name": "Scribe", "cat": "suite",
        "status": "live", "free": True, "featured": False,
        "tagline": "Your offline document editor",
        "desc": "A free, fully-offline document editor. No accounts, no cloud, no nonsense — just write.",
        "img_static": "img/scribe_hero.png", "icon": "fa-feather",
        "grad": "#7c5cff,#9d83ff", "url_name": "main_site:scribe",
        "platforms": ["windows"],
    },
    {
        "key": "contour", "name": "Contour", "cat": "tool",
        "status": "soon", "free": False, "featured": False,
        "tagline": "Your drawing & handwriting guide",
        "desc": "Upload an image or pick a handwriting style and learn to draw it. Trace in AR through your camera, or export coloring-book pages.",
        "img_static": "img/contour_hero.png", "icon": "fa-pen-nib",
        "grad": "#36e0a0,#22d3ee", "url_name": "main_site:contour",
        "platforms": ["apple", "android"],
    },
    {
        "key": "inference", "name": "Inference", "cat": "game",
        "status": "soon", "free": False, "featured": False,
        "tagline": "Run the machine. Take over the AI world.",
        "desc": "A strategy game where you run the machine — upgrade your model and seize control of the AI world.",
        "img_static": "img/inference_hero.png", "icon": "fa-microchip",
        "grad": "#8854d0,#a55eea", "url_name": "main_site:inference",
        "platforms": ["windows"],
    },
]

# url_name -> which top-nav item should be highlighted
_SECTION_BY_URL = {
    "home": "home",
    "software_center": "software",
    "apex_studio": "software", "lucidcut": "software", "movie_word_scanner": "software",
    "scribe": "software", "contour": "software", "inference": "software",
    "game_portal": "software", "student_suite_launch": "software",
    "about": "about", "policy": "about",
    "community": "community", "contact": "community",
    "store": "store",
}


def site(request):
    plats = set()
    for p in PRODUCTS:
        plats.update(p["platforms"])
    live = [p for p in PRODUCTS if p["status"] == "live"]
    soon = [p for p in PRODUCTS if p["status"] == "soon"]
    active = ""
    match = getattr(request, "resolver_match", None)
    if match is not None:
        active = _SECTION_BY_URL.get(match.url_name, "")
    return {
        "stripe_pk": getattr(settings, "STRIPE_PUBLISHABLE_KEY", ""),
        "products": PRODUCTS,
        "featured_products": [p for p in PRODUCTS if p.get("featured")],
        "active_section": active,
        "stats": {
            "live": len(live),
            "soon": len(soon),
            "platforms": len(plats),
            "total": len(PRODUCTS),
        },
    }
