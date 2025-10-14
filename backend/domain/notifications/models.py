from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Literal, Dict, Any


@dataclass
class NotificationAction:
    """Represents an action that can be taken on a notification."""
    label: str
    action: str
    url: Optional[str] = None


@dataclass
class Notification:
    """Core notification model."""
    id: str
    type: str
    source: Literal['local', 'cloud']
    title: str
    summary: str
    timestamp: datetime
    read: bool = False
    dismissed: bool = False
    content: Optional[str] = None
    actions: List[NotificationAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None

