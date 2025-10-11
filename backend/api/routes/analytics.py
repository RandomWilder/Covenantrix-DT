"""
Analytics Routes
Document classification and metadata extraction
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from domain.analytics.service import AnalyticsService
from infrastructure.ai.openai_client import OpenAIClient
from infrastructure.storage.analytics_storage import AnalyticsStorage
from core.dependencies import get_analytics_storage
from core.config import get_settings, Settings
from api.schemas.analytics import (
    ClassificationRequest, ClassificationResponse,
    ExtractionRequest, ExtractionResponse,
    AnalyticsRequest, AnalyticsResponse,
    PortfolioSummaryResponse
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


def get_analytics_service(
    settings: Settings = Depends(get_settings)
) -> AnalyticsService:
    """Get analytics service with LLM"""
    if not settings.openai.api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured"
        )
    
    client = OpenAIClient(settings.openai.api_key)
    
    async def llm_func(prompt: str, system_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        return await client.create_completion(messages, temperature=0.3)
    
    return AnalyticsService(llm_func)


@router.post("/classify", response_model=ClassificationResponse)
async def classify_document(
    request: ClassificationRequest,
    service: AnalyticsService = Depends(get_analytics_service),
    storage: AnalyticsStorage = Depends(get_analytics_storage)
) -> ClassificationResponse:
    """
    Classify a document
    
    Args:
        request: Classification request
        service: Analytics service
        storage: Analytics storage
        
    Returns:
        Classification result
    """
    try:
        classification = await service.classify_only(
            content=request.content,
            filename=request.filename
        )
        
        # Save to storage
        await storage.save_classification(
            document_id=request.document_id,
            filename=request.filename,
            classification=classification.to_dict()
        )
        
        return ClassificationResponse(
            success=True,
            classification=classification.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=ExtractionResponse)
async def extract_metadata(
    request: ExtractionRequest,
    service: AnalyticsService = Depends(get_analytics_service),
    storage: AnalyticsStorage = Depends(get_analytics_storage)
) -> ExtractionResponse:
    """
    Extract metadata from document
    
    Args:
        request: Extraction request
        service: Analytics service
        storage: Analytics storage
        
    Returns:
        Extracted metadata
    """
    try:
        metadata = await service.extract_only(
            content=request.content,
            filename=request.filename
        )
        
        # Save to storage
        await storage.save_metadata(
            document_id=request.document_id,
            filename=request.filename,
            metadata=metadata.to_dict()
        )
        
        return ExtractionResponse(
            success=True,
            metadata=metadata.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalyticsResponse)
async def analyze_document(
    request: AnalyticsRequest,
    service: AnalyticsService = Depends(get_analytics_service),
    storage: AnalyticsStorage = Depends(get_analytics_storage)
) -> AnalyticsResponse:
    """
    Complete document analysis (classification + extraction)
    
    Args:
        request: Analysis request
        service: Analytics service
        storage: Analytics storage
        
    Returns:
        Complete analytics
    """
    try:
        analytics = await service.analyze_document(
            document_id=request.document_id,
            content=request.content,
            filename=request.filename
        )
        
        # Save both to storage
        await storage.save_classification(
            document_id=request.document_id,
            filename=request.filename,
            classification=analytics.classification.to_dict()
        )
        
        await storage.save_metadata(
            document_id=request.document_id,
            filename=request.filename,
            metadata=analytics.metadata.to_dict()
        )
        
        return AnalyticsResponse(
            success=True,
            analytics=analytics.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    storage: AnalyticsStorage = Depends(get_analytics_storage)
) -> PortfolioSummaryResponse:
    """
    Get portfolio summary
    
    Returns:
        Portfolio statistics
    """
    try:
        summary = await storage.get_portfolio_summary()
        
        return PortfolioSummaryResponse(
            success=True,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Portfolio summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{document_id}")
async def get_document_analytics(
    document_id: str,
    storage: AnalyticsStorage = Depends(get_analytics_storage)
):
    """
    Get analytics for specific document
    
    Args:
        document_id: Document identifier
        storage: Analytics storage
        
    Returns:
        Document analytics
    """
    try:
        analytics = await storage.get_document(document_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Analytics not found")
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))