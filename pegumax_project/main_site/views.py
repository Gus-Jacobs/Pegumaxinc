from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm
from .models import SoftwareIdea, FullAccessInquiry, ContactMessage, UserLoginActivity # Ensure these models exist
from .forms import SignUpForm, UserProfileEditForm, CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
import json
from django.contrib.auth.models import User
from django.core.mail import send_mail
from bot_monitor.models import BotStatus, BotActivityLog # Ensure these models exist and app is configured
from django.utils import timezone
from django.db.utils import ProgrammingError
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

def is_admin(user):
    return user.is_authenticated and user.is_staff

def home_view(request):
    return render(request, 'index.html')

def software_center_view(request):
    return render(request, 'software-center.html')

def about_view(request):
    return render(request, 'about.html')

@login_required
def community_view(request):
    return render(request, 'community.html')

@login_required
def store_view(request):
    return render(request, 'store.html')

@login_required
def admin_login_view(request):
    return render(request, 'admin-login.html')

@login_required
def account_view(request):
    return render(request, 'account.html')

def movie_word_scanner_view(request):
    return render(request, 'movie-word-scanner.html')

def policy_view(request):
    return render(request, 'main_site/policy.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main_site:home')
    else:
        form = SignUpForm()
    return render(request, 'main_site/signup.html', {'form': form})

@login_required
@require_POST
@csrf_exempt
def edit_profile_view(request):
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
        else:
            errors = {field: error_list[0] for field, error_list in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
@require_POST
@csrf_exempt
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return JsonResponse({'success': True, 'message': 'Password updated successfully!'})
        else:
            errors = {field: error_list[0] for field, error_list in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def get_login_history_view(request):
    login_activities = UserLoginActivity.objects.filter(user=request.user).order_by('-timestamp')[:10]
    
    current_ip = request.META.get('REMOTE_ADDR')
    current_ua = request.META.get('HTTP_USER_AGENT', '')[:255]

    history_data = []
    for activity in login_activities:
        is_current_device = (activity.ip_address == current_ip and activity.user_agent == current_ua)
        history_data.append({
            'timestamp': activity.timestamp.strftime("%b %d, %Y, %I:%M %p %Z"),
            'ip_address': activity.ip_address or "N/A",
            'user_agent': activity.user_agent or "N/A",
            'is_current_device': is_current_device,
        })
    return JsonResponse({'history': history_data})

@require_POST
@csrf_exempt
@login_required # Or remove if guests can submit
def submit_software_idea_view(request):
    if request.method == 'POST':
        idea_text = request.POST.get('idea-description')
        idea_name = request.POST.get('idea-name', 'Anonymous')
        idea_email = request.user.email if request.user.is_authenticated else request.POST.get('idea-email', 'Not provided')
        idea_type = request.POST.get('idea-type', 'Other')

        if not idea_text:
            return JsonResponse({'success': False, 'message': 'Idea description cannot be empty.'}, status=400)

        subject = f"New Software Idea Submission from {idea_name} ({idea_email})"
        message_body = f"User: {request.user.username if request.user.is_authenticated else 'Guest'}\nEmail: {idea_email}\nType: {idea_type}\n\nIdea Description:\n{idea_text}"
        try:
            send_mail(subject, message_body, 'noreply@pegumax.com', ['pegumaxinc@gmail.com'])
            return JsonResponse({'success': True, 'message': 'Thank you! Your idea has been submitted.'})
        except Exception as e:
            print(f"Error sending idea email: {e}")
            return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

@require_POST
@csrf_exempt
def full_access_pass_inquiry_view(request):
    if request.method == 'POST':
        email = request.POST.get('interest-email')
        interest_tools_worth = request.POST.get('interest-tools-worth', 'N/A')
        interest_replaces = request.POST.get('interest-replaces', 'N/A')
        interest_wants = request.POST.get('interest-wants', 'N/A')

        if not email:
            return JsonResponse({'success': False, 'message': 'Email address is required.'}, status=400)

        subject = "Full Access Pass Inquiry"
        message_body = (
            f"Email: {email}\n"
            f"Tools worth: {interest_tools_worth}\n"
            f"Replaces: {interest_replaces}\n"
            f"Wants: {interest_wants}"
        )
        try:
            send_mail(subject, message_body, 'noreply@pegumax.com', ['pegumaxinc@gmail.com'])
            return JsonResponse({'success': True, 'message': 'Thank you for your interest! We will be in touch.'})
        except Exception as e:
            print(f"Error sending full access inquiry email: {e}")
            return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

def contact_page_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject_user = request.POST.get('subject')
        message = request.POST.get('message')

        email_subject = f"Contact Form Submission: {subject_user} from {name}"
        email_body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        try:
            send_mail(email_subject, email_body, 'noreply@pegumax.com', ['pegumaxinc@gmail.com'])
            messages.success(request, "Thank you for your message! We'll get back to you soon.")
            return redirect('main_site:contact')
        except Exception as e:
            print(f"Error sending contact email: {e}")
            messages.error(request, "An error occurred while sending your message. Please try again.")
            return render(request, 'main_site/contact.html', {'error_message': 'Failed to send message.'})
    return render(request, 'main_site/contact.html')

@login_required
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    context = {
        'total_users_count': 0,
        'total_configured_bots_count': 0,
        'active_bots_count': 0,
        'recent_logs_for_popup_json': [],
        'critical_logs_for_popup_json': [],
        'unacknowledged_general_logs_count': 0,
        'unacknowledged_critical_logs_count': 0,
        'dashboard_error_message': "Data fetching is minimal for debugging."
    }

    try:
        context['total_users_count'] = User.objects.count()
        context['dashboard_error_message'] = "Successfully fetched user count. Other data is still disabled."
    except Exception as e_user:
        context['dashboard_error_message'] = f"Error fetching user count: {type(e_user).__name__} - {e_user}"
        print(f"ERROR in admin_dashboard_view (User count): {context['dashboard_error_message']}")

    try:
        context['total_configured_bots_count'] = BotStatus.objects.count()
        active_threshold = timezone.now() - timezone.timedelta(minutes=5)
        context['active_bots_count'] = BotStatus.objects.filter(last_heartbeat__gte=active_threshold).count()

        context['dashboard_error_message'] = "Successfully fetched user, BotStatus count, and active bots. BotActivityLog data is still disabled."
    except Exception as e_status:
        context['dashboard_error_error_message'] = f"Error fetching BotStatus: {type(e_status).__name__} - {e_status}"
        print(f"ERROR in admin_dashboard_view (BotStatus): {context['dashboard_error_message']}")

    try:
        log_fields = ['id', 'timestamp', 'log_level', 'message', 'bot_id', 'platform', 'is_acknowledged']
        context['recent_logs_for_popup_json'] = list(
            BotActivityLog.objects.filter(is_acknowledged=False).order_by('-timestamp').values(*log_fields)[:20]
        )
        context['critical_logs_for_popup_json'] = list(
            BotActivityLog.objects.filter(log_level__in=['ERROR', 'CRITICAL'], is_acknowledged=False)
            .order_by('-timestamp').values(*log_fields)[:20]
        )
        context['unacknowledged_general_logs_count'] = BotActivityLog.objects.filter(is_acknowledged=False).count()
        context['unacknowledged_critical_logs_count'] = BotActivityLog.objects.filter(
            is_acknowledged=False,  
            log_level__in=['ERROR', 'CRITICAL']
        ).count()
        if "Error" not in context['dashboard_error_message'] and "failed" not in context['dashboard_error_message'].lower() \
           and "schema error" not in context['dashboard_error_message'].lower():
            context['dashboard_error_message'] = "All dashboard data fetched successfully."
        
    except ProgrammingError as db_error:
        error_msg = f"Database schema error (BotActivityLog): {type(db_error).__name__} - {db_error}. Check model fields (e.g. bot_id, platform, is_acknowledged) and migrations."
        print(f"ERROR in admin_dashboard_view (BotActivityLog - Schema): {error_msg}")
        context['dashboard_error_message'] = error_msg
    except Exception as e_logs:
        context['dashboard_error_message'] = f"Error fetching BotActivityLog data: {type(e_logs).__name__} - {e_logs}"
        print(f"ERROR in admin_dashboard_view (BotActivityLog): {context['dashboard_error_message']}")
 
    return render(request, 'main_site/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def live_bot_overview_view(request):
    bots_data = []
    all_bot_statuses = BotStatus.objects.all()

    for bot_status in all_bot_statuses:
        latest_activity = BotActivityLog.objects.filter(bot_id=bot_status.bot_id).order_by('-timestamp').first()
        
        button_action = "START_REQUESTED"
        button_text = "Start Bot"
        button_class = "success"
        if "running" in bot_status.status_message.lower():
            button_action = "STOP_REQUESTED"
            button_text = "Stop Bot"
            button_class = "danger"
        elif "error" in bot_status.status_message.lower():
            button_action = "RESTART_REQUESTED"
            button_text = "Restart Bot"
            button_class = "warning"
            
        bots_data.append({
            'id': bot_status.bot_id,
            'name': getattr(bot_status, 'name', bot_status.bot_id),
            'status_message': bot_status.status_message,
            'last_heartbeat': bot_status.last_heartbeat,
            'latest_task': latest_activity.message if latest_activity else "No recent activity",
            'total_earnings': getattr(bot_status, 'total_earnings', "0.00"),
            'button_action': button_action,
            'button_text': button_text,
            'button_class': button_class,
            'jobs_scraped_today': "N/A",
            'tasks_completed_today': "N/A",
        })
    context = {
        'bots': bots_data,
        'bots_data_json': bots_data
    }
    print(f"DEBUG: bots_data_json being sent to template: {context['bots_data_json']}")
    return render(request, 'main_site/live_bot_overview.html', context)

@login_required
@user_passes_test(is_admin)
def bot_detail_view(request, bot_id: str):
    bot_name = "Freelance Bot"
    if bot_id != "freelance-bot":
        pass

    context = {
        'bot_id': bot_id,
        'bot_name': bot_name,
    }
    return render(request, 'main_site/bot_detail_page.html', context)

def careers_view(request):
    return render(request, 'main_site/careers.html')

# --- NEW: View for submitting subscription interest ---
@require_POST
@csrf_exempt
def submit_subscription_interest_view(request):
    if request.method == 'POST':
        interest_email = request.POST.get('interest-email', '')
        interest_tools_worth = request.POST.get('interest-tools-worth', '')
        interest_replaces = request.POST.get('interest-replaces', '')
        interest_wants = request.POST.get('interest-wants', '')

        print(f"New Subscription Interest from: {interest_email}")
        print(f"Tools worth: {interest_tools_worth}")
        print(f"Replaces: {interest_replaces}")
        print(f"Wants: {interest_wants}")

        return JsonResponse({'success': True, 'message': 'Thanks for your interest! We\'ll notify you when it\'s live.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
