"""
FastAPI Dependency Injection
Provides dependencies for route handlers
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status

from core.config import get_settings, Settings
from core.exceptions import ConfigurationError
from domain.documents.service import DocumentService
from domain.analytics.service import AnalyticsService
from domain.agents.orchestrator import AgentOrchestrator
from domain.chat.service import ChatService
from infrastructure.ai.rag_engine import RAGEngine
from infrastructure.ai.agent_data_access import AgentDataAccessService
from infrastructure.external.external_data_service import ExternalDataService
from infrastructure.storage.lightrag_storage import LightRAGStorage
from infrastructure.storage.analytics_storage import AnalyticsStorage
from infrastructure.storage.document_registry import DocumentRegistry
from infrastructure.storage.chat_storage import ChatStorage
from infrastructure.storage.user_settings_storage import UserSettingsStorage
from infrastructure.storage.notification_storage import NotificationStorage
from domain.integrations.ocr import OCRService
from domain.integrations.google_oauth import GoogleOAuthService
from infrastructure.external.google_api import GoogleAPIService
from domain.notifications.service import NotificationService

logger = logging.getLogger(__name__)

# Global RAG engine instance (set during startup)
_rag_engine_instance: Optional[RAGEngine] = None

# Global storage instances (manual singletons)
_lightrag_storage: Optional[LightRAGStorage] = None
_analytics_storage: Optional[AnalyticsStorage] = None
_document_registry: Optional[DocumentRegistry] = None
_chat_storage: Optional[ChatStorage] = None
_agent_registry: Optional['AgentRegistry'] = None
_agent_data_access: Optional[AgentDataAccessService] = None
_external_data_service: Optional[ExternalDataService] = None
_ocr_service: Optional[OCRService] = None
_user_settings_storage: Optional[UserSettingsStorage] = None
_oauth_service: Optional[GoogleOAuthService] = None
_notification_storage: Optional[NotificationStorage] = None
_subscription_service: Optional['SubscriptionService'] = None


def set_rag_engine(rag_engine: Optional[RAGEngine]) -> None:
    """
    Set global RAG engine instance (called from main.py during startup)
    
    Args:
        rag_engine: Initialized RAG engine instance or None if unavailable
    """
    global _rag_engine_instance
    _rag_engine_instance = rag_engine


def rag_engine_available() -> bool:
    """
    Check if RAG engine is available (non-blocking check)
    
    Returns:
        bool: True if RAG engine is initialized and available
    """
    global _rag_engine_instance
    return _rag_engine_instance is not None


def reranker_available() -> bool:
    """
    Check if Cohere reranker is available (non-blocking check)
    
    Returns:
        bool: True if Cohere is configured in RAG engine
    """
    global _rag_engine_instance
    if _rag_engine_instance is None:
        return False
    
    try:
        # Check if RAG engine has reranker configured
        return hasattr(_rag_engine_instance, 'reranker') and _rag_engine_instance.reranker is not None
    except Exception as e:
        logger.error(f"Error checking reranker availability: {e}")
        return False


def ocr_service_available() -> bool:
    """
    Check if OCR service is available (non-blocking check)
    
    Returns:
        bool: True if OCR service is initialized and available
    """
    global _ocr_service
    return _ocr_service is not None


def set_ocr_service(ocr_service: Optional[OCRService]) -> None:
    """
    Set global OCR service instance
    
    Args:
        ocr_service: Initialized OCR service instance or None if unavailable
    """
    global _ocr_service
    _ocr_service = ocr_service


# Settings dependency
def get_config() -> Settings:
    """Get application settings"""
    return get_settings()


# Storage dependencies (manual singleton pattern)
def get_lightrag_storage(
    settings: Settings = Depends(get_config)
) -> LightRAGStorage:
    """Get LightRAG storage instance (singleton)"""
    global _lightrag_storage
    if _lightrag_storage is None:
        _lightrag_storage = LightRAGStorage(
            working_dir=settings.storage.working_dir
        )
    return _lightrag_storage


def get_analytics_storage(
    settings: Settings = Depends(get_config)
) -> AnalyticsStorage:
    """Get analytics storage instance (singleton)"""
    global _analytics_storage
    if _analytics_storage is None:
        _analytics_storage = AnalyticsStorage()
    return _analytics_storage


def get_document_registry(
    settings: Settings = Depends(get_config)
) -> DocumentRegistry:
    """Get document registry instance (singleton)"""
    global _document_registry
    if _document_registry is None:
        _document_registry = DocumentRegistry()
    return _document_registry


def get_chat_storage(
    settings: Settings = Depends(get_config)
) -> ChatStorage:
    """Get chat storage instance (singleton)"""
    global _chat_storage
    if _chat_storage is None:
        _chat_storage = ChatStorage(settings.storage.working_dir)
    return _chat_storage


def get_user_settings_storage(
    settings: Settings = Depends(get_config)
) -> UserSettingsStorage:
    """Get user settings storage instance (singleton)"""
    global _user_settings_storage
    if _user_settings_storage is None:
        _user_settings_storage = UserSettingsStorage()
    return _user_settings_storage


def get_notification_storage(
    settings: Settings = Depends(get_config)
) -> NotificationStorage:
    """Get notification storage instance (singleton)"""
    global _notification_storage
    if _notification_storage is None:
        _notification_storage = NotificationStorage(settings.storage.working_dir)
    return _notification_storage


def get_notification_service(
    storage: NotificationStorage = Depends(get_notification_storage)
) -> NotificationService:
    """Get notification service instance"""
    return NotificationService(storage=storage)


def get_oauth_service(
    settings: Settings = Depends(get_config),
    storage: UserSettingsStorage = Depends(get_user_settings_storage)
) -> GoogleOAuthService:
    """Get Google OAuth service instance (singleton)"""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = GoogleOAuthService(config=settings, storage=storage)
    return _oauth_service


def reset_oauth_service() -> None:
    """Reset OAuth service singleton (called after config reload)"""
    global _oauth_service
    _oauth_service = None
    logger.debug("OAuth service singleton reset")


def get_google_api_service(
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
) -> GoogleAPIService:
    """Get Google API service instance"""
    # Create new instance with oauth_service for token refresh
    return GoogleAPIService(oauth_service=oauth_service)


# AI service dependencies
def get_rag_engine() -> RAGEngine:
    """
    Get RAG engine instance (singleton from global)
    
    Returns:
        Initialized RAG engine instance
        
    Raises:
        HTTPException: If RAG engine not initialized
    """
    global _rag_engine_instance
    
    if _rag_engine_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not initialized"
        )
    
    return _rag_engine_instance


def get_ocr_service(
    settings: Settings = Depends(get_config)
) -> Optional[OCRService]:
    """
    Get OCR service instance (singleton)
    Returns global OCR service set during startup
    """
    global _ocr_service
    return _ocr_service


def update_ocr_service_with_user_settings(user_settings: dict) -> None:
    """
    Update OCR service with user settings using strict mode resolution
    Uses api_key_resolver for consistent key resolution (no fallback between modes)
    
    Args:
        user_settings: User settings dictionary
    """
    global _ocr_service
    
    try:
        from core.api_key_resolver import get_api_key_resolver
        
        # Resolve Google API key using strict mode (no cross-mode fallback)
        api_key_resolver = get_api_key_resolver()
        settings = get_settings()
        
        resolved_google_key = api_key_resolver.resolve_google_key(
            user_settings=user_settings,
            fallback_key=settings.google_vision.api_key
        )
        
        # Check if OCR should be enabled
        rag_settings = user_settings.get("rag", {})
        ocr_enabled = rag_settings.get("enable_ocr", True)
        
        if resolved_google_key and ocr_enabled:
            # Create or update OCR service
            _ocr_service = OCRService(
                api_key=resolved_google_key,
                user_settings=user_settings
            )
            key_source = api_key_resolver.get_key_source(user_settings)
            logger.info(f"OCR service updated with key from: {key_source} (strict mode)")
        else:
            # Disable OCR service
            _ocr_service = None
            if not resolved_google_key:
                logger.info("OCR service disabled - no Google API key available")
            else:
                logger.info("OCR service disabled - OCR setting disabled in user settings")
            
    except Exception as e:
        logger.error(f"Failed to update OCR service with user settings: {e}")
        _ocr_service = None


# Domain service dependencies
def get_document_service(
    rag_engine: RAGEngine = Depends(get_rag_engine),
    document_registry: DocumentRegistry = Depends(get_document_registry),
    ocr_service: Optional[OCRService] = Depends(get_ocr_service),
    settings: Settings = Depends(get_config)
) -> DocumentService:
    """Get document service instance"""
    return DocumentService(
        rag_engine=rag_engine,
        document_registry=document_registry,
        max_file_size_mb=settings.storage.max_file_size_mb,
        ocr_service=ocr_service
    )


def get_analytics_service(
    rag_engine: RAGEngine = Depends(get_rag_engine),
    analytics_storage: AnalyticsStorage = Depends(get_analytics_storage)
) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(
        rag_engine=rag_engine,
        storage=analytics_storage
    )


def get_agent_registry() -> 'AgentRegistry':
    """Get agent registry instance (singleton)"""
    global _agent_registry
    if _agent_registry is None:
        from domain.agents.orchestrator import AgentRegistry
        _agent_registry = AgentRegistry()
        # Register available agent types
        from domain.agents.market_research import MarketResearchAgent
        _agent_registry.register_agent_type("market_research", MarketResearchAgent)
    return _agent_registry


def get_agent_data_access_service(
    rag_engine: RAGEngine = Depends(get_rag_engine),
    document_service: DocumentService = Depends(get_document_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> AgentDataAccessService:
    """Get agent data access service instance (singleton)"""
    global _agent_data_access
    if _agent_data_access is None:
        _agent_data_access = AgentDataAccessService(
            rag_engine=rag_engine,
            document_service=document_service,
            analytics_service=analytics_service
        )
    return _agent_data_access


def get_external_data_service() -> ExternalDataService:
    """Get external data service instance (singleton)"""
    global _external_data_service
    if _external_data_service is None:
        _external_data_service = ExternalDataService()
    return _external_data_service




def get_agent_orchestrator(
    registry: 'AgentRegistry' = Depends(get_agent_registry),
    data_access_service: AgentDataAccessService = Depends(get_agent_data_access_service),
    external_data_service: ExternalDataService = Depends(get_external_data_service)
) -> AgentOrchestrator:
    """Get agent orchestrator instance with data services"""
    return AgentOrchestrator(
        registry=registry,
        data_access_service=data_access_service,
        external_data_service=external_data_service
    )


def get_chat_service(
    chat_storage: ChatStorage = Depends(get_chat_storage)
) -> ChatService:
    """Get chat service instance"""
    # Try to get optional dependencies, but don't fail if they're not available
    rag_engine = None
    agent_orchestrator = None
    document_service = None
    
    try:
        rag_engine = get_rag_engine()
    except:
        pass  # RAG engine not available
    
    try:
        agent_orchestrator = get_agent_orchestrator()
    except:
        pass  # Agent orchestrator not available
    
    try:
        document_service = get_document_service()
    except:
        pass  # Document service not available
    
    return ChatService(
        chat_storage=chat_storage,
        rag_engine=rag_engine,
        agent_orchestrator=agent_orchestrator,
        document_service=document_service
    )


# API key validation dependency
async def verify_api_key_configured(
    settings: Settings = Depends(get_config)
) -> None:
    """Verify OpenAI API key is configured"""
    if not settings.openai.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured. Please set API key first."
        )


# Optional API key dependency (doesn't fail if missing)
async def get_optional_api_key(
    settings: Settings = Depends(get_config)
) -> Optional[str]:
    """Get API key if configured, None otherwise"""
    return settings.openai.api_key


# Subscription service management
def set_subscription_service(service: 'SubscriptionService') -> None:
    """
    Set global subscription service instance (called from main.py during startup)
    
    Args:
        service: Initialized subscription service instance
    """
    global _subscription_service
    _subscription_service = service
    logger.debug("Subscription service registered globally")


def get_subscription_service() -> 'SubscriptionService':
    """
    Get subscription service instance (dependency injection)
    
    Returns:
        Subscription service instance
        
    Raises:
        HTTPException: If subscription service not initialized
    """
    global _subscription_service
    
    if _subscription_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Subscription service not initialized"
        )
    
    return _subscription_service


def subscription_service_available() -> bool:
    """
    Check if subscription service is available (non-blocking check)
    
    Returns:
        bool: True if subscription service is initialized and available
    """
    global _subscription_service
    return _subscription_service is not None


def get_subscription_aware_document_service(
    rag_engine: RAGEngine = Depends(get_rag_engine),
    document_registry: DocumentRegistry = Depends(get_document_registry),
    ocr_service: Optional[OCRService] = Depends(get_ocr_service),
    subscription_service: 'SubscriptionService' = Depends(get_subscription_service),
    settings: Settings = Depends(get_config)
) -> DocumentService:
    """
    Get subscription-aware document service instance
    
    This service enforces subscription limits before processing documents
    """
    # Get current subscription limits
    subscription = subscription_service.get_current_subscription()
    
    # Use subscription-based file size limit if available
    max_file_size_mb = settings.storage.max_file_size_mb
    if subscription.features.max_doc_size_mb > 0:
        max_file_size_mb = min(max_file_size_mb, subscription.features.max_doc_size_mb)
    
    return DocumentService(
        rag_engine=rag_engine,
        document_registry=document_registry,
        max_file_size_mb=max_file_size_mb,
        ocr_service=ocr_service
    )