"""
API Middleware
"""
from api.middleware.cors import setup_cors
from api.middleware.error_handler import add_exception_handlers
from api.middleware.logging import LoggingMiddleware

__all__ = [
    "setup_cors",
    "add_exception_handlers",
    "LoggingMiddleware"
]