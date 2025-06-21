from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import BasePermission
# from .serializers import BotActivityLogSerializer # Old name
from .models import BotActivityLog, BotStatus # Import BotStatus
from .serializers import (
    BotActivityLogCreateSerializer, BotActivityLogDisplaySerializer, BotStatusSerializer
)
from django.utils.decorators import method_decorator # Ensure this is imported
from django.conf import settings
from django.utils import timezone # For timedelta

# Simple API Key Permission
class HasBotAPIKey(BasePermission):
    def has_permission(self, request, view):
        api_key = request.headers.get('X-Bot-API-Key')
        return api_key == getattr(settings, 'BOT_REMOTE_LOG_API_KEY', None)

from django.views.decorators.csrf import csrf_exempt #py manage.py rusnerver 8080 Ensure this is imported

class LogReceiverView(APIView):
    authentication_classes = [] # Explicitly disable session/basic auth for this API view
    permission_classes = [HasBotAPIKey]
    # csrf_exempt = True # This is not a standard DRF attribute for exemption.
    # Instead, ensure CsrfViewMiddleware is correctly configured and @method_decorator(csrf_exempt) on dispatch is used.

    authentication_classes = []  # Explicitly disable authentication
    permission_classes = [] # Explicitly disable permission checks
    @method_decorator(csrf_exempt) # Keep this decorator on dispatch
    def dispatch(self, *args, **kwargs): # It's generally better to apply csrf_exempt to dispatch
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs): # Used by RemoteLogger
        log_data_list = request.data # Assuming request.data is already parsed by DRF
        if not isinstance(log_data_list, list):
            # Allow single log entry for simplicity if RemoteLogger sends one sometimes
            if isinstance(log_data_list, dict):
                log_data_list = [log_data_list]
            else:
                return Response({"error": "Expected a list or a single log entry object."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BotActivityLogCreateSerializer(data=log_data_list, many=True)
        authentication_classes = [] # Explicitly disable authentication
        permission_classes = [] # Explicitly disable permission checks

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "logs received"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DashboardDataView(APIView):
    # permission_classes = [IsAdminUser] # TODO: Add appropriate permissions for dashboard access

    def get(self, request, format=None):
        bot_status_obj = BotStatus.get_status()
        active_threshold = timezone.now() - timezone.timedelta(minutes=10) # Bot active if heartbeat within 10 mins
        is_bot_active = bot_status_obj.last_heartbeat >= active_threshold

        unread_logs_count = BotActivityLog.objects.filter(is_acknowledged=False).count()
        critical_errors_count = BotActivityLog.objects.filter(
            log_level__in=['ERROR', 'CRITICAL'],
            is_acknowledged=False,
            timestamp__gte=timezone.now() - timezone.timedelta(days=3)
        ).count()

        return Response({
            'is_bot_active': is_bot_active,
            'active_bot_count': 1 if is_bot_active else 0,
            'unread_logs_count': unread_logs_count,
            'critical_errors_count': critical_errors_count,
            'last_heartbeat': bot_status_obj.last_heartbeat,
            'bot_status_message': bot_status_obj.status_message,
            'bot_command': bot_status_obj.command
        })

class BotLogDataView(APIView): # Renamed from BotLogView to avoid conflict if any
    # permission_classes = [IsAdminUser] # TODO: Add appropriate permissions

    def get(self, request, format=None):
        bot_id_filter = request.query_params.get('bot_id', None)
        limit = int(request.query_params.get('limit', 50))

        queryset = BotActivityLog.objects.all()
        if bot_id_filter:
            queryset = queryset.filter(bot_id=bot_id_filter)
        
        serializer = BotActivityLogDisplaySerializer(queryset.order_by('-timestamp')[:limit], many=True)
        return Response(serializer.data)

class AcknowledgeLogsView(APIView):
    # permission_classes = [IsAdminUser] # TODO: Add appropriate permissions

    def post(self, request, format=None):
        log_ids = request.data.get('log_ids', [])
        acknowledge_all = request.data.get('acknowledge_all', False)

        if not isinstance(log_ids, list):
            return Response({'error': 'log_ids must be a list'}, status=status.HTTP_400_BAD_REQUEST)
        
        if acknowledge_all:
            updated_count = BotActivityLog.objects.filter(is_acknowledged=False).update(
                is_acknowledged=True, 
                acknowledged_at=timezone.now()
            )
        else:
            updated_count = BotActivityLog.objects.filter(id__in=log_ids, is_acknowledged=False).update(
            is_acknowledged=True, 
            acknowledged_at=timezone.now()
        )
        return Response({'message': f'{updated_count} logs acknowledged.'}, status=status.HTTP_200_OK)

class LiveBotStatusDataView(APIView):
    """
    A dedicated API endpoint to provide live status data for all bots,
    formatted specifically for the live_bot_overview.html page.
    """
    # permission_classes = [IsAdminUser] # TODO: Secure this for admin users

    def get(self, request, format=None):
        bots_data = []
        all_bot_statuses = BotStatus.objects.all()

        for bot_status in all_bot_statuses:
            latest_activity = BotActivityLog.objects.filter(bot_id=bot_status.bot_id).order_by('-timestamp').first()
            
            # This logic is duplicated from live_bot_overview_view, which is fine for now.
            # It could be refactored into a helper function later.
            active_threshold = timezone.now() - timezone.timedelta(minutes=5)
            is_online = bot_status.last_heartbeat >= active_threshold
            
            bots_data.append({
                'id': bot_status.bot_id,
                'name': getattr(bot_status, 'name', bot_status.bot_id),
                'status_message': bot_status.status_message,
                'last_heartbeat': bot_status.last_heartbeat.isoformat(), # Use ISO format for JS
                'is_online': is_online,
                'bot_started_at': bot_status.bot_started_at.isoformat() if bot_status.bot_started_at else None, # Ensure this field exists in model
                'latest_task': latest_activity.message if latest_activity else "No recent activity",
                'total_earnings': str(bot_status.total_earnings), # Ensure this field exists in model
                # Add any other stats needed by the card
                'jobs_scraped_today': bot_status.jobs_scraped_today,
                'proposals_sent_today': bot_status.proposals_sent_today,
                'command': bot_status.command, # Include the pending command
            })
        
        return Response(bots_data)


class BotCommandView(APIView): # For bot to send heartbeats and receive commands
    permission_classes = [HasBotAPIKey] # Bot uses API key

    authentication_classes = [] # Explicitly disable authentication
    permission_classes = [] # Explicitly disable permission checks
    @method_decorator(csrf_exempt) # Apply csrf_exempt to the dispatch method
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, format=None): # Bot sends its status
        bot_id = request.data.get("bot_id", "freelance-bot-main")
        status_message = request.data.get("status_message", "Unknown")
        
        # Use get_or_create to handle the bot status object
        bot_status, created = BotStatus.objects.get_or_create(bot_id=bot_id)
        
        # Update status and heartbeat
        bot_status.status_message = status_message
        bot_status.last_heartbeat = timezone.now()
        
        # Update optional stats if the bot sends them
        if 'proposals_sent_today' in request.data:
            bot_status.proposals_sent_today = request.data['proposals_sent_today']
        if 'jobs_scraped_today' in request.data:
            bot_status.jobs_scraped_today = request.data['jobs_scraped_today']
        if 'total_earnings' in request.data:
            bot_status.total_earnings = request.data['total_earnings']
            
        # Get the command to send back to the bot
        command_to_bot = bot_status.command
        
        # If the bot is about to receive a command, reset it in the DB immediately.
        # This makes the command a "fire-once" instruction.
        if command_to_bot != "NONE":
            bot_status.command = "NONE"
        
        bot_status.save()

        return Response({"message": "Heartbeat received.", "command": command_to_bot}, status=status.HTTP_200_OK)

    # permission_classes_for_set_command = [IsAdminUser] # TODO: Separate permission for admin to set command
    def put(self, request, format=None): # Admin dashboard uses this to send commands
        # This method should have stricter permissions (e.g., IsAdminUser)
        # For simplicity, reusing HasBotAPIKey here is NOT secure for admin actions.
        # You'd typically have a separate endpoint or different permission for admin.
        # This is a conceptual example; secure this properly.
        command = request.data.get("command") # e.g., "STOP_REQUESTED", "NONE"
        if command in ["STOP_REQUESTED", "START_REQUESTED", "RESTART_REQUESTED", "NONE"]: # Accept all valid commands from the frontend
            bot_id = request.data.get("bot_id", "freelance-bot-main")
            # Use get_or_create to be safe
            bot_status, created = BotStatus.objects.get_or_create(bot_id=bot_id)
            bot_status.command = command
            bot_status.save()
            return Response({"message": f"Command '{command}' sent to bot '{bot_id}'."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid command."}, status=status.HTTP_400_BAD_REQUEST)
