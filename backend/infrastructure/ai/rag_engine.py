"""
RAG Engine
Wrapper for LightRAG with clean interface and Cohere reranking
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import os

from core.config import get_settings
from core.exceptions import ServiceNotAvailableError

logger = logging.getLogger(__name__)

# Try to import LightRAG
try:
    from lightrag import LightRAG, QueryParam
    from lightrag.base import EmbeddingFunc
    from lightrag.kg.shared_storage import initialize_pipeline_status
    LIGHTRAG_AVAILABLE = True
    logger.info("[OK] LightRAG imported successfully")
except ImportError as e:
    LIGHTRAG_AVAILABLE = False
    logger.error(f"[ERROR] LightRAG import failed: {e}")

# Try to import Cohere
try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    logger.warning("Cohere SDK not installed - reranking will be disabled")


class RAGEngine:
    """
    Clean RAG engine interface wrapping LightRAG with Cohere reranking
    """
    
    def __init__(self, api_key: Optional[str] = None, user_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize RAG engine
        
        Args:
            api_key: OpenAI API key
            user_settings: User settings for configuration
        """
        if not LIGHTRAG_AVAILABLE:
            raise ServiceNotAvailableError(
                "LightRAG not available",
                service="lightrag"
            )
        
        settings = get_settings()
        self.api_key = api_key or settings.openai.api_key
        
        if not self.api_key:
            logger.error("[ERROR] OpenAI API key not found in configuration")
            raise ValueError("OpenAI API key required for RAG engine")
        
        # Debug logging
        logger.info(f"[DEBUG] RAG Engine received key - length: {len(self.api_key)}, starts with: {self.api_key[:15] if len(self.api_key) >= 15 else self.api_key}")
        
        # Set API key in environment for LightRAG
        os.environ["OPENAI_API_KEY"] = self.api_key
        logger.info(f"[DEBUG] Set OPENAI_API_KEY env var - length: {len(os.environ['OPENAI_API_KEY'])}, starts with: {os.environ['OPENAI_API_KEY'][:15]}")
        
        self.working_dir = settings.storage.working_dir
        self.is_initialized = False
        self._rag: Optional[LightRAG] = None
        self.logger = logging.getLogger(__name__)
        
        # Store user settings for configuration
        self.user_settings = user_settings or {}
        
        logger.info(f"[OK] RAG Engine created with API key (length: {len(self.api_key)})")
    
    def _create_embedding_func(self):
        """Create embedding function wrapped in LightRAG's EmbeddingFunc"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.api_key)
        
        async def embedding_func(texts: list[str]) -> list[list[float]]:
            """Generate embeddings for texts using text-embedding-3-large"""
            response = await client.embeddings.create(
                model="text-embedding-3-large",
                input=texts
            )
            return [item.embedding for item in response.data]
        
        # Wrap in LightRAG's EmbeddingFunc object
        return EmbeddingFunc(
            embedding_dim=3072,
            max_token_size=8192,
            func=embedding_func
        )
    
    def _create_llm_func(self):
        """Create LLM function for LightRAG"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.api_key)
        
        async def llm_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            history_messages: Optional[List] = None,
            **kwargs
        ) -> str:
            """
            Generate completion using OpenAI
            
            Note: Filters out LightRAG-internal parameters before calling OpenAI API
            """
            # Filter out LightRAG-specific parameters that OpenAI doesn't accept
            lightrag_internal_params = {
                'hashing_kv',           # Used by LightRAG for caching
                'mode',                 # Query mode parameter
                'use_model_func',       # Internal function selection
                'llm_response_cache',   # Cache management
                'keyword_extraction',   # Query-time keyword extraction flag
                'return_context',       # Context return flag
                'streaming',            # Streaming flag
            }
            
            # Build valid OpenAI parameters
            openai_kwargs = {
                k: v for k, v in kwargs.items() 
                if k not in lightrag_internal_params
            }
            
            # Build messages array
            messages = []
            
            # Enhance system prompt with language matching instruction
            enhanced_system_prompt = system_prompt or "You are a helpful assistant."
            if system_prompt and "Respond in the same language" not in system_prompt:
                enhanced_system_prompt += " Respond in the same language as the user's query."
            
            messages.append({"role": "system", "content": enhanced_system_prompt})
            
            # Add history messages if provided
            if history_messages:
                messages.extend(history_messages)
            
            messages.append({"role": "user", "content": prompt})
            
            # Get model from settings or use default
            model = self.user_settings.get("rag", {}).get("llm_model", "gpt-4o-mini")
            
            # Call OpenAI with filtered parameters
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                **openai_kwargs
            )
            
            return response.choices[0].message.content
        
        return llm_func
    
    def _create_streaming_llm_func(self):
        """Create streaming LLM function for LightRAG"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.api_key)
        
        async def streaming_llm_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            history_messages: Optional[List] = None,
            **kwargs
        ):
            """
            Generate streaming completion using OpenAI
            
            Note: Filters out LightRAG-internal parameters before calling OpenAI API
            Yields content tokens as they arrive
            """
            # Filter out LightRAG-specific parameters that OpenAI doesn't accept
            lightrag_internal_params = {
                'hashing_kv',           # Used by LightRAG for caching
                'mode',                 # Query mode parameter
                'use_model_func',       # Internal function selection
                'llm_response_cache',   # Cache management
                'keyword_extraction',   # Query-time keyword extraction flag
                'return_context',       # Context return flag
                'streaming',            # Streaming flag
            }
            
            # Build valid OpenAI parameters
            openai_kwargs = {
                k: v for k, v in kwargs.items() 
                if k not in lightrag_internal_params
            }
            
            # Build messages array
            messages = []
            
            # Enhance system prompt with language matching instruction
            enhanced_system_prompt = system_prompt or "You are a helpful assistant."
            if system_prompt and "Respond in the same language" not in system_prompt:
                enhanced_system_prompt += " Respond in the same language as the user's query."
            
            messages.append({"role": "system", "content": enhanced_system_prompt})
            
            # Add history messages if provided
            if history_messages:
                messages.extend(history_messages)
            
            messages.append({"role": "user", "content": prompt})
            
            # Get model from settings or use default
            model = self.user_settings.get("rag", {}).get("llm_model", "gpt-4o-mini")
            
            # Call OpenAI with streaming enabled
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **openai_kwargs
            )
            
            # Yield tokens as they arrive
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        return streaming_llm_func
    
    def _create_rerank_func(self):
        """
        Create async reranking function using Cohere API
        
        CRITICAL FIX: Returns list of dicts with 'index' and 'relevance_score' keys,
        NOT reranked documents. LightRAG uses the indices to reorder documents internally.
        
        Uses Cohere's rerank-english-v3.0 model for optimal relevance scoring.
        Requires COHERE_API_KEY in environment.
        """
        if not COHERE_AVAILABLE:
            self.logger.warning("Cohere SDK not available - reranking disabled")
            return None
        
        settings = get_settings()
        cohere_api_key = settings.cohere.api_key
        
        if not cohere_api_key:
            self.logger.warning("Cohere API key not configured - reranking disabled")
            return None
        
        # Initialize Cohere client (use ClientV2 for latest API)
        try:
            co = cohere.ClientV2(api_key=cohere_api_key)
            self.logger.info("[OK] Cohere client initialized (ClientV2)")
        except Exception as e:
            self.logger.error(f"Failed to initialize Cohere client: {e}")
            return None
        
        async def rerank_func(query: str, documents: list[str], top_n: int = None, **kwargs) -> list[dict]:
            """
            Rerank documents using Cohere API
            
            CRITICAL: Must return list of dicts with 'index' and 'relevance_score' keys.
            LightRAG will use these indices to reorder the original documents.
            
            Args:
                query: Search query
                documents: List of document texts to rerank
                top_n: Number of top results to return (passed by LightRAG)
                **kwargs: Additional parameters from LightRAG (ignored)
                
            Returns:
                List of dicts: [{"index": int, "relevance_score": float}, ...]
                Sorted by relevance (most relevant first)
            """
            if not documents:
                return []
            
            try:
                # Use top_n from LightRAG or return all documents
                num_results = min(top_n, len(documents)) if top_n else len(documents)
                
                # Call Cohere rerank API
                response = co.rerank(
                    model="rerank-english-v3.0",
                    query=query,
                    documents=documents,
                    top_n=num_results    
                )
                
                # CRITICAL FIX: Return indices and scores, NOT reranked documents
                # LightRAG expects this exact format
                results = []
                for result in response.results:
                    results.append({
                        "index": result.index,
                        "relevance_score": result.relevance_score
                    })
                
                self.logger.debug(f"Reranked {len(documents)} docs → {len(results)} results")
                return results
                
            except Exception as e:
                self.logger.error(f"Cohere rerank failed: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                
                # Fallback: return all documents in original order with neutral scores
                return [
                    {"index": i, "relevance_score": 1.0} 
                    for i in range(min(num_results, len(documents)) if top_n else len(documents))
                ]
        
        return rerank_func
    
    async def initialize(self) -> bool:
        """
        Initialize RAG engine with proper LightRAG initialization sequence
        
        Returns:
            True if successful
        """
        try:
            # Create working directory
            Path(self.working_dir).mkdir(parents=True, exist_ok=True)
            
            # Create rerank function (Cohere-based)
            rerank_func = self._create_rerank_func()
            if rerank_func:
                self.logger.info("[OK] Cohere reranking enabled")
            else:
                self.logger.info("[INFO] Reranking disabled (Cohere API key not configured)")
            
            # Initialize LightRAG with custom functions and optional reranking
            self._rag = LightRAG(
                working_dir=str(self.working_dir),
                llm_model_func=self._create_llm_func(),
                embedding_func=self._create_embedding_func(),
                rerank_model_func=rerank_func  # None if Cohere not configured
            )
            
            # CRITICAL: Initialize LightRAG internal storages (required for document operations)
            self.logger.info("Initializing LightRAG storages...")
            await self._rag.initialize_storages()
            
            # CRITICAL: Initialize pipeline status (required for document insertion)
            self.logger.info("Initializing pipeline status...")
            await initialize_pipeline_status()
            
            self.is_initialized = True
            self.logger.info(f"[OK] RAG engine initialized with text-embedding-3-large (3072 dims)")
            self.logger.info(f"[OK] Working directory: {self.working_dir}")
            
            # Log reranking status clearly
            if rerank_func:
                self.logger.info("[OK] Reranking: ENABLED (Cohere rerank-english-v3.0)")
            else:
                self.logger.info("[OK] Reranking: DISABLED")
            
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] RAG engine initialization failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.is_initialized = False
            return False
    
    async def insert(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Insert document into RAG
        
        Args:
            text: Document text
            metadata: Optional metadata (note: LightRAG doesn't use metadata, kept for API compatibility)
            
        Returns:
            True if successful
        """
        if not self.is_initialized or not self._rag:
            raise ServiceNotAvailableError(
                "RAG engine not initialized",
                service="rag_engine"
            )
        
        try:
            # LightRAG's native insert - only takes text, no metadata support
            await self._rag.ainsert(text)
            self.logger.debug(f"Inserted {len(text)} chars into RAG")
            return True
            
        except Exception as e:
            self.logger.error(f"RAG insert failed: {str(e)}")
            raise  # Re-raise to let caller handle the error properly
    
    async def query(
        self,
        query: str,
        mode: Optional[str] = None,
        top_k: Optional[int] = None,
        only_context: bool = False
    ) -> Dict[str, Any]:
        """
        Query RAG engine with proper reranking support
        
        Args:
            query: Query string
            mode: Query mode (naive, local, global, hybrid, mix) - uses settings if None
            top_k: Number of results - uses settings if None
            only_context: Return only context without LLM generation
            
        Returns:
            Query results
        """
        if not self.is_initialized or not self._rag:
            raise ServiceNotAvailableError(
                "RAG engine not initialized",
                service="rag_engine"
            )
        
        try:
            # Use settings if parameters not provided
            effective_mode = mode or getattr(self, 'search_mode', 'hybrid')
            effective_top_k = top_k or getattr(self, 'top_k', 5)
            use_reranking = getattr(self, 'use_reranking', True)
            
            # Use "mix" mode when reranking is available (LightRAG recommendation)
            # Mix mode integrates knowledge graph + vector retrieval + reranking
            query_mode = "mix" if (effective_mode == "hybrid" and self._rag.rerank_model_func and use_reranking) else effective_mode
            
            params = QueryParam(
                mode=query_mode,
                top_k=effective_top_k,
                only_need_context=only_context,
                enable_rerank=use_reranking and self._rag.rerank_model_func is not None
            )
            
            # Apply language-specific processing if needed
            effective_language = self.get_effective_language(query)
            
            self.logger.info(f"Query: '{query[:50]}...' | Mode: {query_mode} | Top-K: {effective_top_k} | Rerank: {use_reranking} | Lang: {effective_language}")
            
            result = await self._rag.aquery(query, param=params)
            
            self.logger.debug(f"Query completed successfully")
            
            return {
                "success": True,
                "query": query,
                "response": result,
                "mode": query_mode,
                "language": effective_language,
                "settings_applied": {
                    "search_mode": effective_mode,
                    "top_k": effective_top_k,
                    "use_reranking": use_reranking
                }
            }
            
        except Exception as e:
            self.logger.error(f"RAG query failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "query": query,
                "error": str(e)
            }
    
    async def query_stream(
        self,
        query: str,
        mode: Optional[str] = None,
        top_k: Optional[int] = None
    ):
        """
        Query RAG engine with streaming response
        
        Args:
            query: Query string
            mode: Query mode (naive, local, global, hybrid, mix) - uses settings if None
            top_k: Number of results - uses settings if None
            
        Yields:
            Content tokens as they arrive from LLM
        """
        if not self.is_initialized or not self._rag:
            raise ServiceNotAvailableError(
                "RAG engine not initialized",
                service="rag_engine"
            )
        
        try:
            # Use settings if parameters not provided
            effective_mode = mode or getattr(self, 'search_mode', 'hybrid')
            effective_top_k = top_k or getattr(self, 'top_k', 5)
            use_reranking = getattr(self, 'use_reranking', True)
            
            # Use "mix" mode when reranking is available
            query_mode = "mix" if (effective_mode == "hybrid" and self._rag.rerank_model_func and use_reranking) else effective_mode
            
            # Apply language-specific processing if needed
            effective_language = self.get_effective_language(query)
            
            # Add language matching instruction to system prompt
            language_instruction = f"Respond in the same language as the user's query ({effective_language})."
            
            self.logger.info(f"Streaming Query: '{query[:50]}...' | Mode: {query_mode} | Top-K: {effective_top_k} | Rerank: {use_reranking} | Lang: {effective_language}")
            
            # For streaming, we need to handle this differently
            # We'll use the streaming LLM function directly with context retrieval
            
            # First, get context from RAG (non-streaming retrieval)
            params = QueryParam(
                mode=query_mode,
                top_k=effective_top_k,
                only_need_context=True,  # Only get context, not LLM response
                enable_rerank=use_reranking and self._rag.rerank_model_func is not None
            )
            
            # Get context from LightRAG
            context = await self._rag.aquery(query, param=params)
            
            # Now use streaming LLM function to generate response with context
            streaming_llm = self._create_streaming_llm_func()
            
            # Build prompt with context
            prompt = f"Context:\n{context}\n\nQuery: {query}"
            system_prompt = f"You are a helpful assistant. {language_instruction}"
            
            # Stream tokens from LLM
            async for token in streaming_llm(
                prompt=prompt,
                system_prompt=system_prompt
            ):
                yield token
            
            self.logger.debug(f"Streaming query completed successfully")
            
        except Exception as e:
            self.logger.error(f"RAG streaming query failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Yield error message as fallback
            yield "I'm sorry, I encountered an error processing your request."
    
    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """
        Apply user settings to RAG engine
        
        Args:
            settings: User settings dictionary
        """
        try:
            self.user_settings = settings
            
            # Apply RAG-specific settings
            rag_settings = settings.get("rag", {})
            
            # Update search mode and top-k settings
            self.search_mode = rag_settings.get("search_mode", "hybrid")
            self.top_k = rag_settings.get("top_k", 5)
            self.use_reranking = rag_settings.get("use_reranking", True)
            
            # Store LLM model setting
            self.llm_model = rag_settings.get("llm_model", "gpt-4o-mini")
            
            # Apply language settings
            language_settings = settings.get("language", {})
            self.preferred_language = language_settings.get("preferred", "en")
            self.agent_language = language_settings.get("agent_language", "auto")
            
            # Apply API key settings if in custom mode
            api_keys = settings.get("api_keys", {})
            if api_keys.get("mode") == "custom":
                # Update API keys if provided
                if api_keys.get("openai"):
                    self.api_key = api_keys["openai"]
                    os.environ["OPENAI_API_KEY"] = self.api_key
                
                if api_keys.get("cohere"):
                    os.environ["COHERE_API_KEY"] = api_keys["cohere"]
            
            self.logger.info(f"Settings applied: mode={self.search_mode}, top_k={self.top_k}, reranking={self.use_reranking}, llm_model={self.llm_model}")
            
        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
            raise
    
    def get_effective_language(self, query: str) -> str:
        """
        Get effective language for query processing
        
        Args:
            query: User query
            
        Returns:
            Language code to use
        """
        if self.agent_language == "auto":
            # Simple language detection based on query
            # This is a basic implementation - could be enhanced with proper language detection
            if any(char in query for char in "אבגדהוזחטיכסעפצקרשת"):
                return "he"  # Hebrew
            elif any(char in query for char in "ñáéíóúü"):
                return "es"  # Spanish
            elif any(char in query for char in "àâäéèêëïîôùûüÿç"):
                return "fr"  # French
            elif any(char in query for char in "äöüß"):
                return "de"  # German
            else:
                return "en"  # Default to English
        else:
            return self.agent_language
    
    def get_status(self) -> Dict[str, Any]:
        """Get RAG engine status"""
        return {
            "initialized": self.is_initialized,
            "working_dir": str(self.working_dir),
            "available": LIGHTRAG_AVAILABLE,
            "api_key_configured": bool(self.api_key),
            "embedding_model": "text-embedding-3-large",
            "embedding_dimensions": 3072,
            "reranking_enabled": self._rag.rerank_model_func is not None if self._rag else False,
            "user_settings": self.user_settings,
            "search_mode": getattr(self, 'search_mode', 'hybrid'),
            "top_k": getattr(self, 'top_k', 5),
            "use_reranking": getattr(self, 'use_reranking', True),
            "llm_model": getattr(self, 'llm_model', 'gpt-4o-mini'),
            "preferred_language": getattr(self, 'preferred_language', 'en'),
            "agent_language": getattr(self, 'agent_language', 'auto')
        }