"""
Agent Data Access Service
Implements IAgentDataAccess interface for agent document queries
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from domain.agents.base import IAgentDataAccess
from infrastructure.ai.rag_engine import RAGEngine
from domain.documents.service import DocumentService
from domain.analytics.service import AnalyticsService

logger = logging.getLogger(__name__)


class AgentDataAccessService(IAgentDataAccess):
    """
    Agent data access service implementation
    Provides agents with access to document data and analytics
    """
    
    def __init__(
        self,
        rag_engine: RAGEngine,
        document_service: DocumentService,
        analytics_service: AnalyticsService
    ):
        """
        Initialize agent data access service
        
        Args:
            rag_engine: RAG engine for document queries
            document_service: Document service for document operations
            analytics_service: Analytics service for document analytics
        """
        self.rag_engine = rag_engine
        self.document_service = document_service
        self.analytics_service = analytics_service
        self.logger = logging.getLogger(__name__)
    
    async def get_document_content(self, document_id: str) -> Optional[str]:
        """
        Get document content by ID
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document content or None if not found
        """
        try:
            # Get document from registry
            document = await self.document_service.get_document(document_id)
            if not document:
                self.logger.warning(f"Document not found: {document_id}")
                return None
            
            # Return document content
            return document.content
            
        except Exception as e:
            self.logger.error(f"Failed to get document content: {e}")
            return None
    
    async def get_document_analytics(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analytics for document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document analytics or None if not found
        """
        try:
            # Get analytics from analytics service
            analytics = await self.analytics_service.get_document_analytics(document_id)
            if not analytics:
                self.logger.warning(f"Analytics not found for document: {document_id}")
                return None
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get document analytics: {e}")
            return None
    
    async def query_documents(
        self,
        query: str,
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query documents using RAG
        
        Args:
            query: Natural language query
            document_ids: Optional list of document IDs to search
            
        Returns:
            Query results with response and metadata
        """
        try:
            # Use RAG engine to query documents
            if document_ids:
                # Query specific documents
                results = await self.rag_engine.query_documents(
                    query=query,
                    document_ids=document_ids
                )
            else:
                # Query all documents
                results = await self.rag_engine.query(
                    query=query
                )
            
            return {
                "response": results.get("response", ""),
                "sources": results.get("sources", []),
                "metadata": results.get("metadata", {}),
                "query": query,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to query documents: {e}")
            return {
                "response": "",
                "sources": [],
                "metadata": {},
                "query": query,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents available to agents
        
        Returns:
            List of document metadata
        """
        try:
            # Get documents from document service
            documents = await self.document_service.list_documents()
            
            # Convert to agent-friendly format
            document_list = []
            for doc in documents:
                document_list.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "content_type": doc.content_type,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "size_bytes": doc.size_bytes,
                    "status": doc.status.value if hasattr(doc.status, 'value') else str(doc.status)
                })
            
            return document_list
            
        except Exception as e:
            self.logger.error(f"Failed to list documents: {e}")
            return []
    
    async def get_document_entities(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get extracted entities from document
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of extracted entities
        """
        try:
            analytics = await self.get_document_analytics(document_id)
            if not analytics:
                return []
            
            # Extract entities from analytics
            entities = analytics.get("metadata", {}).get("entities", [])
            return entities
            
        except Exception as e:
            self.logger.error(f"Failed to get document entities: {e}")
            return []
    
    async def get_document_monetary_values(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get monetary values from document
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of monetary values
        """
        try:
            analytics = await self.get_document_analytics(document_id)
            if not analytics:
                return []
            
            # Extract monetary values from analytics
            monetary_values = analytics.get("metadata", {}).get("monetary_values", [])
            return monetary_values
            
        except Exception as e:
            self.logger.error(f"Failed to get document monetary values: {e}")
            return []
    
    async def search_documents_by_content(
        self,
        search_query: str,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents by content using semantic search
        
        Args:
            search_query: Search query
            document_ids: Optional list of document IDs to search
            
        Returns:
            List of matching documents with relevance scores
        """
        try:
            # Use RAG engine for semantic search
            if document_ids:
                results = await self.rag_engine.search_documents(
                    query=search_query,
                    document_ids=document_ids
                )
            else:
                results = await self.rag_engine.search(
                    query=search_query
                )
            
            # Format results for agents
            search_results = []
            for result in results.get("results", []):
                search_results.append({
                    "document_id": result.get("document_id"),
                    "content": result.get("content", ""),
                    "relevance_score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Failed to search documents: {e}")
            return []
    
    async def get_document_summary(self, document_id: str) -> Optional[str]:
        """
        Get document summary
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document summary or None
        """
        try:
            analytics = await self.get_document_analytics(document_id)
            if not analytics:
                return None
            
            # Extract summary from analytics
            summary = analytics.get("summary", "")
            return summary if summary else None
            
        except Exception as e:
            self.logger.error(f"Failed to get document summary: {e}")
            return None
