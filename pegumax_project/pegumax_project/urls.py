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
# from django.conf.urls.static import static # This is for serving media in DEBUG, often not needed for static
# from django.views.generic import RedirectView # No longer needed if using direct serve for Flutter

from django.views.static import serve # <--- IMPORT THIS for serving static files directly

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')), # Django's built-in auth URLs (login, logout, password reset, etc.)
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')), # API for bot communication

    # --- START: URL Patterns for serving the Flutter Student Suite app directly ---
    # With WhiteNoise in production, these `serve` views are usually intercepted by WhiteNoise
    # which efficiently serves the static files. However, they are necessary for Django's
    # URL resolution to point to the correct file location.

    # 1. Serve the base index.html for the Flutter app when navigating directly to its root URL.
    # When a user goes to /software-center/student-suite/, this serves the index.html.
    re_path(r'^software-center/student-suite/$', serve, {
        'document_root': settings.STATIC_ROOT,
        'path': 'frontend/student-suite-web/index.html',
        'insecure': True # Use insecure=True for serve() in production with WhiteNoise.
                         # WhiteNoise takes precedence, so this isn't a security vulnerability here.
    }),

    # 2. Crucial for Flutter's HTML5 History Mode and asset loading.
    # This pattern captures any sub-paths under /software-center/student-suite/ (like
    # /software-center/student-suite/dashboard, /software-center/student-suite/main.dart.js,
    # or /software-center/student-suite/assets/image.png).
    # It tells Django to serve these files from the 'frontend/student-suite-web/' subdirectory
    # within your STATIC_ROOT. Flutter's router then takes over for internal routes.
    re_path(r'^software-center/student-suite/(?P<path>.*)$', serve, {
        'document_root': settings.STATIC_ROOT / 'frontend' / 'student-suite-web',
        'insecure': True # Same reasoning as above for 'insecure=True'
    }),
    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

# This block is specifically for serving media files (e.g., user-uploaded images)
# during local development (when DEBUG is True).
# In production, media files should be served by a dedicated web server (like Nginx)
# or a cloud storage service (like AWS S3).
if settings.DEBUG:
    # This serves media files during development
    # Ensure settings.MEDIA_URL and settings.MEDIA_ROOT are defined in settings.py if using.
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    pass # Keeping this section clean if you're not actively using it for development media.
