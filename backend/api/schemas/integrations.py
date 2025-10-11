"""
Integration API Schemas
Request and response models for external integrations
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any, List, Optional


class OAuthUrlResponse(BaseModel):
    """OAuth URL response"""
    success: bool
    auth_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request"""
    code: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """OAuth callback response"""
    success: bool
    account: Dict[str, Any]
    message: str


class AccountResponse(BaseModel):
    """OAuth account response"""
    success: bool
    account: Dict[str, Any]


class AccountListResponse(BaseModel):
    """OAuth account list response"""
    success: bool
    accounts: List[Dict[str, Any]]
    total_count: int


class DriveFileResponse(BaseModel):
    """Drive file response"""
    success: bool
    file: Dict[str, Any]


class DriveFileListResponse(BaseModel):
    """Drive file list response"""
    success: bool
    files: List[Dict[str, Any]]
    total_count: int


class DriveDownloadRequest(BaseModel):
    """Drive file download request"""
    file_ids: List[str] = Field(..., min_items=1, description="File IDs to download")
    process_immediately: bool = Field(True, description="Process files immediately after download")


class DriveDownloadResponse(BaseModel):
    """Drive file download response"""
    success: bool
    batch_id: str
    downloaded_files: List[Dict[str, Any]]
    message: str


class IntegrationStatusResponse(BaseModel):
    """Integration status response"""
    success: bool
    integrations: Dict[str, Any]