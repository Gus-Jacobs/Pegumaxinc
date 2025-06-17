from django.db import models
from django.conf import settings

class UserLoginActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'User Login Activity'
        verbose_name_plural = 'User Login Activities'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user.username} - {self.timestamp}'

class SoftwareIdea(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    user_email = models.EmailField(max_length=254, blank=True, null=True) # For non-logged-in users
    idea_title = models.CharField(max_length=200)
    idea_description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='submitted') # e.g., submitted, under review, approved, rejected

    def __str__(self):
        return f"Idea: {self.idea_title} by {self.user.username if self.user else self.user_email}"

class FullAccessInquiry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    user_email = models.EmailField(max_length=254, blank=True, null=True) # For non-logged-in users
    reason_for_inquiry = models.TextField()
    contact_method = models.CharField(max_length=100, blank=True, null=True) # e.g., email, phone
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending') # e.g., pending, contacted, resolved

    def __str__(self):
        return f"Full Access Inquiry from {self.user.username if self.user else self.user_email} at {self.submitted_at.strftime('%Y-%m-%d')}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.name} ({self.email}) - {self.subject}"

# UserLoginHistory seems to be a duplicate of UserLoginActivity.
# If UserLoginActivity serves the purpose of tracking login history,
# you might not need UserLoginHistory.
# If UserLoginHistory is distinct, you would define it here.
# For now, assuming UserLoginActivity is the intended model for login history.
