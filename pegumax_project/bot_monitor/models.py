from django.db import models
from django.utils import timezone # Import timezone

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
    bot_id = models.CharField(max_length=100, db_index=True, null=True, blank=True) # Link to the bot instance
    source = models.CharField(max_length=100, blank=True, null=True) # e.g., main_loop, scraper, task_handler

    # New fields for dashboard interaction
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [{self.log_level}] {self.message}"

    class Meta:
        ordering = ['-timestamp']

# BotStatus should be a top-level class, not nested under BotActivityLog.Meta
class BotStatus(models.Model):
    """Singleton model to track bot's last known activity and commands."""
    bot_id = models.CharField(max_length=100, unique=True, default="freelance-bot-main") # Added for clarity if you plan multiple bots
    # Ensure the following lines are indented correctly under BotStatus
    last_heartbeat = models.DateTimeField(default=timezone.now)
    status_message = models.CharField(max_length=255, default="Idle") # e.g., Running, Idle, Error, Starting, Stopping
    # command can be 'NONE', 'STOP_REQUESTED'
    bot_started_at = models.DateTimeField(default=timezone.now)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    jobs_scraped_today = models.IntegerField(default=0)
    proposals_sent_today = models.IntegerField(default=0)
    command = models.CharField(max_length=50, default="NONE")

    def __str__(self):
        return f"Bot ID: {self.bot_id} - Status: {self.status_message} (Heartbeat: {self.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')}, Command: {self.command})"

    @classmethod
    def update_status(cls, bot_id_val="freelance-bot-main", status_msg="Running", command_val=None):
        obj, created = cls.objects.get_or_create(bot_id=bot_id_val)
        
        # If the bot is just starting, reset the start time
        if created or obj.status_message in ["Idle", "Stopped"]:
            obj.bot_started_at = timezone.now()

        obj.last_heartbeat = timezone.now()
        obj.status_message = status_msg
        if command_val is not None: # Only update command if a value is provided
            obj.command = command_val # Set new command
        
        obj.save()
        return obj

    @classmethod
    def get_status(cls, bot_id_val="freelance-bot-main"):
        obj, created = cls.objects.get_or_create(bot_id=bot_id_val) # Ensure it always exists for the given bot_id
        return obj
