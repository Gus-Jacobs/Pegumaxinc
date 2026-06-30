"""
URL configuration for pegumax_project project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.sitemaps.views import sitemap
from main_site.sitemaps import StaticViewSitemap
from . import views # Import your custom views.py

sitemaps = {"static": StaticViewSitemap}

# --- Define handlers for custom error pages ---
handler404 = 'pegumax_project.views.custom_404_view'
handler500 = 'pegumax_project.views.custom_500_view'
# --- END handlers ---


urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
    # Classic /favicon.ico lookup (browsers + Google's favicon crawler hit this first).
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),
    # security.txt (RFC 9116) — legitimacy/security-contact signal for scanners.
    path('.well-known/security.txt', TemplateView.as_view(template_name='security.txt', content_type='text/plain')),
    path('security.txt', RedirectView.as_view(url='/.well-known/security.txt', permanent=True)),
    path('', include('main_site.urls', namespace='main_site')),
    path('academy/', include('academy.urls', namespace='academy')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')),

    # --- START: URL Patterns for serving the Flutter Student Suite app with Clean URLs ---

    # 1. Serve Flutter's *assets* (MUST BE FIRST)
    # This pattern explicitly matches any path that has at least one character
    # AFTER '/software-center/student-suite/'.
    # This ensures it captures files like 'main.dart.js' but NOT the base URL itself.
    # It must come FIRST.
    re_path(r'^software-center/student-suite/(?P<path>.+)$', views.serve_flutter_asset, name='student_suite_assets'),


    # 2. Serve the base index.html for the Flutter app AND handle Flutter's internal routing (deep links)
    # This pattern catches:
    #   - /software-center/student-suite/ (with trailing slash)
    #   - /software-center/student-suite (without trailing slash)
    #   - /software-center/student-suite/dashboard (deep link)
    #   - /software-center/student-suite/settings/profile (deep link)
    # It must come AFTER the asset serving pattern.
    # CRITICAL: Ensure 'name=student_suite_app_launch' is present on THIS line.
    re_path(r'^software-center/student-suite/?(?:.*)?$', TemplateView.as_view(template_name='frontend/student-suite-web/index.html'), name='student_suite_app_launch'),


    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
if settings.DEBUG:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    pass
