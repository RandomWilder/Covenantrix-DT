"""
Analytics Domain Exceptions
"""
from core.exceptions import CovenantrixException
from fastapi import status


class AnalyticsError(CovenantrixException):
    """Base analytics error"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="ANALYTICS_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class ClassificationError(AnalyticsError):
    """Classification failed"""
    
    def __init__(self, message: str):
        super().__init__(f"Classification error: {message}")


class ExtractionError(AnalyticsError):
    """Metadata extraction failed"""
    
    def __init__(self, message: str):
        super().__init__(f"Extraction error: {message}")