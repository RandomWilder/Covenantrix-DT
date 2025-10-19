"""
Document Domain Models
Pure Python models representing document business entities
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentType(str, Enum):
    """Document type classification"""
    CONTRACT = "contract"
    LEASE_AGREEMENT = "lease_agreement"
    EMPLOYMENT = "employment"
    LEGAL = "legal"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    GENERAL = "general"


@dataclass
class DocumentMetadata:
    """Document metadata"""
    filename: str
    file_size_bytes: int
    mime_type: str
    uploaded_at: datetime
    language: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    
    @property
    def file_size_mb(self) -> float:
        """File size in megabytes"""
        return round(self.file_size_bytes / (1024 * 1024), 2)


@dataclass
class ProcessingResult:
    """Result of document processing"""
    success: bool
    char_count: int
    chunk_count: int
    processing_time_seconds: float
    error_message: Optional[str] = None
    ocr_applied: bool = False


@dataclass
class Document:
    """
    Core document entity
    Represents a document in the system with its metadata and processing status
    """
    id: str
    metadata: DocumentMetadata
    status: DocumentStatus
    content_hash: str
    created_at: datetime
    updated_at: datetime
    processing_result: Optional[ProcessingResult] = None
    
    # Content (not always loaded)
    content: Optional[str] = None
    
    # Current processing stage and message (for documents being processed)
    processing_stage: Optional[str] = None
    processing_message: Optional[str] = None
    
    @classmethod
    def create_new(
        cls,
        filename: str,
        file_size_bytes: int,
        mime_type: str,
        content_hash: str,
        document_id: Optional[str] = None
    ) -> "Document":
        """Create a new document instance"""
        now = datetime.utcnow()
        
        return cls(
            id=document_id or str(uuid.uuid4()),
            metadata=DocumentMetadata(
                filename=filename,
                file_size_bytes=file_size_bytes,
                mime_type=mime_type,
                uploaded_at=now
            ),
            status=DocumentStatus.PENDING,
            content_hash=content_hash,
            created_at=now,
            updated_at=now
        )
    
    def mark_processing(self) -> None:
        """Mark document as processing"""
        self.status = DocumentStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_processed(
        self,
        char_count: int,
        chunk_count: int,
        processing_time: float,
        ocr_applied: bool = False
    ) -> None:
        """Mark document as successfully processed"""
        self.status = DocumentStatus.PROCESSED
        self.updated_at = datetime.utcnow()
        self.processing_result = ProcessingResult(
            success=True,
            char_count=char_count,
            chunk_count=chunk_count,
            processing_time_seconds=processing_time,
            ocr_applied=ocr_applied
        )
    
    def mark_failed(self, error_message: str) -> None:
        """Mark document as failed"""
        self.status = DocumentStatus.FAILED
        self.updated_at = datetime.utcnow()
        self.processing_result = ProcessingResult(
            success=False,
            char_count=0,
            chunk_count=0,
            processing_time_seconds=0,
            error_message=error_message
        )
    
    def mark_deleted(self) -> None:
        """Mark document as deleted (soft delete)"""
        self.status = DocumentStatus.DELETED
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "document_id": self.id,
            "filename": self.metadata.filename,
            "file_size_mb": self.metadata.file_size_mb,
            "status": self.status.value,
            "uploaded_at": self.metadata.uploaded_at.isoformat(),
            "char_count": self.processing_result.char_count if self.processing_result else 0,
            "chunk_count": self.processing_result.chunk_count if self.processing_result else 0,
            "processed_at": self.updated_at.isoformat() if self.status == DocumentStatus.PROCESSED else None,
            "ocr_applied": self.processing_result.ocr_applied if self.processing_result else False
        }
        
        # Include processing stage and message if document is currently processing
        if hasattr(self, 'processing_stage') and hasattr(self, 'processing_message'):
            result["processing"] = {
                "stage": self.processing_stage,
                "message": self.processing_message
            }
        
        return result


@dataclass
class DocumentQuery:
    """Document query parameters"""
    query_text: str
    mode: str = "hybrid"  # naive, local, global, hybrid, mix
    document_ids: Optional[List[str]] = None
    only_context: bool = False
    
    def validate(self) -> None:
        """Validate query parameters"""
        valid_modes = ["naive", "local", "global", "hybrid", "mix"]
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid mode: {self.mode}. Must be one of {valid_modes}")
        
        if not self.query_text.strip():
            raise ValueError("Query text cannot be empty")


@dataclass
class QueryResult:
    """Result of a document query"""
    query: str
    response: str
    mode: str
    documents_searched: int
    processing_time_seconds: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "response": self.response,
            "mode": self.mode,
            "documents_searched": self.documents_searched,
            "processing_time": self.processing_time_seconds,
            "timestamp": self.timestamp.isoformat()
        }