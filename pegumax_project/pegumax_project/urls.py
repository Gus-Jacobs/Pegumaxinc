"""
URL configuration for pegumax_project project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView
from . import views # Import your custom views.py

# --- Define handlers for custom error pages ---
handler404 = 'pegumax_project.views.custom_404_view'
handler500 = 'pegumax_project.views.custom_500_view'
# --- END handlers ---


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')),

    # --- START: URL Patterns for serving the Flutter Student Suite app with Clean URLs ---

    # 1. EXACT Match for the Flutter App Root HTML (with and without trailing slash)
    # This ensures that when the user navigates directly to the base URL,
    # the index.html is served specifically as the entry point.
    path('software-center/student-suite/', TemplateView.as_view(template_name='frontend/student-suite-web/index.html'), name='student_suite_app_launch_base'),
    path('software-center/student-suite', TemplateView.as_view(template_name='frontend/student-suite-web/index.html'), name='student_suite_app_launch_no_slash'), # Handle no trailing slash

    # 2. Serve Flutter's *assets* (JS, CSS, fonts, images, manifest, etc.)
    # This pattern explicitly matches any request that has at least one character
    # AFTER '/software-center/student-suite/'.
    # This ensures it captures files like 'main.dart.js' but NOT the base URL itself.
    # This must come BEFORE the general deep-link catch-all.
    re_path(r'^software-center/student-suite/(?P<path>.+)$', views.serve_flutter_asset, name='student_suite_assets'),

    # 3. Handle Flutter's internal routing (deep links)
    # This pattern acts as a fallback for any sub-path under 'software-center/student-suite/'
    # that wasn't matched by the asset server. This is for Flutter's client-side router.
    # It must come AFTER the exact root HTML serving patterns AND the asset serving pattern.
    re_path(r'^software-center/student-suite/(?P<path>.*)/?$', TemplateView.as_view(template_name='frontend/student-suite-web/index.html')),


    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
if settings.DEBUG:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    pass
