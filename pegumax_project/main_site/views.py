from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm
from .models import SoftwareIdea, FullAccessInquiry, ContactMessage, UserLoginActivity # Make sure you have models.py
from .forms import SignUpForm, UserProfileEditForm, CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .models import UserLoginActivity
from django.contrib import messages
from django.contrib.auth.models import User # Import the User model
from django.core.mail import send_mail
# Add any other necessary imports, e.g., models from bot_monitor
from bot_monitor.models import BotStatus, BotActivityLog # Assuming these are your models


def is_admin(user):
    return user.is_authenticated and user.is_staff # or user.is_superuser

# ... (your existing views like home, signup, login_view, etc.)

# @login_required # Allow guest access to home page
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
    # Total configured bots (assuming each BotStatus entry is a configured bot)
    total_configured_bots_count = BotStatus.objects.count()

    # For popups - initial data (can be fetched via AJAX too)
    # For now, let's count unacknowledged logs for notifications
    # Convert QuerySets to list of dicts for JSON serialization
    recent_logs_list = list(BotActivityLog.objects.order_by('-timestamp').values(
        'timestamp', 'log_level', 'message', 'bot_id', 'platform' # Added platform
    )[:20])
    critical_logs_list = list(BotActivityLog.objects.filter(log_level__in=['ERROR', 'CRITICAL']).order_by('-timestamp').values(
        'timestamp', 'log_level', 'message', 'bot_id', 'platform' # Added platform
    )[:20])

    # Notification counts (example: unacknowledged logs)
    # You'd need to refine this logic, perhaps based on logs since last admin login or a specific timeframe
    # For simplicity, count unacknowledged logs.
    unacknowledged_general_logs_count = BotActivityLog.objects.filter(is_acknowledged=False).count()
    unacknowledged_critical_logs_count = BotActivityLog.objects.filter(is_acknowledged=False, log_level__in=['ERROR', 'CRITICAL']).count()

    # Get current running status for the single bot (if only one)
    # This is for the "Active Bots" card which you wanted to show total bots,
    # but the original template had "Active Bots". Let's provide both.
    active_bots_count = 0
    bot_status_instance = BotStatus.objects.first()
    if bot_status_instance: # Check if an instance exists
        if hasattr(bot_status_instance, 'status_message') and isinstance(bot_status_instance.status_message, str) and \
           "running" in bot_status_instance.status_message.lower():
            active_bots_count = 1
        
    total_users_count = User.objects.count()
    context = {
        'total_users_count': total_users_count,
        'total_configured_bots_count': total_configured_bots_count, # For the card you mentioned
        'active_bots_count': active_bots_count,
        'recent_logs_for_popup_json': recent_logs_list, # Pass as JSON-ready list
        'critical_logs_for_popup_json': critical_logs_list, # Pass as JSON-ready list
        'unacknowledged_general_logs_count': min(unacknowledged_general_logs_count, 20), # Cap at 20 for display
        'unacknowledged_critical_logs_count': min(unacknowledged_critical_logs_count, 20), # Cap at 20

    }
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
