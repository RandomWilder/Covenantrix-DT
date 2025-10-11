"""
Covenantrix Backend Application
FastAPI application with clean architecture
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.logging_config import setup_logging
from core.dependencies import set_rag_engine
from api.middleware.error_handler import add_exception_handlers
from api.middleware.logging import LoggingMiddleware

# Import routers
from api.routes import (
    health, documents, queries, analytics,
    agents, integrations, auth, storage, chat
)
from api.routes import settings as settings_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting Covenantrix Backend...")
    
    # Initialize RAG engine
    settings = get_settings()
    
    if settings.openai.api_key:
        try:
            from infrastructure.ai.rag_engine import RAGEngine, LIGHTRAG_AVAILABLE
            from infrastructure.storage.user_settings_storage import UserSettingsStorage
            
            # Load user settings
            user_settings_storage = UserSettingsStorage()
            user_settings = await user_settings_storage.load_settings()
            user_settings_dict = user_settings.model_dump()
            
            if LIGHTRAG_AVAILABLE:
                rag_engine = RAGEngine(api_key=settings.openai.api_key, user_settings=user_settings_dict)
                await rag_engine.initialize()
                
                # Apply user settings to RAG engine
                rag_engine.apply_settings(user_settings_dict)
                
                # Store globally for dependency injection
                set_rag_engine(rag_engine)
                
                logger.info("✓ RAG engine initialized and registered with user settings")
            else:
                logger.warning("⚠ LightRAG not available - install with: pip install lightrag-hku")
        except Exception as e:
            logger.error(f"✗ RAG engine initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Don't continue if RAG engine fails - it's critical for chat functionality
            raise
    else:
        logger.warning("⚠ OpenAI API key not configured - RAG features disabled")
    
    logger.info("✓ Covenantrix Backend ready")
    
    yield
    
    logger.info("🛑 Shutting down Covenantrix Backend...")


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