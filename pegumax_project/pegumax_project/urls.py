from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')),

    # --- START: URL Patterns for serving the Flutter Student Suite app with WhiteNoise ---

    # The collected index.html will be at /static/frontend/student-suite-web/index.html
    # when WhiteNoise serves it.

    # 1. Handle the base URL for the Flutter app
    # When a request for /software-center/student-suite/ comes in, redirect to the actual collected index.html.
    # CHANGE THIS LINE to match the new path:
    path('software-center/student-suite/', RedirectView.as_view(url=f'{settings.STATIC_URL}frontend/student-suite-web/index.html')),

    # 2. Handle Flutter's HTML5 History Mode (deep linking)
    # For any sub-path under /software-center/student-suite/, also redirect to index.html.
    # CHANGE THIS LINE to match the new path:
    re_path(r'^software-center/student-suite/(?:.*)?$', RedirectView.as_view(url=f'{settings.STATIC_URL}frontend/student-suite-web/index.html')),

    # --- END: URL Patterns for serving the Flutter Student Suite app ---
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
