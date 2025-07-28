"""
URL configuration for pegumax_project project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView
from django.views.static import serve as django_serve_static # Import the original if needed elsewhere, but not here for Flutter assets
from . import views # Import your new custom views.py

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')),

    # --- START: URL Patterns for serving the Flutter Student Suite app with Clean URLs ---

    # 1. Serve Flutter's *assets* (JS, CSS, fonts, images, manifest, etc.)
    # This pattern explicitly matches files like flutter_bootstrap.js, main.dart.js,
    # assets/some_image.png, manifest.json, etc.
    # It must come BEFORE the index.html catch-all to ensure assets are served directly.
    # We use our custom view here instead of django.views.static.serve directly.
    re_path(r'^software-center/student-suite/(?P<path>(?!index\.html$).*)$', views.serve_flutter_asset),

    # 2. Serve the base index.html for the Flutter app and handle Flutter's internal routing:
    # This pattern matches '/software-center/student-suite/' and any deep links
    # (e.g., /software-center/student-suite/dashboard, /software-center/student-suite/profile).
    # It must come AFTER the static file serving pattern for the app.
    re_path(r'^software-center/student-suite(?:/.*)?$', TemplateView.as_view(template_name='frontend/student-suite-web/index.html')),

    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
# Note: django.views.static.serve is often used here with the static() helper from django.conf.urls.static
# if settings.DEBUG:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
