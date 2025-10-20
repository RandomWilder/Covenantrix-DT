"""
Google Vision OCR Integration
OCR-specific Google Vision API integration for document processing
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import mimetypes
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

from infrastructure.external.google_vision_client import GoogleVisionClient, VisionAPIResponse
from domain.integrations.models import OCRResult
from domain.integrations.exceptions import OCRError, GoogleVisionAPIError

logger = logging.getLogger(__name__)


class GoogleVisionOCR:
    """
    Google Vision OCR service
    Handles OCR processing using Google Vision API
    """
    
    # Supported formats for OCR
    SUPPORTED_IMAGE_FORMATS = {'png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp'}
    SUPPORTED_PDF_FORMATS = {'pdf'}
    SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS | SUPPORTED_PDF_FORMATS
    
    # Quality thresholds
    DEFAULT_MIN_CONFIDENCE = 0.3  # Lowered to be more permissive
    DEFAULT_MIN_CHAR_COUNT = 1  # Lowered to be more permissive
    
    def __init__(
        self,
        api_key: str,
        project_id: Optional[str] = None,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        min_char_count: int = DEFAULT_MIN_CHAR_COUNT,
        preferred_language: Optional[str] = None
    ):
        """
        Initialize Google Vision OCR service
        
        Args:
            api_key: Google Vision API key
            project_id: Google Cloud project ID (optional)
            min_confidence: Minimum confidence threshold for OCR results
            min_char_count: Minimum character count for valid results
            preferred_language: Preferred language for OCR processing (None for auto-detection)
        """
        self.api_key = api_key
        self.project_id = project_id
        self.min_confidence = min_confidence
        self.min_char_count = min_char_count
        self.preferred_language = preferred_language
        self.logger = logging.getLogger(__name__)
        
        if not api_key:
            raise OCRError("Google Vision API key is required")
    
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
        try:
            # Validate file format
            if not self._is_supported_format(filename, mime_type):
                raise OCRError(f"Unsupported file format: {filename}")
            
            # Determine processing method based on file type
            file_ext = Path(filename).suffix.lower().lstrip('.')
            
            if file_ext in self.SUPPORTED_IMAGE_FORMATS:
                return await self._process_image(file_content, filename)
            elif file_ext in self.SUPPORTED_PDF_FORMATS:
                return await self._process_pdf(file_content, filename)
            else:
                raise OCRError(f"Unsupported file format: {file_ext}")
                
        except GoogleVisionAPIError as e:
            self.logger.error(f"Google Vision API error: {str(e)}")
            raise OCRError(f"OCR processing failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"OCR processing failed: {str(e)}")
            raise OCRError(f"OCR processing failed: {str(e)}")
    
    async def _process_image(
        self,
        image_content: bytes,
        filename: str
    ) -> OCRResult:
        """Process image file with Google Vision API"""
        async with GoogleVisionClient(self.api_key, self.project_id) as client:
            # Prepare language hints
            language_hints = [self.preferred_language] if self.preferred_language else None
            
            # Try enhanced handwriting detection first for better mixed content support
            try:
                response = await client.detect_handwriting(
                    image_content=image_content,
                    language_hints=language_hints,
                    max_results=10
                )
            except Exception as e:
                # Fallback to standard text detection if handwriting detection fails
                self.logger.warning(f"Handwriting detection failed, falling back to standard: {e}")
                response = await client.detect_text(
                    image_content=image_content,
                    language_hints=language_hints,
                    max_results=10
                )
            
            # Validate and process result
            return self._create_ocr_result(response, filename)
    
    async def _process_pdf(
        self,
        pdf_content: bytes,
        filename: str
    ) -> OCRResult:
        """Process PDF file by converting pages to images and sending to Google Vision API"""
        start_time = datetime.utcnow()
        self.logger.info(f"Converting PDF to images: {filename}")
        
        pdf_doc = None
        try:
            # Open PDF document
            pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
            page_count = len(pdf_doc)
            self.logger.info(f"PDF has {page_count} pages")
            
            # Process each page
            all_texts = []
            all_confidences = []
            
            async with GoogleVisionClient(self.api_key, self.project_id) as client:
                # Prepare language hints
                language_hints = [self.preferred_language] if self.preferred_language else None
                
                for page_num in range(page_count):
                    # Get page
                    page = pdf_doc[page_num]
                    
                    # Create 300 DPI transformation matrix
                    mat = fitz.Matrix(300/72, 300/72)
                    
                    # Render page to pixmap
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to PIL Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # Convert to PNG bytes
                    img_bytes_io = BytesIO()
                    img.save(img_bytes_io, format='PNG')
                    img_bytes = img_bytes_io.getvalue()
                    
                    # Send to Google Vision API
                    try:
                        response = await client.detect_text(
                            image_content=img_bytes,
                            language_hints=language_hints,
                            max_results=10,
                            use_document_detection=True
                        )
                        
                        # Store results
                        page_text = response.text
                        page_confidence = response.confidence
                        
                        all_texts.append(page_text)
                        all_confidences.append(page_confidence)
                        
                        self.logger.info(f"Page {page_num + 1}: extracted {len(page_text)} chars, confidence={page_confidence:.2f}")
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to process page {page_num + 1}: {e}")
                        # Continue with other pages even if one fails
                        all_texts.append("")
                        all_confidences.append(0.0)
            
            # Combine results
            combined_text = "\n\n".join([text for text in all_texts if text])
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(f"PDF processing complete: {len(combined_text)} chars, {avg_confidence:.2f} confidence, {processing_time:.2f}s")
            
            # Create OCR result
            return OCRResult(
                text=self._clean_text(combined_text),
                confidence=avg_confidence,
                language=None,  # Language detection from first page could be added if needed
                page_count=page_count,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"PDF processing failed: {str(e)}")
            raise OCRError(f"PDF processing failed: {str(e)}")
        finally:
            # Ensure PDF document is properly closed
            if pdf_doc is not None:
                pdf_doc.close()
    
    def _create_ocr_result(self, response: VisionAPIResponse, filename: str) -> OCRResult:
        """Create OCRResult from VisionAPIResponse"""
        # Debug: Log what we're getting from Google Vision
        self.logger.info(f"Google Vision response for {filename}: text_length={len(response.text)}, confidence={response.confidence}")
        if len(response.text) == 0:
            self.logger.warning(f"No text extracted from {filename}")
            # Log the raw response for debugging
            self.logger.debug(f"Raw response keys: {list(response.raw_response.keys()) if response.raw_response else 'None'}")
        
        # Clean and validate text
        text = self._clean_text(response.text)
        
        # Validate quality
        is_valid, error_msg = self._validate_quality(text, response.confidence)
        if not is_valid:
            self.logger.warning(f"OCR quality validation failed for {filename}: {error_msg}")
        
        return OCRResult(
            text=text,
            confidence=response.confidence,
            language=response.language,
            page_count=response.page_count,
            processing_time=response.processing_time
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def _validate_quality(
        self,
        text: str,
        confidence: float
    ) -> tuple[bool, Optional[str]]:
        """
        Validate OCR result quality
        
        Args:
            text: Extracted text
            confidence: Confidence score
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check minimum character count
        if len(text) < self.min_char_count:
            return False, f"Text too short: {len(text)} < {self.min_char_count}"
        
        # Check confidence threshold
        if confidence < self.min_confidence:
            return False, f"Low confidence: {confidence:.2f} < {self.min_confidence}"
        
        # Check for gibberish (basic validation)
        if self._is_gibberish(text):
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
        if len(text) < 10:  # Temporarily lowered for debugging
            return False
        
        # Check ratio of letters to total characters
        letters = sum(c.isalpha() for c in text)
        ratio = letters / len(text)
        
        # If less than 50% letters, likely gibberish or corrupted
        return ratio < 0.5
    
    def _is_supported_format(self, filename: str, mime_type: Optional[str]) -> bool:
        """Check if file format is supported for OCR"""
        file_ext = Path(filename).suffix.lower().lstrip('.')
        
        self.logger.debug(f"Checking format support for {filename}: ext='{file_ext}', mime='{mime_type}'")
        self.logger.debug(f"Supported formats: {self.SUPPORTED_FORMATS}")
        
        # Check by extension
        if file_ext in self.SUPPORTED_FORMATS:
            self.logger.debug(f"File format supported by extension: {file_ext}")
            return True
        
        # Check by MIME type
        if mime_type:
            if mime_type.startswith('image/') and file_ext in self.SUPPORTED_IMAGE_FORMATS:
                self.logger.debug(f"File format supported by MIME type (image): {mime_type}")
                return True
            if mime_type == 'application/pdf' and file_ext in self.SUPPORTED_PDF_FORMATS:
                self.logger.debug(f"File format supported by MIME type (PDF): {mime_type}")
                return True
        
        self.logger.debug(f"File format not supported: {filename}")
        return False
    
    def validate_image_format(self, filename: str) -> bool:
        """Validate if file is an image format supported by OCR"""
        file_ext = Path(filename).suffix.lower().lstrip('.')
        return file_ext in self.SUPPORTED_IMAGE_FORMATS
    
    def validate_pdf_format(self, filename: str) -> bool:
        """Validate if file is a PDF format supported by OCR"""
        file_ext = Path(filename).suffix.lower().lstrip('.')
        return file_ext in self.SUPPORTED_PDF_FORMATS
    
    def is_image_file(self, mime_type: str) -> bool:
        """Check if MIME type is an image"""
        return mime_type.startswith('image/')
    
    def is_pdf_file(self, mime_type: str) -> bool:
        """Check if MIME type is PDF"""
        return mime_type == 'application/pdf'
    
    def estimate_processing_time(self, file_size_mb: float, is_pdf: bool = False) -> float:
        """
        Estimate OCR processing time
        
        Args:
            file_size_mb: File size in MB
            is_pdf: Whether file is PDF
            
        Returns:
            Estimated time in seconds
        """
        if is_pdf:
            # PDFs take longer due to page processing
            return max(5.0, file_size_mb * 3.0)
        else:
            # Images are faster
            return max(2.0, file_size_mb * 1.5)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Google Vision OCR service
        
        Returns:
            Health check result
        """
        try:
            async with GoogleVisionClient(self.api_key, self.project_id) as client:
                health_result = await client.health_check()
                
                return {
                    "service": "google_vision_ocr",
                    "status": health_result["status"],
                    "api_key_configured": bool(self.api_key),
                    "project_id": self.project_id,
                    "supported_formats": list(self.SUPPORTED_FORMATS),
                    "min_confidence": self.min_confidence,
                    "min_char_count": self.min_char_count,
                    "preferred_language": self.preferred_language,
                    **health_result
                }
                
        except Exception as e:
            return {
                "service": "google_vision_ocr",
                "status": "unhealthy",
                "error": str(e),
                "api_key_configured": bool(self.api_key),
                "project_id": self.project_id
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get OCR service status"""
        return {
            "available": bool(self.api_key),
            "api_key_configured": bool(self.api_key),
            "project_id": self.project_id,
            "supported_formats": list(self.SUPPORTED_FORMATS),
            "min_confidence": self.min_confidence,
            "min_char_count": self.min_char_count,
            "preferred_language": self.preferred_language
        }
