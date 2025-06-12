from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import UserLoginActivity

@receiver(user_logged_in)
def record_user_login(sender, request, user, **kwargs):
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    UserLoginActivity.objects.create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent
    )

