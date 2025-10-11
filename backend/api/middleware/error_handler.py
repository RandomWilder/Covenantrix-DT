"""
Global Exception Handlers
Converts exceptions to proper HTTP responses
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from core.exceptions import CovenantrixException

logger = logging.getLogger(__name__)


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add global exception handlers to FastAPI app
    
    Args:
        app: FastAPI application
    """
    
    @app.exception_handler(CovenantrixException)
    async def covenantrix_exception_handler(
        request: Request,
        exc: CovenantrixException
    ):
        """Handle custom Covenantrix exceptions"""
        logger.error(
            f"Covenantrix error: {exc.error_code} - {exc.message}",
            extra={"details": exc.details}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError"""
        logger.error(f"ValueError: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "VALIDATION_ERROR",
                "message": str(exc)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions"""
        logger.exception("Unhandled exception occurred")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }
        )