"""
OCR Service
Business logic for Optical Character Recognition
"""
import logging
from typing import Optional, BinaryIO
import time

from domain.integrations.models import OCRResult
from domain.integrations.exceptions import OCRError

logger = logging.getLogger(__name__)

# Try to import Google Vision OCR
try:
    from infrastructure.external.google_vision_ocr import GoogleVisionOCR
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    logger.warning("Google Vision OCR not available - install google-cloud-vision")


class OCRService:
    """
    OCR service
    Handles optical character recognition for images and scanned documents
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = ['png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp']
    
    def __init__(self, api_key: Optional[str] = None, user_settings: Optional[dict] = None):
        """
        Initialize OCR service
        
        Args:
            api_key: Google Vision API key (optional)
            user_settings: User settings for configuration
        """
        self.api_key = api_key
        self.user_settings = user_settings or {}
        
        # Initialize Google Vision OCR if available
        self.google_vision_ocr = None
        if GOOGLE_VISION_AVAILABLE and api_key:
            try:
                self.google_vision_ocr = GoogleVisionOCR(
                    api_key=api_key,
                    min_confidence=self.user_settings.get("ocr_min_confidence", 0.3),
                    min_char_count=self.user_settings.get("ocr_min_char_count", 5),
                    preferred_language=self.user_settings.get("preferred_language", None)  # None = auto-detect
                )
                logger.info("Google Vision OCR initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Vision OCR: {e}")
                self.google_vision_ocr = None
        else:
            if not GOOGLE_VISION_AVAILABLE:
                logger.warning("Google Vision OCR not available - install google-cloud-vision")
            if not api_key:
                logger.warning("Google Vision API key not provided")
        
        # Apply settings
        self._apply_settings()
    
    @property
    def is_available(self) -> bool:
        """Check if OCR service is available"""
        return self.google_vision_ocr is not None
    
    def validate_image_format(self, filename: str) -> bool:
        """
        Validate image format
        
        Args:
            filename: Image filename
            
        Returns:
            True if supported
        """
        extension = filename.lower().split('.')[-1]
        return extension in self.SUPPORTED_FORMATS
    
    def is_image_file(self, mime_type: str) -> bool:
        """
        Check if MIME type is an image
        
        Args:
            mime_type: File MIME type
            
        Returns:
            True if image
        """
        return mime_type.startswith('image/')
    
    def estimate_processing_time(self, file_size_mb: float) -> float:
        """
        Estimate OCR processing time
        
        Args:
            file_size_mb: File size in MB
            
        Returns:
            Estimated time in seconds
        """
        # Rough estimate: ~2 seconds per MB
        return max(2.0, file_size_mb * 2.0)
    
    def create_ocr_result(
        self,
        text: str,
        confidence: float,
        language: Optional[str],
        page_count: int,
        processing_time: float
    ) -> OCRResult:
        """
        Create OCR result object
        
        Args:
            text: Extracted text
            confidence: Confidence score (0-1)
            language: Detected language
            page_count: Number of pages processed
            processing_time: Processing time in seconds
            
        Returns:
            OCR result
        """
        result = OCRResult(
            text=text,
            confidence=confidence,
            language=language,
            page_count=page_count,
            processing_time=processing_time
        )
        
        logger.info(
            f"OCR completed: {len(text)} chars, "
            f"confidence: {confidence:.2f}, "
            f"time: {processing_time:.2f}s"
        )
        
        return result
    
    def validate_ocr_quality(
        self,
        result: OCRResult,
        min_confidence: float = 0.6,
        min_char_count: int = 50
    ) -> tuple[bool, Optional[str]]:
        """
        Validate OCR result quality
        
        Args:
            result: OCR result
            min_confidence: Minimum confidence threshold
            min_char_count: Minimum character count
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if result.confidence < min_confidence:
            return False, f"Low confidence: {result.confidence:.2f} < {min_confidence}"
        
        if len(result.text) < min_char_count:
            return False, f"Text too short: {len(result.text)} < {min_char_count}"
        
        # Check if text is mostly gibberish (very basic check)
        if self._is_gibberish(result.text):
            return False, "Text appears to be gibberish"
        
        return True, None
    
    def _is_gibberish(self, text: str) -> bool:
        """
        Basic check for gibberish text
        
        Args:
            text: Text to check
            
        Returns:
            True if likely gibberish
        """
        if len(text) < 50:
            return False
        
        # Check ratio of letters to total characters
        letters = sum(c.isalpha() for c in text)
        ratio = letters / len(text)
        
        # If less than 50% letters, likely gibberish or corrupted
        return ratio < 0.5
    
    def _apply_settings(self) -> None:
        """Apply user settings to OCR service"""
        try:
            # Apply RAG settings for OCR enablement
            rag_settings = self.user_settings.get("rag", {})
            self.enable_ocr = rag_settings.get("enable_ocr", True)
            
            # Apply language settings - use None for auto-detection unless explicitly set
            language_settings = self.user_settings.get("language", {})
            self.preferred_language = language_settings.get("preferred", None)
            
            # Apply API key settings if in custom mode
            api_keys = self.user_settings.get("api_keys", {})
            if api_keys.get("mode") == "custom" and api_keys.get("google"):
                self.api_key = api_keys["google"]
                self.is_available = bool(self.api_key)
            
            logger.info(f"OCR settings applied: enabled={self.enable_ocr}, language={self.preferred_language}")
            
        except Exception as e:
            logger.error(f"Failed to apply OCR settings: {e}")
            # Set defaults if settings application fails
            self.enable_ocr = True
            self.preferred_language = None  # Auto-detect language
    
    def apply_settings(self, settings: dict) -> None:
        """
        Apply user settings to OCR service
        
        Args:
            settings: User settings dictionary
        """
        try:
            self.user_settings = settings
            self._apply_settings()
            
        except Exception as e:
            logger.error(f"Failed to apply OCR settings: {e}")
            raise
    
    def is_ocr_enabled(self) -> bool:
        """
        Check if OCR is enabled based on settings
        
        Returns:
            True if OCR should be used
        """
        return getattr(self, 'enable_ocr', True) and self.is_available
    
    def get_preferred_language(self) -> str:
        """
        Get preferred language for OCR processing
        
        Returns:
            Language code
        """
        return getattr(self, 'preferred_language', None)
    
    async def extract_text(
        self,
        file_content: bytes,
        filename: str,
        mime_type: Optional[str] = None
    ) -> OCRResult:
        """
        Extract text from file using Google Vision OCR
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            mime_type: File MIME type (optional)
            
        Returns:
            OCRResult with extracted text and metadata
        """
        if not self.google_vision_ocr:
            raise OCRError("Google Vision OCR not available")
        
        if not self.is_ocr_enabled():
            raise OCRError("OCR is disabled in settings")
        
        try:
            return await self.google_vision_ocr.extract_text(
                file_content=file_content,
                filename=filename,
                mime_type=mime_type
            )
        except Exception as e:
            logger.error(f"OCR text extraction failed: {str(e)}")
            raise OCRError(f"OCR text extraction failed: {str(e)}")
    
    async def health_check(self) -> dict:
        """
        Perform health check on OCR service
        
        Returns:
            Health check result
        """
        if not self.google_vision_ocr:
            return {
                "status": "unavailable",
                "error": "Google Vision OCR not initialized",
                "available": False
            }
        
        try:
            return await self.google_vision_ocr.health_check()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "available": False
            }
    
    def get_status(self) -> dict:
        """
        Get OCR service status
        
        Returns:
            Status dictionary
        """
        status = {
            "available": self.is_available,
            "api_key_configured": bool(self.api_key),
            "enabled": self.is_ocr_enabled(),
            "preferred_language": self.get_preferred_language(),
            "supported_formats": self.SUPPORTED_FORMATS,
            "google_vision_available": GOOGLE_VISION_AVAILABLE,
            "google_vision_initialized": self.google_vision_ocr is not None
        }
        
        # Add Google Vision OCR status if available
        if self.google_vision_ocr:
            status.update(self.google_vision_ocr.get_status())
        
        return status