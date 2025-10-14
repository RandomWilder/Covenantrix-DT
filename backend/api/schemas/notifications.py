"""Notification API schemas."""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel

from domain.notifications.models import Notification, NotificationAction


class NotificationActionSchema(BaseModel):
    """Schema for notification action."""
    label: str
    action: str
    url: Optional[str] = None


class NotificationResponse(BaseModel):
    """API response for a single notification."""
    id: str
    type: str
    source: Literal['local', 'cloud']
    title: str
    summary: str
    content: Optional[str] = None
    actions: List[NotificationActionSchema] = []
    timestamp: datetime
    read: bool
    dismissed: bool
    metadata: Dict[str, Any] = {}
    expires_at: Optional[datetime] = None
    
    @classmethod
    def from_domain(cls, notification: Notification) -> "NotificationResponse":
        """Convert domain notification to API response."""
        return cls(
            id=notification.id,
            type=notification.type,
            source=notification.source,
            title=notification.title,
            summary=notification.summary,
            content=notification.content,
            actions=[
                NotificationActionSchema(
                    label=a.label,
                    action=a.action,
                    url=a.url
                )
                for a in notification.actions
            ],
            timestamp=notification.timestamp,
            read=notification.read,
            dismissed=notification.dismissed,
            metadata=notification.metadata,
            expires_at=notification.expires_at
        )


class NotificationListResponse(BaseModel):
    """Response for list of notifications."""
    notifications: List[NotificationResponse]


class UnreadCountResponse(BaseModel):
    """Response for unread count."""
    count: int


class DeleteResponse(BaseModel):
    """Response for deletion operations."""
    success: bool
    message: str


class CleanupResponse(BaseModel):
    """Response for cleanup operation."""
    deleted_count: int
    success: bool


class CreateNotificationRequest(BaseModel):
    """Request to create a new notification."""
    type: str
    source: Literal['local', 'cloud']
    title: str
    summary: str
    content: Optional[str] = None
    actions: Optional[List[NotificationActionSchema]] = None
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None

