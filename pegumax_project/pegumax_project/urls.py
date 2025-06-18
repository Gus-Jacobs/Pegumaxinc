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
from django.urls import path, include # Add include
from django.conf import settings
from django.conf.urls.static import static
# from django.views.generic import TemplateView # We'll use custom views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')), # Django's built-in auth URLs (login, logout, password reset, etc.)
    # Dashboard and bot monitoring URLs will be included via main_site.urls
    # Example: path('dashboard/', include('main_site.dashboard_urls')), # if you create a separate dashboard_urls.py
    # For now, we assume main_site.urls will define them.
    path('bot-api/', include('bot_monitor.urls', namespace='bot_monitor')), # API for bot communication
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
