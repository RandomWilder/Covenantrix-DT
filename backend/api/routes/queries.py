"""
Document Query Routes
Query documents using RAG
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import logging

from domain.documents.service import DocumentService
from core.dependencies import get_document_service, get_subscription_service
from api.schemas.documents import QueryRequest, QueryResponse

router = APIRouter(prefix="/queries", tags=["queries"])
logger = logging.getLogger(__name__)


@router.post("", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    service: DocumentService = Depends(get_document_service),
    subscription_service = Depends(get_subscription_service)
) -> QueryResponse:
    """
    Query documents using RAG
    
    Args:
        request: Query request with text and parameters
        service: Document service
        
    Returns:
        Query response with answer
    """
    # Get subscription for tier information
    subscription = await subscription_service.get_current_subscription_async()
    
    # Check subscription query limits
    try:
        allowed, reason = await subscription_service.check_query_allowed()
        if not allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Query limit exceeded: {reason}"
            )
    except Exception as e:
        logger.error(f"Subscription check failed: {e}")
        # Continue if subscription service is unavailable
    
    try:
        result = await service.query_documents(
            query_text=request.query,
            mode=request.mode,
            document_ids=request.document_ids
        )
        
        # Record query without session tracking
        logger.info(f"Recording semantic search query for tier {subscription.tier}")
        await subscription_service.usage_tracker.record_query(
            tier=subscription.tier,
            query_type="semantic_search",
            success=True,
            tokens_used=None  # Could be extracted from result if available
        )
        logger.info(f"Semantic search query recorded successfully for tier {subscription.tier}")
        
        # Track advanced search feature usage for specific query modes
        if request.mode and request.mode != "semantic":
            await subscription_service.usage_tracker.record_feature_usage("advanced_search")
        
        # Session tracking removed
        
        return QueryResponse(
            success=True,
            query=result.query,
            response=result.response,
            mode=result.mode,
            processing_time=result.processing_time_seconds,
            documents_searched=result.documents_searched
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))