"""
Covenantrix Backend Application
FastAPI application with clean architecture
"""
import sys
import os
from pathlib import Path

# Add backend directory to Python path for embedded Python distributions
# This ensures imports work regardless of how the application is executed
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Load .env file FIRST, before any other imports
# This is critical for pydantic-settings to pick up environment variables
# override=True ensures .env values take precedence over existing env vars
from dotenv import load_dotenv

# Explicitly specify .env file path in backend directory
env_file_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_file_path, override=True)

# Debug: Log what was loaded (only in dev mode)
if os.getenv("NODE_ENV") == "development":
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if client_id:
        print(f"[DEBUG] Loaded GOOGLE_CLIENT_ID: {client_id[:20]}...")
    else:
        print(f"[DEBUG] GOOGLE_CLIENT_ID not found in environment")
    print(f"[DEBUG] .env file path: {env_file_path}")
    print(f"[DEBUG] .env file exists: {env_file_path.exists()}")

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings, reload_settings

# Force reload settings after dotenv is loaded to ensure environment variables are picked up
# This is critical because Settings might be instantiated during imports above
reload_settings()

# Reset OAuth service singleton to pick up new config
from core.dependencies import reset_oauth_service
reset_oauth_service()

from core.logging_config import setup_logging
from core.dependencies import set_rag_engine, set_ocr_service, set_subscription_service
from api.middleware.error_handler import add_exception_handlers
from api.middleware.logging import LoggingMiddleware
from api.middleware.subscription_enforcement import add_subscription_enforcement_middleware

# Import routers
from api.routes import (
    health, documents, queries, analytics,
    agents, integrations, auth, storage, chat, services, google, notifications, subscription
)
from api.routes import settings as settings_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - strict mode, global state approach"""
    logger.info("Starting Covenantrix Backend...")
    
    # Initialize RAG engine with key resolution (ONCE at startup)
    settings = get_settings()
    
    try:
        from infrastructure.ai.rag_engine import RAGEngine, LIGHTRAG_AVAILABLE
        from infrastructure.storage.user_settings_storage import UserSettingsStorage
        from core.api_key_resolver import get_api_key_resolver
        
        # Load user settings
        user_settings_storage = UserSettingsStorage()
        user_settings = await user_settings_storage.load_settings()
        user_settings_dict = user_settings.model_dump()
        
        # Resolve OpenAI API key ONCE at startup (strict mode - no fallback)
        api_key_resolver = get_api_key_resolver()
        resolved_openai_key = api_key_resolver.resolve_openai_key(
            user_settings=user_settings_dict,
            fallback_key=settings.openai.api_key
        )
        
        # If resolved_key is None, set global rag_engine = None and continue
        if not resolved_openai_key:
            logger.warning("[WARNING] No valid OpenAI API key configured")
            logger.warning("[WARNING] Chat and upload features will be disabled until key is configured")
            set_rag_engine(None)  # Explicitly set to None for global state check
            logger.info("[OK] Backend started without OpenAI key - features disabled")
        
        # If resolved_key exists, initialize RAG engine (this is the ONLY key for entire session)
        elif resolved_openai_key and LIGHTRAG_AVAILABLE:
            key_source = api_key_resolver.get_key_source(user_settings_dict)
            logger.info(f"Using OpenAI key from: {key_source} (strict mode - no fallback)")
            
            try:
                rag_engine = RAGEngine(api_key=resolved_openai_key, user_settings=user_settings_dict)
                await rag_engine.initialize()
                
                # Apply user settings to RAG engine
                rag_engine.apply_settings(user_settings_dict)
                
                # Store globally for dependency injection (global state)
                set_rag_engine(rag_engine)
                
                logger.info("[OK] RAG engine initialized - this is the ONLY key active in system")
            except Exception as init_error:
                logger.error(f"[ERROR] RAG engine initialization failed: {init_error}")
                import traceback
                logger.error(traceback.format_exc())
                # Set to None if initialization fails
                set_rag_engine(None)
                logger.warning("[WARNING] RAG features disabled due to initialization error")
        
        elif resolved_openai_key and not LIGHTRAG_AVAILABLE:
            logger.warning("[WARNING] LightRAG not available - install with: pip install lightrag-hku")
            set_rag_engine(None)
        
        # Initialize OCR service with key resolution (ONCE at startup)
        from domain.integrations.ocr import OCRService
        
        resolved_google_key = api_key_resolver.resolve_google_key(
            user_settings=user_settings_dict,
            fallback_key=settings.google_vision.api_key
        )
        
        # Check if OCR should be enabled
        rag_settings = user_settings_dict.get("rag", {})
        ocr_enabled = rag_settings.get("enable_ocr", True)
        
        if resolved_google_key and ocr_enabled:
            try:
                ocr_service = OCRService(
                    api_key=resolved_google_key,
                    user_settings=user_settings_dict
                )
                set_ocr_service(ocr_service)
                key_source = api_key_resolver.get_key_source(user_settings_dict)
                logger.info(f"[OK] OCR service initialized with key from: {key_source} (strict mode)")
            except Exception as ocr_error:
                logger.error(f"[ERROR] OCR service initialization failed: {ocr_error}")
                set_ocr_service(None)
                logger.warning("[WARNING] OCR features disabled due to initialization error")
        else:
            set_ocr_service(None)
            if not resolved_google_key:
                logger.info("[OK] OCR service disabled - no Google API key available")
            else:
                logger.info("[OK] OCR service disabled - OCR setting disabled")
        
        # Cleanup expired notifications on startup
        from infrastructure.storage.notification_storage import NotificationStorage
        from domain.notifications.service import NotificationService
        try:
            notification_storage = NotificationStorage(settings.storage.working_dir)
            notification_service = NotificationService(storage=notification_storage)
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            deleted_count = await notification_service.cleanup_expired(cutoff_date)
            logger.info(f"[OK] Notification cleanup: removed {deleted_count} expired notifications")
        except Exception as cleanup_error:
            logger.error(f"[WARNING] Notification cleanup failed: {cleanup_error}")
        
        # Initialize subscription service
        from domain.subscription.service import SubscriptionService
        from infrastructure.storage.usage_tracker import UsageTracker
        from domain.subscription.license_validator import LicenseValidator
        
        try:
            usage_tracker = UsageTracker(settings.storage.working_dir)
            license_validator = LicenseValidator()
            subscription_service = SubscriptionService(
                settings_storage=user_settings_storage,
                usage_tracker=usage_tracker,
                license_validator=license_validator,
                notification_service=notification_service
            )
            
            # Check tier expiry and initialize trial if needed
            await subscription_service.check_tier_expiry()
            
            # Store globally for dependency injection
            set_subscription_service(subscription_service)
            
            logger.info("[OK] Subscription service initialized")
        except Exception as sub_error:
            logger.error(f"[ERROR] Subscription service initialization failed: {sub_error}")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("[WARNING] Subscription features disabled")
            
    except Exception as e:
        logger.error(f"[ERROR] Startup error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Continue startup even on error - set services to None
        set_rag_engine(None)
        set_ocr_service(None)
        logger.warning("[WARNING] Continuing startup with features disabled")
    
    logger.info("[OK] Covenantrix Backend ready")
    
    yield
    
    logger.info("Shutting down Covenantrix Backend...")


# Create FastAPI application
def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Covenantrix - Document Intelligence Platform",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    
    # Subscription enforcement middleware
    add_subscription_enforcement_middleware(app)
    
    # Exception handlers
    add_exception_handlers(app)
    
    # Include routers
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(queries.router)
    app.include_router(analytics.router)
    app.include_router(agents.router)
    app.include_router(integrations.router)
    app.include_router(auth.router)
    app.include_router(storage.router)
    app.include_router(chat.router)
    app.include_router(settings_router.router)
    app.include_router(services.router)
    app.include_router(google.router)
    app.include_router(notifications.router)
    app.include_router(subscription.router)
    
    return app


# Create app instance
app = create_application()


@app.get("/")
async def root():
    """Root endpoint"""
    settings = get_settings()
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level="info"
    )