"""Notification API routes."""
import logging
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.notifications import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
    DeleteResponse,
    CleanupResponse,
    CreateNotificationRequest
)
from core.dependencies import get_notification_service
from domain.notifications.service import NotificationService
from domain.notifications.models import NotificationAction
from domain.notifications.exceptions import NotificationNotFoundError, NotificationStorageError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    service: NotificationService = Depends(get_notification_service)
):
    """Get all notifications sorted by timestamp (newest first)."""
    try:
        notifications = await service.get_all_notifications()
        return NotificationListResponse(
            notifications=[NotificationResponse.from_domain(n) for n in notifications]
        )
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    service: NotificationService = Depends(get_notification_service)
):
    """Get count of unread and non-dismissed notifications."""
    try:
        count = await service.get_unread_count()
        return UnreadCountResponse(count=count)
    except Exception as e:
        logger.error(f"Failed to get unread count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """Mark a notification as read."""
    try:
        notification = await service.mark_as_read(notification_id)
        return NotificationResponse.from_domain(notification)
    except NotificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.delete("/{notification_id}", response_model=DeleteResponse)
async def dismiss_notification(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """Dismiss a notification."""
    try:
        await service.dismiss_notification(notification_id)
        return DeleteResponse(success=True, message="Notification dismissed")
    except NotificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to dismiss notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to dismiss notification"
        )


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_notifications(
    service: NotificationService = Depends(get_notification_service)
):
    """Manually trigger cleanup of expired notifications (older than 7 days)."""
    try:
        cutoff_date = datetime.now() - timedelta(days=7)
        deleted_count = await service.cleanup_expired(cutoff_date)
        return CleanupResponse(deleted_count=deleted_count, success=True)
    except Exception as e:
        logger.error(f"Failed to cleanup notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup notifications"
        )


@router.post("", response_model=NotificationResponse)
async def create_notification(
    request: CreateNotificationRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Create a new notification (for Phase 2 update notifications)."""
    try:
        # Convert schema actions to domain actions
        actions = None
        if request.actions:
            actions = [
                NotificationAction(
                    label=a.label,
                    action=a.action,
                    url=a.url
                )
                for a in request.actions
            ]
        
        notification = await service.create_notification(
            type=request.type,
            source=request.source,
            title=request.title,
            summary=request.summary,
            content=request.content,
            actions=actions,
            metadata=request.metadata,
            expires_at=request.expires_at
        )
        return NotificationResponse.from_domain(notification)
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )

