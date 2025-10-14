"""
Settings API Schemas
User settings and configuration management
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, List
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

    @model_validator(mode='after')
    def validate_custom_keys(self) -> 'ApiKeySettings':
        """Validate that custom keys are only provided in custom mode"""
        if self.mode == ApiKeyMode.DEFAULT:
            # In default mode, custom keys should not be provided
            if self.openai is not None or self.cohere is not None or self.google is not None:
                raise ValueError(
                    "Custom API keys cannot be provided in default mode. "
                    "Please switch to custom mode to use custom API keys."
                )
        elif self.mode == ApiKeyMode.CUSTOM:
            # In custom mode, at least one key should be provided
            if self.openai is None and self.cohere is None and self.google is None:
                raise ValueError(
                    "At least one API key must be provided in custom mode. "
                    "Please provide OpenAI, Cohere, or Google Cloud API key."
                )
        return self


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


class FeatureFlags(BaseModel):
    """Tier-based feature limits"""
    max_documents: int = Field(default=3, description="Max documents (-1 = unlimited)")
    max_doc_size_mb: int = Field(default=10, description="Max per-document size")
    max_total_storage_mb: int = Field(default=30, description="Max total storage")
    max_queries_monthly: int = Field(default=-1, description="Monthly query limit (-1 = unlimited)")
    max_queries_daily: int = Field(default=-1, description="Daily query limit (-1 = unlimited)")
    use_default_keys: bool = Field(default=False, description="Allow default API keys")


class SubscriptionSettings(BaseModel):
    """User subscription state - system-managed"""
    tier: str = Field(default="trial", description="trial|free|paid|paid_limited")
    license_key: Optional[str] = Field(default=None, description="JWT license token")
    trial_started_at: Optional[str] = Field(default=None, description="ISO datetime of first launch")
    trial_expires_at: Optional[str] = Field(default=None, description="ISO datetime when trial ends")
    grace_period_started_at: Optional[str] = Field(default=None, description="When grace period began")
    grace_period_expires_at: Optional[str] = Field(default=None, description="When grace period ends")
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    last_tier_change: Optional[str] = Field(default=None, description="ISO datetime of last tier change")


class ProfileSettings(BaseModel):
    """User profile information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class GoogleAccountSettings(BaseModel):
    """Google OAuth account (stored format)"""
    account_id: str
    email: str
    display_name: Optional[str] = None
    provider: str = "google"
    status: str  # connected/expired/revoked
    connected_at: str  # ISO datetime
    last_used: str  # ISO datetime
    # Credentials stored encrypted
    access_token: str
    refresh_token: Optional[str] = None
    token_expiry: str  # ISO datetime
    scopes: List[str]


class UserSettings(BaseModel):
    """Complete user settings"""
    api_keys: ApiKeySettings = Field(default_factory=ApiKeySettings, description="API key settings")
    rag: RAGSettings = Field(default_factory=RAGSettings, description="RAG configuration")
    language: LanguageSettings = Field(default_factory=LanguageSettings, description="Language preferences")
    ui: UISettings = Field(default_factory=UISettings, description="UI settings")
    privacy: PrivacySettings = Field(default_factory=PrivacySettings, description="Privacy settings")
    profile: ProfileSettings = Field(default_factory=ProfileSettings, description="User profile information")
    google_accounts: List[GoogleAccountSettings] = Field(default_factory=list, description="Connected Google accounts")
    subscription: SubscriptionSettings = Field(default_factory=SubscriptionSettings, description="Subscription tier and limits")
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
