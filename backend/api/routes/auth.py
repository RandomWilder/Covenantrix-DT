"""
Authentication Routes
Google OAuth and authentication management
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from domain.integrations.google_oauth import GoogleOAuthService
from api.schemas.auth import AuthStatusResponse, AuthUrlResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/google/status", response_model=AuthStatusResponse)
async def get_google_auth_status() -> AuthStatusResponse:
    """
    Check Google authentication status
    
    Returns:
        Authentication status and account info
    """
    try:
        oauth_service = GoogleOAuthService()
        accounts = await oauth_service.list_accounts()
        
        if not accounts:
            return AuthStatusResponse(
                authenticated=False,
                message="No Google accounts authenticated"
            )
        
        account = accounts[0]  # Use first account
        return AuthStatusResponse(
            authenticated=True,
            account_email=account.email,
            account_id=account.id,
            message="Google account authenticated"
        )
        
    except Exception as e:
        logger.error(f"Google auth status check failed: {e}")
        return AuthStatusResponse(
            authenticated=False,
            message=f"Authentication check failed: {str(e)}"
        )


@router.post("/google/authorize", response_model=AuthUrlResponse)
async def initiate_google_auth() -> AuthUrlResponse:
    """
    Initiate Google OAuth flow
    
    Returns:
        OAuth authorization URL
    """
    try:
        oauth_service = GoogleOAuthService()
        auth_url = await oauth_service.get_authorization_url()
        
        return AuthUrlResponse(
            success=True,
            auth_url=auth_url,
            message="OAuth URL generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Google OAuth initiation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate Google OAuth: {str(e)}"
        )


@router.post("/google/callback")
async def handle_google_callback(
    code: str,
    state: Optional[str] = None
):
    """
    Handle Google OAuth callback
    
    Args:
        code: Authorization code from Google
        state: Optional state parameter
        
    Returns:
        Callback confirmation
    """
    try:
        oauth_service = GoogleOAuthService()
        await oauth_service.handle_callback(code, state)
        
        return {
            "success": True,
            "message": "OAuth callback handled successfully"
        }
        
    except Exception as e:
        logger.error(f"Google OAuth callback failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"OAuth callback failed: {str(e)}"
        )
