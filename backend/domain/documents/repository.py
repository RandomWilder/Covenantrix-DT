"""
Document Repository Interface
Abstract repository pattern - implementations in infrastructure layer
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.documents.models import Document, QueryResult, DocumentQuery


class IDocumentRepository(ABC):
    """
    Abstract repository for document persistence
    Implementations in infrastructure layer
    """
    
    @abstractmethod
    async def save(self, document: Document) -> None:
        """
        Save document to storage
        
        Args:
            document: Document to save
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """
        Get document by ID
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_all(
        self,
        include_deleted: bool = False
    ) -> List[Document]:
        """
        List all documents
        
        Args:
            include_deleted: Include soft-deleted documents
            
        Returns:
            List of documents
        """
        pass
    
    @abstractmethod
    async def delete(self, document_id: str, soft: bool = True) -> bool:
        """
        Delete document
        
        Args:
            document_id: Document to delete
            soft: Soft delete (mark as deleted) vs hard delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def insert_content(
        self,
        document: Document,
        content: str
    ) -> None:
        """
        Insert document content into RAG system
        
        Args:
            document: Document entity
            content: Extracted text content
        """
        pass
    
    @abstractmethod
    async def query(self, query: DocumentQuery) -> QueryResult:
        """
        Query documents using RAG
        
        Args:
            query: Query parameters
            
        Returns:
            Query result with response
        """
        pass
    
    @abstractmethod
    async def get_document_count(self) -> int:
        """Get total number of documents"""
        pass