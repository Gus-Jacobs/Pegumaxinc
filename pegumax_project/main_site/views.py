from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm # Keep for now, SignUpForm might use it
from .models import SoftwareIdea, FullAccessInquiry, ContactMessage, UserLoginActivity
from .forms import SignUpForm, UserProfileEditForm, CustomPasswordChangeForm # Renamed from EditProfileForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
# UserLoginActivity is already imported above
from django.contrib import messages
from django.contrib.auth.models import User # Import the User model
from django.core.mail import send_mail
# Add any other necessary imports, e.g., models from bot_monitor
from bot_monitor.models import BotStatus, BotActivityLog # Assuming these are your models
# Duplicate imports removed
from django.db.utils import ProgrammingError

def is_admin(user):
    return user.is_authenticated and user.is_staff

# @login_required # Typically, home_view is public
# @user_passes_test(is_admin) # And not restricted to admins
def home_view(request):
    return render(request, 'index.html')

@login_required
def software_center_view(request):
    return render(request, 'software-center.html')

@login_required
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
    return render(request, 'admin-login.html') # We'll replace this later

@login_required
def account_view(request):
    return render(request, 'account.html') # We'll replace this later

@login_required
def movie_word_scanner_view(request):
    return render(request, 'movie-word-scanner.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log the user in directly after signup
            return redirect('main_site:home') # Redirect to home page or a profile page
    else:
        form = SignUpForm()
    return render(request, 'main_site/signup.html', {'form': form})

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
        else:
            # Collect form errors to send back as JSON
            errors = {field: error_list[0] for field, error_list in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return JsonResponse({'success': True, 'message': 'Password updated successfully!'})
        else:
            errors = {field: error_list[0] for field, error_list in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def get_login_history_view(request):
    login_activities = UserLoginActivity.objects.filter(user=request.user).order_by('-timestamp')[:10] # Get last 10
    
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

@login_required # Or remove if guests can submit
def submit_software_idea_view(request):
    if request.method == 'POST':
        idea_text = request.POST.get('idea_text')
        user_email = request.user.email if request.user.is_authenticated else request.POST.get('user_email_idea', 'Not provided')

        if not idea_text:
            return JsonResponse({'success': False, 'message': 'Idea text cannot be empty.'}, status=400)

        subject = f"New Software Idea Submission from {user_email}"
        message_body = f"User: {request.user.username if request.user.is_authenticated else 'Guest'}\nEmail: {user_email}\n\nIdea:\n{idea_text}"
        try:
            send_mail(subject, message_body, 'noreply@pegumax.com', ['pegumaxinc@gmail.com']) # REPLACE your_email@example.com
            return JsonResponse({'success': True, 'message': 'Thank you! Your idea has been submitted.'})
        except Exception as e:
            # Log the error e
            return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

def full_access_pass_inquiry_view(request): # Can be accessed by guests
    if request.method == 'POST':
        email = request.POST.get('email_access')
        interest_reason = request.POST.get('interest_reason_access', 'Not specified')

        if not email: # Basic validation
            return JsonResponse({'success': False, 'message': 'Email address is required.'}, status=400)

        subject = "Full Access Pass Inquiry"
        message_body = f"Email: {email}\nReason for Interest:\n{interest_reason}"
        try:
            send_mail(subject, message_body, 'noreply@pegumax.com', ['pegumaxinc@gmail.com']) # REPLACE your_email@example.com
            return JsonResponse({'success': True, 'message': 'Thank you for your interest! We will be in touch.'})
        except Exception as e:
            # Log the error e
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
        send_mail(email_subject, email_body, 'noreply@pegumax.com', ['pegumaxinc@gmail.com']) # REPLACE your_email@example.com
        messages.success(request, "Thank you for your message! We'll get back to you soon.")
        return redirect('main_site:contact') # Redirect to clear form
    return render(request, 'main_site/contact.html')

@login_required
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    # Initialize context with default/empty values
    context = {
        'total_users_count': 0,
        'total_configured_bots_count': 0,
        'active_bots_count': 0,
        'recent_logs_for_popup_json': [],
        'critical_logs_for_popup_json': [],
        'unacknowledged_general_logs_count': 0,
        'unacknowledged_critical_logs_count': 0,
        'dashboard_error_message': "Data fetching is minimal for debugging." # Default message
    }

    # STEP 1: Try fetching only User count
    try:
        context['total_users_count'] = User.objects.count()
        context['dashboard_error_message'] = "Successfully fetched user count. Other data is still disabled."
    except Exception as e_user:
        context['dashboard_error_message'] = f"Error fetching user count: {type(e_user).__name__} - {e_user}"
        print(f"ERROR in admin_dashboard_view (User count): {context['dashboard_error_message']}")

    # STEP 2: Try fetching BotStatus data
    try:
        context['total_configured_bots_count'] = BotStatus.objects.count()
        # Correctly count active bots by checking their status_message
        context['active_bots_count'] = BotStatus.objects.filter(status_message__icontains="running").count()
        # Update error message if this step was successful and previous was too
        context['dashboard_error_message'] = "Successfully fetched user, BotStatus count, and active bots. BotActivityLog data is still disabled."
    except Exception as e_status:
        context['dashboard_error_message'] = f"Error fetching BotStatus: {type(e_status).__name__} - {e_status}"
        print(f"ERROR in admin_dashboard_view (BotStatus): {context['dashboard_error_message']}")

    # STEP 3: Try fetching BotActivityLog data
    try:
        log_fields = ['timestamp', 'log_level', 'message', 'bot_id', 'platform']
        # Using a slightly larger limit for actual display, e.g., 20
        context['recent_logs_for_popup_json'] = list(
            BotActivityLog.objects.order_by('-timestamp').values(*log_fields)[:20]
        )
        context['critical_logs_for_popup_json'] = list(
            BotActivityLog.objects.filter(log_level__in=['ERROR', 'CRITICAL'])
            .order_by('-timestamp').values(*log_fields)[:20]
        )
        context['unacknowledged_general_logs_count'] = min(
            BotActivityLog.objects.filter(is_acknowledged=False).count(), 20 # Cap at 20 for display
        )
        context['unacknowledged_critical_logs_count'] = min(
            BotActivityLog.objects.filter(is_acknowledged=False, log_level__in=['ERROR', 'CRITICAL']).count(), 20
        )
        # Check if any previous step reported an error before declaring full success
        if "Error" not in context['dashboard_error_message'] and "failed" not in context['dashboard_error_message'].lower() \
           and "schema error" not in context['dashboard_error_message'].lower():
             context['dashboard_error_message'] = "All dashboard data fetched successfully."
        # else, the error message from a previous step will remain.
        
    except ProgrammingError as db_error: # Specifically catch schema errors for BotActivityLog
        error_msg = f"Database schema error (BotActivityLog): {type(db_error).__name__} - {db_error}. Check model fields (e.g. bot_id, platform, is_acknowledged) and migrations."
        print(f"ERROR in admin_dashboard_view (BotActivityLog - Schema): {error_msg}")
        context['dashboard_error_message'] = error_msg
    except Exception as e_logs: # General catch-all for other errors during BotActivityLog fetching
        context['dashboard_error_message'] = f"Error fetching BotActivityLog data: {type(e_logs).__name__} - {e_logs}"
        print(f"ERROR in admin_dashboard_view (BotActivityLog): {context['dashboard_error_message']}")
 
    return render(request, 'main_site/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def live_bot_overview_view(request):
    # Fetch data for all bots to display in cards
    bots_data = []
    all_bot_statuses = BotStatus.objects.all() # Assuming BotStatus can have multiple entries

    for bot_status in all_bot_statuses:
        latest_activity = BotActivityLog.objects.filter(bot_id=bot_status.bot_id).order_by('-timestamp').first()
        
        # Determine button state
        button_action = "START_REQUESTED"
        button_text = "Start Bot"
        button_class = "success"
        if "running" in bot_status.status_message.lower():
            button_action = "STOP_REQUESTED"
            button_text = "Stop Bot"
            button_class = "danger"
        elif "error" in bot_status.status_message.lower():
            button_action = "RESTART_REQUESTED" # Assuming your bot handles this
            button_text = "Restart Bot"
            button_class = "warning"
            
        bots_data.append({
            'id': bot_status.bot_id, # Use the unique bot_id from the model
            'name': getattr(bot_status, 'name', bot_status.bot_id), # Use name field if exists, else bot_id
            'status_message': bot_status.status_message,
            'last_heartbeat': bot_status.last_heartbeat,
            'latest_task': latest_activity.message if latest_activity else "No recent activity",
            'total_earnings': getattr(bot_status, 'total_earnings', "0.00"), # Placeholder for earnings
            'button_action': button_action,
            'button_text': button_text,
            'button_class': button_class,
            # Add other stats here once BotStatus model is updated and bot reports them
            'jobs_scraped_today': "N/A", # Placeholder
            'tasks_completed_today': "N/A", # Placeholder
        })

    context = {
        'bots': bots_data,
    }
    return render(request, 'main_site/live_bot_overview.html', context)

@login_required
@user_passes_test(is_admin)
def bot_detail_view(request, bot_id: str):
    # Fetch detailed data for the specific bot_id
    # For now, we only have one bot, so 'bot_id' might be "freelance-bot"
    # This view will use the existing API endpoints from bot_monitor for logs, commands etc.
    # The template bot_detail_page.html will make AJAX calls to those endpoints.
    
    # You might pass the bot_id or some initial bot info to the template
    bot_name = "Freelance Bot" # Placeholder, derive from bot_id if multiple bots
    if bot_id != "freelance-bot":
        # Handle case for unknown bot_id if necessary, e.g., redirect or 404
        pass

    context = {
        'bot_id': bot_id,
        'bot_name': bot_name,
        # Add any other initial context needed for the bot detail page
    }
    return render(request, 'main_site/bot_detail_page.html', context)

# ... (your other views like edit_profile_view, etc.) ...
