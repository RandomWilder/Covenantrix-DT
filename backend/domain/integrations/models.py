"""
Integration Domain Models
Models for external service integrations
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class OAuthProvider(str, Enum):
    """OAuth providers"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class OAuthStatus(str, Enum):
    """OAuth connection status"""
    PENDING = "pending"
    CONNECTED = "connected"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


@dataclass
class OAuthCredentials:
    """OAuth credentials"""
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_at: datetime
    scope: List[str]
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding sensitive data)"""
        return {
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat(),
            "scope": self.scope,
            "is_expired": self.is_expired()
        }


@dataclass
class OAuthAccount:
    """OAuth connected account"""
    id: str
    provider: OAuthProvider
    email: str
    name: Optional[str]
    picture_url: Optional[str]
    credentials: OAuthCredentials
    status: OAuthStatus
    connected_at: datetime
    last_used: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "provider": self.provider.value,
            "email": self.email,
            "name": self.name,
            "picture_url": self.picture_url,
            "status": self.status.value,
            "connected_at": self.connected_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "credentials": self.credentials.to_dict()
        }


@dataclass
class DriveFile:
    """Google Drive file metadata"""
    id: str
    name: str
    mime_type: str
    size: int
    created_time: datetime
    modified_time: datetime
    web_view_link: Optional[str]
    icon_link: Optional[str]
    
    @property
    def size_mb(self) -> float:
        """File size in MB"""
        return round(self.size / (1024 * 1024), 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "mime_type": self.mime_type,
            "size": self.size,
            "size_mb": self.size_mb,
            "created_time": self.created_time.isoformat(),
            "modified_time": self.modified_time.isoformat(),
            "web_view_link": self.web_view_link,
            "icon_link": self.icon_link
        }


@dataclass
class DriveFolder:
    """Google Drive folder metadata"""
    id: str
    name: str
    parent_id: Optional[str]
    created_time: datetime
    modified_time: datetime
    web_view_link: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "created_time": self.created_time.isoformat(),
            "modified_time": self.modified_time.isoformat(),
            "web_view_link": self.web_view_link
        }


@dataclass
class OCRResult:
    """OCR processing result"""
    text: str
    confidence: float
    language: Optional[str]
    page_count: int
    processing_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "page_count": self.page_count,
            "processing_time": self.processing_time,
            "char_count": len(self.text)
        }