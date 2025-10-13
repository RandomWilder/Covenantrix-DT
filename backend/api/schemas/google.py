"""
Google API Schemas
Request and response models for Google OAuth and Drive endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class GoogleAccountResponse(BaseModel):
    """Google account response"""
    account_id: str
    email: str
    display_name: Optional[str] = None
    status: str
    connected_at: str
    last_used: str
    scopes: List[str] = Field(default_factory=list)


class GoogleAccountsListResponse(BaseModel):
    """List of Google accounts response"""
    success: bool = True
    accounts: List[GoogleAccountResponse]


class AuthUrlResponse(BaseModel):
    """OAuth authorization URL response"""
    success: bool = True
    auth_url: str
    message: Optional[str] = None


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request"""
    code: str
    state: Optional[str] = None


class DriveFileResponse(BaseModel):
    """Google Drive file metadata response"""
    id: str
    name: str
    mime_type: Optional[str] = Field(default="", alias="mimeType")
    size: Optional[int] = None
    modified_time: Optional[str] = Field(default="", alias="modifiedTime")
    web_view_link: Optional[str] = Field(None, alias="webViewLink")
    icon_link: Optional[str] = Field(None, alias="iconLink")
    
    class Config:
        populate_by_name = True
        by_alias = True


class DriveFilesListRequest(BaseModel):
    """Drive files list request"""
    account_id: str
    folder_id: Optional[str] = None
    mime_type: Optional[str] = None
    search_query: Optional[str] = None
    page_size: int = Field(default=100, ge=1, le=1000)


class DriveFilesListResponse(BaseModel):
    """Drive files list response"""
    success: bool = True
    files: List[DriveFileResponse]
    account_id: str
    message: Optional[str] = None


class DriveDownloadRequest(BaseModel):
    """Drive file download request"""
    account_id: str
    file_ids: List[str]


class DriveFileStreamRequest(BaseModel):
    """Drive file stream request for streaming endpoint"""
    account_id: str
    file_ids: List[str]


class DriveDownloadResult(BaseModel):
    """Single file download result"""
    file_id: str
    success: bool
    document_id: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None


class DriveDownloadResponse(BaseModel):
    """Drive file download response"""
    success: bool
    results: List[DriveDownloadResult]
    message: Optional[str] = None


class AccountRemoveResponse(BaseModel):
    """Account removal response"""
    success: bool = True
    message: str

