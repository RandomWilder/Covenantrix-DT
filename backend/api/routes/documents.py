"""
Document Management Routes
Upload, list, query, and delete documents
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Optional
import logging
import json
import time
import asyncio
from datetime import datetime

from domain.integrations.ocr import OCRService

from domain.documents.service import DocumentService
from domain.documents.models import Document
from infrastructure.ai.document_processor import DocumentProcessor
from infrastructure.storage.file_storage import FileStorage
from core.dependencies import get_document_service, get_subscription_aware_document_service, get_ocr_service, get_subscription_service
from api.schemas.documents import (
    DocumentResponse, DocumentListResponse, DocumentUploadResponse,
    BatchUploadResponse, BatchUploadItem, GoogleDriveFileRequest,
    GoogleDriveListResponse, GoogleDriveFileInfo, DocumentEntitiesResponse,
    DocumentProgressStage, DocumentProgressEvent, BatchProgressEvent
)

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_subscription_aware_document_service),
    ocr_service: Optional[OCRService] = Depends(get_ocr_service),
    subscription_service = Depends(get_subscription_service)
) -> DocumentUploadResponse:
    """
    Upload a document for processing
    
    Args:
        file: File to upload
        service: Document service
        
    Returns:
        Upload confirmation with document ID
    """
    # Check subscription upload limits
    try:
        allowed, reason = await subscription_service.check_upload_allowed()
        if not allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Upload limit exceeded: {reason}"
            )
    except Exception as e:
        logger.error(f"Subscription check failed: {e}")
        # Continue if subscription service is unavailable
    
    # Pre-operation global state check (DO NOT re-resolve keys)
    from core.dependencies import get_rag_engine
    if get_rag_engine() is None:
        logger.warning("Document upload blocked - no valid OpenAI API key configured")
        raise HTTPException(
            status_code=400,
            detail="No valid OpenAI API key configured. Please configure your API key in Settings to upload documents."
        )
    
    # NEW: Check subscription limits
    from core.dependencies import get_subscription_service
    subscription_service = get_subscription_service()
    
    can_upload, reason = await subscription_service.check_upload_allowed()
    if not can_upload:
        current_subscription = await subscription_service.get_current_subscription_async()
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "upload_limit_reached",
                "message": reason,
                "current_tier": current_subscription.tier,
                "upgrade_required": True
            }
        )
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset for potential re-reading
        
        # NEW: Check file size against tier limit
        file_size_mb = len(content) / (1024 * 1024)
        tier_limits = await subscription_service.get_current_limits_async()
        current_subscription = await subscription_service.get_current_subscription_async()
        
        if file_size_mb > tier_limits["max_doc_size_mb"]:
            raise HTTPException(
                status_code=413,  # Payload Too Large
                detail={
                    "error": "file_too_large",
                    "file_size_mb": round(file_size_mb, 2),
                    "max_size_mb": tier_limits["max_doc_size_mb"],
                    "current_tier": current_subscription.tier
                }
            )
        
        # Create document
        document = await service.upload_document(
            file_content=content,
            filename=file.filename
        )
        
        # Extract text
        processor = DocumentProcessor(ocr_service=ocr_service)
        extracted_text = await processor.extract_text(
            content,
            file.filename
        )
        
        # Validate content
        if not processor.validate_content(extracted_text):
            raise HTTPException(
                status_code=422,
                detail="Extracted content quality is too low"
            )
        
        # Process document
        import time
        start_time = time.time()
        
        await service.process_document(
            document_id=document.id,
            extracted_content=extracted_text,
            processing_time=time.time() - start_time
        )
        
        # Enhanced document recording with tier and format context
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
        await subscription_service.usage_tracker.record_document_upload(
            doc_id=document.id,
            size_mb=file_size_mb,
            tier_at_upload=current_subscription.tier,
            format=file_extension
        )
        
        logger.info(f"Document uploaded and processed: {document.id}")
        
        return DocumentUploadResponse(
            success=True,
            document_id=document.id,
            filename=file.filename,
            message="Document uploaded and processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/stream")
async def upload_documents_stream(
    files: List[UploadFile] = File(...),
    service: DocumentService = Depends(get_document_service),
    ocr_service: Optional[OCRService] = Depends(get_ocr_service)
):
    """
    Upload multiple documents with real-time progress streaming
    
    Args:
        files: List of files to upload
        service: Document service
        ocr_service: Optional OCR service
        
    Returns:
        Server-Sent Events stream with progress updates
    """
    # Pre-operation global state check (DO NOT re-resolve keys)
    from core.dependencies import get_rag_engine
    if get_rag_engine() is None:
        logger.warning("Batch document upload blocked - no valid OpenAI API key configured")
        raise HTTPException(
            status_code=400,
            detail="No valid OpenAI API key configured. Please configure your API key in Settings to upload documents."
        )
    
    # NEW: Get subscription service for limit checks
    from core.dependencies import get_subscription_service
    subscription_service = get_subscription_service()
    current_subscription = await subscription_service.get_current_subscription_async()
    tier_limits = await subscription_service.get_current_limits_async()
    
    # CRITICAL: Read all file contents BEFORE creating the generator
    # FastAPI closes UploadFile objects when the route function returns,
    # so we must read them before returning StreamingResponse
    if not files:
        async def error_stream():
            error_event = {"error": "No files provided"}
            yield f"data: {json.dumps(error_event)}\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    # Read all file contents into memory before streaming
    file_contents = []
    filenames = []
    file_sizes_mb = []
    for file_index, file in enumerate(files):
        filename = file.filename or f"file_{file_index}"
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        # NEW: Check file size against tier limit
        if file_size_mb > tier_limits["max_doc_size_mb"]:
            raise HTTPException(
                status_code=413,  # Payload Too Large
                detail={
                    "error": "file_too_large",
                    "filename": filename,
                    "file_size_mb": round(file_size_mb, 2),
                    "max_size_mb": tier_limits["max_doc_size_mb"],
                    "current_tier": current_subscription.tier
                }
            )
        
        file_contents.append(content)
        filenames.append(filename)
        file_sizes_mb.append(file_size_mb)
    
    async def generate_progress_stream():
        """Generate SSE stream with PARALLEL processing and isolated failure handling"""
        try:
            total_files = len(file_contents)
            completed_files = 0
            successful_files = 0
            failed_files = 0
            
            # Shared queue for all progress events from parallel tasks
            shared_progress_queue = asyncio.Queue()
            
            # Semaphore to limit concurrent document processing (max 2)
            # This controls upload + text extraction parallelism
            processing_semaphore = asyncio.Semaphore(2)
            
            # CRITICAL: Semaphore for RAG engine operations (max 1)
            # LightRAG has internal queueing that returns immediately when a document is queued
            # We MUST ensure only ONE document enters RAG at a time to avoid state inconsistencies
            rag_insert_semaphore = asyncio.Semaphore(1)
            
            # Track document results
            document_results = {}
            
            async def process_single_document(file_index: int, content: bytes, filename: str, file_size_mb: float):
                """Process a single document with isolated error handling and timeout"""
                nonlocal completed_files, successful_files, failed_files
                
                async with processing_semaphore:
                    document_id = None
                    try:
                        # Check if upload is allowed for this document
                        can_upload, reason = await subscription_service.check_upload_allowed()
                        if not can_upload:
                            # Put failure event in shared queue
                            await shared_progress_queue.put({
                                'type': 'progress',
                                'file_index': file_index,
                                'filename': filename,
                                'document_id': None,
                                'stage': DocumentProgressStage.FAILED,
                                'message': reason,
                                'percent': 0,
                                'error': reason
                            })
                            document_results[file_index] = {'success': False, 'error': reason}
                            return
                        
                        # Stage 1: Initializing (10%)
                        await shared_progress_queue.put({
                            'type': 'progress',
                            'file_index': file_index,
                            'filename': filename,
                            'document_id': None,
                            'stage': DocumentProgressStage.INITIALIZING,
                            'message': service.STAGE_MESSAGES["initializing"],
                            'percent': 10
                        })
                        
                        # Upload document
                        document = await service.upload_document(
                            file_content=content,
                            filename=filename
                        )
                        document_id = document.id
                        
                        # Stage 2: Reading (25%)
                        await shared_progress_queue.put({
                            'type': 'progress',
                            'file_index': file_index,
                            'filename': filename,
                            'document_id': document_id,
                            'stage': DocumentProgressStage.READING,
                            'message': service.STAGE_MESSAGES["reading"],
                            'percent': 25
                        })
                        
                        # Extract text
                        processor = DocumentProcessor(ocr_service=ocr_service)
                        start_time = time.time()
                        extracted_text = await processor.extract_text(content, filename)
                        
                        # Validate content
                        if not processor.validate_content(extracted_text):
                            raise ValueError("Extracted content quality is too low")
                        
                        ocr_used = processor.ocr_used
                        
                        # Progress tracking for smart timeout
                        last_progress_time = {'time': time.time()}
                        
                        # Create document-specific progress callback
                        async def document_progress_callback(stage: str, percent: int):
                            """Forward progress to shared queue with document context"""
                            # Update last progress time - this resets the timeout
                            last_progress_time['time'] = time.time()
                            
                            # Get actual message from registry (includes rotating messages)
                            registry_data = await service.registry.get_document(document_id)
                            processing_data = registry_data.get('processing', {}) if registry_data else {}
                            actual_message = processing_data.get('message', service.STAGE_MESSAGES.get(stage, "Processing..."))
                            
                            await shared_progress_queue.put({
                                'type': 'progress',
                                'file_index': file_index,
                                'filename': filename,
                                'document_id': document_id,
                                'stage': DocumentProgressStage(stage),
                                'message': actual_message,
                                'percent': percent
                            })
                        
                        # CRITICAL: Acquire RAG semaphore before processing
                        # This ensures only ONE document at a time enters LightRAG
                        # Prevents "Request queued" race condition where ainsert() returns immediately
                        async with rag_insert_semaphore:
                            # SMART TIMEOUT: Only timeout if no progress for 5 minutes
                            # This allows large documents (300+ pages) to process without time limits
                            # as long as they're making progress (chunks being extracted)
                            try:
                                # Create the processing task
                                processing_task = asyncio.create_task(
                                    service.process_document(
                                        document_id=document_id,
                                        extracted_content=extracted_text,
                                        processing_time=time.time() - start_time,
                                        ocr_applied=ocr_used,
                                        progress_callback=document_progress_callback
                                    )
                                )
                                
                                # Monitor task with progress-based timeout
                                inactivity_timeout = 300.0  # 5 minutes of no progress = stuck
                                check_interval = 10.0  # Check every 10 seconds
                                
                                while not processing_task.done():
                                    try:
                                        # Wait for task completion, but check periodically
                                        await asyncio.wait_for(
                                            asyncio.shield(processing_task),
                                            timeout=check_interval
                                        )
                                    except asyncio.TimeoutError:
                                        # Check interval expired, verify progress
                                        time_since_progress = time.time() - last_progress_time['time']
                                        
                                        if time_since_progress > inactivity_timeout:
                                            # No progress for 5 minutes - process is stuck
                                            processing_task.cancel()
                                            raise asyncio.TimeoutError(
                                                f"No progress for {inactivity_timeout}s - process appears stuck"
                                            )
                                        # else: Progress detected, continue monitoring
                                
                                # Task completed successfully, get result
                                await processing_task
                            
                                # Enhanced document recording with tier and format context
                                file_extension = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
                                await subscription_service.usage_tracker.record_document_upload(
                                    doc_id=document_id,
                                    size_mb=file_size_mb,
                                    tier_at_upload=current_subscription.tier,
                                    format=file_extension
                                )
                                
                                # Success!
                                document_results[file_index] = {
                                    'success': True,
                                    'document_id': document_id,
                                    'filename': filename
                                }
                                successful_files += 1
                                logger.info(f"Document uploaded and processed: {document_id} ({filename})")
                                
                            except asyncio.TimeoutError as e:
                                # Document-level timeout - mark as failed but continue with others
                                error_msg = "Processing stalled - no progress detected for 5 minutes. The process may be stuck."
                                logger.warning(f"Document processing timeout (inactivity) for {filename} ({document_id}): {str(e)}")
                                
                                # Mark document as failed in registry
                                await service.registry.update_status(
                                    document_id=document_id,
                                    status="failed",
                                    processing_info={'error': error_msg}
                                )
                                
                                await shared_progress_queue.put({
                                    'type': 'progress',
                                    'file_index': file_index,
                                    'filename': filename,
                                    'document_id': document_id,
                                    'stage': DocumentProgressStage.FAILED,
                                    'message': service.STAGE_MESSAGES["failed"],
                                    'percent': 0,
                                    'error': error_msg
                                })
                                
                                document_results[file_index] = {
                                    'success': False,
                                    'error': error_msg,
                                    'filename': filename
                                }
                                failed_files += 1
                        
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"Document processing failed for {filename}: {error_msg}")
                        
                        # If document was created, mark as failed
                        if document_id:
                            try:
                                await service.registry.update_status(
                                    document_id=document_id,
                                    status="failed",
                                    processing_info={'error': error_msg}
                                )
                            except:
                                pass  # Registry update failed, continue
                        
                        # Emit failure event
                        await shared_progress_queue.put({
                            'type': 'progress',
                            'file_index': file_index,
                            'filename': filename,
                            'document_id': document_id,
                            'stage': DocumentProgressStage.FAILED,
                            'message': service.STAGE_MESSAGES["failed"],
                            'percent': 0,
                            'error': error_msg
                        })
                        
                        document_results[file_index] = {
                            'success': False,
                            'error': error_msg,
                            'filename': filename
                        }
                        failed_files += 1
                    
                    finally:
                        completed_files += 1
                        # Signal completion for this document
                        await shared_progress_queue.put({
                            'type': 'document_complete',
                            'file_index': file_index,
                            'filename': filename
                        })
            
            # Create tasks for ALL documents (they'll process in parallel up to semaphore limit)
            processing_tasks = []
            for file_index, (content, filename, file_size_mb) in enumerate(zip(file_contents, filenames, file_sizes_mb)):
                task = asyncio.create_task(
                    process_single_document(file_index, content, filename, file_size_mb)
                )
                processing_tasks.append(task)
            
            # Monitor progress and yield events as they arrive
            while completed_files < total_files:
                try:
                    # Wait for next progress event (with timeout to check completion status)
                    event = await asyncio.wait_for(shared_progress_queue.get(), timeout=0.5)
                    
                    if event['type'] == 'progress':
                        # Create and yield progress event
                        progress_event = DocumentProgressEvent(
                            filename=event['filename'],
                            document_id=event.get('document_id'),
                            stage=event['stage'],
                            message=event['message'],
                            progress_percent=event['percent'],
                            timestamp=datetime.utcnow().isoformat(),
                            error=event.get('error')
                        )
                        
                        # Calculate overall progress based on completed files
                        overall_progress = int((completed_files / total_files) * 100)
                        
                        batch_event = BatchProgressEvent(
                            total_files=total_files,
                            current_file_index=event['file_index'],
                            file_progress=progress_event,
                            overall_progress_percent=overall_progress
                        )
                        
                        yield f"data: {batch_event.model_dump_json()}\n\n"
                    
                    elif event['type'] == 'document_complete':
                        # Document completed, update overall progress
                        overall_progress = int((completed_files / total_files) * 100)
                        logger.debug(f"Document {event['file_index']}/{total_files} completed. Overall: {overall_progress}%")
                
                except asyncio.TimeoutError:
                    # No events in queue, just continue checking
                    continue
            
            # Wait for all tasks to complete (should already be done)
            await asyncio.gather(*processing_tasks, return_exceptions=True)
            
            # Emit final summary
            summary = {
                'type': 'batch_complete',
                'total_files': total_files,
                'successful': successful_files,
                'failed': failed_files,
                'timestamp': datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(summary)}\n\n"
            
            logger.info(f"Batch upload completed: {successful_files}/{total_files} successful, {failed_files} failed")
            
        except Exception as e:
            logger.error(f"Streaming upload failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            error_event = {
                "error": "Internal server error",
                "detail": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    include_deleted: bool = False,
    service: DocumentService = Depends(get_document_service)
) -> DocumentListResponse:
    """
    List all documents
    
    Args:
        include_deleted: Include soft-deleted documents
        service: Document service
        
    Returns:
        List of documents
    """
    try:
        # NEW: Apply tier-based visibility filtering
        from core.dependencies import get_subscription_service
        subscription_service = get_subscription_service()
        current_subscription = await subscription_service.get_current_subscription_async()
        current_tier = current_subscription.tier
        
        documents = await service.list_documents(
            include_deleted=include_deleted,
            subscription_tier=current_tier
        )
        
        return DocumentListResponse(
            success=True,
            documents=[doc.to_dict() for doc in documents],
            total_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"List documents failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """
    Get document by ID
    
    Args:
        document_id: Document identifier
        service: Document service
        
    Returns:
        Document details
    """
    try:
        document = await service.get_document(document_id)
        
        return DocumentResponse(
            success=True,
            document=document.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Get document failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    hard_delete: bool = False,
    service: DocumentService = Depends(get_document_service)
):
    """
    Delete document
    
    Args:
        document_id: Document to delete
        hard_delete: Permanently delete vs soft delete
        service: Document service
        
    Returns:
        Deletion confirmation
    """
    try:
        await service.delete_document(document_id, hard_delete)
        
        return {
            "success": True,
            "document_id": document_id,
            "message": "Document deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Delete document failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_documents_batch(
    files: List[UploadFile] = File(...),
    service: DocumentService = Depends(get_document_service),
    ocr_service: Optional[OCRService] = Depends(get_ocr_service)
) -> BatchUploadResponse:
    """
    Upload multiple documents for processing
    
    Args:
        files: List of files to upload
        service: Document service
        
    Returns:
        Batch upload results with individual file status
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
        
        # Read file contents
        file_contents = []
        filenames = []
        
        for file in files:
            if not file.filename:
                continue
                
            content = await file.read()
            await file.seek(0)  # Reset for potential re-reading
            
            file_contents.append(content)  # Store the actual content bytes
            filenames.append(file.filename)
        
        # Process batch upload
        results = await service.upload_documents_batch(
            files=file_contents,
            filenames=filenames,
            max_concurrent=3
        )
        
        # Process each uploaded document through the pipeline
        processor = DocumentProcessor(ocr_service=ocr_service)
        for i, result in enumerate(results):
            if result["success"]:
                try:
                    # Get file content (already read as bytes)
                    file_content = file_contents[i]
                    
                    # Extract text
                    extracted_text = await processor.extract_text(
                        file_content,
                        filenames[i]
                    )
                    
                    # Validate content
                    if processor.validate_content(extracted_text):
                        # Process document through RAG
                        import time
                        start_time = time.time()
                        
                        await service.process_document(
                            document_id=result["document_id"],
                            extracted_content=extracted_text,
                            processing_time=time.time() - start_time
                        )
                        
                        logger.info(f"Document processed successfully: {result['document_id']}")
                    else:
                        logger.warning(f"Document content quality too low: {result['document_id']}")
                        result["error"] = "Content quality too low for processing"
                        result["success"] = False
                        
                except Exception as e:
                    logger.error(f"Document processing failed for {result['document_id']}: {e}")
                    result["error"] = f"Processing failed: {str(e)}"
                    result["success"] = False
        
        # Convert to response format
        batch_items = [
            BatchUploadItem(
                filename=result["filename"],
                document_id=result["document_id"],
                success=result["success"],
                error=result["error"],
                file_size=result["file_size"]
            )
            for result in results
        ]
        
        successful_uploads = sum(1 for item in batch_items if item.success)
        failed_uploads = len(batch_items) - successful_uploads
        
        return BatchUploadResponse(
            success=failed_uploads == 0,
            total_files=len(batch_items),
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            results=batch_items,
            message=f"Processed {len(batch_items)} files: {successful_uploads} successful, {failed_uploads} failed"
        )
        
    except Exception as e:
        logger.error(f"Batch upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/drive", response_model=BatchUploadResponse)
async def upload_from_google_drive(
    request: GoogleDriveFileRequest,
    service: DocumentService = Depends(get_document_service),
    subscription_service = Depends(get_subscription_service)
) -> BatchUploadResponse:
    """
    Download and process files from Google Drive
    
    Args:
        request: Google Drive file selection request
        service: Document service
        
    Returns:
        Batch upload results for downloaded files
    """
    try:
        # Import Google Drive service
        from domain.integrations.google_drive import GoogleDriveService
        
        drive_service = GoogleDriveService()
        
        # Download files from Google Drive
        downloaded_files = []
        filenames = []
        
        for file_id in request.file_ids:
            try:
                file_content, filename = await drive_service.download_file(file_id)
                downloaded_files.append(file_content)
                filenames.append(filename)
            except Exception as e:
                logger.error(f"Failed to download Google Drive file {file_id}: {e}")
                # Continue with other files
                continue
        
        if not downloaded_files:
            raise HTTPException(status_code=400, detail="No files could be downloaded from Google Drive")
        
        # Process downloaded files
        results = await service.upload_documents_batch(
            files=downloaded_files,
            filenames=filenames,
            max_concurrent=3
        )
        
        # Record usage for successful uploads
        current_subscription = await subscription_service.get_current_subscription_async()
        for result in results:
            if result["success"] and result["document_id"]:
                file_extension = result["filename"].split('.')[-1].lower() if '.' in result["filename"] else 'unknown'
                file_size_mb = result["file_size"] / (1024 * 1024) if result["file_size"] else 0
                await subscription_service.usage_tracker.record_document_upload(
                    doc_id=result["document_id"],
                    size_mb=file_size_mb,
                    tier_at_upload=current_subscription.tier,
                    format=file_extension
                )
        
        # Convert to response format
        batch_items = [
            BatchUploadItem(
                filename=result["filename"],
                document_id=result["document_id"],
                success=result["success"],
                error=result["error"],
                file_size=result["file_size"]
            )
            for result in results
        ]
        
        successful_uploads = sum(1 for item in batch_items if item.success)
        failed_uploads = len(batch_items) - successful_uploads
        
        return BatchUploadResponse(
            success=failed_uploads == 0,
            total_files=len(batch_items),
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            results=batch_items,
            message=f"Downloaded and processed {len(batch_items)} files from Google Drive: {successful_uploads} successful, {failed_uploads} failed"
        )
        
    except Exception as e:
        logger.error(f"Google Drive upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drive/files", response_model=GoogleDriveListResponse)
async def list_google_drive_files(
    folder_id: Optional[str] = None,
    page_token: Optional[str] = None
) -> GoogleDriveListResponse:
    """
    List files from Google Drive
    
    Args:
        folder_id: Optional folder ID to list files from
        page_token: Optional pagination token
        
    Returns:
        List of Google Drive files
    """
    try:
        from domain.integrations.google_drive import GoogleDriveService
        
        drive_service = GoogleDriveService()
        files, next_token = await drive_service.list_files(
            folder_id=folder_id,
            page_token=page_token
        )
        
        # Convert to response format
        file_infos = [
            GoogleDriveFileInfo(
                file_id=file["id"],
                name=file["name"],
                mime_type=file["mimeType"],
                size=file.get("size"),
                modified_time=file.get("modifiedTime"),
                web_view_link=file.get("webViewLink")
            )
            for file in files
        ]
        
        return GoogleDriveListResponse(
            success=True,
            files=file_infos,
            next_page_token=next_token
        )
        
    except Exception as e:
        logger.error(f"Google Drive file listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/entities", response_model=DocumentEntitiesResponse)
async def get_document_entities(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
) -> DocumentEntitiesResponse:
    """
    Get extracted entities for a document
    
    Args:
        document_id: Document UUID
        service: Document service
        
    Returns:
        Document entities with grouped summary
    """
    try:
        # Get document entities using the service
        domain_entity_summary = await service.get_document_entities(document_id)
        
        # Get document name for response
        document = await service.get_document(document_id)
        document_name = document.metadata.filename if document else "Unknown Document"
        
        # Convert domain EntitySummary to API EntitySummary
        from api.schemas.documents import EntitySummary as APIEntitySummary, EntityInfo as APIEntityInfo
        
        api_entity_summary = APIEntitySummary(
            people=[APIEntityInfo(name=entity.name, description=entity.description) for entity in domain_entity_summary.people],
            organizations=[APIEntityInfo(name=entity.name, description=entity.description) for entity in domain_entity_summary.organizations],
            locations=[APIEntityInfo(name=entity.name, description=entity.description) for entity in domain_entity_summary.locations],
            financial=[APIEntityInfo(name=entity.name, description=entity.description) for entity in domain_entity_summary.financial],
            dates_and_terms=[APIEntityInfo(name=entity.name, description=entity.description) for entity in domain_entity_summary.dates_and_terms]
        )
        
        return DocumentEntitiesResponse(
            document_id=document_id,
            document_name=document_name,
            entity_summary=api_entity_summary
        )
        
    except Exception as e:
        logger.error(f"Failed to get document entities for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))