"""
Integration Domain Exceptions
"""
from typing import Optional
from core.exceptions import CovenantrixException
from fastapi import status


class IntegrationError(CovenantrixException):
    """Base integration error"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="INTEGRATION_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class OAuthError(IntegrationError):
    """OAuth error"""
    
    def __init__(self, message: str, provider: str = "google"):
        super().__init__(f"OAuth error ({provider}): {message}")
        self.details = {"provider": provider}


class InvalidStateError(OAuthError):
    """Invalid OAuth state"""
    
    def __init__(self, message: str):
        super().__init__(message)


class TokenExpiredError(OAuthError):
    """OAuth token expired"""
    
    def __init__(self, message: str):
        super().__init__(message)


class UnauthorizedError(IntegrationError):
    """Unauthorized access"""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.status_code = status.HTTP_401_UNAUTHORIZED


class DriveError(IntegrationError):
    """Google Drive error"""
    
    def __init__(self, message: str):
        super().__init__(f"Drive error: {message}")


class FileNotFoundError(DriveError):
    """Drive file not found"""
    
    def __init__(self, file_id: str):
        super().__init__(f"File not found: {file_id}")
        self.details = {"file_id": file_id}
        self.status_code = status.HTTP_404_NOT_FOUND


class OCRError(IntegrationError):
    """OCR processing error"""
    
    def __init__(self, message: str):
        super().__init__(f"OCR error: {message}")


class GoogleVisionAPIError(IntegrationError):
    """Google Vision API error"""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(f"Google Vision API error: {message}")
        if status_code:
            self.status_code = status_code


class ExternalAPIError(IntegrationError):
    """External API error"""
    
    def __init__(self, message: str, service: str):
        super().__init__(f"External API error ({service}): {message}")
        self.details = {"service": service}