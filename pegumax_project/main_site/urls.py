from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = 'main_site'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('software-center/', views.software_center_view, name='software_center'),
    path('about/', views.about_view, name='about'),
    # Personal portfolio — direct-URL only (pegumax.com/AugustineJacobs). Not linked in nav/footer.
    path('AugustineJacobs/', views.portfolio_view, name='portfolio'),
    path('AugustineJacobs', views.portfolio_view),  # tolerate no trailing slash
    path('community/', views.community_view, name='community'),
    path('store/', views.store_view, name='store'),
    path('admin-login/', views.admin_login_view, name='admin_login'), # Temporary
    path('account/', views.account_view, name='account'),
    path('movie-word-scanner/', views.movie_word_scanner_view, name='movie_word_scanner'), # legacy -> LucidCut
    path('lucidcut/', views.lucidcut_view, name='lucidcut'),
    path('scribe/', views.scribe_view, name='scribe'),
    path('contour/', views.contour_view, name='contour'),
    path('inference/', views.inference_view, name='inference'),
    path('game-portal/', views.game_portal, name='game_portal'),
    path('apex-studio/', views.apex_studio_view, name='apex_studio'), # NEW APEX STUDIO ROUTE

    # --- Student Suite TikTok ad squeeze page + tracked store redirects ---
    # Landing page for paid TikTok traffic (short, on-brand URL for the ad).
    path('student-suite/', views.student_suite_landing_view, name='student_suite_landing'),
    # Buttons on the squeeze page point here. Server-side 302 (TikTok-safe) and
    # every click is logged. No trailing slash to match the <a href> exactly and
    # avoid an APPEND_SLASH 301 hop; slash variants included for safety.
    path('redirect/ios', views.redirect_ios, name='redirect_ios'),
    path('redirect/android', views.redirect_android, name='redirect_android'),
    path('redirect/ios/', views.redirect_ios),
    path('redirect/android/', views.redirect_android),
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
    path('policy/', views.policy_view, name='policy'),
    path('careers/', views.careers_view, name='careers'),
    # Live TikTok paid traffic lands on this URL. Serve the high-converting
    # squeeze page here directly (rerouted from the old launch page) so we don't
    # have to change the destination in TikTok Ads Manager and trigger a campaign
    # re-review. The old full launch page template (student-suite-launch.html)
    # still exists but is no longer served by this route.
    path('software-center/student-suite-launch/', views.student_suite_landing_view, name='student_suite_launch'),
    # --- NEW: URL for submitting subscription interest ---
    path('submit-subscription-interest/', views.submit_subscription_interest_view, name='submit_subscription_interest'),
    path('payment-success/', views.payment_success_view, name='payment-success'),
    path('payment-cancelled/', views.payment_cancelled_view, name='payment-cancelled'),
    # --- NEW: unified message endpoint for the redesigned site (contact/feedback/idea/bug) ---
    path('api/message/', views.api_submit_message, name='api_message'),
    # --- NEW: Stripe donations (embedded checkout) ---
    path('donate/config/', views.donate_config, name='donate_config'),
    path('donate/create-session/', views.create_donation_session, name='create_donation_session'),
    path('donate/complete/', views.donation_complete, name='donation_complete'),
]


