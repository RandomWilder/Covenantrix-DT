"""
Authentication API Schemas
Request and response models for authentication operations
"""
from pydantic import BaseModel
from typing import Optional


class AuthStatusResponse(BaseModel):
    """Google authentication status response"""
    authenticated: bool
    account_email: Optional[str] = None
    account_id: Optional[str] = None
    message: str


class AuthUrlResponse(BaseModel):
    """OAuth authorization URL response"""
    success: bool
    auth_url: str
    message: str
