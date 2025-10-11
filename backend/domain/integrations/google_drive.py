"""
Google Drive Service
Business logic for Google Drive integration
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.integrations.models import (
    OAuthAccount, DriveFile, DriveFolder
)
from domain.integrations.exceptions import (
    DriveError, FileNotFoundError, UnauthorizedError
)

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """
    Google Drive service
    Handles Drive file and folder operations
    """
    
    # Supported MIME types for document processing
    SUPPORTED_MIME_TYPES = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
        'application/msword',  # DOC
        'text/plain',
        'text/rtf',
        'image/png',
        'image/jpeg',
        'image/tiff',
        'image/gif',
        'image/bmp',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # XLSX
        'application/vnd.ms-excel',  # XLS
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # PPTX
        'application/vnd.ms-powerpoint'  # PPT
    ]
    
    def __init__(self):
        """Initialize Drive service"""
        pass
    
    def validate_account(self, account: OAuthAccount) -> None:
        """
        Validate account has Drive access
        
        Args:
            account: OAuth account
            
        Raises:
            UnauthorizedError: Account lacks Drive scope
        """
        required_scope = 'https://www.googleapis.com/auth/drive.readonly'
        if required_scope not in account.credentials.scope:
            raise UnauthorizedError(
                f"Account {account.email} lacks Google Drive access"
            )
    
    def is_supported_file(self, mime_type: str) -> bool:
        """
        Check if file type is supported for processing
        
        Args:
            mime_type: File MIME type
            
        Returns:
            True if supported
        """
        return mime_type in self.SUPPORTED_MIME_TYPES
    
    def filter_supported_files(
        self,
        files: List[DriveFile]
    ) -> List[DriveFile]:
        """
        Filter files to supported types only
        
        Args:
            files: List of Drive files
            
        Returns:
            Filtered list
        """
        supported = [
            file for file in files
            if self.is_supported_file(file.mime_type)
        ]
        
        if len(supported) < len(files):
            logger.info(
                f"Filtered {len(files) - len(supported)} unsupported files"
            )
        
        return supported
    
    def validate_file_size(
        self,
        file: DriveFile,
        max_size_mb: int = 50
    ) -> bool:
        """
        Validate file size
        
        Args:
            file: Drive file
            max_size_mb: Maximum size in MB
            
        Returns:
            True if valid
        """
        return file.size_mb <= max_size_mb
    
    def create_batch_metadata(
        self,
        files: List[DriveFile],
        account: OAuthAccount
    ) -> Dict[str, Any]:
        """
        Create metadata for batch download
        
        Args:
            files: Files to download
            account: OAuth account
            
        Returns:
            Batch metadata
        """
        import uuid
        
        batch_id = str(uuid.uuid4())
        
        metadata = {
            "batch_id": batch_id,
            "account_id": account.id,
            "account_email": account.email,
            "total_files": len(files),
            "total_size_mb": sum(f.size_mb for f in files),
            "file_ids": [f.id for f in files],
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Created batch: {batch_id} with {len(files)} files "
            f"({metadata['total_size_mb']:.2f} MB)"
        )
        
        return metadata
    
    def parse_folder_path(
        self,
        folders: List[DriveFolder],
        folder_id: str
    ) -> str:
        """
        Parse folder path from folder list
        
        Args:
            folders: List of folders
            folder_id: Target folder ID
            
        Returns:
            Folder path string
        """
        # Build folder map
        folder_map = {f.id: f for f in folders}
        
        # Build path
        path_parts = []
        current_id = folder_id
        
        while current_id and current_id in folder_map:
            folder = folder_map[current_id]
            path_parts.insert(0, folder.name)
            current_id = folder.parent_id
        
        return "/".join(path_parts) if path_parts else "/"
    
    def organize_files_by_type(
        self,
        files: List[DriveFile]
    ) -> Dict[str, List[DriveFile]]:
        """
        Organize files by MIME type
        
        Args:
            files: List of files
            
        Returns:
            Dictionary mapping MIME type to files
        """
        organized = {}
        
        for file in files:
            mime = file.mime_type
            if mime not in organized:
                organized[mime] = []
            organized[mime].append(file)
        
        return organized
    
    def get_processing_priority(self, file: DriveFile) -> int:
        """
        Get processing priority for file (higher = more priority)
        
        Args:
            file: Drive file
            
        Returns:
            Priority value (1-10)
        """
        # PDF files have highest priority
        if file.mime_type == 'application/pdf':
            return 10
        
        # Documents
        if 'word' in file.mime_type or 'text' in file.mime_type:
            return 8
        
        # Images (require OCR)
        if 'image' in file.mime_type:
            return 5
        
        # Default
        return 3
    
    def sort_files_by_priority(
        self,
        files: List[DriveFile]
    ) -> List[DriveFile]:
        """
        Sort files by processing priority
        
        Args:
            files: List of files
            
        Returns:
            Sorted list (highest priority first)
        """
        return sorted(
            files,
            key=lambda f: self.get_processing_priority(f),
            reverse=True
        )
    
    async def download_file(self, file_id: str) -> tuple[bytes, str]:
        """
        Download file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Tuple of (file_content, filename)
            
        Raises:
            FileNotFoundError: File not found
            DriveError: Download failed
        """
        try:
            from infrastructure.external.google_api import GoogleAPIService
            
            # Get credentials from OAuth service
            from domain.integrations.google_oauth import GoogleOAuthService
            oauth_service = GoogleOAuthService()
            
            # Get active account
            accounts = await oauth_service.list_accounts()
            if not accounts:
                raise DriveError("No Google account authenticated")
            
            account = accounts[0]  # Use first account
            self.validate_account(account)
            
            # Initialize API service with credentials
            api_service = GoogleAPIService(credentials=account.credentials.to_dict())
            
            # Download file content
            file_content = await api_service.download_file(file_id)
            
            # Get file metadata for filename
            files, _ = await api_service.list_files()
            file_metadata = next((f for f in files if f.get("id") == file_id), None)
            
            if not file_metadata:
                raise FileNotFoundError(f"File metadata not found for {file_id}")
            
            filename = file_metadata.get("name", f"drive_file_{file_id}")
            
            logger.info(f"Downloaded file from Google Drive: {filename}")
            return file_content, filename
            
        except Exception as e:
            logger.error(f"Failed to download Google Drive file {file_id}: {e}")
            raise DriveError(f"Download failed: {str(e)}")
    
    async def list_files(
        self,
        folder_id: Optional[str] = None,
        page_token: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List files from Google Drive
        
        Args:
            folder_id: Optional folder ID to list from
            page_token: Optional pagination token
            
        Returns:
            Tuple of (files_list, next_page_token)
            
        Raises:
            DriveError: Listing failed
        """
        try:
            from infrastructure.external.google_api import GoogleAPIService
            
            # Get credentials from OAuth service
            from domain.integrations.google_oauth import GoogleOAuthService
            oauth_service = GoogleOAuthService()
            
            # Get active account
            accounts = await oauth_service.list_accounts()
            if not accounts:
                raise DriveError("No Google account authenticated")
            
            account = accounts[0]  # Use first account
            self.validate_account(account)
            
            # Initialize API service with credentials
            api_service = GoogleAPIService(credentials=account.credentials.to_dict())
            
            # List files
            files = await api_service.list_files(
                folder_id=folder_id,
                page_size=100
            )
            
            # Filter to supported files only
            supported_files = [
                f for f in files
                if self.is_supported_file(f.get("mimeType", ""))
            ]
            
            logger.info(f"Listed {len(supported_files)} supported files from Google Drive")
            return supported_files, None  # Simplified - no pagination for now
            
        except Exception as e:
            logger.error(f"Failed to list Google Drive files: {e}")
            raise DriveError(f"File listing failed: {str(e)}")