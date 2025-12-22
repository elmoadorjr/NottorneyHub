"""
Logging system for AnkiPH Addon
"""

import logging
import os
from datetime import datetime
from aqt import mw

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class AnkiPHLogger:
    """Central logger for the AnkiPH addon"""
    
    def __init__(self, name="AnkiPH"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers if already initialized
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            self.logger.addHandler(console_handler)
            
            # File handler (optional, but useful)
            try:
                addon_dir = os.path.dirname(__file__)
                log_dir = os.path.join(addon_dir, "logs")
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                log_file = os.path.join(log_dir, "ankiph.log")
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
                self.logger.addHandler(file_handler)
            except Exception as e:
                # Fallback to console only if file logging fails
                print(f"Failed to initialize file logging: {e}")

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.logger.exception(msg, *args, **kwargs)

# Global logger instance
logger = AnkiPHLogger()
