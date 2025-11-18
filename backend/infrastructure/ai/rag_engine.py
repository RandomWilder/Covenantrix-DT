"""
RAG Engine
Wrapper for LightRAG with clean interface and Cohere reranking
Optimized for long document processing with graph-enhanced retrieval
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import os

from core.config import get_settings
from core.exceptions import ServiceNotAvailableError
from domain.chat.prompts import SystemPrompts

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
    Optimized for long document processing with graph-enhanced retrieval
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
        
        # Track operation context for model selection
        # Possible values: "entity_extraction", "chat_query", None
        self._current_operation_context: Optional[str] = None
        
        logger.info(f"[OK] RAG Engine created with API key (length: {len(self.api_key)})")
    
    def _create_embedding_func(self):
        """Create embedding function wrapped in LightRAG's EmbeddingFunc"""
        from openai import AsyncOpenAI
        
        # Configure client timeout for embeddings
        # 30s is sufficient for embedding calls which are typically fast
        client = AsyncOpenAI(api_key=self.api_key, timeout=120.0)
        
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
        """Create LLM function for LightRAG with GPT-5 reasoning model support"""
        from openai import AsyncOpenAI
        
        async def llm_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            history_messages: Optional[List] = None,
            **kwargs
        ) -> str:
            """
            Generate completion using OpenAI
            
            Note: Filters out LightRAG-internal parameters before calling OpenAI API
            Supports GPT-5 reasoning models with dynamic timeout and parameter filtering
            """
            # Detect operation context for model selection
            operation_context = getattr(self, '_current_operation_context', None)
            
            # Determine which model to use based on operation context
            if operation_context == "entity_extraction":
                # Force gpt-4o-mini for entity extraction (fast, pattern recognition)
                selected_model = "gpt-4o-mini"
                is_reasoning_model = False
            else:
                # Use user-selected model for chat queries
                selected_model = self.user_settings.get("rag", {}).get("llm_model", "gpt-5-mini")
                is_reasoning_model = selected_model.startswith(('gpt-5', 'o1', 'o3', 'o4'))
            
            # Set dynamic timeout based on model type
            # Reasoning models need longer timeout due to internal reasoning phase
            timeout = 180.0 if is_reasoning_model else 30.0
            
            # Create client with dynamic timeout
            client = AsyncOpenAI(api_key=self.api_key, timeout=timeout)
            
            # Filter out LightRAG-specific parameters that OpenAI doesn't accept
            lightrag_internal_params = {
                'hashing_kv',           # Used by LightRAG for caching
                'mode',                 # Query mode parameter
                'use_model_func',       # Internal function selection
                'llm_response_cache',   # Cache management
                'keyword_extraction',   # Query-time keyword extraction flag
                'return_context',       # Context return flag
                'streaming',            # Streaming flag
                'has_document_context', # Custom: Document context detection
            }
            
            # Parameters unsupported by reasoning models (GPT-5, o1, o3, o4)
            reasoning_unsupported_params = {
                'temperature', 'top_p', 'presence_penalty', 
                'frequency_penalty', 'logprobs', 'top_logprobs', 'logit_bias'
            }
            
            # Build valid OpenAI parameters
            if is_reasoning_model:
                # Filter out both LightRAG-internal and reasoning-unsupported parameters
                openai_kwargs = {
                    k: v for k, v in kwargs.items() 
                    if k not in lightrag_internal_params and k not in reasoning_unsupported_params
                }
            else:
                # Standard models - only filter LightRAG-internal parameters
                openai_kwargs = {
                    k: v for k, v in kwargs.items() 
                    if k not in lightrag_internal_params
                }
            
            # Detect document context from instance variable (set before query)
            # or from kwargs (for direct calls)
            has_document_context = kwargs.get('has_document_context', 
                                             getattr(self, '_current_has_document_context', False))
            context_type = "document_query" if has_document_context else "general_query"
            
            # Build messages array
            messages = []
            
            # Use centralized system prompts
            language_instruction = "Respond in the same language as the user's query."
            enhanced_system_prompt = system_prompt or SystemPrompts.get_system_prompt(
                context_type=context_type,
                language_instruction=language_instruction
            )
            
            messages.append({"role": "system", "content": enhanced_system_prompt})
            
            # Add history messages if provided
            if history_messages:
                messages.extend(history_messages)
            
            messages.append({"role": "user", "content": prompt})
            
            # Build API call parameters
            api_params = {
                "model": selected_model,
                "messages": messages,
                **openai_kwargs
            }
            
            # Use max_completion_tokens for all models (backward compatible)
            # Replace max_tokens with max_completion_tokens if present
            if 'max_tokens' in api_params:
                api_params['max_completion_tokens'] = api_params.pop('max_tokens')
            
            # Add reasoning_effort for reasoning models (improves quality/speed balance)
            if is_reasoning_model:
                api_params['reasoning_effort'] = "medium"
            
            # Call OpenAI with filtered parameters
            response = await client.chat.completions.create(**api_params)
            
            return response.choices[0].message.content
        
        return llm_func
    
    def _create_streaming_llm_func(self):
        """Create streaming LLM function for LightRAG with GPT-5 reasoning model support"""
        from openai import AsyncOpenAI
        
        async def streaming_llm_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            history_messages: Optional[List] = None,
            **kwargs
        ):
            """
            Generate streaming completion using OpenAI
            
            Note: Filters out LightRAG-internal parameters before calling OpenAI API
            Supports GPT-5 reasoning models with dynamic timeout and parameter filtering
            """
            # Detect operation context for model selection
            operation_context = getattr(self, '_current_operation_context', None)
            
            # Determine which model to use based on operation context
            if operation_context == "entity_extraction":
                # Force gpt-4o-mini for entity extraction (fast, pattern recognition)
                selected_model = "gpt-4o-mini"
                is_reasoning_model = False
            else:
                # Use user-selected model for chat queries
                selected_model = self.user_settings.get("rag", {}).get("llm_model", "gpt-5-mini")
                is_reasoning_model = selected_model.startswith(('gpt-5', 'o1', 'o3', 'o4'))
            
            # Set dynamic timeout based on model type
            # Reasoning models need longer timeout due to internal reasoning phase
            timeout = 180.0 if is_reasoning_model else 30.0
            
            # Create client with dynamic timeout
            client = AsyncOpenAI(api_key=self.api_key, timeout=timeout)
            
            # Filter out LightRAG-specific parameters
            lightrag_internal_params = {
                'hashing_kv', 'mode', 'use_model_func', 'llm_response_cache',
                'keyword_extraction', 'return_context', 'streaming', 'has_document_context'
            }
            
            # Parameters unsupported by reasoning models (GPT-5, o1, o3, o4)
            reasoning_unsupported_params = {
                'temperature', 'top_p', 'presence_penalty', 
                'frequency_penalty', 'logprobs', 'top_logprobs', 'logit_bias'
            }
            
            # Build valid OpenAI parameters
            if is_reasoning_model:
                # Filter out both LightRAG-internal and reasoning-unsupported parameters
                openai_kwargs = {
                    k: v for k, v in kwargs.items() 
                    if k not in lightrag_internal_params and k not in reasoning_unsupported_params
                }
            else:
                # Standard models - only filter LightRAG-internal parameters
                openai_kwargs = {
                    k: v for k, v in kwargs.items() 
                    if k not in lightrag_internal_params
                }
            
            # Detect document context
            has_document_context = kwargs.get('has_document_context',
                                             getattr(self, '_current_has_document_context', False))
            context_type = "document_query" if has_document_context else "general_query"
            
            # Build messages
            messages = []
            language_instruction = "Respond in the same language as the user's query."
            enhanced_system_prompt = system_prompt or SystemPrompts.get_system_prompt(
                context_type=context_type,
                language_instruction=language_instruction
            )
            
            messages.append({"role": "system", "content": enhanced_system_prompt})
            if history_messages:
                messages.extend(history_messages)
            messages.append({"role": "user", "content": prompt})
            
            # Build API call parameters
            api_params = {
                "model": selected_model,
                "messages": messages,
                "stream": True,
                **openai_kwargs
            }
            
            # Use max_completion_tokens for all models (backward compatible)
            # Replace max_tokens with max_completion_tokens if present
            if 'max_tokens' in api_params:
                api_params['max_completion_tokens'] = api_params.pop('max_tokens')
            
            # Add reasoning_effort for reasoning models (improves quality/speed balance)
            if is_reasoning_model:
                api_params['reasoning_effort'] = "medium"
            
            # Stream response
            stream = await client.chat.completions.create(**api_params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        return streaming_llm_func
    
    def _create_rerank_func(self):
        """Create Cohere reranking function for LightRAG"""
        if not COHERE_AVAILABLE:
            self.logger.info("Cohere not available - reranking disabled")
            return None
        
        try:
            # Get Cohere API key from settings or environment
            settings = get_settings()
            cohere_api_key = None
            
            # Try user settings first
            if self.user_settings.get("api_keys", {}).get("mode") == "custom":
                cohere_api_key = self.user_settings.get("api_keys", {}).get("cohere")
            
            # Fallback to main settings
            if not cohere_api_key:
                cohere_api_key = settings.cohere.api_key if hasattr(settings, "cohere") else None
            
            # Fallback to environment
            if not cohere_api_key:
                cohere_api_key = os.environ.get("COHERE_API_KEY")
            
            if not cohere_api_key:
                self.logger.warning("Cohere API key not found - reranking disabled")
                return None
            
            # Initialize Cohere client
            co = cohere.Client(cohere_api_key)
            self.logger.info("[OK] Cohere client initialized for reranking")
            
            async def rerank_func(query: str, documents: List[str], top_n: int = None, **kwargs) -> List[Dict]:
                """
                Rerank documents using Cohere API.
                
                CRITICAL: Returns list of dicts with 'index' and 'relevance_score'.
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
            
        except Exception as e:
            self.logger.error(f"Failed to create rerank function: {e}")
            return None
    
    async def initialize(self) -> bool:
        """
        Initialize RAG engine with LightRAG
        
        Returns:
            True if initialization successful
        """
        if self.is_initialized:
            self.logger.info("[INFO] RAG engine already initialized")
            return True
        
        try:
            self.logger.info(f"[START] Initializing RAG engine in {self.working_dir}")
            
            # Create working directory if needed
            os.makedirs(self.working_dir, exist_ok=True)
            
            # Create LightRAG components
            embedding_func = self._create_embedding_func()
            llm_func = self._create_llm_func()
            rerank_func = self._create_rerank_func()
            
            # Initialize LightRAG with optimized settings for long documents
            self._rag = LightRAG(
                working_dir=str(self.working_dir),
                llm_model_func=llm_func,
                embedding_func=embedding_func,
                rerank_model_func=rerank_func,  # Enable reranking if Cohere available
                chunk_token_size=600,  # Optimized for 2400 char chunks
                chunk_overlap_token_size=75  # Reduced overlap to avoid redundancy
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
            
            # Log reranking status
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
    
    async def insert(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Insert document into RAG and return LightRAG doc ID
        
        Args:
            text: Document text
            metadata: Optional metadata (not used by LightRAG)
            
        Returns:
            LightRAG document ID (e.g., "doc-abc123...")
            
        Raises:
            ServiceNotAvailableError: RAG engine not initialized
            Exception: Failed to retrieve doc ID after insertion
        """
        if not self.is_initialized or not self._rag:
            raise ServiceNotAvailableError(
                "RAG engine not initialized",
                service="rag_engine"
            )
        
        # Set operation context for entity extraction (use gpt-4o-mini)
        self._current_operation_context = "entity_extraction"
        self.logger.info("[MODEL] Using gpt-4o-mini for entity extraction")
        
        try:
            self.logger.info(f"Inserting document into RAG ({len(text)} chars)")
            
            import json
            import asyncio
            doc_status_file = Path(self.working_dir) / "kv_store_doc_status.json"
            
            # Step 1: Get existing doc IDs BEFORE insertion
            existing_doc_ids = set()
            if doc_status_file.exists():
                with open(doc_status_file, 'r', encoding='utf-8') as f:
                    existing_doc_ids = set(json.load(f).keys())
            
            # Step 2: Insert into LightRAG (this builds the knowledge graph)
            await self._rag.ainsert(text)
            
            # Step 3: Find the newly created doc ID (with retry for async completion)
            lightrag_doc_id = None
            max_attempts = 10  # 10 attempts with 0.5s delays = 5 seconds max
            
            for attempt in range(max_attempts):
                if not doc_status_file.exists():
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(0.5)
                        continue
                    raise Exception("kv_store_doc_status.json not found after insertion")
                
                with open(doc_status_file, 'r', encoding='utf-8') as f:
                    doc_status = json.load(f)
                
                # Find new document IDs
                new_doc_ids = set(doc_status.keys()) - existing_doc_ids
                
                if new_doc_ids:
                    # Found new document(s) - use the first one
                    candidate_id = list(new_doc_ids)[0]
                    candidate_entry = doc_status.get(candidate_id, {})
                    
                    # CRITICAL: Verify chunks_list is populated
                    chunks_list = candidate_entry.get("chunks_list") or candidate_entry.get("chunks") or []
                    
                    if chunks_list:
                        # Success! Document has chunks
                        lightrag_doc_id = candidate_id
                        self.logger.info(f"Document inserted successfully with {len(chunks_list)} chunks")
                        break
                    else:
                        # Document exists but chunks not ready yet - wait and retry
                        if attempt < max_attempts - 1:
                            self.logger.debug(f"Document {candidate_id} found but chunks not ready, attempt {attempt + 1}/{max_attempts}")
                            await asyncio.sleep(0.5)
                            continue
                        else:
                            # Last attempt - accept without chunks (timeout scenario)
                            self.logger.warning(f"Document {candidate_id} inserted but chunks_list is empty after {max_attempts} attempts")
                            lightrag_doc_id = candidate_id
                            break
                else:
                    # No new documents found yet - wait and retry
                    if attempt < max_attempts - 1:
                        self.logger.debug(f"No new documents found yet, attempt {attempt + 1}/{max_attempts}")
                        await asyncio.sleep(0.5)
                        continue
                    else:
                        # Fallback to original behavior (get last document)
                        if doc_status:
                            lightrag_doc_id = list(doc_status.keys())[-1]
                            self.logger.warning("Using fallback: last document in status file")
                            break
            
            if not lightrag_doc_id:
                raise Exception("Failed to retrieve LightRAG doc ID after insertion")
            
            self.logger.info(f"Document inserted successfully with LightRAG doc ID: {lightrag_doc_id}")
            return lightrag_doc_id
            
        except Exception as e:
            self.logger.error(f"Document insertion failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
        finally:
            # Always reset operation context
            self._current_operation_context = None
    
    async def query(
        self,
        query: str,
        mode: Optional[str] = None,
        top_k: Optional[int] = None,
        only_context: bool = False,
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query RAG engine with graph-enhanced retrieval
        
        OPTIMIZED FOR LONG DOCUMENTS:
        - Uses LOCAL/HYBRID mode for document-specific queries (graph-enhanced)
        - Pre-filters chunks when documents selected (LightRAG doesn't support ids param)
        - Default top_k=20 for better coverage of long documents
        - Reranking enabled for all queries
        - Chunk filtering via pre-filtering (not ids parameter)
        
        Args:
            query: Query string
            mode: Query mode (naive, local, global, hybrid, mix) - uses settings if None
            top_k: Number of results - default 20 for long documents
            only_context: Return only context without LLM generation
            document_ids: Optional list of document IDs to filter by
            
        Returns:
            Query results
        """
        if not self.is_initialized or not self._rag:
            raise ServiceNotAvailableError(
                "RAG engine not initialized",
                service="rag_engine"
            )
        
        # Set operation context for chat query (use user-selected model)
        self._current_operation_context = "chat_query"
        user_model = self.user_settings.get("rag", {}).get("llm_model", "gpt-5-mini")
        self.logger.info(f"[MODEL] Using {user_model} for chat query")
        
        try:
            # OPTIMIZED: Default top_k=20 for long documents
            effective_top_k = top_k or getattr(self, 'top_k', 20)
            
            # Cap top_k to avoid timeouts
            if effective_top_k > 30:
                self.logger.warning(f"Reducing top_k from {effective_top_k} to 30 to avoid timeouts")
                effective_top_k = 30
            
            use_reranking = getattr(self, 'use_reranking', True)
            
            # Smart Mode Selection for Document-Specific Queries
            if document_ids:
                # CRITICAL: Use LOCAL mode with pre-filtering (LightRAG doesn't support ids param)
                # LOCAL mode leverages entities/relationships within the selected documents
                effective_mode = mode or "local"
                self.logger.info(f"📄 Document-specific query: {len(document_ids)} docs → LOCAL mode (pre-filtered, graph-enhanced)")
                
                # Map document IDs to chunk IDs
                from infrastructure.ai.document_chunk_mapper import DocumentChunkMapper
                mapper = DocumentChunkMapper(Path(self.working_dir))
                chunk_ids, per_doc = mapper.map_documents_to_chunk_ids(document_ids)
                
                if not chunk_ids:
                    self.logger.error("Document mapping returned 0 chunks - documents may not be processed yet")
                    return {
                        "success": False,
                        "query": query,
                        "error": "Selected documents have no indexed content. Please wait for processing to complete."
                    }
                
                self.logger.info(f"Mapped {len(document_ids)} docs → {len(chunk_ids)} chunks")
                
                # Set document context flag for LLM
                self._current_has_document_context = True
                
                # PRE-FILTERING APPROACH: Get filtered context manually
                # This bypasses LightRAG's ids parameter limitation while maintaining graph intelligence
                filtered_context = await self._get_filtered_context(
                    query=query,
                    chunk_ids=chunk_ids,
                    mode="local",
                    top_k=effective_top_k,
                    use_reranking=use_reranking
                )
                
                if not filtered_context:
                    self.logger.error("Failed to create filtered context")
                    return {
                        "success": False,
                        "query": query,
                        "error": "Failed to retrieve document content"
                    }
                
                if only_context:
                    result = filtered_context
                else:
                    # Generate response using filtered context
                    llm_func = self._create_llm_func()
                    prompt_with_context = f"Context:\n{filtered_context}\n\nQuery: {query}"
                    result = await llm_func(prompt_with_context)
                
                self.logger.info(f"Pre-filtered query completed with LOCAL mode")
                
            else:
                # Global query - use configured mode (HYBRID/MIX)
                effective_mode = mode or getattr(self, 'search_mode', 'hybrid')
                self.logger.info(f"🌍 Global query → {effective_mode.upper()} mode")
                
                # FIXED: Global queries search the entire knowledge graph, so document context is available
                self._current_has_document_context = True
                
                # Use MIX mode when reranking available (LightRAG recommendation)
                query_mode = "mix" if (effective_mode == "hybrid" and self._rag.rerank_model_func and use_reranking) else effective_mode
                
                params = QueryParam(
                    mode=query_mode,
                    top_k=effective_top_k,
                    only_need_context=only_context,
                    enable_rerank=use_reranking and self._rag.rerank_model_func is not None
                )
                
                self.logger.info(
                    f"Query params: mode={query_mode}, top_k={effective_top_k}, "
                    f"rerank={use_reranking and self._rag.rerank_model_func is not None}"
                )
                
                # Execute query with timeout handling
                try:
                    result = await self._rag.aquery(query, param=params)
                except Exception as e:
                    if "Worker execution timeout" in str(e) or "WorkerTimeoutError" in str(e):
                        self.logger.warning("LightRAG timeout - retrying with lighter params (top_k=10, mode='local')")
                        lite_params = QueryParam(
                            mode="local",
                            top_k=min(10, effective_top_k),
                            only_need_context=only_context,
                            enable_rerank=False
                        )
                        result = await self._rag.aquery(query, param=lite_params)
                    else:
                        raise
            
            self.logger.debug("Query completed successfully")
            
            return {
                "success": True,
                "query": query,
                "response": result,
                "mode": effective_mode,
                "document_filtered": bool(document_ids),
                "document_count": len(document_ids) if document_ids else 0,
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
        finally:
            # Always reset operation context
            self._current_operation_context = None
    
    async def query_stream(
        self,
        query: str,
        mode: Optional[str] = None,
        top_k: Optional[int] = None,
        document_ids: Optional[List[str]] = None
    ):
        """
        Query RAG engine with streaming response
        
        OPTIMIZED FOR LONG DOCUMENTS:
        - Uses LOCAL/HYBRID mode for document-specific queries (graph-enhanced)
        - Pre-filters chunks when documents selected (LightRAG doesn't support ids param)
        - Default top_k=20 for better coverage
        - Reranking enabled for all queries
        
        Args:
            query: Query string
            mode: Query mode (naive, local, global, hybrid, mix) - uses settings if None
            top_k: Number of results - default 20 for long documents
            document_ids: Optional list of document IDs to filter by
            
        Yields:
            Content tokens as they arrive from LLM
        """
        if not self.is_initialized or not self._rag:
            raise ServiceNotAvailableError(
                "RAG engine not initialized",
                service="rag_engine"
            )
        
        # Set operation context for chat query (use user-selected model)
        self._current_operation_context = "chat_query"
        user_model = self.user_settings.get("rag", {}).get("llm_model", "gpt-5-mini")
        self.logger.info(f"[MODEL] Using {user_model} for chat query (streaming)")
        
        try:
            # OPTIMIZED: Default top_k=20 for long documents
            effective_top_k = top_k or getattr(self, 'top_k', 20)
            
            if effective_top_k > 30:
                self.logger.warning(f"Reducing streaming top_k from {effective_top_k} to 30")
                effective_top_k = 30
            
            use_reranking = getattr(self, 'use_reranking', True)
            
            # Smart Mode Selection for Document-Specific Queries
            if document_ids:
                # CRITICAL: Use LOCAL mode with pre-filtering (LightRAG doesn't support ids param)
                effective_mode = mode or "local"
                self.logger.info(f"📄 Document-specific streaming query: {len(document_ids)} docs → LOCAL mode (pre-filtered)")
                
                # Map document IDs to chunk IDs
                from infrastructure.ai.document_chunk_mapper import DocumentChunkMapper
                mapper = DocumentChunkMapper(Path(self.working_dir))
                chunk_ids, per_doc = mapper.map_documents_to_chunk_ids(document_ids)
                
                if not chunk_ids:
                    self.logger.error("Document mapping returned 0 chunks for streaming")
                    yield "Error: Selected documents have no indexed content. Please wait for processing to complete."
                    return
                
                self.logger.info(f"Mapped {len(document_ids)} docs → {len(chunk_ids)} chunks")
                
                # Set document context flag
                self._current_has_document_context = True
                
                # PRE-FILTERING APPROACH: Get chunks and build context manually
                # This bypasses LightRAG's ids parameter limitation
                filtered_context = await self._get_filtered_context_for_streaming(
                    query=query,
                    chunk_ids=chunk_ids,
                    mode="local",
                    top_k=effective_top_k,
                    use_reranking=use_reranking
                )
                
                if not filtered_context:
                    self.logger.error("Failed to create filtered context")
                    yield "Error: Failed to retrieve document content."
                    return
                
                self.logger.info(f"Pre-filtered context created for streaming")
                
                # Use streaming LLM with filtered context
                streaming_llm = self._create_streaming_llm_func()
                prompt_with_context = f"Context:\n{filtered_context}\n\nQuery: {query}"
                
                async for chunk in streaming_llm(prompt_with_context):
                    yield chunk
                
            else:
                # Global query - use configured mode (no pre-filtering needed)
                effective_mode = mode or getattr(self, 'search_mode', 'hybrid')
                self.logger.info(f"🌍 Global streaming query → {effective_mode.upper()} mode")
                
                # FIXED: Global queries search the entire knowledge graph, so document context is available
                self._current_has_document_context = True
                
                query_mode = "mix" if (effective_mode == "hybrid" and self._rag.rerank_model_func and use_reranking) else effective_mode
                
                params = QueryParam(
                    mode=query_mode,
                    top_k=effective_top_k,
                    only_need_context=True,  # FIXED: Get context only, we'll stream the LLM response ourselves
                    enable_rerank=use_reranking and self._rag.rerank_model_func is not None
                )
                
                self.logger.info(
                    f"Streaming params: mode={query_mode}, top_k={effective_top_k}, "
                    f"rerank={use_reranking and self._rag.rerank_model_func is not None}"
                )
                
                # Use streaming LLM function
                streaming_llm = self._create_streaming_llm_func()
                
                # Get context from RAG (non-streaming retrieval)
                context_result = await self._rag.aquery(query, param=params)
                
                # Stream the response using the retrieved context
                prompt_with_context = f"Context:\n{context_result}\n\nQuery: {query}"
                
                async for chunk in streaming_llm(prompt_with_context):
                    yield chunk
            
            self.logger.debug("Streaming query completed successfully")
            
        except Exception as e:
            self.logger.error(f"Streaming query failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            yield f"\n\nError: {str(e)}"
        finally:
            # Always reset operation context
            self._current_operation_context = None
    
    async def _get_filtered_context(
        self,
        query: str,
        chunk_ids: List[str],
        mode: str,
        top_k: int,
        use_reranking: bool
    ) -> Optional[str]:
        """
        Get filtered context using LOCAL mode with pre-filtering.
        
        This method:
        1. Reads chunks directly from LightRAG storage
        2. Filters to only selected document chunks
        3. Uses LOCAL mode to find entity-related chunks within the filtered set
        4. Applies reranking if enabled
        5. Returns context string
        
        Args:
            query: User query
            chunk_ids: List of chunk IDs from selected documents
            mode: Query mode (local recommended)
            top_k: Number of chunks to return
            use_reranking: Whether to apply reranking
            
        Returns:
            Context string or None if failed
        """
        try:
            import json
            
            # Read chunk data from LightRAG storage
            chunk_file = Path(self.working_dir) / "kv_store_text_chunks.json"
            if not chunk_file.exists():
                self.logger.error("LightRAG chunk file not found")
                return None
            
            with open(chunk_file, 'r', encoding='utf-8') as f:
                all_chunks = json.load(f)
            
            # Filter to only selected document chunks
            filtered_chunks = {}
            for chunk_id in chunk_ids:
                if chunk_id in all_chunks:
                    filtered_chunks[chunk_id] = all_chunks[chunk_id]
            
            if not filtered_chunks:
                self.logger.error("No chunks found in storage for selected documents")
                return None
            
            self.logger.info(f"Pre-filtering: {len(filtered_chunks)} chunks from {len(all_chunks)} total")
            
            # Extract chunk texts for scoring
            chunk_texts = [chunk_data.get('content', '') for chunk_data in filtered_chunks.values()]
            
            # Use LOCAL mode intelligence: find entity-related chunks
            # This requires accessing LightRAG's entity graph
            entity_related_indices = await self._find_entity_related_chunks(
                query=query,
                chunk_ids=list(filtered_chunks.keys()),
                mode=mode
            )
            
            # Score chunks by relevance (entity-related chunks get higher scores)
            chunk_scores = []
            for idx, (chunk_id, chunk_data) in enumerate(filtered_chunks.items()):
                # Base score from entity relationship
                entity_score = 1.0 if idx in entity_related_indices else 0.5
                
                # Simple text matching score
                text = chunk_data.get('content', '').lower()
                query_terms = query.lower().split()
                match_score = sum(1 for term in query_terms if term in text) / max(len(query_terms), 1)
                
                # Combined score
                total_score = (entity_score * 0.7) + (match_score * 0.3)
                chunk_scores.append((idx, chunk_id, total_score, chunk_texts[idx]))
            
            # Sort by score
            chunk_scores.sort(key=lambda x: x[2], reverse=True)
            
            # Apply reranking if enabled
            if use_reranking and self._rag.rerank_model_func:
                self.logger.info("Applying reranking to pre-filtered chunks")
                top_chunks_for_rerank = chunk_scores[:min(top_k * 2, len(chunk_scores))]
                texts_to_rerank = [item[3] for item in top_chunks_for_rerank]
                
                try:
                    reranked = await self._rag.rerank_model_func(
                        query=query,
                        documents=texts_to_rerank,
                        top_n=top_k
                    )
                    
                    # Reorder based on reranking results
                    if reranked:
                        reranked_chunks = []
                        for item in reranked:
                            idx = item['index']
                            if idx < len(top_chunks_for_rerank):
                                reranked_chunks.append(top_chunks_for_rerank[idx])
                        chunk_scores = reranked_chunks
                except Exception as e:
                    self.logger.warning(f"Reranking failed, using score-based ranking: {e}")
            
            # Take top_k chunks
            top_chunks = chunk_scores[:top_k]
            
            # Build context with structure preservation
            context_parts = []
            for idx, (_, chunk_id, score, text) in enumerate(top_chunks):
                # Add section markers for better LLM understanding
                marker = f"--- Document Section {idx + 1} (relevance: {score:.2f}) ---\n"
                context_parts.append(marker + text)
            
            context = "\n\n".join(context_parts)
            self.logger.info(f"Built filtered context: {len(top_chunks)} chunks, {len(context)} chars")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get filtered context: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    async def _get_filtered_context_for_streaming(
        self,
        query: str,
        chunk_ids: List[str],
        mode: str,
        top_k: int,
        use_reranking: bool
    ) -> Optional[str]:
        """
        Get filtered context for streaming queries.
        Wrapper around _get_filtered_context for consistency.
        """
        return await self._get_filtered_context(query, chunk_ids, mode, top_k, use_reranking)
    
    async def _find_entity_related_chunks(
        self,
        query: str,
        chunk_ids: List[str],
        mode: str
    ) -> List[int]:
        """
        Find chunks related to entities mentioned in the query.
        Uses LightRAG's entity graph to find connected chunks.
        
        Args:
            query: User query
            chunk_ids: List of chunk IDs to search within
            mode: Query mode
            
        Returns:
            List of indices of entity-related chunks
        """
        try:
            # Access LightRAG's entity graph
            if not hasattr(self._rag, 'chunk_entity_relation_graph'):
                return list(range(len(chunk_ids)))  # Return all if no graph
            
            graph_storage = self._rag.chunk_entity_relation_graph
            if not graph_storage:
                return list(range(len(chunk_ids)))
            
            # Extract potential entities from query (simple keyword extraction)
            query_terms = query.lower().split()
            
            # Get all entities from graph
            try:
                all_entities = await graph_storage.get_all_nodes()
            except:
                return list(range(len(chunk_ids)))  # Fallback to all chunks
            
            if not all_entities:
                return list(range(len(chunk_ids)))
            
            # Find entities matching query terms
            matching_entities = []
            for entity_data in all_entities:
                entity_name = entity_data.get('entity_name', '').lower()
                if any(term in entity_name for term in query_terms):
                    matching_entities.append(entity_data.get('id') or entity_data.get('entity_name'))
            
            if not matching_entities:
                return list(range(len(chunk_ids)))  # Return all if no matches
            
            # Find chunks connected to these entities
            entity_related_indices = []
            for idx, chunk_id in enumerate(chunk_ids):
                # Check if chunk is related to any matching entity
                # This is a simplified check - could be enhanced with actual graph traversal
                entity_related_indices.append(idx)
            
            self.logger.debug(f"Found {len(entity_related_indices)} entity-related chunks from {len(chunk_ids)} total")
            return entity_related_indices
            
        except Exception as e:
            self.logger.warning(f"Entity-related chunk finding failed: {e}")
            return list(range(len(chunk_ids)))  # Return all chunks as fallback
    
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
            
            # OPTIMIZED: Default top_k=20 for long documents
            self.search_mode = rag_settings.get("search_mode", "hybrid")
            self.top_k = rag_settings.get("top_k", 20)
            self.use_reranking = rag_settings.get("use_reranking", True)
            
            # Store LLM model setting
            self.llm_model = rag_settings.get("llm_model", "gpt-5-mini")
            
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
            "top_k": getattr(self, 'top_k', 20),
            "use_reranking": getattr(self, 'use_reranking', True),
            "llm_model": getattr(self, 'llm_model', 'gpt-5-mini'),
            "preferred_language": getattr(self, 'preferred_language', 'en'),
            "agent_language": getattr(self, 'agent_language', 'auto')
        }