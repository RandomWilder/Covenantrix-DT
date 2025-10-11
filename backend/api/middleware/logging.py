"""
Request/Response Logging Middleware
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log details"""
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", "none")
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        # Process request
        start_time = time.time()
        
        try:
            response: Response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} - {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "duration": duration,
                    "status_code": response.status_code
                }
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {str(e)} - {duration:.3f}s",
                extra={"request_id": request_id, "duration": duration}
            )
            raise