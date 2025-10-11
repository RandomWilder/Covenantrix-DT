"""
Custom Exception Classes
Hierarchical exception structure for better error handling
"""
from typing import Optional, Dict, Any
from fastapi import status


class CovenantrixException(Exception):
    """Base exception for all application errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Domain Exceptions

class DocumentException(CovenantrixException):
    """Base exception for document-related errors"""
    pass


class DocumentNotFoundError(DocumentException):
    """Document not found in storage"""
    
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            error_code="DOCUMENT_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"document_id": document_id}
        )


class DocumentProcessingError(DocumentException):
    """Error during document processing"""
    
    def __init__(self, message: str, document_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="DOCUMENT_PROCESSING_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"document_id": document_id} if document_id else {}
        )


class InvalidDocumentFormatError(DocumentException):
    """Invalid or unsupported document format"""
    
    def __init__(self, filename: str, supported_formats: list):
        super().__init__(
            message=f"Unsupported document format: {filename}",
            error_code="INVALID_DOCUMENT_FORMAT",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "filename": filename,
                "supported_formats": supported_formats
            }
        )


class AnalyticsException(CovenantrixException):
    """Base exception for analytics-related errors"""
    pass


class ClassificationError(AnalyticsException):
    """Error during document classification"""
    
    def __init__(self, message: str, document_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="CLASSIFICATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"document_id": document_id} if document_id else {}
        )


class ExtractionError(AnalyticsException):
    """Error during metadata extraction"""
    
    def __init__(self, message: str, document_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="EXTRACTION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"document_id": document_id} if document_id else {}
        )


class AgentException(CovenantrixException):
    """Base exception for agent-related errors"""
    pass


class AgentNotFoundError(AgentException):
    """Agent not found in registry"""
    
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent not found: {agent_id}",
            error_code="AGENT_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"agent_id": agent_id}
        )


class AgentExecutionError(AgentException):
    """Error during agent task execution"""
    
    def __init__(self, message: str, agent_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="AGENT_EXECUTION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"agent_id": agent_id} if agent_id else {}
        )


class IntegrationException(CovenantrixException):
    """Base exception for external integration errors"""
    pass


class OAuthError(IntegrationException):
    """OAuth authentication error"""
    
    def __init__(self, message: str, provider: str = "google"):
        super().__init__(
            message=message,
            error_code="OAUTH_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"provider": provider}
        )


class ExternalAPIError(IntegrationException):
    """External API call failed"""
    
    def __init__(self, message: str, service: str):
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service}
        )


# Alias for compatibility
class ExternalServiceError(ExternalAPIError):
    """Alias for ExternalAPIError"""
    pass


class StorageException(CovenantrixException):
    """Base exception for storage-related errors"""
    pass


class StorageError(StorageException):
    """General storage error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {}
        )


class StorageReadError(StorageException):
    """Error reading from storage"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="STORAGE_READ_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class StorageWriteError(StorageException):
    """Error writing to storage"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="STORAGE_WRITE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ConfigurationError(CovenantrixException):
    """Configuration error"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ServiceNotAvailableError(CovenantrixException):
    """Service not available error"""
    
    def __init__(self, message: str, service: str):
        super().__init__(
            message=message,
            error_code="SERVICE_NOT_AVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service}
        )


class ProcessingError(CovenantrixException):
    """Processing error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details or {}
        )