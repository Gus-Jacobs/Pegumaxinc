"""
URL configuration for pegumax_project project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView
from . import views # Import your custom views.py

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')),

    # --- START: URL Patterns for serving the Flutter Student Suite app with Clean URLs ---

    # 1. Serve Flutter's *assets* (JS, CSS, fonts, images, manifest, etc.)
    # This pattern explicitly matches any path that has at least one character
    # AFTER '/software-center/student-suite/'.
    # This ensures it captures files like 'main.dart.js' but NOT the base URL itself.
    # It must come FIRST.
    re_path(r'^software-center/student-suite/(?P<path>.+)$', views.serve_flutter_asset),


    # 2. Serve the base index.html for the Flutter app AND handle Flutter's internal routing (deep links)
    # This pattern catches:
    #   - /software-center/student-suite/ (with trailing slash)
    #   - /software-center/student-suite (without trailing slash)
    #   - /software-center/student-suite/dashboard (deep link)
    #   - /software-center/student-suite/settings/profile (deep link)
    # It must come AFTER the asset serving pattern.
    re_path(r'^software-center/student-suite/?(?:.*)?$', TemplateView.as_view(template_name='frontend/student-suite-web/index.html')),

    # The previous third pattern is redundant and problematic. The second pattern now handles both root and deep links.

    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
# (Your original static() helper block here if you use it for media)
# if settings.DEBUG:
#    from django.conf.urls.static import static
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
