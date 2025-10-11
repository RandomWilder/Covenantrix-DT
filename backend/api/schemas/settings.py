"""
Settings API Schemas
User settings and configuration management
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from enum import Enum


class ApiKeyMode(str, Enum):
    """API key mode options"""
    DEFAULT = "default"
    CUSTOM = "custom"


class SearchMode(str, Enum):
    """RAG search mode options"""
    NAIVE = "naive"
    LOCAL = "local"
    GLOBAL = "global"
    HYBRID = "hybrid"


class LanguageCode(str, Enum):
    """Supported language codes"""
    EN = "en"
    ES = "es"
    FR = "fr"
    HE = "he"
    DE = "de"


class Theme(str, Enum):
    """UI theme options"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class FontSize(str, Enum):
    """Font size options"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ApiKeySettings(BaseModel):
    """API key configuration"""
    mode: ApiKeyMode = Field(default=ApiKeyMode.DEFAULT, description="API key mode")
    openai: Optional[str] = Field(default=None, description="OpenAI API key (custom mode only)")
    cohere: Optional[str] = Field(default=None, description="Cohere API key (custom mode only)")
    google: Optional[str] = Field(default=None, description="Google Cloud API key (custom mode only)")

    @field_validator("openai", "cohere", "google")
    @classmethod
    def validate_custom_keys(cls, v, info):
        """Validate that custom keys are only provided in custom mode"""
        if v is not None and info.data.get("mode") == "default":
            raise ValueError("Custom API keys can only be set in custom mode")
        return v


class RAGSettings(BaseModel):
    """RAG engine configuration"""
    search_mode: SearchMode = Field(default=SearchMode.HYBRID, description="Search mode")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top results to retrieve")
    use_reranking: bool = Field(default=True, description="Enable Cohere reranking")
    enable_ocr: bool = Field(default=True, description="Enable Google Vision OCR")

    @field_validator("use_reranking")
    @classmethod
    def validate_reranking(cls, v, info):
        """Validate reranking requires Cohere key"""
        # Note: This validation should be done at the service level
        # where we can check if Cohere API key is actually available
        return v


class LanguageSettings(BaseModel):
    """Language preferences"""
    preferred: LanguageCode = Field(default=LanguageCode.EN, description="Preferred language")
    agent_language: LanguageCode | Literal["auto"] = Field(default="auto", description="Agent response language")
    ui_language: LanguageCode | Literal["auto"] = Field(default="auto", description="UI language")

    @field_validator("agent_language", "ui_language")
    @classmethod
    def validate_auto_language(cls, v):
        """Validate auto language setting"""
        if v == "auto":
            return v
        if v not in [lang.value for lang in LanguageCode]:
            raise ValueError(f"Invalid language code: {v}")
        return v


class UISettings(BaseModel):
    """UI appearance settings"""
    theme: Theme = Field(default=Theme.SYSTEM, description="UI theme")
    compact_mode: bool = Field(default=False, description="Enable compact mode")
    font_size: FontSize = Field(default=FontSize.MEDIUM, description="Font size")


class PrivacySettings(BaseModel):
    """Privacy and data settings"""
    enable_telemetry: bool = Field(default=False, description="Enable usage telemetry")
    enable_cloud_backup: bool = Field(default=False, description="Enable cloud backup (future)")
    retain_history: bool = Field(default=True, description="Retain chat history")


class UserSettings(BaseModel):
    """Complete user settings"""
    api_keys: ApiKeySettings = Field(default_factory=ApiKeySettings, description="API key settings")
    rag: RAGSettings = Field(default_factory=RAGSettings, description="RAG configuration")
    language: LanguageSettings = Field(default_factory=LanguageSettings, description="Language preferences")
    ui: UISettings = Field(default_factory=UISettings, description="UI settings")
    privacy: PrivacySettings = Field(default_factory=PrivacySettings, description="Privacy settings")
    version: str = Field(default="1.0", description="Settings schema version")
    last_updated: Optional[str] = Field(default=None, description="Last update timestamp")


class SettingsResponse(BaseModel):
    """Settings API response"""
    success: bool = True
    settings: UserSettings
    message: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    """Settings update request"""
    settings: UserSettings


class ApiKeyValidationRequest(BaseModel):
    """API key validation request"""
    openai: Optional[str] = None
    cohere: Optional[str] = None
    google: Optional[str] = None


class ApiKeyValidationResponse(BaseModel):
    """API key validation response"""
    success: bool
    openai_valid: Optional[bool] = None
    cohere_valid: Optional[bool] = None
    google_valid: Optional[bool] = None
    message: Optional[str] = None
    errors: Optional[dict] = None


class SettingsApplyRequest(BaseModel):
    """Apply settings to services"""
    settings: UserSettings
    restart_required: bool = False


class SettingsApplyResponse(BaseModel):
    """Settings application response"""
    success: bool
    message: str
    restart_required: bool = False
    applied_services: list[str] = []
