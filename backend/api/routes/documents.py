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
from core.dependencies import get_document_service, get_ocr_service
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
    service: DocumentService = Depends(get_document_service),
    ocr_service: Optional[OCRService] = Depends(get_ocr_service)
) -> DocumentUploadResponse:
    """
    Upload a document for processing
    
    Args:
        file: File to upload
        service: Document service
        
    Returns:
        Upload confirmation with document ID
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset for potential re-reading
        
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
    for file_index, file in enumerate(files):
        filename = file.filename or f"file_{file_index}"
        content = await file.read()
        file_contents.append(content)
        filenames.append(filename)
    
    async def generate_progress_stream():
        """Generate SSE stream with progress updates"""
        try:
            total_files = len(file_contents)
            
            for file_index, (content, filename) in enumerate(zip(file_contents, filenames)):
                try:
                    # Stage 1: Initializing (10%)
                    progress_event = DocumentProgressEvent(
                        filename=filename,
                        document_id=None,
                        stage=DocumentProgressStage.INITIALIZING,
                        message=service.STAGE_MESSAGES["initializing"],
                        progress_percent=10,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    batch_event = BatchProgressEvent(
                        total_files=total_files,
                        current_file_index=file_index,
                        file_progress=progress_event,
                        overall_progress_percent=int((file_index / total_files) * 100)
                    )
                    yield f"data: {batch_event.model_dump_json()}\n\n"
                    
                    # Upload document
                    document = await service.upload_document(
                        file_content=content,
                        filename=filename
                    )
                    
                    # Stage 2: Reading (with OCR if needed)
                    progress_event = DocumentProgressEvent(
                        filename=filename,
                        document_id=document.id,
                        stage=DocumentProgressStage.READING,
                        message=service.STAGE_MESSAGES["reading"],
                        progress_percent=25,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    batch_event.file_progress = progress_event
                    yield f"data: {batch_event.model_dump_json()}\n\n"
                    
                    # Extract text
                    processor = DocumentProcessor(ocr_service=ocr_service)
                    start_time = time.time()
                    extracted_text = await processor.extract_text(content, filename)
                    
                    # Validate content
                    if not processor.validate_content(extracted_text):
                        raise ValueError("Extracted content quality is too low")
                    
                    # Get OCR usage from processor
                    ocr_used = processor.ocr_used
                    
                    # Create progress queue for streaming updates from service
                    progress_queue = asyncio.Queue()
                    
                    async def queue_callback(stage: str, percent: int):
                        """Callback that puts progress events into queue"""
                        await progress_queue.put({
                            'stage': stage,
                            'percent': percent
                        })
                    
                    # Run processing in background task
                    process_task = asyncio.create_task(
                        service.process_document(
                            document_id=document.id,
                            extracted_content=extracted_text,
                            processing_time=time.time() - start_time,
                            ocr_applied=ocr_used,
                            progress_callback=queue_callback
                        )
                    )
                    
                    # Yield progress events from queue until processing completes
                    while not process_task.done():
                        try:
                            event = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                            
                            # Create progress event from service callback
                            progress_event = DocumentProgressEvent(
                                filename=filename,
                                document_id=document.id,
                                stage=DocumentProgressStage(event['stage']),
                                message=service.STAGE_MESSAGES.get(event['stage'], "Processing..."),
                                progress_percent=event['percent'],
                                timestamp=datetime.utcnow().isoformat()
                            )
                            
                            # Calculate overall progress
                            file_progress = (file_index + (event['percent'] / 100)) / total_files
                            batch_event.file_progress = progress_event
                            batch_event.overall_progress_percent = int(file_progress * 100)
                            
                            yield f"data: {batch_event.model_dump_json()}\n\n"
                            
                        except asyncio.TimeoutError:
                            continue
                    
                    # Wait for task completion and check for exceptions
                    await process_task
                    
                    # Drain remaining events from queue
                    while not progress_queue.empty():
                        try:
                            event = progress_queue.get_nowait()
                            progress_event = DocumentProgressEvent(
                                filename=filename,
                                document_id=document.id,
                                stage=DocumentProgressStage(event['stage']),
                                message=service.STAGE_MESSAGES.get(event['stage'], "Processing..."),
                                progress_percent=event['percent'],
                                timestamp=datetime.utcnow().isoformat()
                            )
                            batch_event.file_progress = progress_event
                            batch_event.overall_progress_percent = int(((file_index + 1) / total_files) * 100)
                            yield f"data: {batch_event.model_dump_json()}\n\n"
                        except asyncio.QueueEmpty:
                            break
                    
                    logger.info(f"Document uploaded and processed: {document.id}")
                    
                except Exception as e:
                    logger.error(f"Document processing failed for {filename}: {e}")
                    
                    # Emit failure event
                    progress_event = DocumentProgressEvent(
                        filename=filename,
                        document_id=None,
                        stage=DocumentProgressStage.FAILED,
                        message=service.STAGE_MESSAGES["failed"],
                        progress_percent=0,
                        timestamp=datetime.utcnow().isoformat(),
                        error=str(e)
                    )
                    batch_event = BatchProgressEvent(
                        total_files=total_files,
                        current_file_index=file_index,
                        file_progress=progress_event,
                        overall_progress_percent=int(((file_index + 1) / total_files) * 100)
                    )
                    yield f"data: {batch_event.model_dump_json()}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming upload failed: {e}")
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
        documents = await service.list_documents(include_deleted)
        
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
    service: DocumentService = Depends(get_document_service)
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