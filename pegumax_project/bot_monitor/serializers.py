from rest_framework import serializers
from .models import BotActivityLog, BotStatus

class BotActivityLogCreateSerializer(serializers.ModelSerializer): # For receiving logs from bot
    class Meta:
        model = BotActivityLog
        # Fields that the bot sends. 'timestamp' is auto-added.
        # 'is_acknowledged', 'acknowledged_at' get defaults.
        fields = ['message', 'log_level', 'platform', 'source']

    def create(self, validated_data):
        # Custom logic if needed, e.g., transforming incoming data before saving
        return BotActivityLog.objects.create(**validated_data)

class BotActivityLogDisplaySerializer(serializers.ModelSerializer): # For sending logs to dashboard
    class Meta:
        model = BotActivityLog
        fields = ['id', 'timestamp', 'log_level', 'message', 'platform', 'source', 'is_acknowledged', 'acknowledged_at']

class BotStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotStatus
        fields = ['last_heartbeat', 'status_message', 'command']
