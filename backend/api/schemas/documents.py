"""
Document API Schemas
Request and response models for document operations
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    success: bool
    document_id: str
    filename: str
    message: str


class DocumentResponse(BaseModel):
    """Single document response"""
    success: bool
    document: Dict[str, Any]


class DocumentListResponse(BaseModel):
    """Document list response"""
    success: bool
    documents: List[Dict[str, Any]]
    total_count: int


class QueryRequest(BaseModel):
    """Document query request"""
    query: str = Field(..., min_length=1, description="Query text")
    mode: str = Field("hybrid", description="Query mode: naive, local, global, hybrid, mix")
    document_ids: Optional[List[str]] = Field(None, description="Optional document ID filter")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the key terms of the lease agreement?",
                "mode": "hybrid",
                "document_ids": None
            }
        }


class QueryResponse(BaseModel):
    """Document query response"""
    success: bool
    query: str
    response: str
    mode: str
    processing_time: float
    documents_searched: int


class BatchUploadItem(BaseModel):
    """Individual file upload result"""
    filename: str
    document_id: Optional[str] = None
    success: bool
    error: Optional[str] = None
    file_size: Optional[int] = None


class BatchUploadResponse(BaseModel):
    """Batch upload response"""
    success: bool
    total_files: int
    successful_uploads: int
    failed_uploads: int
    results: List[BatchUploadItem]
    message: str


class GoogleDriveFileRequest(BaseModel):
    """Google Drive file selection request"""
    file_ids: List[str] = Field(..., description="List of Google Drive file IDs to download")
    folder_id: Optional[str] = Field(None, description="Optional folder ID to list files from")


class GoogleDriveFileInfo(BaseModel):
    """Google Drive file information"""
    file_id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    modified_time: Optional[str] = None
    web_view_link: Optional[str] = None


class GoogleDriveListResponse(BaseModel):
    """Google Drive file list response"""
    success: bool
    files: List[GoogleDriveFileInfo]
    next_page_token: Optional[str] = None


class EntityInfo(BaseModel):
    """Individual entity information"""
    name: str
    description: str


class EntitySummary(BaseModel):
    """Grouped entity summary"""
    people: List[EntityInfo]
    organizations: List[EntityInfo]
    locations: List[EntityInfo]
    financial: List[EntityInfo]
    dates_and_terms: List[EntityInfo]


class DocumentEntitiesResponse(BaseModel):
    """Document entities response"""
    document_id: str
    document_name: str
    entity_summary: EntitySummary


class DocumentProgressStage(str, Enum):
    """Document processing stage"""
    INITIALIZING = "initializing"
    READING = "reading"
    UNDERSTANDING = "understanding"
    BUILDING_CONNECTIONS = "building_connections"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentProgressEvent(BaseModel):
    """Single document progress event"""
    filename: str
    document_id: Optional[str] = None
    stage: DocumentProgressStage
    message: str
    progress_percent: int = Field(ge=0, le=100)
    timestamp: str
    error: Optional[str] = None


class BatchProgressEvent(BaseModel):
    """Batch upload progress event"""
    total_files: int
    current_file_index: int
    file_progress: DocumentProgressEvent
    overall_progress_percent: int = Field(ge=0, le=100)