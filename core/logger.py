import logging
import os
# import sys # Not strictly needed for this specific fix
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "bot.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logger(name="freelance_bot", log_level=logging.INFO):
    """
    Sets up a logger that logs to both console and a file.
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers(): # Avoid adding multiple handlers if already configured
        return logger

    logger.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    ch = logging.StreamHandler() # Let console handler use default stream encoding
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler (Rotates logs, 1MB per file, keeps 5 backups)
    # Explicitly set encoding for file handler to UTF-8
    fh = RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=5, encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

bot_logger = setup_logger()