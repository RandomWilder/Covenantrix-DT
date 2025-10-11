"""
File Storage
Physical file storage management
"""
import logging
from typing import Optional
from pathlib import Path
import shutil
import hashlib

from core.config import get_settings
from core.exceptions import StorageError

logger = logging.getLogger(__name__)


class FileStorage:
    """
    File storage service for managing physical files
    """
    
    def __init__(self):
        """Initialize file storage"""
        settings = get_settings()
        self.storage_dir = Path(settings.storage.working_dir) / "files"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def _get_file_path(self, document_id: str) -> Path:
        """Get file path for document"""
        # Use subdirectories to avoid too many files in one directory
        subdir = document_id[:2]
        return self.storage_dir / subdir / document_id
    
    async def save_file(
        self,
        document_id: str,
        content: bytes,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Save file to storage
        
        Args:
            document_id: Document UUID
            content: File content
            metadata: Optional metadata
            
        Returns:
            File path
        """
        try:
            file_path = self._get_file_path(document_id)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(content)
            
            self.logger.info(f"Saved file: {document_id} ({len(content)} bytes)")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save file: {e}")
            raise StorageError(
                f"Failed to save file: {str(e)}",
                details={"document_id": document_id}
            )
    
    async def get_file(self, document_id: str) -> Optional[bytes]:
        """
        Get file content
        
        Args:
            document_id: Document UUID
            
        Returns:
            File content or None
        """
        try:
            file_path = self._get_file_path(document_id)
            
            if not file_path.exists():
                self.logger.warning(f"File not found: {document_id}")
                return None
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.logger.debug(f"Retrieved file: {document_id}")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to get file: {e}")
            return None
    
    async def delete_file(self, document_id: str) -> bool:
        """
        Delete file from storage
        
        Args:
            document_id: Document UUID
            
        Returns:
            True if successful
        """
        try:
            file_path = self._get_file_path(document_id)
            
            if not file_path.exists():
                self.logger.warning(f"File not found: {document_id}")
                return False
            
            file_path.unlink()
            self.logger.info(f"Deleted file: {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete file: {e}")
            return False
    
    async def file_exists(self, document_id: str) -> bool:
        """
        Check if file exists
        
        Args:
            document_id: Document UUID
            
        Returns:
            True if exists
        """
        file_path = self._get_file_path(document_id)
        return file_path.exists()
    
    @staticmethod
    def compute_hash(content: bytes) -> str:
        """
        Compute content hash
        
        Args:
            content: File content
            
        Returns:
            SHA-256 hash
        """
        return hashlib.sha256(content).hexdigest()
    
    async def get_storage_stats(self) -> dict:
        """
        Get storage statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.storage_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                "file_count": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_path": str(self.storage_dir)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return {}