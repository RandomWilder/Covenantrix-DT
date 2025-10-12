"""
Service Status Routes
Provides status endpoints for checking service availability
"""
import logging
from fastapi import APIRouter, Depends
from core.config import Settings, get_settings
from core.dependencies import (
    rag_engine_available,
    reranker_available,
    ocr_service_available as ocr_available
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/status")
async def get_services_status(
    settings: Settings = Depends(get_settings)
):
    """
    Check availability of all services based on global state
    
    Returns detailed status of:
    - OpenAI API (RAG engine)
    - Cohere API (reranking)
    - Google Vision API (OCR)
    - Feature availability (chat, upload, reranking, ocr)
    
    This endpoint does not perform validation, it only checks
    the current global state of initialized services.
    """
    openai_available = rag_engine_available()
    cohere_available = reranker_available()
    google_available = ocr_available()
    
    return {
        "openai_available": openai_available,
        "cohere_available": cohere_available,
        "google_available": google_available,
        "features": {
            "chat": openai_available,
            "upload": openai_available,
            "reranking": cohere_available,
            "ocr": google_available
        }
    }

