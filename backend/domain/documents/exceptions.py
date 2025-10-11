"""
Document Domain Exceptions
"""
from typing import Optional, List
from core.exceptions import CovenantrixException
from fastapi import status


class DocumentError(CovenantrixException):
    """Base document error"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="DOCUMENT_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class DocumentNotFoundError(DocumentError):
    """Document not found"""
    
    def __init__(self, document_id: str):
        super().__init__(f"Document not found: {document_id}")
        self.details = {"document_id": document_id}
        self.status_code = status.HTTP_404_NOT_FOUND


class InvalidDocumentFormatError(DocumentError):
    """Invalid document format"""
    
    def __init__(self, filename: str, supported_formats: List[str]):
        super().__init__(f"Unsupported format: {filename}")
        self.details = {
            "filename": filename,
            "supported_formats": supported_formats
        }
        self.status_code = status.HTTP_400_BAD_REQUEST


class DocumentProcessingError(DocumentError):
    """Document processing failed"""
    
    def __init__(self, message: str, document_id: Optional[str] = None):
        super().__init__(message)
        if document_id:
            self.details = {"document_id": document_id}


class StorageError(DocumentError):
    """Storage operation failed"""
    
    def __init__(self, message: str):
        super().__init__(f"Storage error: {message}")
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR