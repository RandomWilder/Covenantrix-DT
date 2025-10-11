"""
Analytics API Schemas
Request and response models for document analytics
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class ClassificationRequest(BaseModel):
    """Document classification request"""
    document_id: str
    filename: str
    content: str = Field(..., min_length=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "contract.pdf",
                "content": "This is a lease agreement between..."
            }
        }


class ClassificationResponse(BaseModel):
    """Document classification response"""
    success: bool
    classification: Dict[str, Any]


class ExtractionRequest(BaseModel):
    """Metadata extraction request"""
    document_id: str
    filename: str
    content: str = Field(..., min_length=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "contract.pdf",
                "content": "Monthly rent is $2,500. Contract starts on 2024-01-01..."
            }
        }


class ExtractionResponse(BaseModel):
    """Metadata extraction response"""
    success: bool
    metadata: Dict[str, Any]


class AnalyticsRequest(BaseModel):
    """Complete analytics request (classification + extraction)"""
    document_id: str
    filename: str
    content: str = Field(..., min_length=50)


class AnalyticsResponse(BaseModel):
    """Complete analytics response"""
    success: bool
    analytics: Dict[str, Any]


class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary response"""
    success: bool
    summary: Dict[str, Any]


class UpdateClassificationRequest(BaseModel):
    """Update classification request"""
    category: Optional[str] = None
    sub_type: Optional[str] = None
    user_confirmed: Optional[bool] = None