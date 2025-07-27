"""
URL configuration for pegumax_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path # Ensure re_path is imported
from django.conf import settings
from django.conf.urls.static import static # This is for serving media in DEBUG, often not needed for static
from django.views.generic import RedirectView # Ensure RedirectView is imported

# Note: os is not directly used here as paths are relative to STATIC_URL,
# which is derived from settings.BASE_DIR in settings.py.

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')), # Django's built-in auth URLs (login, logout, password reset, etc.)
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')), # API for bot communication

    # --- START: URL Patterns for serving the Flutter Student Suite app with WhiteNoise ---
    # These patterns redirect incoming URLs to the actual location of index.html
    # within the /static/ path, which WhiteNoise then serves.

    # 1. Handle the base URL for the Flutter app (e.g., /software-center/student-suite/)
    # This ensures that when a user navigates directly to this path, the Flutter index.html is loaded.
    path('software-center/student-suite/', RedirectView.as_view(url=f'{settings.STATIC_URL}frontend/student-suite-web/index.html')),

    # 2. Handle Flutter's HTML5 History Mode (deep linking)
    # This is crucial for paths like /software-center/student-suite/dashboard or /software-center/student-suite/profile.
    # It redirects any sub-path under /software-center/student-suite/ back to index.html,
    # allowing Flutter's client-side router to then handle the specific route.
    # The (?:.*)? part means "match any characters, zero or more times, optionally followed by a slash".
    re_path(r'^software-center/student-suite/(?:.*)/?$', RedirectView.as_view(url=f'{settings.STATIC_URL}frontend/student-suite-web/index.html')),

    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
# In production, media files should be served by a dedicated web server (like Nginx)
# or a cloud storage service (like AWS S3).
if settings.DEBUG:
    # This serves media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Note: You typically do NOT need to manually serve STATIC_URL here if
    # 'whitenoise.runserver_nostatic' is in INSTALLED_APPS, as it handles
    # static file serving for Django's runserver in debug mode.
    # If you remove 'whitenoise.runserver_nostatic', you might add:
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
