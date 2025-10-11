"""
Chat Domain Models
Pure Python models for chat system
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Source:
    """Source citation for message responses"""
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    confidence: Optional[float] = None
    excerpt: Optional[str] = None


@dataclass
class Message:
    """Chat message entity"""
    id: str
    role: MessageRole
    content: str
    sources: List[Source] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create_user_message(cls, content: str, message_id: Optional[str] = None) -> "Message":
        """Create a user message"""
        return cls(
            id=message_id or str(uuid.uuid4()),
            role=MessageRole.USER,
            content=content
        )
    
    @classmethod
    def create_assistant_message(
        cls, 
        content: str, 
        sources: List[Source] = None,
        message_id: Optional[str] = None
    ) -> "Message":
        """Create an assistant message"""
        return cls(
            id=message_id or str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=content,
            sources=sources or []
        )


@dataclass
class Conversation:
    """Chat conversation entity"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = field(default_factory=list)
    
    @classmethod
    def create_new(cls, title: str, conversation_id: Optional[str] = None) -> "Conversation":
        """Create a new conversation"""
        now = datetime.utcnow()
        return cls(
            id=conversation_id or str(uuid.uuid4()),
            title=title,
            created_at=now,
            updated_at=now
        )
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation"""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def get_last_messages(self, count: int = 10) -> List[Message]:
        """Get the last N messages for context"""
        return self.messages[-count:] if self.messages else []


@dataclass
class ChatResponse:
    """Response from chat service"""
    conversation_id: str
    message_id: str
    response: str
    sources: List[Source] = field(default_factory=list)
    agent_used: Optional[str] = None


@dataclass
class ConversationSummary:
    """Summary of conversation for listing"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_preview: Optional[str] = None
