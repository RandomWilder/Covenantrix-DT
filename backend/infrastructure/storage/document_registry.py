"""
Document Registry
Tracks all documents in the system with their metadata
"""
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import asyncio

from core.config import get_settings
from domain.documents.models import Document, DocumentStatus

logger = logging.getLogger(__name__)


class DocumentRegistry:
    """
    Registry for tracking all documents
    JSON-based storage with metadata
    """
    
    def __init__(self):
        """Initialize document registry"""
        settings = get_settings()
        self.storage_dir = Path(settings.storage.working_dir)
        self.registry_file = self.storage_dir / "document_registry.json"
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Initialize registry
        self._init_registry()
    
    def _init_registry(self) -> None:
        """Initialize registry file"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.registry_file.exists():
            default_data = {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "documents": {}
            }
            self._write_registry(default_data)
            self.logger.info(f"Initialized document registry: {self.registry_file}")
    
    def _read_registry(self) -> Dict[str, Any]:
        """Read registry file"""
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to read registry: {e}")
            return {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "documents": {}
            }
    
    def _write_registry(self, data: Dict[str, Any]) -> None:
        """Write registry file"""
        try:
            data["last_updated"] = datetime.utcnow().isoformat()
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to write registry: {e}")
            raise
    
    async def register_document(
        self,
        document_id: str,
        filename: str,
        file_size_bytes: int,
        content_hash: str,
        mime_type: str
    ) -> bool:
        """
        Register a new document
        
        Args:
            document_id: Document UUID
            filename: Original filename
            file_size_bytes: File size in bytes
            content_hash: Content hash
            mime_type: MIME type
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                data = self._read_registry()
                
                # Check if already exists
                if document_id in data["documents"]:
                    self.logger.warning(f"Document already registered: {document_id}")
                    return False
                
                data["documents"][document_id] = {
                    "document_id": document_id,
                    "filename": filename,
                    "file_size_bytes": file_size_bytes,
                    "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
                    "content_hash": content_hash,
                    "mime_type": mime_type,
                    "status": DocumentStatus.PENDING.value,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                self._write_registry(data)
                self.logger.info(f"Registered document: {document_id} ({filename})")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to register document: {e}")
                return False
    
    async def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        processing_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update document status
        
        Args:
            document_id: Document UUID
            status: New status
            processing_info: Processing metadata
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                data = self._read_registry()
                
                if document_id not in data["documents"]:
                    self.logger.warning(f"Document not found: {document_id}")
                    return False
                
                data["documents"][document_id]["status"] = status.value
                data["documents"][document_id]["updated_at"] = datetime.utcnow().isoformat()
                
                if processing_info:
                    data["documents"][document_id]["processing"] = processing_info
                
                self._write_registry(data)
                self.logger.info(f"Updated status for {document_id}: {status.value}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to update status: {e}")
                return False
    
    async def update_processing_stage(
        self,
        document_id: str,
        stage: str,
        progress_percent: int,
        message: str
    ) -> bool:
        """
        Update document processing stage
        
        Args:
            document_id: Document UUID
            stage: Processing stage name
            progress_percent: Progress percentage (0-100)
            message: User-friendly message
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                data = self._read_registry()
                
                if document_id not in data["documents"]:
                    self.logger.warning(f"Document not found: {document_id}")
                    return False
                
                # Update processing stage info
                if "processing" not in data["documents"][document_id]:
                    data["documents"][document_id]["processing"] = {}
                
                data["documents"][document_id]["processing"]["stage"] = stage
                data["documents"][document_id]["processing"]["progress_percent"] = progress_percent
                data["documents"][document_id]["processing"]["message"] = message
                data["documents"][document_id]["processing"]["stage_updated_at"] = datetime.utcnow().isoformat()
                data["documents"][document_id]["updated_at"] = datetime.utcnow().isoformat()
                
                self._write_registry(data)
                self.logger.debug(f"Updated stage for {document_id}: {stage} ({progress_percent}%)")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to update processing stage: {e}")
                return False
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata
        
        Args:
            document_id: Document UUID
            
        Returns:
            Document metadata or None
        """
        async with self._lock:
            try:
                data = self._read_registry()
                return data["documents"].get(document_id)
            except Exception as e:
                self.logger.error(f"Failed to get document: {e}")
                return None
    
    async def list_documents(
        self,
        status: Optional[DocumentStatus] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all documents
        
        Args:
            status: Filter by status
            include_deleted: Include deleted documents
            
        Returns:
            List of documents
        """
        async with self._lock:
            try:
                data = self._read_registry()
                documents = list(data["documents"].values())
                
                # Filter by status
                if status:
                    documents = [d for d in documents if d.get("status") == status.value]
                
                # Filter deleted
                if not include_deleted:
                    documents = [d for d in documents if d.get("status") != DocumentStatus.DELETED.value]
                
                return documents
                
            except Exception as e:
                self.logger.error(f"Failed to list documents: {e}")
                return []
    
    async def delete_document(self, document_id: str, soft_delete: bool = True) -> bool:
        """
        Delete document from registry
        
        Args:
            document_id: Document UUID
            soft_delete: Mark as deleted instead of removing
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                data = self._read_registry()
                
                if document_id not in data["documents"]:
                    self.logger.warning(f"Document not found: {document_id}")
                    return False
                
                if soft_delete:
                    data["documents"][document_id]["status"] = DocumentStatus.DELETED.value
                    data["documents"][document_id]["deleted_at"] = datetime.utcnow().isoformat()
                else:
                    del data["documents"][document_id]
                
                self._write_registry(data)
                self.logger.info(f"Deleted document: {document_id} (soft={soft_delete})")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to delete document: {e}")
                return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics
        
        Returns:
            Statistics dictionary
        """
        docs = await self.list_documents(include_deleted=True)
        
        stats = {
            "total_documents": len(docs),
            "by_status": {},
            "total_size_mb": 0.0
        }
        
        for doc in docs:
            status = doc.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["total_size_mb"] += doc.get("file_size_mb", 0.0)
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        
        return stats
    
    async def reset_registry(self) -> bool:
        """
        Reset document registry to clean state
        
        This will:
        - Clear all document entries
        - Reset registry to initial state
        - Maintain registry structure
        
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                # Create clean registry data
                clean_data = {
                    "version": "1.0",
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": datetime.utcnow().isoformat(),
                    "documents": {}
                }
                
                # Write clean registry
                self._write_registry(clean_data)
                
                self.logger.info("Document registry reset to clean state")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to reset registry: {e}")
                return False