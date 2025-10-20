"""
Document Service
Business logic for document management
"""
import logging
from typing import List, Optional, BinaryIO, TYPE_CHECKING, Callable, Awaitable
from datetime import datetime
from pathlib import Path
import hashlib
import magic  # python-magic for MIME type detection

from domain.documents.models import (
    Document, DocumentQuery, QueryResult, DocumentStatus
)
from domain.documents.exceptions import (
    DocumentNotFoundError,
    InvalidDocumentFormatError,
    DocumentProcessingError
)
from domain.entities.service import EntityExtractionService
from domain.entities.models import EntitySummary
from core.exceptions import ConfigurationError

# Avoid circular imports
if TYPE_CHECKING:
    from infrastructure.ai.rag_engine import RAGEngine
    from infrastructure.storage.document_registry import DocumentRegistry
    from domain.integrations.ocr import OCRService

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Document domain service
    Orchestrates document upload, processing, and querying
    
    Design: Works directly with RAGEngine (for content) and DocumentRegistry (for metadata)
    following LightRAG's philosophy of text-only processing
    """
    
    # Supported file formats
    SUPPORTED_FORMATS = [
        'pdf', 'docx', 'doc', 'txt', 'rtf',
        'png', 'jpg', 'jpeg', 'tiff', 'gif', 'bmp',
        'xlsx', 'xls', 'pptx', 'ppt'
    ]
    
    # Stage messages for progress tracking
    STAGE_MESSAGES = {
        "initializing": "Preparing document...",
        "reading": "Reading document content...",
        "understanding": "Analyzing document structure...",
        "building_connections": "Building knowledge connections...",
        "finalizing": "Completing processing...",
        "completed": "Document ready",
        "failed": "Processing failed"
    }
    
    # Rotating messages for 75% stage
    ROTATING_MESSAGES = [
        "Building knowledge connections...",
        "Analyzing document relationships...", 
        "Creating semantic links...",
        "Processing document structure...",
        "Establishing connections...",
        "Building knowledge graph..."
    ]
    
    def __init__(
        self,
        rag_engine: 'RAGEngine',
        document_registry: 'DocumentRegistry',
        max_file_size_mb: int = 50,
        ocr_service: Optional['OCRService'] = None
    ):
        """
        Initialize document service
        
        Args:
            rag_engine: RAG engine for content insertion/querying
            document_registry: Document metadata registry
            max_file_size_mb: Maximum file size in MB
            ocr_service: Optional OCR service for fallback processing
        """
        self.rag_engine = rag_engine
        self.registry = document_registry
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.ocr_service = ocr_service
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        document_id: Optional[str] = None
    ) -> Document:
        """
        Upload and register a document (metadata only, content processed separately)
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            document_id: Optional custom document ID
            
        Returns:
            Created document entity
            
        Raises:
            InvalidDocumentFormatError: Unsupported format
            DocumentProcessingError: Processing failed
        """
        logger.info(f"Uploading document: {filename}")
        
        # Get file content (already bytes)
        content = file_content
        file_size = len(content)
        
        # Validate file size
        if file_size > self.max_file_size_bytes:
            raise DocumentProcessingError(
                f"File too large: {file_size / (1024*1024):.2f}MB "
                f"(max: {self.max_file_size_mb}MB)"
            )
        
        # Validate format
        extension = filename.lower().split('.')[-1]
        if extension not in self.SUPPORTED_FORMATS:
            raise InvalidDocumentFormatError(
                filename=filename,
                supported_formats=self.SUPPORTED_FORMATS
            )
        
        # Detect MIME type
        mime_type = magic.from_buffer(content, mime=True)
        
        # Calculate content hash
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Create document entity
        document = Document.create_new(
            filename=filename,
            file_size_bytes=file_size,
            mime_type=mime_type,
            content_hash=content_hash,
            document_id=document_id
        )
        
        # Register in document registry (note: using document.metadata.* for nested attributes)
        await self.registry.register_document(
            document_id=document.id,
            filename=document.metadata.filename,
            file_size_bytes=document.metadata.file_size_bytes,
            content_hash=document.content_hash,
            mime_type=document.metadata.mime_type
        )
        
        logger.info(f"Document registered: {document.id}")
        return document
    
    async def process_document(
        self,
        document_id: str,
        extracted_content: str,
        processing_time: float,
        ocr_applied: bool = False,
        progress_callback: Optional[Callable[[str, int], Awaitable[None]]] = None
    ) -> Document:
        """
        Process document content and store in RAG
        
        Args:
            document_id: Document to process
            extracted_content: Extracted text
            processing_time: Processing time in seconds
            ocr_applied: Whether OCR was used
            progress_callback: Optional callback for progress updates (stage, percent)
            
        Returns:
            Updated document
            
        Raises:
            DocumentNotFoundError: Document not found
        """
        # Get document from registry
        doc_data = await self.registry.get_document(document_id)
        if not doc_data:
            raise DocumentNotFoundError(document_id)
        
        # Reconstruct document entity from registry data
        from domain.documents.models import DocumentMetadata
        
        document = Document(
            id=doc_data["document_id"],
            metadata=DocumentMetadata(
                filename=doc_data["filename"],
                file_size_bytes=doc_data["file_size_bytes"],
                mime_type=doc_data["mime_type"],
                uploaded_at=datetime.fromisoformat(doc_data["created_at"])
            ),
            status=DocumentStatus(doc_data["status"]),
            content_hash=doc_data["content_hash"],
            created_at=datetime.fromisoformat(doc_data["created_at"]),
            updated_at=datetime.fromisoformat(doc_data["updated_at"])
        )
        
        # Mark as processing
        document.mark_processing()
        await self.registry.update_status(
            document_id=document.id,
            status=document.status
        )
        
        try:
            # Stage 1: Reading (25%)
            if progress_callback:
                await progress_callback("reading", 25)
            await self.registry.update_processing_stage(
                document_id=document.id,
                stage="reading",
                progress_percent=25,
                message=self.STAGE_MESSAGES["reading"]
            )
            
            # Stage 2: Understanding (50%)
            if progress_callback:
                await progress_callback("understanding", 50)
            await self.registry.update_processing_stage(
                document_id=document.id,
                stage="understanding",
                progress_percent=50,
                message=self.STAGE_MESSAGES["understanding"]
            )
            
            # Stage 3: Building connections (75%)
            if progress_callback:
                await progress_callback("building_connections", 75)
            await self.registry.update_processing_stage(
                document_id=document.id,
                stage="building_connections",
                progress_percent=75,
                message=self.STAGE_MESSAGES["building_connections"]
            )
            
            # Start rotating messages task
            import asyncio
            rotation_task = None
            try:
                # Start rotating messages
                rotation_task = asyncio.create_task(
                    self._rotate_messages(document.id, progress_callback)
                )
                
                # Insert into LightRAG and capture LightRAG doc ID
                lightrag_doc_id = await self.rag_engine.insert(extracted_content)
                # Store the mapping in registry
                await self.registry.store_lightrag_doc_id(document.id, lightrag_doc_id)
                
            finally:
                # Always cancel rotation task
                if rotation_task and not rotation_task.done():
                    rotation_task.cancel()
                    try:
                        await rotation_task
                    except asyncio.CancelledError:
                        pass  # Expected when task is cancelled
            
            # Stage 4: Finalizing (90%)
            if progress_callback:
                await progress_callback("finalizing", 90)
            await self.registry.update_processing_stage(
                document_id=document.id,
                stage="finalizing",
                progress_percent=90,
                message=self.STAGE_MESSAGES["finalizing"]
            )
            
            # Calculate stats
            char_count = len(extracted_content)
            chunk_count = self._estimate_chunks(extracted_content)
            
            # Mark as processed
            document.mark_processed(
                char_count=char_count,
                chunk_count=chunk_count,
                processing_time=processing_time,
                ocr_applied=ocr_applied
            )
            
            # Update registry with new status and processing info
            processing_info = {
                "char_count": char_count,
                "chunk_count": chunk_count,
                "processing_time": processing_time,
                "ocr_applied": ocr_applied
            }
            
            await self.registry.update_status(
                document_id=document.id,
                status=document.status,
                processing_info=processing_info
            )
            
            # Stage 5: Completed (100%)
            if progress_callback:
                await progress_callback("completed", 100)
            await self.registry.update_processing_stage(
                document_id=document.id,
                stage="completed",
                progress_percent=100,
                message=self.STAGE_MESSAGES["completed"]
            )
            
            logger.info(f"Document processed: {document.id} ({char_count} chars, {chunk_count} chunks)")
            return document
            
        except Exception as e:
            # Mark as failed
            document.mark_failed(str(e))
            await self.registry.update_status(
                document_id=document.id,
                status=document.status,
                processing_info={"error": str(e)}
            )
            
            # Emit failed stage
            if progress_callback:
                await progress_callback("failed", 0)
            await self.registry.update_processing_stage(
                document_id=document.id,
                stage="failed",
                progress_percent=0,
                message=self.STAGE_MESSAGES["failed"]
            )
            
            logger.error(f"Document processing failed: {document.id} - {e}")
            raise DocumentProcessingError(str(e), document_id)
    
    async def get_document(self, document_id: str) -> Document:
        """
        Get document by ID
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document entity
            
        Raises:
            DocumentNotFoundError: Document not found
        """
        doc_data = await self.registry.get_document(document_id)
        
        if not doc_data:
            raise DocumentNotFoundError(document_id)
        
        from domain.documents.models import DocumentMetadata, ProcessingResult
        
        # Extract processing result if available
        processing_result = None
        if "processing" in doc_data and doc_data["processing"]:
            processing_data = doc_data["processing"]
            processing_result = ProcessingResult(
                success=True,
                char_count=processing_data.get("char_count", 0),
                chunk_count=processing_data.get("chunk_count", 0),
                processing_time_seconds=processing_data.get("processing_time", 0.0),
                ocr_applied=processing_data.get("ocr_applied", False)
            )
        
        return Document(
            id=doc_data["document_id"],
            metadata=DocumentMetadata(
                filename=doc_data["filename"],
                file_size_bytes=doc_data["file_size_bytes"],
                mime_type=doc_data["mime_type"],
                uploaded_at=datetime.fromisoformat(doc_data["created_at"])
            ),
            status=DocumentStatus(doc_data["status"]),
            content_hash=doc_data["content_hash"],
            created_at=datetime.fromisoformat(doc_data["created_at"]),
            updated_at=datetime.fromisoformat(doc_data["updated_at"]),
            processing_result=processing_result
        )
    
    async def list_documents(
        self,
        include_deleted: bool = False,
        subscription_tier: Optional[str] = None
    ) -> List[Document]:
        """
        List all documents from registry with tier-based visibility
        
        Args:
            include_deleted: Include soft-deleted documents
            subscription_tier: User's subscription tier for filtering
            
        Returns:
            List of documents (filtered by tier limits if applicable)
        """
        docs_data = await self.registry.list_documents(
            status=None,
            include_deleted=include_deleted
        )
        
        from domain.documents.models import DocumentMetadata, ProcessingResult
        
        documents = []
        for doc_data in docs_data:
            # Extract processing result if available
            processing_result = None
            processing_stage = None
            processing_message = None
            
            if "processing" in doc_data and doc_data["processing"]:
                processing_data = doc_data["processing"]
                processing_result = ProcessingResult(
                    success=True,
                    char_count=processing_data.get("char_count", 0),
                    chunk_count=processing_data.get("chunk_count", 0),
                    processing_time_seconds=processing_data.get("processing_time", 0.0),
                    ocr_applied=processing_data.get("ocr_applied", False)
                )
                
                # Extract current processing stage and message for processing documents
                if doc_data["status"] == "processing":
                    processing_stage = processing_data.get("stage")
                    processing_message = processing_data.get("message")
            
            documents.append(Document(
                id=doc_data["document_id"],
                metadata=DocumentMetadata(
                    filename=doc_data["filename"],
                    file_size_bytes=doc_data["file_size_bytes"],
                    mime_type=doc_data["mime_type"],
                    uploaded_at=datetime.fromisoformat(doc_data["created_at"])
                ),
                status=DocumentStatus(doc_data["status"]),
                content_hash=doc_data["content_hash"],
                created_at=datetime.fromisoformat(doc_data["created_at"]),
                updated_at=datetime.fromisoformat(doc_data["updated_at"]),
                processing_result=processing_result,
                processing_stage=processing_stage,
                processing_message=processing_message
            ))
        
        # NEW: Apply tier-based visibility filtering
        if subscription_tier:
            from domain.subscription.tier_config import TIER_LIMITS
            
            if subscription_tier == "paid_limited":
                # Show only first 3 documents by upload date (oldest first)
                documents = sorted(documents, key=lambda d: d.created_at)[:3]
            else:
                # Apply max_documents limit if not unlimited
                tier_config = TIER_LIMITS.get(subscription_tier)
                if tier_config:
                    max_docs = tier_config["max_documents"]
                    if max_docs != -1:
                        documents = sorted(documents, key=lambda d: d.created_at)[:max_docs]
        
        return documents
    
    async def delete_document(
        self,
        document_id: str,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete document
        
        Args:
            document_id: Document to delete
            hard_delete: Permanently delete vs soft delete
            
        Returns:
            True if deleted
            
        Raises:
            DocumentNotFoundError: Document not found
        """
        # Note: LightRAG doesn't support content deletion,
        # so we only delete metadata from registry
        success = await self.registry.delete_document(
            document_id,
            soft_delete=not hard_delete
        )
        
        if not success:
            raise DocumentNotFoundError(document_id)
        
        if hard_delete:
            logger.warning(f"Hard delete requested but LightRAG content remains: {document_id}")
        
        logger.info(f"Document deleted: {document_id} (hard={hard_delete})")
        return True
    
    async def query_documents(
        self,
        query_text: str,
        mode: str = "hybrid",
        document_ids: Optional[List[str]] = None
    ) -> QueryResult:
        """
        Query documents using RAG
        
        Args:
            query_text: Query string
            mode: Query mode (naive, local, global, hybrid, mix)
            document_ids: Optional document scope filter (not implemented in LightRAG)
            
        Returns:
            Query result
        """
        import time
        start_time = time.time()
        
        logger.info(f"Querying documents: '{query_text[:50]}...' (mode: {mode})")
        
        # Execute RAG query (optionally filtered by document_ids)
        result = await self.rag_engine.query(
            query=query_text,
            mode=mode,
            document_ids=document_ids
        )
        
        # Get document count from registry
        all_docs = await self.registry.list_documents(include_deleted=False)
        doc_count = len(all_docs)
        
        processing_time = time.time() - start_time
        
        return QueryResult(
            query=query_text,
            response=result.get("response", ""),
            mode=mode,
            documents_searched=doc_count,
            processing_time_seconds=processing_time
        )
    
    def _estimate_chunks(self, content: str, chunk_size: int = 1200) -> int:
        """Estimate number of chunks for content"""
        return max(1, len(content) // chunk_size)
    
    async def _rotate_messages(
        self, 
        document_id: str, 
        progress_callback: Optional[Callable[[str, int], Awaitable[None]]]
    ) -> None:
        """
        Rotate messages during the 75% processing stage
        
        Args:
            document_id: Document being processed
            progress_callback: Optional progress callback
        """
        import asyncio
        
        try:
            message_index = 0
            while True:
                # Get current rotating message
                message = self.ROTATING_MESSAGES[message_index % len(self.ROTATING_MESSAGES)]
                
                # Update registry with rotating message
                await self.registry.update_processing_stage(
                    document_id=document_id,
                    stage="building_connections",
                    progress_percent=75,
                    message=message
                )
                
                # Call progress callback if provided
                if progress_callback:
                    await progress_callback("building_connections", 75)
                
                # Wait 2-3 seconds before next rotation
                await asyncio.sleep(2.5)
                
                # Move to next message
                message_index += 1
                
        except asyncio.CancelledError:
            # Task was cancelled - this is expected when rag_engine.insert() completes
            logger.debug(f"Message rotation cancelled for document {document_id}")
        except Exception as e:
            # Log error but don't raise - rotation failure shouldn't affect main processing
            logger.warning(f"Message rotation error for document {document_id}: {e}")
    
    async def upload_documents_batch(
        self,
        files: List[bytes],
        filenames: List[str],
        max_concurrent: int = 3
    ) -> List[dict]:
        """
        Upload multiple documents in parallel
        
        Args:
            files: List of file contents
            filenames: List of filenames
            max_concurrent: Maximum concurrent uploads
            
        Returns:
            List of upload results with success/error status
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        logger.info(f"Starting batch upload of {len(files)} files")
        
        # Create semaphore to limit concurrent uploads
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def upload_single_file(file_content: bytes, filename: str) -> dict:
            """Upload a single file with semaphore control"""
            async with semaphore:
                try:
                    # Upload document
                    document = await self.upload_document(file_content, filename)
                    
                    return {
                        "filename": filename,
                        "document_id": document.id,
                        "success": True,
                        "error": None,
                        "file_size": document.metadata.file_size_bytes
                    }
                    
                except Exception as e:
                    logger.error(f"Batch upload failed for {filename}: {e}")
                    return {
                        "filename": filename,
                        "document_id": None,
                        "success": False,
                        "error": str(e),
                        "file_size": None
                    }
        
        # Process all files concurrently
        tasks = [
            upload_single_file(file, filename)
            for file, filename in zip(files, filenames)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions from gather
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "filename": filenames[i],
                    "document_id": None,
                    "success": False,
                    "error": str(result),
                    "file_size": None
                })
            else:
                processed_results.append(result)
        
        successful = sum(1 for r in processed_results if r["success"])
        failed = len(processed_results) - successful
        
        logger.info(f"Batch upload completed: {successful} successful, {failed} failed")
        
        return processed_results
    
    async def reset_storage(self) -> dict:
        """
        Reset all storage data - CLEARS EVERYTHING
        
        This method will:
        - Clear all LightRAG storage files
        - Clear document registry
        - Reinitialize LightRAG storage
        - Return system to clean state
        
        Returns:
            Reset operation details
        """
        import os
        from pathlib import Path
        
        logger.warning("Starting storage reset - clearing all data")
        
        try:
            # Get storage directory
            storage_dir = Path(self.rag_engine.working_dir)
            
            # Define LightRAG storage files to clear
            lightrag_files = [
                "kv_store_doc_status.json",
                "kv_store_text_chunks.json", 
                "kv_store_full_docs.json",
                "kv_store_full_entities.json",
                "kv_store_full_relations.json",
                "kv_store_llm_response_cache.json",
                "vdb_chunks.json",
                "vdb_entities.json",
                "vdb_relationships.json",
                "graph_chunk_entity_relation.graphml"
            ]
            
            # Clear LightRAG storage files
            cleared_files = []
            for filename in lightrag_files:
                file_path = storage_dir / filename
                if file_path.exists():
                    file_path.unlink()  # Delete the file
                    cleared_files.append(filename)
                    logger.debug(f"Cleared LightRAG file: {filename}")
            
            # Clear document registry
            registry_cleared = await self.registry.reset_registry()
            
            # Reinitialize LightRAG storage
            logger.info("Reinitializing LightRAG storage...")
            rag_reinitialized = await self.rag_engine.initialize()
            
            # Verify clean state
            remaining_files = []
            for filename in lightrag_files:
                file_path = storage_dir / filename
                if file_path.exists():
                    remaining_files.append(filename)
            
            result = {
                "lightrag_files_cleared": cleared_files,
                "registry_cleared": registry_cleared,
                "rag_reinitialized": rag_reinitialized,
                "remaining_files": remaining_files,
                "storage_directory": str(storage_dir),
                "total_files_cleared": len(cleared_files)
            }
            
            if remaining_files:
                logger.warning(f"Some files still exist after reset: {remaining_files}")
                result["warning"] = f"Some files could not be cleared: {remaining_files}"
            else:
                logger.info("All LightRAG storage files cleared successfully")
            
            logger.info(f"Storage reset completed: {len(cleared_files)} files cleared")
            return result
            
        except Exception as e:
            logger.error(f"Storage reset failed: {e}")
            raise
    
    async def get_document_entities(self, document_id: str) -> EntitySummary:
        """
        Get extracted entities for a document
        
        Args:
            document_id: Document UUID
            
        Returns:
            EntitySummary with grouped entities
            
        Raises:
            DocumentNotFoundError: If document not found
            DocumentProcessingError: If entity extraction fails
        """
        try:
            # Verify document exists
            document = await self.get_document(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document {document_id} not found")
            
            # Initialize entity extraction service
            from core.config import get_settings
            settings = get_settings()
            storage_path = Path(settings.storage.working_dir)
            entity_service = EntityExtractionService(storage_path)
            
            # Extract entities
            entity_summary = entity_service.extract_document_entities(document_id)
            
            logger.info(f"Extracted entities for document {document_id}: "
                       f"{len(entity_summary.people)} people, "
                       f"{len(entity_summary.organizations)} organizations, "
                       f"{len(entity_summary.locations)} locations, "
                       f"{len(entity_summary.financial)} financial, "
                       f"{len(entity_summary.dates_and_terms)} dates/terms")
            
            return entity_summary
            
        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to extract entities for document {document_id}: {e}")
            raise DocumentProcessingError(f"Entity extraction failed: {e}")