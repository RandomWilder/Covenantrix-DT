"""
Subscription Enforcement Middleware
Enforces tier limits on API endpoints before processing requests
"""
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class SubscriptionEnforcementMiddleware:
    """
    Middleware to enforce subscription tier limits
    
    Checks subscription limits before processing requests and returns
    appropriate error responses when limits are exceeded.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        """
        Process request through subscription enforcement
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Check if this is a request that needs subscription enforcement
        if self._needs_subscription_check(request):
            try:
                # Import here to avoid circular imports
                from core.dependencies import get_subscription_service
                from domain.subscription.service import SubscriptionService
                
                # Get subscription service (this will be injected by FastAPI)
                # For middleware, we need to get it differently
                subscription_service = self._get_subscription_service()
                
                if subscription_service:
                    # Check upload limits for document uploads
                    if request.url.path.startswith("/api/documents/upload"):
                        allowed, reason = await subscription_service.check_upload_allowed()
                        if not allowed:
                            response = JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={
                                    "error": "Upload limit exceeded",
                                    "detail": reason,
                                    "tier": subscription_service.get_current_subscription().tier
                                }
                            )
                            await response(scope, receive, send)
                            return
                    
                    # Check query limits for chat/queries
                    elif request.url.path.startswith("/api/chat/") or request.url.path.startswith("/api/queries/"):
                        allowed, reason = await subscription_service.check_query_allowed()
                        if not allowed:
                            response = JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={
                                    "error": "Query limit exceeded",
                                    "detail": reason,
                                    "tier": subscription_service.get_current_subscription().tier
                                }
                            )
                            await response(scope, receive, send)
                            return
                
            except Exception as e:
                logger.error(f"Subscription enforcement error: {e}")
                # Continue with request if enforcement fails
                pass
        
        # Continue with the request
        await self.app(scope, receive, send)
    
    def _needs_subscription_check(self, request: Request) -> bool:
        """
        Check if request needs subscription enforcement
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if request needs subscription checking
        """
        # Only check POST requests for resource-consuming operations
        if request.method != "POST":
            return False
        
        # Check specific endpoints that consume resources
        protected_paths = [
            "/api/documents/upload",
            "/api/chat/message",
            "/api/queries/query"
        ]
        
        return any(request.url.path.startswith(path) for path in protected_paths)
    
    def _get_subscription_service(self):
        """
        Get subscription service instance
        
        Returns:
            SubscriptionService instance or None
        """
        try:
            # Import here to avoid circular imports
            from core.dependencies import get_subscription_service
            # Try to get the service, but handle the case where it's not available
            try:
                return get_subscription_service()
            except Exception:
                # Service not available, return None
                return None
        except Exception as e:
            logger.error(f"Failed to get subscription service: {e}")
            return None


def add_subscription_enforcement_middleware(app):
    """
    Add subscription enforcement middleware to FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(SubscriptionEnforcementMiddleware)
    logger.info("Subscription enforcement middleware added")
