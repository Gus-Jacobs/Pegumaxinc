from django.urls import path
from .views import (
    LogReceiverView, DashboardDataView, BotLogDataView, 
    AcknowledgeLogsView, BotCommandView
)

app_name = 'bot_monitor' # This line is crucial for namespacing


urlpatterns = [
    path('receive-logs/', LogReceiverView.as_view(), name='receive_logs'),
    path('dashboard-data/', DashboardDataView.as_view(), name='dashboard_data'),
    path('get-logs/', BotLogDataView.as_view(), name='get_bot_logs'),
    path('acknowledge-logs/', AcknowledgeLogsView.as_view(), name='acknowledge_logs'),
    path('bot-command/', BotCommandView.as_view(), name='bot_command'), # For heartbeat and commands
]
