import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

def get_logger(name: str = "zecpath", 
               log_file: Optional[str] = None, 
               level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with rotating file handler and console output.
    
    Args:
        name: Name of the logger (e.g., 'parsers', 'engines')
        log_file: Optional path to the log file. Defaults to 'logs/<name>.log'.
        level: Logging level (default: logging.INFO)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if the logger was already initialized
    if logger.handlers:
        return logger

    # Ensure log directory exists
    if log_file is None:
        log_file = os.path.join("logs", f"{name}.log")
    
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Professional formatting
    # Example: 2026-03-29 12:00:00,000 - parser - INFO - Extraction started
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler (5 MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Global default logger instance
system_logger = get_logger("ai_system")
