"""
Chat API Schemas
Request and response models for chat operations
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from api.schemas.common import BaseResponse


class Source(BaseModel):
    """Source citation for message responses"""
    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document name")
    page_number: Optional[int] = Field(None, description="Page number")
    confidence: Optional[float] = Field(None, description="Confidence score")
    excerpt: Optional[str] = Field(None, description="Relevant excerpt")


class Message(BaseModel):
    """Chat message"""
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    sources: List[Source] = Field(default_factory=list, description="Message sources")
    timestamp: str = Field(..., description="Message timestamp")


class Conversation(BaseModel):
    """Chat conversation"""
    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    messages: List[Message] = Field(default_factory=list, description="Conversation messages")


class ConversationSummary(BaseModel):
    """Conversation summary for listing"""
    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    message_count: int = Field(..., description="Number of messages")
    last_message_preview: Optional[str] = Field(None, description="Preview of last message")


# Request Schemas

class ChatMessageRequest(BaseModel):
    """Send message request"""
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    message: str = Field(..., min_length=1, description="User message")
    agent_id: Optional[str] = Field(None, description="Selected agent ID")
    document_ids: Optional[List[str]] = Field(None, description="Document IDs for context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "What are the key terms in this contract?",
                "agent_id": "market_research_agent",
                "document_ids": ["doc1", "doc2"]
            }
        }


class CreateConversationRequest(BaseModel):
    """Create conversation request"""
    title: str = Field(..., min_length=1, description="Conversation title")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Contract Analysis Discussion"
            }
        }


# Response Schemas

class ChatMessageResponse(BaseResponse):
    """Send message response"""
    conversation_id: str = Field(..., description="Conversation ID")
    message_id: str = Field(..., description="Message ID")
    response: str = Field(..., description="Assistant response")
    sources: List[Source] = Field(default_factory=list, description="Response sources")
    agent_used: Optional[str] = Field(None, description="Agent used for response")


class ConversationResponse(BaseResponse):
    """Conversation response"""
    conversation: Conversation = Field(..., description="Conversation data")


class ConversationListResponse(BaseResponse):
    """Conversation list response"""
    conversations: List[ConversationSummary] = Field(..., description="List of conversations")
    total_count: int = Field(..., description="Total number of conversations")


class MessageListResponse(BaseResponse):
    """Message list response"""
    messages: List[Message] = Field(..., description="List of messages")
    total_count: int = Field(..., description="Total number of messages")


class ConversationCreatedResponse(BaseResponse):
    """Conversation created response"""
    conversation: ConversationSummary = Field(..., description="Created conversation")


class ConversationDeletedResponse(BaseResponse):
    """Conversation deleted response"""
    conversation_id: str = Field(..., description="Deleted conversation ID")
    deleted: bool = Field(True, description="Deletion status")


class StreamTokenResponse(BaseModel):
    """Streaming token response"""
    token: Optional[str] = Field(None, description="Content token")
    done: bool = Field(False, description="Stream completion flag")
    message_id: Optional[str] = Field(None, description="Message ID when done")
    sources: Optional[List[Source]] = Field(None, description="Response sources when done")