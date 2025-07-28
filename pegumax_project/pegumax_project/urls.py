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
    # This pattern matches any file request *within* the Flutter app's URL space.
    # It must come FIRST to ensure that assets are served directly and not index.html.
    # It explicitly captures a 'path' after the 'student-suite/' part.
    # This also means requests to 'software-center/student-suite/' won't match this one.
    re_path(r'^software-center/student-suite/(?P<path>.*)$', views.serve_flutter_asset),


    # 2. Serve the base index.html for the Flutter app
    # This pattern matches ONLY the exact root of the Flutter app, with or without a trailing slash.
    # It MUST be placed after the asset serving pattern.
    re_path(r'^software-center/student-suite/?$', TemplateView.as_view(template_name='frontend/student-suite-web/index.html')),


    # 3. Handle Flutter's internal routing (deep links)
    # This pattern acts as a fallback for any sub-path under 'software-center/student-suite/'
    # that wasn't matched by the asset server. This is for Flutter's client-side router.
    # This must come AFTER both the asset serving pattern and the exact root HTML serving pattern.
    re_path(r'^software-center/student-suite/(?P<path>.*)/?$', TemplateView.as_view(template_name='frontend/student-suite-web/index.html')),


    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
# (Your original static() helper block here if you use it for media)
# if settings.DEBUG:
#    from django.conf.urls.static import static
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
