"""
User Settings Storage
Persistent storage for user settings with encryption support
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from api.schemas.settings import UserSettings
from core.config import get_settings
from core.security import APIKeyManager
from core.exceptions import StorageError

logger = logging.getLogger(__name__)


class UserSettingsStorage:
    """
    User settings storage service
    Handles loading, saving, and migration of user settings
    """
    
    def __init__(self):
        """Initialize settings storage"""
        self.settings = get_settings()
        self.storage_path = self.settings.storage.working_dir / "user_settings.json"
        self.api_key_manager = APIKeyManager()
        
        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def load_settings(self) -> UserSettings:
        """
        Load user settings from storage
        
        Returns:
            User settings object
        """
        try:
            if not self.storage_path.exists():
                logger.info("No settings file found, creating defaults")
                return await self._create_default_settings()
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle settings migration if needed
            data = await self._migrate_settings(data)
            
            # Decrypt sensitive data (API keys)
            data = await self._decrypt_sensitive_data(data)
            
            # Create settings object
            settings = UserSettings(**data)
            
            logger.info("Settings loaded successfully")
            return settings
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in settings file: {e}")
            return await self._create_default_settings()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            raise StorageError(
                f"Failed to load user settings: {str(e)}",
                details={"storage_path": str(self.storage_path)}
            )
    
    async def save_settings(self, settings: UserSettings) -> None:
        """
        Save user settings to storage
        
        Args:
            settings: User settings to save
        """
        try:
            # Update timestamp
            settings.last_updated = datetime.utcnow().isoformat()
            
            # Convert to dictionary
            settings_dict = settings.model_dump()
            
            # Encrypt sensitive data
            settings_dict = await self._encrypt_sensitive_data(settings_dict)
            
            # Save to file
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)
            
            logger.info("Settings saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            raise StorageError(
                f"Failed to save user settings: {str(e)}",
                details={"storage_path": str(self.storage_path)}
            )
    
    async def _create_default_settings(self) -> UserSettings:
        """Create default settings"""
        default_settings = UserSettings()
        await self.save_settings(default_settings)
        return default_settings
    
    async def _migrate_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate settings from older versions
        
        Args:
            data: Raw settings data
            
        Returns:
            Migrated settings data
        """
        try:
            version = data.get("version", "0.0")
            
            # Version 1.0 migration
            if version == "0.0":
                logger.info("Migrating settings from version 0.0 to 1.0")
                
                # Add default structure if missing
                if "api_keys" not in data:
                    data["api_keys"] = {
                        "mode": "default",
                        "openai": None,
                        "cohere": None,
                        "google": None
                    }
                
                if "rag" not in data:
                    data["rag"] = {
                        "search_mode": "hybrid",
                        "top_k": 5,
                        "use_reranking": True,
                        "enable_ocr": True
                    }
                
                if "language" not in data:
                    data["language"] = {
                        "preferred": "en",
                        "agent_language": "auto",
                        "ui_language": "auto"
                    }
                
                if "ui" not in data:
                    data["ui"] = {
                        "theme": "system",
                        "compact_mode": False,
                        "font_size": "medium"
                    }
                
                if "privacy" not in data:
                    data["privacy"] = {
                        "enable_telemetry": False,
                        "enable_cloud_backup": False,
                        "retain_history": True
                    }
                
                data["version"] = "1.0"
            
            return data
            
        except Exception as e:
            logger.error(f"Settings migration failed: {e}")
            # Return data as-is if migration fails
            return data
    
    async def _encrypt_sensitive_data(self, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive data in settings
        
        Args:
            settings_dict: Settings dictionary
            
        Returns:
            Settings with encrypted sensitive data
        """
        try:
            # Encrypt API keys if in custom mode
            if settings_dict.get("api_keys", {}).get("mode") == "custom":
                api_keys = settings_dict["api_keys"]
                
                if api_keys.get("openai"):
                    api_keys["openai"] = self.api_key_manager.encrypt_key(api_keys["openai"])
                
                if api_keys.get("cohere"):
                    api_keys["cohere"] = self.api_key_manager.encrypt_key(api_keys["cohere"])
                
                if api_keys.get("google"):
                    api_keys["google"] = self.api_key_manager.encrypt_key(api_keys["google"])
            
            return settings_dict
            
        except Exception as e:
            logger.error(f"Failed to encrypt sensitive data: {e}")
            # Return unencrypted data if encryption fails
            return settings_dict
    
    async def _decrypt_sensitive_data(self, settings_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive data in settings
        
        Args:
            settings_dict: Settings dictionary
            
        Returns:
            Settings with decrypted sensitive data
        """
        try:
            # Decrypt API keys if in custom mode
            if settings_dict.get("api_keys", {}).get("mode") == "custom":
                api_keys = settings_dict["api_keys"]
                
                # Decrypt OpenAI key
                if api_keys.get("openai"):
                    try:
                        api_keys["openai"] = self.api_key_manager.decrypt_key(api_keys["openai"])
                    except Exception as e:
                        logger.warning(f"Failed to decrypt OpenAI key, assuming plain text: {e}")
                        # Key is already plain text or invalid - leave as is
                
                # Decrypt Cohere key
                if api_keys.get("cohere"):
                    try:
                        api_keys["cohere"] = self.api_key_manager.decrypt_key(api_keys["cohere"])
                    except Exception as e:
                        logger.warning(f"Failed to decrypt Cohere key, assuming plain text: {e}")
                
                # Decrypt Google key
                if api_keys.get("google"):
                    try:
                        api_keys["google"] = self.api_key_manager.decrypt_key(api_keys["google"])
                    except Exception as e:
                        logger.warning(f"Failed to decrypt Google key, assuming plain text: {e}")
            
            return settings_dict
            
        except Exception as e:
            logger.error(f"Failed to decrypt sensitive data: {e}")
            # Return data as-is if decryption fails
            return settings_dict
    
    async def backup_settings(self, backup_path: Optional[Path] = None) -> Path:
        """
        Create backup of current settings
        
        Args:
            backup_path: Optional backup file path
            
        Returns:
            Backup file path
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.storage_path.parent / f"user_settings_backup_{timestamp}.json"
            
            # Copy current settings to backup
            if self.storage_path.exists():
                import shutil
                shutil.copy2(self.storage_path, backup_path)
                logger.info(f"Settings backup created: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create settings backup: {e}")
            raise StorageError(
                f"Failed to create settings backup: {str(e)}",
                details={"backup_path": str(backup_path)}
            )
    
    async def restore_settings(self, backup_path: Path) -> None:
        """
        Restore settings from backup
        
        Args:
            backup_path: Backup file path
        """
        try:
            if not backup_path.exists():
                raise StorageError(f"Backup file not found: {backup_path}")
            
            # Copy backup to current settings
            import shutil
            shutil.copy2(backup_path, self.storage_path)
            
            logger.info(f"Settings restored from backup: {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to restore settings: {e}")
            raise StorageError(
                f"Failed to restore settings: {str(e)}",
                details={"backup_path": str(backup_path)}
            )
    
    async def get_settings_info(self) -> Dict[str, Any]:
        """
        Get settings file information
        
        Returns:
            Settings file metadata
        """
        try:
            info = {
                "exists": self.storage_path.exists(),
                "path": str(self.storage_path),
                "size_bytes": 0,
                "last_modified": None,
                "version": None
            }
            
            if self.storage_path.exists():
                stat = self.storage_path.stat()
                info["size_bytes"] = stat.st_size
                info["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                # Get version from file
                try:
                    with open(self.storage_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        info["version"] = data.get("version", "unknown")
                except Exception:
                    info["version"] = "unknown"
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get settings info: {e}")
            return {"error": str(e)}
