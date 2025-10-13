"""
Logging Configuration
Structured logging with context and proper formatting
"""
import logging
import sys
from typing import Optional
from pathlib import Path

from core.config import get_settings


class ContextFilter(logging.Filter):
    """Add context information to log records"""
    
    def filter(self, record):
        # Add default values if not present
        if not hasattr(record, 'request_id'):
            record.request_id = 'N/A'
        if not hasattr(record, 'user_id'):
            record.user_id = 'N/A'
        
        # Handle Unicode in log messages (e.g., Hebrew filenames)
        # Ensure message formatting doesn't fail on non-ASCII characters
        try:
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                # Try to encode/decode to catch potential issues early
                record.msg.encode('utf-8')
        except Exception:
            # If there's any encoding issue, replace with safe representation
            record.msg = repr(record.msg)
        
        return True


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> None:
    """
    Configure application logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    settings = get_settings()
    
    # Determine log level
    level = log_level or ("DEBUG" if settings.server.debug else "INFO")
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with UTF-8 encoding for Hebrew/Unicode filenames
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set UTF-8 encoding for the stream to handle non-ASCII characters
    # This prevents UnicodeEncodeError on Windows console
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass  # Fallback if reconfigure fails
    
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ContextFilter())
    
    # File handler (optional) with UTF-8 encoding
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.addFilter(ContextFilter())
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level),
        handlers=handlers
    )
    
    # Set levels for specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)