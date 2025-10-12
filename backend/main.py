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

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.logging_config import setup_logging
from core.dependencies import set_rag_engine, set_ocr_service
from api.middleware.error_handler import add_exception_handlers
from api.middleware.logging import LoggingMiddleware

# Import routers
from api.routes import (
    health, documents, queries, analytics,
    agents, integrations, auth, storage, chat, services
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