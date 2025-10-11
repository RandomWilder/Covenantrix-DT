"""
Chat Domain Exceptions
"""
from core.exceptions import CovenantrixException
from fastapi import status


class ChatError(CovenantrixException):
    """Base chat error"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="CHAT_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class ConversationNotFoundError(ChatError):
    """Conversation not found"""
    
    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Conversation not found: {conversation_id}"
        )


class MessageProcessingError(ChatError):
    """Message processing failed"""
    
    def __init__(self, message: str, conversation_id: str = None):
        super().__init__(
            message=message
        )


class InvalidMessageError(ChatError):
    """Invalid message format or content"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message
        )


class ConversationStorageError(ChatError):
    """Error saving or loading conversation"""
    
    def __init__(self, message: str, conversation_id: str = None):
        super().__init__(
            message=message
        )
