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
from django.urls import path, include, re_path
from django.conf import settings
# Removed: from django.views.static import serve
# Removed: from django.views.generic import RedirectView

# <--- NEW: Import TemplateView
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')), # Django's built-in auth URLs (login, logout, password reset, etc.)
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')), # API for bot communication

    # --- START: URL Patterns for serving the Flutter Student Suite app with TemplateView ---
    # This pattern will serve the index.html from its collected static location
    # for both the base path and any sub-paths (Flutter's HTML5 History Mode).
    # WhiteNoise will then handle serving the actual assets (JS, CSS, images)
    # from the /static/frontend/student-suite-web/ path as needed by index.html.

    # This single re_path serves the Flutter app's index.html
    # for /software-center/student-suite/ AND any paths under it
    # (e.g., /software-center/student-suite/dashboard, /software-center/student-suite/profile).
    # The Flutter client-side router will then handle the specific path after index.html loads.
    re_path(r'^software-center/student-suite(?:/.*)?$', TemplateView.as_view(template_name='frontend/student-suite-web/index.html')),

    # NOTE: The previous django.views.static.serve patterns for the Flutter app are removed.
    # WhiteNoise (configured in settings.py) will serve static assets like .js, .css, .png
    # directly from your STATIC_URL/STATIC_ROOT without needing explicit URL patterns here.
    # Flutter's <base href> in index.html ensures it requests assets correctly from
    # paths like /software-center/student-suite/main.dart.js, which WhiteNoise then resolves
    # from /static/frontend/student-suite-web/main.dart.js.
    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
# In production, media files should be served by a dedicated web server (like Nginx)
# or a cloud storage service (like AWS S3).
if settings.DEBUG:
    # This serves media files during development
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    pass
