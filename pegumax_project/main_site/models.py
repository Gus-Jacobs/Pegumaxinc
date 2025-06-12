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
