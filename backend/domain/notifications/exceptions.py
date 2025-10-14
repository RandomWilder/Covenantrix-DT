"""Notification domain exceptions."""


class NotificationError(Exception):
    """Base exception for notification domain."""
    pass


class NotificationNotFoundError(NotificationError):
    """Raised when a notification is not found."""
    pass


class NotificationStorageError(NotificationError):
    """Raised when a storage operation fails."""
    pass

