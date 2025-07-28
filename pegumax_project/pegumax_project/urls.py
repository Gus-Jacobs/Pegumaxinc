"""
URL configuration for pegumax_project project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings

# Import TemplateView for the root index.html
from django.views.generic import TemplateView
# Import serve for serving specific static files (assets)
from django.views.static import serve


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')),

    # --- START: URL Patterns for serving the Flutter Student Suite app with Clean URLs ---

    # 1. Catch-all for the Flutter App itself:
    # This pattern will serve the index.html for the base URL and for any deep links
    # (e.g., /software-center/student-suite/dashboard).
    # It must come *before* the static file serving pattern for the app,
    # otherwise, requests like 'software-center/student-suite/main.dart.js' would
    # try to serve index.html. Wait, NO. This logic is reversed.
    # We need to serve the assets FIRST, then the catch-all for index.html.

    # REVISED LOGIC:
    # First, try to serve exact static files (like .js, .css, .json etc.)
    # from the Flutter app's directory under STATIC_ROOT.
    # If the request doesn't end with a known static file extension, or is the root,
    # then serve index.html.

    # 1. Serve Flutter's *assets* (JS, CSS, fonts, images, manifest, etc.)
    # This pattern explicitly matches files like flutter_bootstrap.js, main.dart.js,
    # assets/some_image.png, manifest.json, etc.
    # This must come BEFORE the index.html catch-all to ensure assets are served directly.
    re_path(r'^software-center/student-suite/(?P<path>(?!index\.html$).*)$', serve, {
        'document_root': settings.STATIC_ROOT / 'frontend' / 'student-suite-web',
        'insecure': True # Necessary for serve() in production (DEBUG=False)
    }),
    # The `(?!index\.html$)` negative lookahead ensures this pattern doesn't
    # mistakenly serve `index.html` if someone explicitly requests `.../student-suite/index.html`.
    # It also means the pattern won't match the base URL `.../student-suite/` (without a path).

    # 2. Serve the base index.html for the Flutter app and handle Flutter's internal routing:
    # This pattern matches '/software-center/student-suite/' and any deep links
    # (e.g., /software-center/student-suite/dashboard, /software-center/student-suite/profile).
    # It must come AFTER the static file serving pattern for the app.
    re_path(r'^software-center/student-suite(?:/.*)?$', TemplateView.as_view(template_name='frontend/student-suite-web/index.html')),

    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
if settings.DEBUG:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    pass
