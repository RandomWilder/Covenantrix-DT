"""
Google API Routes
OAuth and Drive integration endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import time
import asyncio
from datetime import datetime

from api.schemas.google import (
    GoogleAccountsListResponse,
    GoogleAccountResponse,
    AuthUrlResponse,
    OAuthCallbackRequest,
    DriveFilesListRequest,
    DriveFilesListResponse,
    DriveFileResponse,
    DriveDownloadRequest,
    DriveDownloadResponse,
    DriveDownloadResult,
    DriveFileStreamRequest,
    AccountRemoveResponse
)
from api.schemas.documents import (
    DocumentProgressStage,
    DocumentProgressEvent,
    BatchProgressEvent
)
from core.config import get_settings
from core.dependencies import get_oauth_service, get_google_api_service, get_document_service, get_subscription_service
from domain.integrations.google_oauth import GoogleOAuthService
from domain.integrations.exceptions import OAuthError
from domain.documents.service import DocumentService
from infrastructure.external.google_api import GoogleAPIService
from infrastructure.ai.document_processor import DocumentProcessor
from domain.integrations.ocr import OCRService
from core.dependencies import get_ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google", tags=["google"])


@router.get("/accounts", response_model=GoogleAccountsListResponse)
async def list_google_accounts(
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
) -> GoogleAccountsListResponse:
    """
    List connected Google accounts
    
    Returns:
        List of connected accounts
    """
    try:
        accounts = await oauth_service.list_accounts()
        
        account_responses = [
            GoogleAccountResponse(
                account_id=acc.id,
                email=acc.email,
                display_name=acc.name,
                status=acc.status.value,
                connected_at=acc.connected_at.isoformat(),
                last_used=acc.last_used.isoformat(),
                scopes=acc.credentials.scope if acc.credentials else []
            )
            for acc in accounts
        ]
        
        return GoogleAccountsListResponse(
            success=True,
            accounts=account_responses
        )
        
    except Exception as e:
        logger.error(f"Failed to list Google accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accounts/connect", response_model=AuthUrlResponse)
async def initiate_oauth(
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
) -> AuthUrlResponse:
    """
    Initiate OAuth flow
    
    Returns:
        Authorization URL for user to visit
    """
    try:
        auth_url = await oauth_service.get_authorization_url()
        
        return AuthUrlResponse(
            success=True,
            auth_url=auth_url,
            message="Visit the URL to authorize access"
        )
        
    except OAuthError as e:
        logger.error(f"OAuth initiation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during OAuth initiation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accounts/callback", response_model=GoogleAccountResponse)
async def handle_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter for CSRF validation"),
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
) -> GoogleAccountResponse:
    """
    Handle OAuth callback
    
    Args:
        code: Authorization code from Google
        state: State parameter for CSRF validation
        
    Returns:
        Connected account details
    """
    try:
        account = await oauth_service.handle_callback(code, state)
        
        return GoogleAccountResponse(
            account_id=account.id,
            email=account.email,
            display_name=account.name,
            status=account.status.value,
            connected_at=account.connected_at.isoformat(),
            last_used=account.last_used.isoformat()
        )
        
    except OAuthError as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/accounts/{account_id}", response_model=AccountRemoveResponse)
async def remove_google_account(
    account_id: str,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
) -> AccountRemoveResponse:
    """
    Remove Google account
    
    Args:
        account_id: Account ID to remove
        
    Returns:
        Removal confirmation
    """
    try:
        await oauth_service.revoke_account(account_id)
        
        return AccountRemoveResponse(
            success=True,
            message=f"Account {account_id} removed successfully"
        )
        
    except OAuthError as e:
        logger.error(f"Account removal failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during account removal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drive/files", response_model=DriveFilesListResponse)
async def list_drive_files(
    account_id: str = Query(..., description="Google account ID"),
    folder_id: Optional[str] = Query(None, description="Folder ID to list files from"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
    search_query: Optional[str] = Query(None, description="Search query"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of results"),
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
    api_service: GoogleAPIService = Depends(get_google_api_service)
) -> DriveFilesListResponse:
    """
    List files from Google Drive
    
    Args:
        account_id: Google account ID
        folder_id: Optional folder ID to list from
        mime_type: Optional MIME type filter
        search_query: Optional search query
        page_size: Number of results
        
    Returns:
        List of Drive files
    """
    try:
        # Get valid access token
        access_token = await oauth_service.ensure_valid_token(account_id)
        
        # List files
        files = await api_service.list_files(
            access_token=access_token,
            account_id=account_id,
            folder_id=folder_id,
            mime_type=mime_type,
            page_size=page_size,
            search_query=search_query
        )
        
        # Convert to response format
        file_responses = []
        for file_data in files:
            file_responses.append(DriveFileResponse(
                id=file_data["id"],
                name=file_data["name"],
                mimeType=file_data.get("mimeType", ""),
                size=file_data.get("size"),
                modifiedTime=file_data.get("modifiedTime", ""),
                webViewLink=file_data.get("webViewLink"),
                iconLink=file_data.get("iconLink")
            ))
        
        return DriveFilesListResponse(
            success=True,
            files=file_responses,
            account_id=account_id
        )
        
    except OAuthError as e:
        logger.error(f"OAuth error listing Drive files: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list Drive files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drive/download", response_model=DriveDownloadResponse)
async def download_drive_files(
    request: DriveDownloadRequest,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
    api_service: GoogleAPIService = Depends(get_google_api_service),
    document_service: DocumentService = Depends(get_document_service)
) -> DriveDownloadResponse:
    """
    Download files from Google Drive and process through upload pipeline
    
    Flow:
    1. Validate account exists and is active
    2. Download each file_id via api_service
    3. Pass bytes to document_service.upload_document()
    4. Return results with document IDs
    
    Args:
        request: Download request with account ID and file IDs
        
    Returns:
        Download results
    """
    try:
        # Get valid access token
        access_token = await oauth_service.ensure_valid_token(request.account_id)
        
        results = []
        
        for file_id in request.file_ids:
            try:
                # Get file metadata first
                metadata = await api_service.get_file_metadata(
                    access_token=access_token,
                    file_id=file_id,
                    account_id=request.account_id
                )
                
                filename = metadata.get("name", f"drive_file_{file_id}")
                logger.info(f"Downloading Drive file: {filename} ({file_id})")
                
                # Download file content
                content = await api_service.download_file(
                    access_token=access_token,
                    file_id=file_id,
                    account_id=request.account_id
                )
                
                # Process through document upload pipeline
                document = await document_service.upload_document(
                    file_content=content,
                    filename=filename
                )
                
                logger.info(f"Drive file uploaded successfully: {filename} -> {document.id}")
                
                results.append(DriveDownloadResult(
                    file_id=file_id,
                    success=True,
                    filename=filename,
                    document_id=document.id
                ))
                
            except Exception as e:
                logger.error(f"Failed to download/process file {file_id}: {e}")
                results.append(DriveDownloadResult(
                    file_id=file_id,
                    success=False,
                    error=str(e)
                ))
        
        # Check if any succeeded
        any_success = any(r.success for r in results)
        
        return DriveDownloadResponse(
            success=any_success,
            results=results,
            message=f"Downloaded {sum(1 for r in results if r.success)} of {len(results)} files"
        )
        
    except OAuthError as e:
        logger.error(f"OAuth error downloading files: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to download files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drive/download/stream")
async def download_drive_files_stream(
    request: DriveFileStreamRequest,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
    api_service: GoogleAPIService = Depends(get_google_api_service),
    document_service: DocumentService = Depends(get_document_service),
    ocr_service: Optional[OCRService] = Depends(get_ocr_service),
    subscription_service = Depends(get_subscription_service)
):
    """
    Download files from Google Drive with streaming progress updates
    
    Similar to /api/documents/upload/stream but for Drive files.
    Each file is downloaded from Drive then processed through document pipeline
    with real-time progress updates via Server-Sent Events.
    
    Args:
        request: Stream request with account ID and file IDs
        
    Returns:
        Server-Sent Events stream with progress updates
    """
    # Pre-operation global state check
    from core.dependencies import get_rag_engine
    if get_rag_engine() is None:
        logger.warning("Drive download blocked - no valid OpenAI API key configured")
        raise HTTPException(
            status_code=400,
            detail="No valid OpenAI API key configured. Please configure your API key in Settings to upload documents."
        )
    
    # Validate account and get access token before streaming
    try:
        access_token = await oauth_service.ensure_valid_token(request.account_id)
    except OAuthError as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    
    async def generate_progress_stream():
        """Generate SSE stream with progress updates"""
        try:
            total_files = len(request.file_ids)
            
            for file_index, file_id in enumerate(request.file_ids):
                try:
                    # Stage 1: Initializing (10%)
                    progress_event = DocumentProgressEvent(
                        filename=file_id,  # Temporary, will be updated
                        document_id=None,
                        stage=DocumentProgressStage.INITIALIZING,
                        message="Preparing to download from Drive...",
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
                    
                    # Get file metadata from Drive
                    metadata = await api_service.get_file_metadata(
                        access_token=access_token,
                        file_id=file_id,
                        account_id=request.account_id
                    )
                    filename = metadata.get("name", f"drive_file_{file_id}")
                    
                    # Stage 2: Downloading from Drive (25%)
                    progress_event = DocumentProgressEvent(
                        filename=filename,
                        document_id=None,
                        stage=DocumentProgressStage.READING,
                        message="Downloading from Google Drive...",
                        progress_percent=25,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    batch_event.file_progress = progress_event
                    yield f"data: {batch_event.model_dump_json()}\n\n"
                    
                    # Download file content
                    content = await api_service.download_file(
                        access_token=access_token,
                        file_id=file_id,
                        account_id=request.account_id
                    )
                    
                    # Upload document (creates DB record)
                    document = await document_service.upload_document(
                        file_content=content,
                        filename=filename
                    )
                    
                    # Stage 3: Understanding/Extracting text (40%)
                    progress_event = DocumentProgressEvent(
                        filename=filename,
                        document_id=document.id,
                        stage=DocumentProgressStage.UNDERSTANDING,
                        message=document_service.STAGE_MESSAGES["understanding"],
                        progress_percent=40,
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
                    
                    # Get OCR usage
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
                        document_service.process_document(
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
                            
                            # Get actual message from registry (includes rotating messages)
                            registry_data = await document_service.registry.get_document(document.id)
                            processing_data = registry_data.get('processing', {}) if registry_data else {}
                            actual_message = processing_data.get('message', document_service.STAGE_MESSAGES.get(event['stage'], "Processing..."))
                            
                            # Create progress event from service callback
                            progress_event = DocumentProgressEvent(
                                filename=filename,
                                document_id=document.id,
                                stage=DocumentProgressStage(event['stage']),
                                message=actual_message,
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
                            
                            # Get actual message from registry (includes rotating messages)
                            registry_data = await document_service.registry.get_document(document.id)
                            processing_data = registry_data.get('processing', {}) if registry_data else {}
                            actual_message = processing_data.get('message', document_service.STAGE_MESSAGES.get(event['stage'], "Processing..."))
                            
                            progress_event = DocumentProgressEvent(
                                filename=filename,
                                document_id=document.id,
                                stage=DocumentProgressStage(event['stage']),
                                message=actual_message,
                                progress_percent=event['percent'],
                                timestamp=datetime.utcnow().isoformat()
                            )
                            batch_event.file_progress = progress_event
                            batch_event.overall_progress_percent = int(((file_index + 1) / total_files) * 100)
                            yield f"data: {batch_event.model_dump_json()}\n\n"
                        except asyncio.QueueEmpty:
                            break
                    
                    # Enhanced document recording with tier and format context
                    file_extension = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
                    file_size_mb = len(content) / (1024 * 1024)  # Convert bytes to MB
                    current_subscription = await subscription_service.get_current_subscription_async()
                    await subscription_service.usage_tracker.record_document_upload(
                        doc_id=document.id,
                        size_mb=file_size_mb,
                        tier_at_upload=current_subscription.tier,
                        format=file_extension
                    )
                    
                    logger.info(f"Drive file downloaded and processed: {filename} -> {document.id}")
                    
                except Exception as e:
                    logger.error(f"Drive file processing failed for {file_id}: {e}")
                    
                    # Emit failure event
                    progress_event = DocumentProgressEvent(
                        filename=filename if 'filename' in locals() else file_id,
                        document_id=None,
                        stage=DocumentProgressStage.FAILED,
                        message="Processing failed",
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
            logger.error(f"Streaming Drive download failed: {e}")
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

