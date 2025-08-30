"""
Logging configuration for JuniorGPT
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m', # Red background
        'ENDC': '\033[0m',      # End color
        'BOLD': '\033[1m',      # Bold
    }
    
    def format(self, record):
        # Add color to levelname
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            record.colored_levelname = (
                f"{self.COLORS[record.levelname]}{self.COLORS['BOLD']}"
                f"{record.levelname}{self.COLORS['ENDC']}"
            )
        else:
            record.colored_levelname = record.levelname
            
        return super().format(record)

class SecurityFilter(logging.Filter):
    """Filter to remove sensitive information from logs"""
    
    SENSITIVE_PATTERNS = [
        'api_key',
        'password',
        'token',
        'secret',
        'authorization',
        'bearer',
    ]
    
    def filter(self, record):
        if hasattr(record, 'msg'):
            msg = str(record.msg).lower()
            for pattern in self.SENSITIVE_PATTERNS:
                if pattern in msg:
                    # Replace sensitive data with placeholder
                    record.msg = record.msg.replace(
                        record.args[0] if record.args else '',
                        '[REDACTED]'
                    )
        return True

def setup_logging(
    log_level: str = 'INFO',
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    include_console: bool = True
) -> logging.Logger:
    """
    Set up comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        include_console: Whether to include console output
        
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger('juniorgpt')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create security filter
    security_filter = SecurityFilter()
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(security_filter)
        logger.addHandler(file_handler)
    
    # Console handler
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(colored_levelname)s - %(name)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(security_filter)
        logger.addHandler(console_handler)
    
    # Error handler (separate file for errors)
    if log_file:
        error_file = log_file.replace('.log', '_errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
                'Exception: %(exc_info)s\n'
                'Stack: %(stack_info)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(f'juniorgpt.{name}')

class LogContext:
    """Context manager for adding context to log messages"""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = logging.getLogRecordFactory()
        
    def __enter__(self):
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
            
        logging.setLogRecordFactory(record_factory)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)