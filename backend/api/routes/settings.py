"""
Settings API Routes
User settings and configuration management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from api.schemas.settings import (
    SettingsResponse, SettingsUpdateRequest, SettingsApplyRequest,
    ApiKeyValidationRequest, ApiKeyValidationResponse, SettingsApplyResponse
)
from infrastructure.storage.user_settings_storage import UserSettingsStorage
from core.security import APIKeyManager
from core.config import get_settings, Settings
from core.api_key_resolver import get_api_key_resolver

router = APIRouter(prefix="/api/settings", tags=["settings"])
logger = logging.getLogger(__name__)

# Initialize services
settings_storage = UserSettingsStorage()
api_key_manager = APIKeyManager()


# ==================== Shared Validation Functions ====================

async def _validate_openai_key(api_key: str) -> tuple[bool, Optional[str]]:
    """
    Validate OpenAI API key
    
    Args:
        api_key: OpenAI API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check format first
        if not (api_key.startswith("sk-") and len(api_key) > 20):
            return False, "Invalid OpenAI API key format. Please check your key and try again."
        
        # Perform actual API validation
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=api_key)
        try:
            # Make a minimal API call to verify the key
            await client.embeddings.create(
                model="text-embedding-3-small",
                input="test"
            )
            logger.info("API key validation: type=openai, result=valid")
            return True, None
        except Exception as api_error:
            error_msg = str(api_error)
            if "invalid" in error_msg.lower() or "authentication" in error_msg.lower():
                return False, "Invalid OpenAI API key. Please check your key and try again."
            return False, f"OpenAI API key validation failed: {error_msg[:100]}"
    except Exception as e:
        return False, f"OpenAI validation error: {str(e)}"


async def _validate_cohere_key(api_key: str) -> tuple[bool, Optional[str]]:
    """
    Validate Cohere API key using official check-api-key endpoint
    
    Args:
        api_key: Cohere API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check format first
        if len(api_key) < 20:
            return False, "Invalid Cohere API key format. Please check your key and try again."
        
        # Perform actual API validation using official Cohere endpoint
        try:
            import httpx
            
            url = "https://api.cohere.ai/v1/check-api-key"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    is_valid = result.get("valid", False)
                    
                    if is_valid:
                        logger.info("API key validation: type=cohere, result=valid")
                        return True, None
                    else:
                        return False, "Invalid Cohere API key. Please check your key and try again."
                else:
                    logger.warning(f"Cohere validation failed with status {response.status_code}")
                    return False, "Invalid Cohere API key. Please check your key and try again."
                    
        except ImportError:
            # httpx not installed - skip actual validation
            logger.warning("httpx not available - format validation only")
            return True, None
        except Exception as api_error:
            logger.error(f"Cohere API validation error: {api_error}")
            return False, f"Invalid Cohere API key. Please check your key and try again."
    except Exception as e:
        return False, f"Cohere validation error: {str(e)}"


async def _validate_google_key(api_key: str) -> tuple[bool, Optional[str]]:
    """
    Validate Google Cloud API key (format validation only)
    
    Args:
        api_key: Google Cloud API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # For Google Cloud, we'll do format validation only
        if len(api_key) > 20:
            logger.info("API key validation: type=google, result=valid (format)")
            return True, None
        else:
            return False, "Invalid Google API key format. Please check your key and try again."
    except Exception as e:
        return False, f"Google validation error: {str(e)}"


# ==================== Routes ====================

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
    Update user settings with strict validation for custom mode
    
    Args:
        request: Settings update request
        
    Returns:
        Updated settings
    """
    try:
        # Check if custom mode - validate all provided keys
        if request.settings.api_keys and request.settings.api_keys.mode == "custom":
            validation_errors = {}
            
            # Validate OpenAI key if provided
            if request.settings.api_keys.openai:
                openai_key = request.settings.api_keys.openai
                logger.info(f"[DEBUG] Validating custom OpenAI key: length={len(openai_key)}, starts with={openai_key[:15] if len(openai_key) >= 15 else openai_key}")
                
                is_valid, error_msg = await _validate_openai_key(openai_key)
                if not is_valid:
                    validation_errors["openai"] = error_msg
            
            # Validate Cohere key if provided
            if request.settings.api_keys.cohere:
                is_valid, error_msg = await _validate_cohere_key(request.settings.api_keys.cohere)
                if not is_valid:
                    validation_errors["cohere"] = error_msg
            
            # Validate Google key if provided
            if request.settings.api_keys.google:
                is_valid, error_msg = await _validate_google_key(request.settings.api_keys.google)
                if not is_valid:
                    validation_errors["google"] = error_msg
            
            # If any validation failed, reject save with HTTP 400
            if validation_errors:
                logger.warning(f"Settings save blocked - validation failed: {validation_errors}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Invalid API keys provided",
                        "errors": validation_errors
                    }
                )
        
        # NEW: Validate API key mode against subscription tier
        if request.settings.api_keys and request.settings.api_keys.mode == "default":
            from core.dependencies import get_subscription_service
            subscription_service = get_subscription_service()
            current_subscription = await subscription_service.get_current_subscription_async()
            
            if not current_subscription.features.use_default_keys:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "default_keys_not_allowed",
                        "message": f"Your {current_subscription.tier} tier requires custom API keys",
                        "current_tier": current_subscription.tier,
                        "allowed_mode": "custom"
                    }
                )
        
        # Default mode: NEVER block saves (system keys managed externally)
        # Update timestamp
        request.settings.last_updated = datetime.utcnow().isoformat()
        
        # Save settings
        await settings_storage.save_settings(request.settings)
        
        logger.info(f"Settings updated successfully (mode: {request.settings.api_keys.mode if request.settings.api_keys else 'default'})")
        
        return SettingsResponse(
            success=True,
            settings=request.settings,
            message="Settings updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        )


@router.post("/api-keys/validate", response_model=ApiKeyValidationResponse)
async def validate_api_keys(request: ApiKeyValidationRequest):
    """
    Validate API keys before saving (onBlur validation)
    Performs actual API calls to verify key validity
    
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
        
        # Validate OpenAI key using shared function
        if request.openai:
            is_valid, error_msg = await _validate_openai_key(request.openai)
            validation_results["openai_valid"] = is_valid
            if not is_valid:
                errors["openai"] = error_msg
        
        # Validate Cohere key using shared function
        if request.cohere:
            is_valid, error_msg = await _validate_cohere_key(request.cohere)
            validation_results["cohere_valid"] = is_valid
            if not is_valid:
                errors["cohere"] = error_msg
        
        # Validate Google key using shared function
        if request.google:
            is_valid, error_msg = await _validate_google_key(request.google)
            validation_results["google_valid"] = is_valid
            if not is_valid:
                errors["google"] = error_msg
        
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


@router.get("/key-status")
async def get_key_status():
    """
    Check if a valid OpenAI API key is currently active
    Checks global RAG engine state without re-resolving keys
    
    Returns:
        Key availability status
    """
    try:
        from core.dependencies import get_rag_engine
        
        # Load current user settings
        user_settings = await settings_storage.load_settings()
        mode = user_settings.api_keys.mode if user_settings.api_keys else "default"
        
        # Check global RAG engine state (DO NOT re-resolve key)
        rag_engine = get_rag_engine()
        has_valid_key = rag_engine is not None
        
        if has_valid_key:
            message = f"Valid OpenAI API key configured in {mode} mode"
        else:
            message = "No valid OpenAI API key configured"
        
        return {
            "has_valid_key": has_valid_key,
            "mode": mode,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Failed to check key status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check key status: {str(e)}"
        )


async def reload_rag_with_settings() -> bool:
    """
    Reload RAG engine with new settings and API keys
    Loads fresh settings from storage to get properly encrypted/decrypted keys
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from infrastructure.ai.rag_engine import RAGEngine, LIGHTRAG_AVAILABLE
        from core.dependencies import set_rag_engine
        
        if not LIGHTRAG_AVAILABLE:
            logger.error("LightRAG not available for reload")
            return False
        
        # Load fresh settings from storage (properly encrypted/decrypted)
        user_settings = await settings_storage.load_settings()
        settings_dict = user_settings.model_dump()
        
        # Get system settings
        system_settings = get_settings()
        
        # Resolve OpenAI API key
        api_key_resolver = get_api_key_resolver()
        resolved_key = api_key_resolver.resolve_openai_key(
            user_settings=settings_dict,
            fallback_key=system_settings.openai.api_key
        )
        
        if not resolved_key:
            logger.error("No OpenAI API key available for RAG reload")
            return False
        
        key_source = api_key_resolver.get_key_source(settings_dict)
        logger.info(f"Reloading RAG engine with key from: {key_source}")
        logger.info(f"[DEBUG] Resolved key for reload - length: {len(resolved_key)}, starts with: {resolved_key[:15] if len(resolved_key) >= 15 else resolved_key}")
        
        # Create new RAG engine instance
        rag_engine = RAGEngine(api_key=resolved_key, user_settings=settings_dict)
        await rag_engine.initialize()
        
        # Apply user settings
        rag_engine.apply_settings(settings_dict)
        
        # Update global instance
        set_rag_engine(rag_engine)
        
        logger.info("Services reloaded with new key configuration")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reload RAG engine: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


@router.post("/apply", response_model=SettingsApplyResponse)
async def apply_settings(request: SettingsApplyRequest):
    """
    Apply settings to RAG engine and other services
    Attempts to reload services with new API keys if needed
    
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
        
        # Check if API key mode or custom keys changed
        api_keys = settings_dict.get("api_keys", {})
        mode = api_keys.get("mode", "default")
        
        # Always reload RAG engine when applying settings
        # This ensures strict mode is respected - custom mode uses user keys, default mode uses system keys
        logger.info(f"Applying settings in {mode} mode, reloading RAG engine with strict key resolution")
        reload_success = await reload_rag_with_settings()
        
        if reload_success:
            applied_services.append("rag_engine_reloaded")
            logger.info(f"RAG engine successfully reloaded with {mode} mode key")
            restart_required = False  # Successfully reloaded, no restart needed
        else:
            logger.warning("RAG engine reload failed, restart may be required")
            restart_required = True
        
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


@router.post("/test-mode")
async def set_test_mode(
    mode: str,
    settings: Settings = Depends(get_settings)
):
    """
    Set test mode for API key resolution (development only)
    Allows toggling between system and user keys for testing
    
    Args:
        mode: "system" or "user"
        settings: Application settings
        
    Returns:
        Test mode status
    """
    # Only allow in non-production environments
    if settings.environment.lower() == "production":
        raise HTTPException(
            status_code=403,
            detail="Test mode endpoint not available in production"
        )
    
    try:
        if mode not in ["system", "user"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid mode. Must be 'system' or 'user'"
            )
        
        # Load user settings
        user_settings = await settings_storage.load_settings()
        user_settings_dict = user_settings.model_dump()
        
        # Determine key source
        api_key_resolver = get_api_key_resolver()
        key_source = api_key_resolver.get_key_source(user_settings_dict)
        
        # Get active key
        resolved_key = api_key_resolver.resolve_openai_key(
            user_settings=user_settings_dict,
            fallback_key=settings.openai.api_key
        )
        
        logger.info(f"Test mode query: requested={mode}, active={key_source}")
        
        return {
            "success": True,
            "active_mode": key_source,
            "key_source": key_source,
            "has_key": resolved_key is not None,
            "message": f"Currently using {key_source} key"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test mode failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Test mode failed: {str(e)}"
        )
