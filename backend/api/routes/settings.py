"""
Settings API Routes
User settings and configuration management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
from datetime import datetime

from api.schemas.settings import (
    SettingsResponse, SettingsUpdateRequest, SettingsApplyRequest,
    ApiKeyValidationRequest, ApiKeyValidationResponse, SettingsApplyResponse
)
from infrastructure.storage.user_settings_storage import UserSettingsStorage
from core.security import APIKeyManager
from core.config import get_settings

router = APIRouter(prefix="/settings", tags=["settings"])
logger = logging.getLogger(__name__)

# Initialize services
settings_storage = UserSettingsStorage()
api_key_manager = APIKeyManager()


@router.get("", response_model=SettingsResponse)
async def get_settings_endpoint():
    """
    Retrieve current user settings
    
    Returns:
        Current user settings
    """
    try:
        settings = await settings_storage.load_settings()
        
        return SettingsResponse(
            success=True,
            settings=settings,
            message="Settings retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve settings: {str(e)}"
        )


@router.post("", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest):
    """
    Update user settings
    
    Args:
        request: Settings update request
        
    Returns:
        Updated settings
    """
    try:
        # Update timestamp
        request.settings.last_updated = datetime.utcnow().isoformat()
        
        # Save settings
        await settings_storage.save_settings(request.settings)
        
        logger.info("Settings updated successfully")
        
        return SettingsResponse(
            success=True,
            settings=request.settings,
            message="Settings updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        )


@router.post("/api-keys/validate", response_model=ApiKeyValidationResponse)
async def validate_api_keys(request: ApiKeyValidationRequest):
    """
    Validate API keys before saving
    
    Args:
        request: API key validation request
        
    Returns:
        Validation results
    """
    try:
        validation_results = {
            "openai_valid": None,
            "cohere_valid": None,
            "google_valid": None
        }
        errors = {}
        
        # Validate OpenAI key
        if request.openai:
            try:
                # TODO: Implement actual OpenAI API validation
                # For now, just check format
                if request.openai.startswith("sk-") and len(request.openai) > 20:
                    validation_results["openai_valid"] = True
                else:
                    validation_results["openai_valid"] = False
                    errors["openai"] = "Invalid OpenAI API key format"
            except Exception as e:
                validation_results["openai_valid"] = False
                errors["openai"] = f"OpenAI validation failed: {str(e)}"
        
        # Validate Cohere key
        if request.cohere:
            try:
                # TODO: Implement actual Cohere API validation
                # For now, just check format
                if len(request.cohere) > 20:
                    validation_results["cohere_valid"] = True
                else:
                    validation_results["cohere_valid"] = False
                    errors["cohere"] = "Invalid Cohere API key format"
            except Exception as e:
                validation_results["cohere_valid"] = False
                errors["cohere"] = f"Cohere validation failed: {str(e)}"
        
        # Validate Google Cloud key
        if request.google:
            try:
                # TODO: Implement actual Google Cloud API validation
                # For now, just check format
                if len(request.google) > 20:
                    validation_results["google_valid"] = True
                else:
                    validation_results["google_valid"] = False
                    errors["google"] = "Invalid Google Cloud API key format"
            except Exception as e:
                validation_results["google_valid"] = False
                errors["google"] = f"Google Cloud validation failed: {str(e)}"
        
        # Determine overall success
        all_valid = all(
            v is None or v for v in validation_results.values()
        )
        
        return ApiKeyValidationResponse(
            success=all_valid,
            **validation_results,
            message="API key validation completed" if all_valid else "Some API keys are invalid",
            errors=errors if errors else None
        )
        
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"API key validation failed: {str(e)}"
        )


@router.post("/apply", response_model=SettingsApplyResponse)
async def apply_settings(request: SettingsApplyRequest):
    """
    Apply settings to RAG engine and other services
    
    Args:
        request: Settings application request
        
    Returns:
        Application results
    """
    try:
        applied_services = []
        restart_required = False
        
        # Convert settings to dictionary for processing
        settings_dict = request.settings.model_dump()
        
        # Apply RAG settings
        try:
            from core.dependencies import get_rag_engine
            from infrastructure.ai.rag_engine import RAGEngine
            
            # Get current RAG engine instance
            rag_engine = get_rag_engine()
            if isinstance(rag_engine, RAGEngine):
                rag_engine.apply_settings(settings_dict)
                applied_services.append("rag_engine")
                logger.info("RAG engine settings applied")
            else:
                logger.warning("RAG engine not available for settings application")
        except Exception as e:
            logger.error(f"Failed to apply RAG settings: {e}")
        
        # Apply OCR settings
        try:
            from core.dependencies import update_ocr_service_with_user_settings
            update_ocr_service_with_user_settings(settings_dict)
            applied_services.append("ocr_service")
            logger.info("OCR service settings applied successfully")
        except Exception as e:
            logger.error(f"Failed to apply OCR settings: {e}")
        
        # Apply language settings
        try:
            # Language settings are applied through RAG engine and OCR service
            preferred_lang = settings_dict.get("language", {}).get("preferred", "en")
            agent_lang = settings_dict.get("language", {}).get("agent_language", "auto")
            ui_lang = settings_dict.get("language", {}).get("ui_language", "auto")
            
            logger.info(f"Language settings applied: preferred={preferred_lang}, agent={agent_lang}, ui={ui_lang}")
            applied_services.append("language_service")
        except Exception as e:
            logger.error(f"Failed to apply language settings: {e}")
        
        # Check if restart is required
        if request.settings.api_keys.mode == "custom":
            # API key changes might require restart
            restart_required = True
        
        return SettingsApplyResponse(
            success=True,
            message="Settings applied successfully",
            restart_required=restart_required,
            applied_services=applied_services
        )
        
    except Exception as e:
        logger.error(f"Failed to apply settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply settings: {str(e)}"
        )


@router.get("/defaults", response_model=SettingsResponse)
async def get_default_settings():
    """
    Get default settings template
    
    Returns:
        Default settings
    """
    try:
        from api.schemas.settings import UserSettings
        
        default_settings = UserSettings()
        
        return SettingsResponse(
            success=True,
            settings=default_settings,
            message="Default settings retrieved"
        )
        
    except Exception as e:
        logger.error(f"Failed to get default settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get default settings: {str(e)}"
        )


@router.post("/reset")
async def reset_settings():
    """
    Reset settings to defaults
    
    Returns:
        Reset confirmation
    """
    try:
        from api.schemas.settings import UserSettings
        
        default_settings = UserSettings()
        await settings_storage.save_settings(default_settings)
        
        logger.info("Settings reset to defaults")
        
        return {
            "success": True,
            "message": "Settings reset to defaults"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset settings: {str(e)}"
        )
