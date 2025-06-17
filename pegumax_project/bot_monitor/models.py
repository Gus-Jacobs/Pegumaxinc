from django.db import models

class BotActivityLog(models.Model):
    LOG_LEVEL_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
        ('DEBUG', 'Debug'), # For more detailed, less frequent summary logs
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    platform = models.CharField(max_length=50, blank=True, null=True) # e.g., Freelancer, Upwork, System
    log_level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, default='INFO')
    message = models.TextField()
    source = models.CharField(max_length=100, blank=True, null=True) # e.g., main_loop, scraper, task_handler

    # New fields for dashboard interaction
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [{self.log_level}] {self.message}"

    class Meta:
        ordering = ['-timestamp']

    class BotStatus(models.Model):
    """Singleton model to track bot's last known activity and commands."""
    # Indentation was missing for the class body
    last_heartbeat = models.DateTimeField(default=timezone.now)
    status_message = models.CharField(max_length=255, default="Idle") # e.g., Running, Idle, Error, Starting, Stopping
    # command can be 'NONE', 'STOP_REQUESTED'
    command = models.CharField(max_length=50, default="NONE")

    def __str__(self):
        return f"Bot Status: {self.status_message} (Last heartbeat: {self.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')}, Command: {self.command})"

    @classmethod
    def update_status(cls, status_msg="Running", command_val=None):
        defaults = {'last_heartbeat': timezone.now(), 'status_message': status_msg}
        if command_val is not None: # Only update command if a value is provided
            defaults['command'] = command_val
        obj, created = cls.objects.update_or_create(pk=1, defaults=defaults)
        return obj

    @classmethod
    def get_status(cls):
        obj, created = cls.objects.get_or_create(pk=1) # Ensure it always exists
        return obj
