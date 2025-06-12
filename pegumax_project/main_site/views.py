from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm, UserProfileEditForm, CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserLoginActivity
from django.contrib import messages
from django.contrib.auth.models import User # Import the User model
from django.core.mail import send_mail




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
def admin_dashboard_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('main_site:home')

    total_users_count = User.objects.count() # Get total user count

    context = {
        'total_users_count': total_users_count,
    }
    return render(request, 'main_site/admin_dashboard.html', context)

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

@login_required
def live_bot_mode_view(request):
    if not request.user.is_staff:
        return redirect('main_site:home')
    # You would fetch actual bot data here in a real scenario
    return render(request, 'main_site/live_bot_mode.html')

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