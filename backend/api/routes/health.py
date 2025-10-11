"""
Health Check Routes
System health and status endpoints
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import platform
import sys

from core.config import get_settings, Settings
from infrastructure.ai.rag_engine import RAGEngine, LIGHTRAG_AVAILABLE
from core.dependencies import get_rag_engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version,
        "platform": platform.platform()
    }


@router.get("/detailed")
async def detailed_health(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Detailed health check with service status
    
    Returns:
        Detailed health information
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app": {
            "name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment
        },
        "services": {
            "lightrag": LIGHTRAG_AVAILABLE,
            "openai_configured": bool(settings.openai.api_key)
        },
        "storage": {
            "working_dir": str(settings.storage.working_dir),
            "max_file_size_mb": settings.storage.max_file_size_mb
        }
    }
    
    return health_data


@router.get("/rag")
async def rag_health(
    rag_engine: RAGEngine = Depends(get_rag_engine)
) -> Dict[str, Any]:
    """
    RAG engine health check
    
    Returns:
        RAG engine status
    """
    return rag_engine.get_status()