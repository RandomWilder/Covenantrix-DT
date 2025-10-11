"""
Entity domain exceptions
"""


class EntityExtractionError(Exception):
    """Base exception for entity extraction errors"""
    pass


class EntityNotFoundError(EntityExtractionError):
    """Raised when entity data is not found"""
    pass


class EntityProcessingError(EntityExtractionError):
    """Raised when entity processing fails"""
    pass
