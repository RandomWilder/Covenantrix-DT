"""Notification domain service."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from .models import Notification, NotificationAction
from .exceptions import NotificationNotFoundError

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self, storage):
        """Initialize with storage dependency."""
        self.storage = storage
    
    async def create_notification(
        self,
        type: str,
        source: str,
        title: str,
        summary: str,
        content: Optional[str] = None,
        actions: Optional[List[NotificationAction]] = None,
        metadata: Optional[dict] = None,
        expires_at: Optional[datetime] = None
    ) -> Notification:
        """Create a new notification with deduplication support."""
        metadata = metadata or {}
        
        # Check for deduplication key
        if 'dedup_key' in metadata:
            dedup_key = metadata['dedup_key']
            existing = await self.storage.find_by_metadata('dedup_key', dedup_key)
            if existing and not existing.dismissed:
                logger.info(f"Found existing notification with dedup_key={dedup_key}, returning existing")
                return existing
        
        # Create new notification
        notification = Notification(
            id=str(uuid4()),
            type=type,
            source=source,
            title=title,
            summary=summary,
            content=content,
            actions=actions or [],
            timestamp=datetime.utcnow(),
            read=False,
            dismissed=False,
            metadata=metadata,
            expires_at=expires_at
        )
        
        await self.storage.save_notification(notification)
        logger.info(f"Created notification: {notification.id}")
        return notification
    
    async def get_all_notifications(self) -> List[Notification]:
        """Retrieve all active (non-dismissed) notifications sorted newest first."""
        all_notifications = await self.storage.get_all_notifications()
        # Filter out dismissed notifications
        notifications = [n for n in all_notifications if not n.dismissed]
        return notifications
    
    async def get_unread_count(self) -> int:
        """Count unread and non-dismissed notifications."""
        notifications = await self.storage.get_all_notifications()
        count = sum(1 for n in notifications if not n.read and not n.dismissed)
        return count
    
    async def mark_as_read(self, notification_id: str) -> Notification:
        """Mark a notification as read."""
        notification = await self.storage.find_by_id(notification_id)
        if not notification:
            raise NotificationNotFoundError(f"Notification {notification_id} not found")
        
        notification.read = True
        await self.storage.update_notification(notification)
        logger.info(f"Marked notification {notification_id} as read")
        return notification
    
    async def dismiss_notification(self, notification_id: str) -> Notification:
        """Dismiss a notification."""
        notification = await self.storage.find_by_id(notification_id)
        if not notification:
            raise NotificationNotFoundError(f"Notification {notification_id} not found")
        
        notification.dismissed = True
        await self.storage.update_notification(notification)
        logger.info(f"Dismissed notification {notification_id}")
        return notification
    
    async def cleanup_expired(self, cutoff_date: Optional[datetime] = None) -> int:
        """Delete notifications older than cutoff date (default: 7 days ago)."""
        if cutoff_date is None:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        deleted_count = await self.storage.delete_expired(cutoff_date)
        logger.info(f"Cleaned up {deleted_count} expired notifications")
        return deleted_count

