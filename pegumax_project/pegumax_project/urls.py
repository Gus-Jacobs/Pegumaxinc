"""
URL configuration for pegumax_project project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView
from . import views # Import your custom views.py

# --- NEW: Define handlers for custom error pages ---
handler404 = 'pegumax_project.views.custom_404_view'
handler500 = 'pegumax_project.views.custom_500_view'
# --- END NEW ---


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')),

    # --- START: URL Patterns for serving the Flutter Student Suite app with Clean URLs ---

    # 1. Serve Flutter's *assets* (MUST BE FIRST)
    re_path(r'^software-center/student-suite/(?P<path>.*)$', views.serve_flutter_asset),


    # 2. Serve the base index.html for the Flutter app AND handle Flutter's internal routing (deep links)
    re_path(r'^software-center/student-suite/?(?:.*)?$', TemplateView.as_view(template_name='frontend/student-suite-web/index.html'), name='student_suite_app_launch'),

    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
if settings.DEBUG:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    pass
