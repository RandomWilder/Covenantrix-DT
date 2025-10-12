"""
API Key Resolution Layer
Handles resolution of API keys with strict mode enforcement (no automatic fallback)
"""
import logging
from typing import Optional, Dict, Any

from core.security import APIKeyManager

logger = logging.getLogger(__name__)


class APIKeyResolver:
    """
    Resolves API keys from user settings or system configuration
    Strict mode enforcement: respects user's mode choice without automatic fallback
    - Custom mode: returns user's custom key or None
    - Default mode: returns system .env key or None
    """
    
    def __init__(self):
        """Initialize API key resolver with encryption manager"""
        self.api_key_manager = APIKeyManager()
    
    def resolve_openai_key(
        self,
        user_settings: Optional[Dict[str, Any]],
        fallback_key: Optional[str]
    ) -> Optional[str]:
        """
        Resolve OpenAI API key from user settings or fallback
        
        Args:
            user_settings: User settings dictionary (may be None)
            fallback_key: Fallback API key from .env (may be None)
            
        Returns:
            Resolved API key or None if unavailable
        """
        return self._resolve_key(
            key_type="openai",
            user_settings=user_settings,
            fallback_key=fallback_key
        )
    
    def resolve_cohere_key(
        self,
        user_settings: Optional[Dict[str, Any]],
        fallback_key: Optional[str]
    ) -> Optional[str]:
        """
        Resolve Cohere API key from user settings or fallback
        
        Args:
            user_settings: User settings dictionary (may be None)
            fallback_key: Fallback API key from .env (may be None)
            
        Returns:
            Resolved API key or None if unavailable
        """
        return self._resolve_key(
            key_type="cohere",
            user_settings=user_settings,
            fallback_key=fallback_key
        )
    
    def resolve_google_key(
        self,
        user_settings: Optional[Dict[str, Any]],
        fallback_key: Optional[str]
    ) -> Optional[str]:
        """
        Resolve Google Cloud API key from user settings or fallback
        
        Args:
            user_settings: User settings dictionary (may be None)
            fallback_key: Fallback API key from .env (may be None)
            
        Returns:
            Resolved API key or None if unavailable
        """
        return self._resolve_key(
            key_type="google",
            user_settings=user_settings,
            fallback_key=fallback_key
        )
    
    def _resolve_key(
        self,
        key_type: str,
        user_settings: Optional[Dict[str, Any]],
        fallback_key: Optional[str]
    ) -> Optional[str]:
        """
        Internal key resolution logic - strict mode enforcement, no fallback
        
        Args:
            key_type: Type of key (openai, cohere, google)
            user_settings: User settings dictionary
            fallback_key: Fallback API key from .env
            
        Returns:
            Resolved API key or None (never falls back between modes)
        """
        try:
            # Check if user settings exist and mode is custom
            if user_settings and isinstance(user_settings, dict):
                api_keys = user_settings.get("api_keys", {})
                mode = api_keys.get("mode", "default")
                
                if mode == "custom":
                    # Custom mode: ONLY check custom key, return None if missing
                    user_key = api_keys.get(key_type)
                    
                    if user_key:
                        # Keys from user_settings are already decrypted by UserSettingsStorage
                        logger.info(f"Resolving {key_type} key: mode=custom, source=user")
                        logger.info(f"[DEBUG] User key length: {len(user_key)}, starts with: {user_key[:15] if len(user_key) >= 15 else user_key}")
                        return user_key
                    else:
                        # No custom key available - return None (no fallback to system)
                        logger.warning(f"Custom mode selected but no {key_type} key configured")
                        return None
            
            # Default mode: ONLY check system key, return None if missing
            if fallback_key:
                logger.info(f"Resolving {key_type} key: mode=default, source=system")
                return fallback_key
            else:
                logger.warning(f"Default mode but no system {key_type} key configured")
                return None
            
        except Exception as e:
            # On exception, log error and return None (no fallback)
            logger.error(f"Error during {key_type} key resolution: {e}")
            return None
    
    def get_key_source(
        self,
        user_settings: Optional[Dict[str, Any]]
    ) -> str:
        """
        Determine the key source being used
        
        Args:
            user_settings: User settings dictionary
            
        Returns:
            Key source: 'user' or 'system'
        """
        if user_settings and isinstance(user_settings, dict):
            api_keys = user_settings.get("api_keys", {})
            mode = api_keys.get("mode", "default")
            
            if mode == "custom":
                return "user"
        
        return "system"


# Global resolver instance
_resolver_instance: Optional[APIKeyResolver] = None


def get_api_key_resolver() -> APIKeyResolver:
    """
    Get or create API key resolver instance (singleton)
    
    Returns:
        API key resolver instance
    """
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = APIKeyResolver()
    return _resolver_instance

