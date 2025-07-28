from django.urls import path
from . import views # Assuming your main_site views are in main_site/views.py
from django.views.generic import TemplateView # Import TemplateView for the new launch page

app_name = 'main_site'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('software-center/', views.software_center_view, name='software_center'),
    path('about/', views.about_view, name='about'),
    path('community/', views.community_view, name='community'),
    path('store/', views.store_view, name='store'),
    path('admin-login/', views.admin_login_view, name='admin_login'), # Temporary
    path('account/', views.account_view, name='account'),
    path('movie-word-scanner/', views.movie_word_scanner_view, name='movie_word_scanner'),
    path('signup/', views.signup_view, name='signup'),
    # Django's auth system will handle login and logout views by default
    # path('login/', views.CustomLoginView.as_view(), name='login'), # If you need a custom login view
    # path('logout/', views.CustomLogoutView.as_view(), name='logout'), # If you need a custom logout view
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'), # Main admin dashboard
    # New URLs for account popups
    path('account/edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('account/change-password/', views.change_password_view, name='change_password_popup'),
    path('account/login-history/', views.get_login_history_view, name='get_login_history'),
    # New URLs for email submissions
    path('submit-idea/', views.submit_software_idea_view, name='submit_software_idea'),
    path('full-access-inquiry/', views.full_access_pass_inquiry_view, name='full_access_inquiry'),
    path('contact/', views.contact_page_view, name='contact'),
    path('admin-dashboard/live-bot-overview/', views.live_bot_overview_view, name='live_bot_overview'),
    path('admin-dashboard/live-bot-mode/<str:bot_id>/', views.bot_detail_view, name='bot_detail_page'),

    # --- NEW: URL for the Student Suite Launch Page ---
    # This renders the static HTML template for the launch page.
    path('software-center/student-suite-launch/', TemplateView.as_view(template_name='main_site/student-suite-launch.html'), name='student_suite_launch'),
]
