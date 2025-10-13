"""
Google API Service
Handles Google API interactions (Drive, etc.)
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List

import httpx

from core.config import get_settings
from core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class GoogleAPIService:
    """
    Google API service for Drive and other services
    """
    
    # Drive API v3 endpoints
    DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
    
    def __init__(self, credentials: Optional[Dict] = None, oauth_service: Optional[Any] = None):
        """
        Initialize Google API service
        
        Args:
            credentials: Google OAuth credentials dict with 'access_token' key
            oauth_service: Optional GoogleOAuthService for token refresh
        """
        settings = get_settings()
        self.credentials = credentials
        self.oauth_service = oauth_service
        self.logger = logging.getLogger(__name__)
    
    async def _request_with_retry(
        self, 
        method: str, 
        url: str, 
        account_id: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """
        Make HTTP request with retry logic
        Handles 401 (token refresh), 429 (rate limit), 500 (server error)
        
        Args:
            method: HTTP method
            url: URL to request
            account_id: Account ID for token refresh
            max_retries: Maximum retry attempts
            **kwargs: Additional arguments for httpx.request
            
        Returns:
            Response data
        """
        backoff = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url, **kwargs)
                    
                    if response.status_code == 401:
                        # Token expired - trigger refresh if oauth_service available
                        if self.oauth_service and account_id:
                            logger.info(f"Token expired, refreshing for account {account_id}")
                            new_token = await self.oauth_service.ensure_valid_token(account_id)
                            # Update headers and retry
                            if "headers" in kwargs:
                                kwargs["headers"]["Authorization"] = f"Bearer {new_token}"
                            continue
                        else:
                            raise ExternalServiceError(
                                "Access token expired and no refresh service available",
                                service="google_drive"
                            )
                    
                    elif response.status_code == 429:
                        # Rate limited - wait and retry
                        wait_time = backoff * (2 ** attempt)
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    elif response.status_code >= 500:
                        # Server error - retry with backoff
                        if attempt < max_retries - 1:
                            wait_time = backoff * (2 ** attempt)
                            logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise ExternalServiceError(
                                f"Google API server error: {response.status_code}",
                                service="google_drive"
                            )
                    
                    # Success - return response
                    response.raise_for_status()
                    
                    # Return JSON for regular responses, bytes for downloads
                    if "alt=media" in url:
                        return response.content
                    else:
                        return response.json()
                    
            except httpx.HTTPStatusError as e:
                if attempt == max_retries - 1:
                    raise ExternalServiceError(
                        f"Google API request failed: {str(e)}",
                        service="google_drive"
                    )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ExternalServiceError(
                        f"Google API request error: {str(e)}",
                        service="google_drive"
                    )
        
        raise ExternalServiceError("Max retries exceeded", service="google_drive")
    
    async def list_files(
        self,
        access_token: str,
        account_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        mime_type: Optional[str] = None,
        page_size: int = 100,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files from Google Drive
        
        Args:
            access_token: OAuth access token
            account_id: Account ID for token refresh
            folder_id: Folder ID to list from (None for root)
            mime_type: Filter by MIME type
            page_size: Number of results per page
            search_query: Search query string
            
        Returns:
            List of file metadata
        """
        try:
            # Build query
            query_parts = []
            
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            
            if mime_type:
                query_parts.append(f"mimeType='{mime_type}'")
            
            if search_query:
                query_parts.append(f"name contains '{search_query}'")
            
            # Don't show trashed files
            query_parts.append("trashed=false")
            
            query = " and ".join(query_parts) if query_parts else None
            
            # Build request params
            params = {
                "pageSize": page_size,
                "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink,iconLink,createdTime)"
            }
            
            if query:
                params["q"] = query
            
            # Make request
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            data = await self._request_with_retry(
                "GET",
                self.DRIVE_FILES_URL,
                account_id=account_id,
                headers=headers,
                params=params
            )
            
            return data.get("files", [])
            
        except Exception as e:
            logger.error(f"Failed to list Drive files: {e}")
            raise ExternalServiceError(
                f"Failed to list Drive files: {str(e)}",
                service="google_drive"
            )
    
    async def download_file(
        self,
        access_token: str,
        file_id: str,
        account_id: Optional[str] = None
    ) -> bytes:
        """
        Download file from Google Drive
        
        Args:
            access_token: OAuth access token
            file_id: File ID
            account_id: Account ID for token refresh
            
        Returns:
            File content as bytes
        """
        try:
            # Build download URL
            url = f"{self.DRIVE_FILES_URL}/{file_id}?alt=media"
            
            # Make request
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            content = await self._request_with_retry(
                "GET",
                url,
                account_id=account_id,
                headers=headers
            )
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to download Drive file: {e}")
            raise ExternalServiceError(
                f"Failed to download Drive file: {str(e)}",
                service="google_drive"
            )
    
    async def get_file_metadata(
        self,
        access_token: str,
        file_id: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get file metadata from Google Drive
        
        Args:
            access_token: OAuth access token
            file_id: File ID
            account_id: Account ID for token refresh
            
        Returns:
            File metadata
        """
        try:
            url = f"{self.DRIVE_FILES_URL}/{file_id}"
            params = {
                "fields": "id,name,mimeType,size,modifiedTime,webViewLink,iconLink,createdTime"
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            data = await self._request_with_retry(
                "GET",
                url,
                account_id=account_id,
                headers=headers,
                params=params
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            raise ExternalServiceError(
                f"Failed to get file metadata: {str(e)}",
                service="google_drive"
            )