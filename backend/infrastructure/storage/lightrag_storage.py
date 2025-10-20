"""
LightRAG Storage
Wrapper for LightRAG storage operations
"""
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.config import get_settings
from infrastructure.ai.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class LightRAGStorage:
    """
    Storage interface for LightRAG
    Provides high-level operations over RAG engine
    """
    
    def __init__(self, rag_engine: Optional[RAGEngine] = None):
        """
        Initialize LightRAG storage
        
        Args:
            rag_engine: RAG engine instance (optional)
        """
        self.rag_engine = rag_engine
        settings = get_settings()
        self.working_dir = Path(settings.storage.working_dir)
        self.logger = logging.getLogger(__name__)
    
    async def store_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store document in RAG
        
        Args:
            document_id: Document UUID
            text: Document text
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        if not self.rag_engine:
            self.logger.warning("RAG engine not available")
            return False
        
        try:
            lightrag_doc_id = await self.rag_engine.insert(text, metadata)
            if lightrag_doc_id:
                self.logger.info(f"Stored document in RAG: {document_id} -> {lightrag_doc_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to store document: {e}")
            return False
    
    async def query_documents(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query documents in RAG
        
        Args:
            query: Query string
            mode: Query mode
            top_k: Number of results
            
        Returns:
            Query results
        """
        if not self.rag_engine:
            self.logger.warning("RAG engine not available")
            return {
                "success": False,
                "error": "RAG engine not initialized"
            }
        
        return await self.rag_engine.query(query, mode, top_k, document_ids=document_ids)
    
    async def get_document_chunks(
        self,
        document_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get chunks for a document
        
        Args:
            document_id: Document UUID
            
        Returns:
            List of chunks
        """
        # Read from LightRAG storage files
        try:
            doc_status_file = self.working_dir / "kv_store_doc_status.json"
            if not doc_status_file.exists():
                self.logger.warning("Document status file not found")
                return []
            
            import json
            with open(doc_status_file, 'r', encoding='utf-8') as f:
                doc_status = json.load(f)
            
            # Get chunks for this document
            chunks = []
            for chunk_id, chunk_data in doc_status.items():
                if document_id in chunk_data.get("file_paths", []):
                    chunks.append({
                        "chunk_id": chunk_id,
                        "token_count": chunk_data.get("token_count", 0)
                    })
            
            self.logger.debug(f"Found {len(chunks)} chunks for {document_id}")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to get chunks: {e}")
            return []
    
    def get_storage_path(self) -> Path:
        """Get RAG storage path"""
        return self.working_dir
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get storage status
        
        Returns:
            Status dictionary
        """
        return {
            "working_dir": str(self.working_dir),
            "initialized": self.rag_engine is not None and self.rag_engine.is_initialized,
            "rag_engine_available": self.rag_engine is not None
        }
    
    def get_entity_cache(self, document_id: str) -> Dict[str, Any]:
        """
        Get entity cache data for a document
        
        Args:
            document_id: Document UUID
            
        Returns:
            Entity cache data
        """
        cache_file = self.working_dir / "kv_store_llm_response_cache.json"
        
        if not cache_file.exists():
            self.logger.warning("Entity cache file not found")
            return {}
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Filter for document-specific entities
            document_entities = {}
            for key, value in cache_data.items():
                if isinstance(value, dict) and value.get("type") == "entity_extraction":
                    # For now, include all entities - in practice, you'd filter by document
                    entity_name = value.get("entity_name", "")
                    if entity_name:
                        document_entities[entity_name] = value
            
            return document_entities
            
        except Exception as e:
            self.logger.error(f"Failed to read entity cache: {e}")
            return {}
    
    def get_entity_relationships(self, document_id: str) -> Dict[str, Any]:
        """
        Get entity relationships for a document
        
        Args:
            document_id: Document UUID
            
        Returns:
            Entity relationships data
        """
        relations_file = self.working_dir / "kv_store_full_relations.json"
        
        if not relations_file.exists():
            self.logger.warning("Relations file not found")
            return {}
        
        try:
            with open(relations_file, 'r', encoding='utf-8') as f:
                relations_data = json.load(f)
            
            return relations_data
            
        except Exception as e:
            self.logger.error(f"Failed to read relations file: {e}")
            return {}
    
    def count_entity_relationships(self, entity_name: str, relationships: Dict[str, Any]) -> int:
        """
        Count relationships for an entity
        
        Args:
            entity_name: Name of the entity
            relationships: Relationships data
            
        Returns:
            Number of relationships
        """
        count = 0
        
        for relation_key, relation_data in relationships.items():
            if isinstance(relation_data, dict):
                # Check if entity appears in the relationship
                if (entity_name in relation_data.get("source", "") or 
                    entity_name in relation_data.get("target", "")):
                    count += 1
        
        return count