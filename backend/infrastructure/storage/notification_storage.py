"""Notification storage implementation."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import asyncio
from filelock import FileLock

from domain.notifications.models import Notification, NotificationAction
from domain.notifications.exceptions import NotificationStorageError

logger = logging.getLogger(__name__)


class NotificationStorage:
    """Storage for notifications using JSON file."""
    
    def __init__(self, working_dir: str):
        """Initialize storage with working directory."""
        self.storage_dir = Path(working_dir) / "rag_storage"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "notifications.json"
        self.lock_file = self.storage_dir / "notifications.json.lock"
        self._ensure_storage_file()
    
    def _ensure_storage_file(self):
        """Ensure storage file exists with proper structure."""
        if not self.storage_file.exists():
            self.storage_file.write_text(json.dumps({"notifications": []}, indent=2))
            logger.info(f"Created notifications storage file at {self.storage_file}")
    
    def _notification_to_dict(self, notification: Notification) -> dict:
        """Convert notification to dictionary for storage."""
        return {
            "id": notification.id,
            "type": notification.type,
            "source": notification.source,
            "title": notification.title,
            "summary": notification.summary,
            "content": notification.content,
            "actions": [
                {"label": a.label, "action": a.action, "url": a.url}
                for a in notification.actions
            ],
            "timestamp": notification.timestamp.isoformat(),
            "read": notification.read,
            "dismissed": notification.dismissed,
            "metadata": notification.metadata,
            "expires_at": notification.expires_at.isoformat() if notification.expires_at else None
        }
    
    def _dict_to_notification(self, data: dict) -> Notification:
        """Convert dictionary to notification object."""
        actions = [
            NotificationAction(
                label=a["label"],
                action=a["action"],
                url=a.get("url")
            )
            for a in data.get("actions", [])
        ]
        
        return Notification(
            id=data["id"],
            type=data["type"],
            source=data["source"],
            title=data["title"],
            summary=data["summary"],
            content=data.get("content"),
            actions=actions,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            read=data.get("read", False),
            dismissed=data.get("dismissed", False),
            metadata=data.get("metadata", {}),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )
    
    async def _read_storage(self) -> dict:
        """Read storage file with locking."""
        lock = FileLock(str(self.lock_file))
        try:
            with lock.acquire(timeout=10):
                data = json.loads(self.storage_file.read_text())
                return data
        except Exception as e:
            logger.error(f"Failed to read notifications storage: {e}")
            raise NotificationStorageError(f"Failed to read storage: {e}")
    
    async def _write_storage(self, data: dict):
        """Write storage file with locking."""
        lock = FileLock(str(self.lock_file))
        try:
            with lock.acquire(timeout=10):
                self.storage_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to write notifications storage: {e}")
            raise NotificationStorageError(f"Failed to write storage: {e}")
    
    async def save_notification(self, notification: Notification):
        """Save a new notification."""
        data = await self._read_storage()
        notifications = data.get("notifications", [])
        notifications.append(self._notification_to_dict(notification))
        data["notifications"] = notifications
        await self._write_storage(data)
        logger.debug(f"Saved notification {notification.id}")
    
    async def get_all_notifications(self) -> List[Notification]:
        """Load all notifications sorted by timestamp (newest first)."""
        data = await self._read_storage()
        notifications = [
            self._dict_to_notification(n)
            for n in data.get("notifications", [])
        ]
        # Sort by timestamp descending
        notifications.sort(key=lambda n: n.timestamp, reverse=True)
        return notifications
    
    async def find_by_id(self, notification_id: str) -> Optional[Notification]:
        """Find a notification by ID."""
        notifications = await self.get_all_notifications()
        for notification in notifications:
            if notification.id == notification_id:
                return notification
        return None
    
    async def find_by_metadata(self, key: str, value: str) -> Optional[Notification]:
        """Find a notification by metadata field."""
        notifications = await self.get_all_notifications()
        for notification in notifications:
            if notification.metadata.get(key) == value:
                return notification
        return None
    
    async def update_notification(self, notification: Notification):
        """Update an existing notification."""
        data = await self._read_storage()
        notifications = data.get("notifications", [])
        
        # Find and update
        updated = False
        for i, n in enumerate(notifications):
            if n["id"] == notification.id:
                notifications[i] = self._notification_to_dict(notification)
                updated = True
                break
        
        if not updated:
            raise NotificationStorageError(f"Notification {notification.id} not found for update")
        
        data["notifications"] = notifications
        await self._write_storage(data)
        logger.debug(f"Updated notification {notification.id}")
    
    async def delete_notification(self, notification_id: str):
        """Delete a notification by ID."""
        data = await self._read_storage()
        notifications = data.get("notifications", [])
        
        # Filter out the notification
        original_count = len(notifications)
        notifications = [n for n in notifications if n["id"] != notification_id]
        
        if len(notifications) == original_count:
            raise NotificationStorageError(f"Notification {notification_id} not found for deletion")
        
        data["notifications"] = notifications
        await self._write_storage(data)
        logger.debug(f"Deleted notification {notification_id}")
    
    async def delete_expired(self, cutoff_date: datetime) -> int:
        """Delete notifications older than cutoff date."""
        data = await self._read_storage()
        notifications = data.get("notifications", [])
        
        original_count = len(notifications)
        notifications = [
            n for n in notifications
            if datetime.fromisoformat(n["timestamp"]) > cutoff_date
        ]
        deleted_count = original_count - len(notifications)
        
        data["notifications"] = notifications
        await self._write_storage(data)
        logger.info(f"Deleted {deleted_count} expired notifications")
        return deleted_count

