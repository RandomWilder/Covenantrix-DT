"""
Application Configuration
Centralized configuration management using pydantic-settings
All config loaded from environment variables with validation

API Key Resolution (Strict Mode):
  This file provides system fallback keys ONLY from .env file.
  These are used when api_keys.mode = "default" in user settings.
  
  Actual key resolution happens in api_key_resolver.py with strict mode:
  - mode = "custom" → Use ONLY user keys from user_settings.json (encrypted)
  - mode = "default" → Use ONLY system keys from .env (this file)
  - NO FALLBACK between modes (strict mode enforcement)
  
  Resolution order:
  1. Load .env keys (this file) as system fallback
  2. Load user_settings.json (user keys + mode preference)
  3. Resolve via api_key_resolver based on mode (no cross-mode fallback)
  4. Initialize services with resolved key or None
  
  Missing keys result in service = None (graceful degradation).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional
from pathlib import Path
import os
import platform


def get_user_data_directory() -> Path:
    """
    Get the user data directory for Covenantrix
    Cross-platform implementation for user directory detection
    
    Returns:
        Path: User data directory path
    """
    system = platform.system().lower()
    
    if system == "windows":
        # Windows: %USERPROFILE%\.covenantrix\
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        return Path(user_profile) / ".covenantrix"
    else:
        # macOS and Linux: ~/.covenantrix/
        return Path.home() / ".covenantrix"


class Settings(BaseSettings):
    """Main application settings - all fields at top level for proper .env loading"""
    
    # Pydantic Settings v2 configuration
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # App metadata
    app_name: str = "Covenantrix"
    version: str = "1.1.83"
    environment: str = Field("development", env="ENVIRONMENT")
    
    # Database configuration
    postgres_host: str = Field("localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_db: str = Field("covenantrix_db", env="POSTGRES_DB")
    postgres_user: str = Field("covenantrix_user", env="POSTGRES_USER")
    postgres_password: Optional[str] = Field(None, env="POSTGRES_PASSWORD")
    
    # OpenAI configuration
    # Note: API key resolution happens via api_key_resolver.py
    # This is the system fallback key from .env
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", env="OPENAI_MODEL")
    openai_embedding_model: str = Field("text-embedding-3-large", env="OPENAI_EMBEDDING_MODEL")
    openai_max_tokens: int = Field(4000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(0.7, env="OPENAI_TEMPERATURE")
    
    # Cohere configuration (for reranking)
    # Note: API key resolution happens via api_key_resolver.py
    # This is the system fallback key from .env
    cohere_api_key: Optional[str] = Field(None, env="COHERE_API_KEY")
    
    # Storage configuration
    storage_working_dir: Path = Field(default_factory=lambda: get_user_data_directory() / "rag_storage", env="STORAGE_WORKING_DIR")
    storage_analytics_file: str = Field("analytics_metadata.json", env="ANALYTICS_FILE")
    storage_max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    
    # Server configuration
    server_host: str = Field("127.0.0.1", env="SERVER_HOST")
    server_port: int = Field(8000, env="SERVER_PORT")
    server_debug: bool = Field(False, env="DEBUG")
    server_reload: bool = Field(False, env="RELOAD")
    server_workers: int = Field(1, env="WORKERS")
    
    # Google Vision configuration
    # Note: API key resolution happens via api_key_resolver.py
    # This is the system fallback key from .env
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    google_vision_enabled: bool = Field(False, env="GOOGLE_VISION_ENABLED")
    google_vision_project_id: Optional[str] = Field(None, env="GOOGLE_VISION_PROJECT_ID")
    
    # OCR Settings
    ocr_enabled: bool = Field(True, env="OCR_ENABLED")
    ocr_min_confidence: float = Field(0.3, env="OCR_MIN_CONFIDENCE")
    ocr_min_char_count: int = Field(5, env="OCR_MIN_CHAR_COUNT")
    ocr_preferred_language: Optional[str] = Field(None, env="OCR_PREFERRED_LANGUAGE")  # None = auto-detect
    
    # Google OAuth configuration
    google_oauth_client_id: Optional[str] = Field(default=None, validation_alias="GOOGLE_CLIENT_ID")
    google_oauth_client_secret: Optional[str] = Field(default=None, validation_alias="GOOGLE_CLIENT_SECRET")
    google_oauth_redirect_uri: str = Field(default="http://localhost:8000/api/google/accounts/callback", validation_alias="GOOGLE_REDIRECT_URI")
    
    # External API configuration
    numbeo_api_key: Optional[str] = Field(None, env="NUMBEO_API_KEY")
    osm_nominatim_base_url: str = Field("https://nominatim.openstreetmap.org", env="OSM_NOMINATIM_BASE_URL")
    eurostat_api_base_url: str = Field("https://ec.europa.eu/eurostat/api", env="EUROSTAT_API_BASE_URL")
    google_maps_api_key: Optional[str] = Field(None, env="GOOGLE_MAPS_API_KEY")
    
    @field_validator("storage_working_dir", mode="before")
    @classmethod
    def ensure_path(cls, v):
        if isinstance(v, str):
            path = Path(v)
        else:
            path = v
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    # Property accessors for nested config compatibility
    @property
    def database(self):
        """Database configuration accessor"""
        class DatabaseConfig:
            def __init__(self, parent):
                self.postgres_host = parent.postgres_host
                self.postgres_port = parent.postgres_port
                self.postgres_db = parent.postgres_db
                self.postgres_user = parent.postgres_user
                self.postgres_password = parent.postgres_password
                
            @property
            def connection_string(self) -> str:
                if not self.postgres_password:
                    return ""
                return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        
        return DatabaseConfig(self)
    
    @property
    def openai(self):
        """OpenAI configuration accessor"""
        class OpenAIConfig:
            def __init__(self, parent):
                self.api_key = parent.openai_api_key
                self.model = parent.openai_model
                self.embedding_model = parent.openai_embedding_model
                self.max_tokens = parent.openai_max_tokens
                self.temperature = parent.openai_temperature
        
        return OpenAIConfig(self)
    
    @property
    def cohere(self):
        """Cohere configuration accessor"""
        class CohereConfig:
            def __init__(self, parent):
                self.api_key = parent.cohere_api_key
        
        return CohereConfig(self)
    
    @property
    def storage(self):
        """Storage configuration accessor"""
        class StorageConfig:
            def __init__(self, parent):
                self.working_dir = parent.storage_working_dir
                self.analytics_file = parent.storage_analytics_file
                self.max_file_size_mb = parent.storage_max_file_size_mb
        
        return StorageConfig(self)
    
    @property
    def server(self):
        """Server configuration accessor"""
        class ServerConfig:
            def __init__(self, parent):
                self.host = parent.server_host
                self.port = parent.server_port
                self.debug = parent.server_debug
                self.reload = parent.server_reload
                self.workers = parent.server_workers
        
        return ServerConfig(self)
    
    @property
    def google_vision(self):
        """Google Vision configuration accessor"""
        class GoogleVisionConfig:
            def __init__(self, parent):
                self.api_key = parent.google_api_key
                self.enabled = parent.google_vision_enabled
                self.project_id = parent.google_vision_project_id
        
        return GoogleVisionConfig(self)
    
    @property
    def ocr(self):
        """OCR configuration accessor"""
        class OCRConfig:
            def __init__(self, parent):
                self.enabled = parent.ocr_enabled
                self.min_confidence = parent.ocr_min_confidence
                self.min_char_count = parent.ocr_min_char_count
                self.preferred_language = parent.ocr_preferred_language
        
        return OCRConfig(self)
    
    @property
    def google_oauth(self):
        """Google OAuth configuration accessor"""
        class GoogleOAuthConfig:
            def __init__(self, parent):
                self.client_id = parent.google_oauth_client_id
                self.client_secret = parent.google_oauth_client_secret
                self.redirect_uri = parent.google_oauth_redirect_uri
        
        return GoogleOAuthConfig(self)
    
    @property
    def external_apis(self):
        """External APIs configuration accessor"""
        class ExternalAPIsConfig:
            def __init__(self, parent):
                self.numbeo_api_key = parent.numbeo_api_key
                self.osm_nominatim_base_url = parent.osm_nominatim_base_url
                self.eurostat_api_base_url = parent.eurostat_api_base_url
                self.google_maps_api_key = parent.google_maps_api_key
        
        return ExternalAPIsConfig(self)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings