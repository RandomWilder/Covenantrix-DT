"""
Analytics Storage
JSON-based storage for document analytics metadata
"""
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import asyncio

from core.config import get_settings

logger = logging.getLogger(__name__)


class AnalyticsStorage:
    """
    Storage service for analytics metadata
    Thread-safe JSON-based storage
    """
    
    def __init__(self):
        """Initialize analytics storage"""
        settings = get_settings()
        self.storage_dir = Path(settings.storage.working_dir)
        self.storage_file = self.storage_dir / settings.storage.analytics_file
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Initialize storage file if it doesn't exist
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Initialize storage file with default structure"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.storage_file.exists():
            default_data = {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "documents": {}
            }
            self._write_storage(default_data)
            self.logger.info(f"Initialized analytics storage: {self.storage_file}")
    
    def _read_storage(self) -> Dict[str, Any]:
        """Read storage file"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to read storage: {e}")
            return {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "documents": {}
            }
    
    def _write_storage(self, data: Dict[str, Any]) -> None:
        """Write storage file"""
        try:
            data["last_updated"] = datetime.utcnow().isoformat()
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to write storage: {e}")
            raise
    
    async def save_classification(
        self,
        document_id: str,
        filename: str,
        classification: Dict[str, Any]
    ) -> bool:
        """
        Save document classification
        
        Args:
            document_id: Document UUID
            filename: Document filename
            classification: Classification data
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                data = self._read_storage()
                
                if document_id not in data["documents"]:
                    data["documents"][document_id] = {
                        "document_id": document_id,
                        "filename": filename,
                        "created_at": datetime.utcnow().isoformat()
                    }
                
                data["documents"][document_id]["classification"] = classification
                data["documents"][document_id]["classification_updated_at"] = datetime.utcnow().isoformat()
                
                self._write_storage(data)
                self.logger.info(f"Saved classification for {document_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save classification: {e}")
                return False
    
    async def save_metadata(
        self,
        document_id: str,
        filename: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Save extracted metadata
        
        Args:
            document_id: Document UUID
            filename: Document filename
            metadata: Extracted metadata
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                data = self._read_storage()
                
                if document_id not in data["documents"]:
                    data["documents"][document_id] = {
                        "document_id": document_id,
                        "filename": filename,
                        "created_at": datetime.utcnow().isoformat()
                    }
                
                data["documents"][document_id]["extracted_metadata"] = metadata
                data["documents"][document_id]["metadata_updated_at"] = datetime.utcnow().isoformat()
                
                self._write_storage(data)
                self.logger.info(f"Saved metadata for {document_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save metadata: {e}")
                return False
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete document analytics
        
        Args:
            document_id: Document UUID
            
        Returns:
            Document analytics or None
        """
        async with self._lock:
            try:
                data = self._read_storage()
                return data["documents"].get(document_id)
            except Exception as e:
                self.logger.error(f"Failed to get document {document_id}: {e}")
                return None
    
    async def get_classification(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document classification
        
        Args:
            document_id: Document UUID
            
        Returns:
            Classification data or None
        """
        doc = await self.get_document(document_id)
        return doc.get("classification") if doc else None
    
    async def get_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get extracted metadata
        
        Args:
            document_id: Document UUID
            
        Returns:
            Metadata or None
        """
        doc = await self.get_document(document_id)
        return doc.get("extracted_metadata") if doc else None
    
    async def get_all_documents(self) -> Dict[str, Any]:
        """
        Get all documents with analytics
        
        Returns:
            Dictionary of all documents
        """
        async with self._lock:
            try:
                data = self._read_storage()
                return data.get("documents", {})
            except Exception as e:
                self.logger.error(f"Failed to get all documents: {e}")
                return {}
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get portfolio summary statistics
        
        Returns:
            Portfolio summary
        """
        docs = await self.get_all_documents()
        
        summary = {
            "total_documents": len(docs),
            "by_category": {},
            "by_language": {},
            "confirmed": 0,
            "pending_confirmation": 0
        }
        
        for doc in docs.values():
            classification = doc.get("classification", {})
            
            # Count by category
            category = classification.get("category", "Unclassified")
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
            
            # Count by language
            language = classification.get("detected_language", "unknown")
            summary["by_language"][language] = summary["by_language"].get(language, 0) + 1
            
            # Confirmation status
            if classification.get("user_confirmed", False):
                summary["confirmed"] += 1
            else:
                summary["pending_confirmation"] += 1
        
        return summary
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document analytics
        
        Args:
            document_id: Document UUID
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                data = self._read_storage()
                
                if document_id in data["documents"]:
                    del data["documents"][document_id]
                    self._write_storage(data)
                    self.logger.info(f"Deleted analytics for {document_id}")
                    return True
                else:
                    self.logger.warning(f"Document not found: {document_id}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Failed to delete document: {e}")
                return False
    
    async def reset_all(self) -> bool:
        """
        Reset all analytics storage
        
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                self._init_storage()
                self.logger.info("Analytics storage reset")
                return True
            except Exception as e:
                self.logger.error(f"Failed to reset storage: {e}")
                return False
    
    async def update_classification(
        self,
        document_id: str,
        category: Optional[str] = None,
        sub_type: Optional[str] = None,
        user_confirmed: Optional[bool] = None
    ) -> bool:
        """
        Update classification fields
        
        Args:
            document_id: Document UUID
            category: New category
            sub_type: New sub-type
            user_confirmed: Confirmation status
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                data = self._read_storage()
                
                if document_id not in data["documents"]:
                    self.logger.warning(f"Document not found: {document_id}")
                    return False
                
                classification = data["documents"][document_id].get("classification", {})
                
                if category is not None:
                    classification["category"] = category
                if sub_type is not None:
                    classification["sub_type"] = sub_type
                if user_confirmed is not None:
                    classification["user_confirmed"] = user_confirmed
                
                classification["updated_at"] = datetime.utcnow().isoformat()
                
                data["documents"][document_id]["classification"] = classification
                self._write_storage(data)
                
                self.logger.info(f"Updated classification for {document_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to update classification: {e}")
                return False