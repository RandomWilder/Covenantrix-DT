"""
Google OAuth Service
Handles Google OAuth authentication flow
"""
import logging
import secrets
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx

from core.config import Settings
from infrastructure.storage.user_settings_storage import UserSettingsStorage
from domain.integrations.models import (
    OAuthAccount, 
    OAuthCredentials, 
    OAuthProvider, 
    OAuthStatus
)
from domain.integrations.exceptions import OAuthError

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """
    Google OAuth service
    Handles OAuth authentication flow
    """
    
    # OAuth endpoints
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    REVOKE_URL = "https://oauth2.googleapis.com/revoke"
    
    # OAuth scopes
    DEFAULT_SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    
    # State expiration in minutes
    STATE_EXPIRY_MINUTES = 10
    
    def __init__(self, config: Settings, storage: UserSettingsStorage):
        """Initialize OAuth service"""
        self.config = config
        self.storage = storage
        # Store state with timestamp for expiration tracking
        self._state_store: Dict[str, Tuple[datetime, datetime]] = {}  # state -> (created_at, expires_at)
    
    async def list_accounts(self) -> List[OAuthAccount]:
        """
        List authenticated Google accounts
        
        Returns:
            List of authenticated accounts
        """
        try:
            settings = await self.storage.load_settings()
            accounts = []
            
            for account_data in settings.google_accounts:
                # Convert storage format to domain model
                credentials = OAuthCredentials(
                    access_token=account_data.access_token,
                    refresh_token=account_data.refresh_token,
                    token_type="Bearer",
                    expires_at=datetime.fromisoformat(account_data.token_expiry),
                    scope=account_data.scopes
                )
                
                account = OAuthAccount(
                    id=account_data.account_id,
                    provider=OAuthProvider.GOOGLE,
                    email=account_data.email,
                    name=account_data.display_name,
                    picture_url=None,
                    credentials=credentials,
                    status=OAuthStatus(account_data.status),
                    connected_at=datetime.fromisoformat(account_data.connected_at),
                    last_used=datetime.fromisoformat(account_data.last_used)
                )
                accounts.append(account)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            return []
    
    async def get_account(self, account_id: str) -> Optional[OAuthAccount]:
        """
        Get specific account by ID
        
        Args:
            account_id: Account ID
            
        Returns:
            Account or None if not found
        """
        accounts = await self.list_accounts()
        for account in accounts:
            if account.id == account_id:
                return account
        return None
    
    def _cleanup_expired_states(self):
        """
        Remove expired states from store
        Prevents memory leaks from abandoned OAuth flows
        """
        now = datetime.utcnow()
        expired_states = [
            state for state, (created_at, expires_at) in self._state_store.items()
            if now > expires_at
        ]
        
        for state in expired_states:
            del self._state_store[state]
            logger.debug(f"Cleaned up expired OAuth state: {state[:8]}...")
        
        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired OAuth states")
    
    async def get_authorization_url(self) -> str:
        """
        Get Google OAuth authorization URL
        
        Returns:
            Authorization URL for OAuth flow
            
        Raises:
            OAuthError: OAuth URL generation failed
        """
        try:
            # Cleanup expired states before generating new one
            self._cleanup_expired_states()
            
            if not self.config.google_oauth_client_id:
                raise OAuthError("Google OAuth client ID not configured")
            
            # Generate random state for CSRF protection
            state = secrets.token_urlsafe(32)
            now = datetime.utcnow()
            expires_at = now + timedelta(minutes=self.STATE_EXPIRY_MINUTES)
            self._state_store[state] = (now, expires_at)
            
            logger.info(f"Generated OAuth state with {self.STATE_EXPIRY_MINUTES} minute expiry")
            
            # Build authorization URL
            params = {
                "client_id": self.config.google_oauth_client_id,
                "redirect_uri": self.config.google_oauth_redirect_uri,
                "response_type": "code",
                "scope": " ".join(self.DEFAULT_SCOPES),
                "access_type": "offline",  # Request refresh token
                "state": state,
                "prompt": "consent"  # Force consent to get refresh token
            }
            
            auth_url = f"{self.AUTHORIZATION_URL}?{urlencode(params)}"
            logger.info("Generated OAuth authorization URL")
            
            return auth_url
            
        except Exception as e:
            logger.error(f"OAuth URL generation failed: {e}")
            raise OAuthError(f"Failed to generate OAuth URL: {str(e)}")
    
    async def handle_callback(self, code: str, state: Optional[str] = None) -> OAuthAccount:
        """
        Handle OAuth callback with authorization code
        
        Args:
            code: Authorization code from Google
            state: Optional state parameter for CSRF validation
            
        Returns:
            Authenticated account
            
        Raises:
            OAuthError: Callback handling failed
        """
        try:
            # Cleanup expired states first
            self._cleanup_expired_states()
            
            # Validate state parameter
            if state and state not in self._state_store:
                raise OAuthError("Invalid or expired state parameter - possible CSRF attack or timeout")
            
            # Clean up used state
            if state:
                del self._state_store[state]
                logger.debug(f"Consumed OAuth state: {state[:8]}...")
            
            # Exchange authorization code for tokens
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": self.config.google_oauth_client_id,
                        "client_secret": self.config.google_oauth_client_secret,
                        "redirect_uri": self.config.google_oauth_redirect_uri,
                        "grant_type": "authorization_code"
                    }
                )
                
                if token_response.status_code != 200:
                    raise OAuthError(f"Token exchange failed: {token_response.text}")
                
                token_data = token_response.json()
                
                # Get user info
                userinfo_response = await client.get(
                    self.USERINFO_URL,
                    headers={"Authorization": f"Bearer {token_data['access_token']}"}
                )
                
                if userinfo_response.status_code != 200:
                    raise OAuthError(f"Failed to fetch user info: {userinfo_response.text}")
                
                userinfo = userinfo_response.json()
            
            # Calculate token expiry
            expires_in = token_data.get("expires_in", 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Create OAuthAccount
            account_id = str(uuid.uuid4())
            credentials = OAuthCredentials(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type="Bearer",
                expires_at=expires_at,
                scope=token_data.get("scope", "").split()
            )
            
            account = OAuthAccount(
                id=account_id,
                provider=OAuthProvider.GOOGLE,
                email=userinfo.get("email"),
                name=userinfo.get("name"),
                picture_url=userinfo.get("picture"),
                credentials=credentials,
                status=OAuthStatus.CONNECTED,
                connected_at=datetime.utcnow(),
                last_used=datetime.utcnow()
            )
            
            # Save to storage
            await self._save_account(account)
            
            logger.info(f"OAuth account connected: {account.email}")
            return account
            
        except Exception as e:
            logger.error(f"OAuth callback handling failed: {e}")
            raise OAuthError(f"OAuth callback failed: {str(e)}")
    
    async def refresh_access_token(self, account_id: str) -> str:
        """
        Refresh access token for account
        
        Args:
            account_id: Account ID
            
        Returns:
            New access token
            
        Raises:
            OAuthError: Token refresh failed
        """
        try:
            account = await self.get_account(account_id)
            if not account:
                raise OAuthError(f"Account not found: {account_id}")
            
            if not account.credentials.refresh_token:
                raise OAuthError("No refresh token available")
            
            # Request new access token
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "client_id": self.config.google_oauth_client_id,
                        "client_secret": self.config.google_oauth_client_secret,
                        "refresh_token": account.credentials.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code != 200:
                    raise OAuthError(f"Token refresh failed: {response.text}")
                
                token_data = response.json()
            
            # Update credentials
            expires_in = token_data.get("expires_in", 3600)
            account.credentials.access_token = token_data["access_token"]
            account.credentials.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            account.last_used = datetime.utcnow()
            
            # Save updated account
            await self._save_account(account, update=True)
            
            logger.info(f"Access token refreshed for account: {account.email}")
            return token_data["access_token"]
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise OAuthError(f"Failed to refresh token: {str(e)}")
    
    async def ensure_valid_token(self, account_id: str) -> str:
        """
        Ensure account has valid access token
        Refreshes if expired
        
        Args:
            account_id: Account ID
            
        Returns:
            Valid access token
        """
        account = await self.get_account(account_id)
        if not account:
            raise OAuthError(f"Account not found: {account_id}")
        
        if account.credentials.is_expired():
            return await self.refresh_access_token(account_id)
        
        return account.credentials.access_token
    
    async def revoke_account(self, account_id: str) -> None:
        """
        Revoke account and remove from storage
        
        Args:
            account_id: Account ID
            
        Raises:
            OAuthError: Revocation failed
        """
        try:
            account = await self.get_account(account_id)
            if not account:
                raise OAuthError(f"Account not found: {account_id}")
            
            # Revoke token with Google
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        self.REVOKE_URL,
                        params={"token": account.credentials.access_token}
                    )
            except Exception as e:
                logger.warning(f"Token revocation with Google failed: {e}")
            
            # Remove from storage
            settings = await self.storage.load_settings()
            settings.google_accounts = [
                acc for acc in settings.google_accounts 
                if acc.account_id != account_id
            ]
            await self.storage.save_settings(settings)
            
            logger.info(f"Account revoked: {account.email}")
            
        except Exception as e:
            logger.error(f"Account revocation failed: {e}")
            raise OAuthError(f"Failed to revoke account: {str(e)}")
    
    async def _save_account(self, account: OAuthAccount, update: bool = False) -> None:
        """
        Save account to storage
        
        Args:
            account: Account to save
            update: If True, update existing account; if False, add new account
        """
        from api.schemas.settings import GoogleAccountSettings
        
        settings = await self.storage.load_settings()
        
        # Convert to storage format
        account_settings = GoogleAccountSettings(
            account_id=account.id,
            email=account.email,
            display_name=account.name,
            provider="google",
            status=account.status.value,
            connected_at=account.connected_at.isoformat(),
            last_used=account.last_used.isoformat(),
            access_token=account.credentials.access_token,
            refresh_token=account.credentials.refresh_token,
            token_expiry=account.credentials.expires_at.isoformat(),
            scopes=account.credentials.scope
        )
        
        if update:
            # Update existing account
            settings.google_accounts = [
                account_settings if acc.account_id == account.id else acc
                for acc in settings.google_accounts
            ]
        else:
            # Add new account
            settings.google_accounts.append(account_settings)
        
        await self.storage.save_settings(settings)