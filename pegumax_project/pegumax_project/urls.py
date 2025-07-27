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
from django.urls import path, include, re_path # Added re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # Added serve

import os # Added os for path manipulation

# Define the root directory where your Flutter build output is located within the Django project.
# This assumes 'frontend/student-suite/' is directly under your Django project's BASE_DIR
# (i.e., next to manage.py and your pegumax_project folder).
FLUTTER_APP_DIR = os.path.join(settings.BASE_DIR, 'frontend', 'student-suite')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')), # Django's built-in auth URLs
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')), # API for bot communication

    # --- START: URL Patterns for serving the Flutter Student Suite app ---
    # These patterns must come AFTER your Django app-specific patterns
    # to ensure Django doesn't try to handle requests meant for Flutter assets.

    # 1. Serve static assets (JS, CSS, fonts, images) for the Flutter app
    # This matches paths like /software-center/student-suite/main.dart.js,
    # /software-center/student-suite/assets/images/logo.png, etc.
    re_path(r'^software-center/student-suite/(?P<path>.*)$', serve, {
        'document_root': FLUTTER_APP_DIR,
    }),

    # 2. Serve the Flutter app's index.html for the base path and for deep links
    # This is crucial for Flutter's HTML5 History Mode (client-side routing).
    # It ensures that direct access to /software-center/student-suite/
    # or any sub-path like /software-center/student-suite/planner
    # will correctly serve the main index.html file, letting Flutter's router take over.
    path('software-center/student-suite/', serve, {
        'document_root': FLUTTER_APP_DIR,
        'path': 'index.html', # Always serve index.html for this specific path
    }),
    re_path(r'^software-center/student-suite/(?:.*)/?$', serve, {
        'document_root': FLUTTER_APP_DIR,
        'path': 'index.html', # Always serve index.html for any sub-path under /software-center/student-suite/
    }),

    # --- END: URL Patterns for serving the Flutter Student Suite app ---

]

# This line should ideally only be used in DEBUG mode for serving media files.
# In production, web servers like Nginx or cloud storage (S3) should serve media.
# If you are serving static files (like your main site's CSS/JS) this way too in DEBUG,
# ensure your STATIC_URL and STATIC_ROOT are correctly configured in settings.py.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # If you also need to serve Django's own static files in DEBUG mode:
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
