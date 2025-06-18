import requests
import time
import threading
from core.logger import bot_logger
from collections import deque

class RemoteLogger:
    def __init__(self, config):
        self.config = config
        self.log_buffer = deque(maxlen=100) # Store up to 100 summary logs before flushing
        self.remote_log_url = self.config.get("django_log_receiver_url") # e.g., "https://your-django-app.onrender.com/bot-api/receive-logs/"
        self.remote_log_api_key = self.config.get("django_log_api_key")
        self.flush_interval_seconds = self.config.get("remote_log_flush_interval_seconds", 3 * 60 * 60) # Default 3 hours
        self.min_buffer_flush_size = self.config.get("remote_log_min_buffer_flush_size", 20) # Flush if buffer has this many items
        
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()

    def add_summary_log(self, message: str, level: str = "INFO", platform: str = "System", source: str = None):
        with self.lock:
            entry = {
                "message": message,
                "log_level": level.upper(),
                "platform": platform,
                "source": source
            }
            self.log_buffer.append(entry)
            bot_logger.debug(f"Remote log added to buffer: {message}")
            if len(self.log_buffer) >= self.min_buffer_flush_size:
                self._flush_buffer_thread() # Flush if buffer is getting full

    def _flush_buffer(self):
        with self.lock:
            if not self.log_buffer:
                return
            logs_to_send = list(self.log_buffer)
            self.log_buffer.clear()
        
        if not self.remote_log_url or not self.remote_log_api_key:
            bot_logger.warning("Remote log URL or API key not configured. Cannot send logs.")
            return

        headers = {"X-Bot-API-Key": self.remote_log_api_key, "Content-Type": "application/json"}
        try:
            response = requests.post(self.remote_log_url, json=logs_to_send, headers=headers, timeout=30)
            if response.status_code == 201:
                bot_logger.info(f"Successfully sent {len(logs_to_send)} summary logs to remote server.")
            else:
                bot_logger.error(f"Failed to send logs to remote server. Status: {response.status_code}, Response: {response.text}")
        except requests.RequestException as e:
            bot_logger.error(f"Error sending logs to remote server: {e}")

    def _flush_buffer_thread(self):
        # Run flush in a separate thread to avoid blocking main operations
        flush_thread = threading.Thread(target=self._flush_buffer, daemon=True)
        flush_thread.start()

    def _periodic_flush(self):
        while self.is_running:
            time.sleep(self.flush_interval_seconds)
            if self.is_running: # Check again after sleep
                bot_logger.info("RemoteLogger: Performing periodic log flush.")
                self._flush_buffer_thread()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._periodic_flush, daemon=True)
            self.thread.start()
            bot_logger.info("RemoteLogger started for periodic log flushing.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            bot_logger.info("RemoteLogger stopping. Flushing remaining logs...")
            self._flush_buffer_thread() # Final flush
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5) # Wait for thread to finish
            bot_logger.info("RemoteLogger stopped.")