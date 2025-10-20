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
from core.dependencies import get_rag_engine, subscription_service_available, get_subscription_service

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
    # Get subscription status if available
    subscription_status = None
    if subscription_service_available():
        try:
            subscription_service = get_subscription_service()
            subscription = subscription_service.get_current_subscription()
            subscription_status = {
                "tier": subscription.tier,
                "features": subscription.get_features().model_dump(),
                "trial_started_at": subscription.trial_started_at,
                "trial_expires_at": subscription.trial_expires_at,
                "grace_period_started_at": subscription.grace_period_started_at,
                "grace_period_expires_at": subscription.grace_period_expires_at
            }
        except Exception:
            subscription_status = {"error": "Failed to load subscription status"}
    
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
            "openai_configured": bool(settings.openai.api_key),
            "subscription_available": subscription_service_available()
        },
        "storage": {
            "working_dir": str(settings.storage.working_dir),
            "max_file_size_mb": settings.storage.max_file_size_mb
        },
        "subscription": subscription_status
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