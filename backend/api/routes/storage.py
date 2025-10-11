"""
Storage Management Routes
Storage operations, system management, and infrastructure endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
import logging

from domain.documents.service import DocumentService
from core.dependencies import get_document_service

router = APIRouter(prefix="/storage", tags=["storage"])
logger = logging.getLogger(__name__)


@router.post("/reset")
async def reset_storage(
    confirm: bool = False,
    service: DocumentService = Depends(get_document_service)
):
    """
    Reset all storage data - CLEARS EVERYTHING
    
    This endpoint will:
    - Clear all LightRAG storage files
    - Clear document registry
    - Reinitialize LightRAG storage
    - Return system to clean state
    
    Args:
        confirm: Must be True to proceed with deletion
        
    Returns:
        Reset confirmation with details
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=400, 
                detail="confirmation required - set confirm=True to proceed with storage reset"
            )
        
        logger.warning("Storage reset requested - clearing all data")
        
        # Call the storage reset method on the service
        result = await service.reset_storage()
        
        logger.info("Storage reset completed successfully")
        
        return {
            "success": True,
            "message": "Storage reset completed successfully",
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Storage reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
