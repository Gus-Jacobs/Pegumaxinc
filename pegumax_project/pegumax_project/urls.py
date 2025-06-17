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
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_site.urls', namespace='main_site')),
    path('accounts/', include('django.contrib.auth.urls')), # Django's built-in auth URLs (login, logout, password reset, etc.)
    path('dashboard/', TemplateView.as_view(template_name='admin_dashboard.html'), name='admin_dashboard'),
    path('live-bot-mode/', TemplateView.as_view(template_name='live_bot_mode.html'), name='live_bot_mode'),
    path('bot-api/', include('bot_monitor.urls')), # Include bot_monitor URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
