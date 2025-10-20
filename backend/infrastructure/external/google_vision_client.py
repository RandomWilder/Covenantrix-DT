"""
Google Vision API Client
Async HTTP client for Google Vision API integration
"""
import logging
import base64
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import aiohttp
import json
from datetime import datetime

from core.exceptions import ProcessingError
from domain.integrations.exceptions import IntegrationError

logger = logging.getLogger(__name__)


@dataclass
class VisionAPIResponse:
    """Google Vision API response wrapper"""
    text: str
    confidence: float
    language: Optional[str]
    page_count: int
    processing_time: float
    raw_response: Dict[str, Any]


class GoogleVisionAPIError(IntegrationError):
    """Google Vision API specific error"""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(f"Google Vision API error: {message}")
        if status_code:
            self.status_code = status_code


class GoogleVisionClient:
    """
    Async Google Vision API client
    Handles authentication and API requests
    """
    
    # API endpoints
    BASE_URL = "https://vision.googleapis.com/v1"
    TEXT_DETECTION_ENDPOINT = f"{BASE_URL}/images:annotate"
    DOCUMENT_TEXT_DETECTION_ENDPOINT = f"{BASE_URL}/files:annotate"
    
    # Rate limits and timeouts
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    REQUEST_TIMEOUT = 30.0
    
    # File size limits
    MAX_IMAGE_SIZE_MB = 20
    MAX_PDF_PAGES = 2000
    
    def __init__(self, api_key: str, project_id: Optional[str] = None):
        """
        Initialize Google Vision API client
        
        Args:
            api_key: Google Vision API key
            project_id: Google Cloud project ID (optional)
        """
        self.api_key = api_key
        self.project_id = project_id
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        if not api_key:
            raise GoogleVisionAPIError("API key is required")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Ensure HTTP session is available"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def detect_text(
        self,
        image_content: bytes,
        language_hints: Optional[List[str]] = None,
        max_results: int = 10,
        use_document_detection: bool = False
    ) -> VisionAPIResponse:
        """
        Detect text in image using Google Vision API
        
        Args:
            image_content: Image file content as bytes
            language_hints: List of language codes to help detection
            max_results: Maximum number of text annotations to return
            
        Returns:
            VisionAPIResponse with extracted text and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            await self._ensure_session()
            
            # Validate image size
            self._validate_image_size(image_content)
            
            # Prepare request
            request_data = self._build_text_detection_request(
                image_content, language_hints, max_results, use_document_detection
            )
            
            # Make API request with retry logic
            response_data = await self._make_api_request(
                self.TEXT_DETECTION_ENDPOINT,
                request_data
            )
            
            # Parse response
            result = self._parse_text_detection_response(response_data)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VisionAPIResponse(
                text=result["text"],
                confidence=result["confidence"],
                language=result.get("language"),
                page_count=1,
                processing_time=processing_time,
                raw_response=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Text detection failed: {str(e)}")
            raise GoogleVisionAPIError(f"Text detection failed: {str(e)}")
    
    async def detect_document_text(
        self,
        pdf_content: bytes,
        language_hints: Optional[List[str]] = None,
        max_results: int = 10
    ) -> VisionAPIResponse:
        """
        Detect text in PDF document using Google Vision API
        
        Args:
            pdf_content: PDF file content as bytes
            language_hints: List of language codes to help detection
            max_results: Maximum number of text annotations to return
            
        Returns:
            VisionAPIResponse with extracted text and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            await self._ensure_session()
            
            # Validate PDF size
            self._validate_pdf_size(pdf_content)
            
            # Prepare request
            request_data = self._build_document_text_detection_request(
                pdf_content, language_hints, max_results
            )
            
            # Make API request with retry logic
            response_data = await self._make_api_request(
                self.DOCUMENT_TEXT_DETECTION_ENDPOINT,
                request_data
            )
            
            # Parse response
            result = self._parse_document_text_detection_response(response_data)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VisionAPIResponse(
                text=result["text"],
                confidence=result["confidence"],
                language=result.get("language"),
                page_count=result.get("page_count", 1),
                processing_time=processing_time,
                raw_response=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Document text detection failed: {str(e)}")
            raise GoogleVisionAPIError(f"Document text detection failed: {str(e)}")
    
    async def detect_handwriting(
        self,
        image_content: bytes,
        language_hints: Optional[List[str]] = None,
        max_results: int = 10
    ) -> VisionAPIResponse:
        """
        Enhanced handwriting detection using Google Vision API
        Optimized for documents with handwritten content
        
        Args:
            image_content: Image file content as bytes
            language_hints: List of language codes to help detection
            max_results: Maximum number of text annotations to return
            
        Returns:
            VisionAPIResponse with extracted text and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            await self._ensure_session()
            
            # Validate image size
            self._validate_image_size(image_content)
            
            # Prepare request with handwriting-optimized features
            request_data = self._build_handwriting_detection_request(
                image_content, language_hints, max_results
            )
            
            # Make API request with retry logic
            response_data = await self._make_api_request(
                self.TEXT_DETECTION_ENDPOINT,
                request_data
            )
            
            # Parse response
            result = self._parse_text_detection_response(response_data)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VisionAPIResponse(
                text=result["text"],
                confidence=result["confidence"],
                language=result.get("language"),
                page_count=1,
                processing_time=processing_time,
                raw_response=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Handwriting detection failed: {str(e)}")
            raise GoogleVisionAPIError(f"Handwriting detection failed: {str(e)}")
    
    def _validate_image_size(self, content: bytes) -> None:
        """Validate image size limits"""
        size_mb = len(content) / (1024 * 1024)
        if size_mb > self.MAX_IMAGE_SIZE_MB:
            raise GoogleVisionAPIError(
                f"Image too large: {size_mb:.2f}MB > {self.MAX_IMAGE_SIZE_MB}MB"
            )
    
    def _validate_pdf_size(self, content: bytes) -> None:
        """Validate PDF size limits"""
        # Basic size check - Google Vision API has 20MB limit for PDFs
        size_mb = len(content) / (1024 * 1024)
        if size_mb > self.MAX_IMAGE_SIZE_MB:
            raise GoogleVisionAPIError(
                f"PDF too large: {size_mb:.2f}MB > {self.MAX_IMAGE_SIZE_MB}MB"
            )
    
    def _build_text_detection_request(
        self,
        image_content: bytes,
        language_hints: Optional[List[str]],
        max_results: int,
        use_document_detection: bool = False
    ) -> Dict[str, Any]:
        """Build text detection API request"""
        # Encode image to base64
        image_b64 = base64.b64encode(image_content).decode('utf-8')
        
        # Choose the appropriate feature type
        if use_document_detection:
            features = [
                {
                    "type": "DOCUMENT_TEXT_DETECTION",
                    "maxResults": max_results
                }
            ]
        else:
            features = [
                {
                    "type": "TEXT_DETECTION",
                    "maxResults": max_results
                }
            ]
        
        request = {
            "requests": [
                {
                    "image": {
                        "content": image_b64
                    },
                    "features": features
                }
            ]
        }
        
        # Add language hints if provided
        if language_hints:
            request["requests"][0]["imageContext"] = {
                "languageHints": language_hints
            }
        
        return request
    
    def _build_document_text_detection_request(
        self,
        pdf_content: bytes,
        language_hints: Optional[List[str]],
        max_results: int
    ) -> Dict[str, Any]:
        """Build document text detection API request"""
        # Encode PDF to base64
        pdf_b64 = base64.b64encode(pdf_content).decode('utf-8')
        
        request = {
            "requests": [
                {
                    "inputConfig": {
                        "mimeType": "application/pdf",
                        "content": pdf_b64
                    },
                    "features": [
                        {
                            "type": "DOCUMENT_TEXT_DETECTION",
                            "maxResults": max_results
                        }
                    ]
                }
            ]
        }
        
        # Add language hints if provided
        if language_hints:
            request["requests"][0]["imageContext"] = {
                "languageHints": language_hints
            }
        
        return request
    
    def _build_handwriting_detection_request(
        self,
        image_content: bytes,
        language_hints: Optional[List[str]],
        max_results: int
    ) -> Dict[str, Any]:
        """Build handwriting-optimized text detection API request"""
        # Encode image to base64
        image_b64 = base64.b64encode(image_content).decode('utf-8')
        
        request = {
            "requests": [
                {
                    "image": {
                        "content": image_b64
                    },
                    "features": [
                        {
                            "type": "TEXT_DETECTION",
                            "maxResults": max_results
                        },
                        {
                            "type": "DOCUMENT_TEXT_DETECTION", 
                            "maxResults": max_results
                        }
                    ],
                    "imageContext": {
                        "textDetectionParams": {
                            "enableTextDetectionConfidenceScore": True
                        }
                    }
                }
            ]
        }
        
        # Add language hints if provided
        if language_hints:
            request["requests"][0]["imageContext"]["languageHints"] = language_hints
        
        return request
    
    async def _make_api_request(
        self,
        endpoint: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make API request with retry logic"""
        url = f"{endpoint}?key={self.api_key}"
        
        for attempt in range(self.MAX_RETRIES):
            try:
                async with self.session.post(
                    url,
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limited
                        if attempt < self.MAX_RETRIES - 1:
                            delay = self.RETRY_DELAY * (2 ** attempt)
                            self.logger.warning(f"Rate limited, retrying in {delay}s")
                            await asyncio.sleep(delay)
                            continue
                    elif response.status == 400:
                        error_data = await response.json()
                        self.logger.error(f"Google Vision API 400 error: {error_data}")
                        error_msg = error_data.get("error", {}).get("message", "Bad request")
                        raise GoogleVisionAPIError(f"Bad request: {error_msg}", 400)
                    elif response.status == 403:
                        error_data = await response.json()
                        error_msg = error_data.get("error", {}).get("message", "Forbidden")
                        raise GoogleVisionAPIError(f"API key invalid or quota exceeded: {error_msg}", 403)
                    else:
                        error_data = await response.json()
                        error_msg = error_data.get("error", {}).get("message", "Unknown error")
                        raise GoogleVisionAPIError(f"API error: {error_msg}", response.status)
            
            except aiohttp.ClientError as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    self.logger.warning(f"Request failed, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                    continue
                raise GoogleVisionAPIError(f"Network error: {str(e)}")
        
        raise GoogleVisionAPIError("Max retries exceeded")
    
    def _parse_text_detection_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse text detection API response"""
        try:
            responses = response_data.get("responses", [])
            if not responses:
                return {"text": "", "confidence": 0.0, "language": None}
            
            response = responses[0]
            
            # Check for fullTextAnnotation first (for PDF documents)
            full_text_annotation = response.get("fullTextAnnotation", {})
            if full_text_annotation:
                # Extract text from fullTextAnnotation
                full_text = full_text_annotation.get("text", "")
                
                # Calculate confidence from blocks
                confidences = []
                pages = full_text_annotation.get("pages", [])
                for page in pages:
                    blocks = page.get("blocks", [])
                    for block in blocks:
                        confidence = block.get("confidence", 0.0)
                        if confidence > 0:
                            confidences.append(confidence)
                
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                # Try to detect language
                language = None
                if pages and "property" in pages[0]:
                    detected_langs = pages[0]["property"].get("detectedLanguages", [])
                    if detected_langs:
                        language = detected_langs[0].get("languageCode")
                
                logger.debug(f"Google Vision API response (fullTextAnnotation): text_length={len(full_text)}, confidence={avg_confidence}")
                
                return {
                    "text": full_text,
                    "confidence": avg_confidence,
                    "language": language
                }
            
            # Fallback to textAnnotations (for image files)
            text_annotations = response.get("textAnnotations", [])
            if not text_annotations:
                return {"text": "", "confidence": 0.0, "language": None}
            
            # Get full text (first annotation contains all text)
            full_text = text_annotations[0].get("description", "")
            
            # Debug: Log what we're getting from the API
            logger.debug(f"Google Vision API response (textAnnotations): {len(text_annotations)} annotations, full_text_length={len(full_text)}")
            
            if len(full_text) == 0 and len(text_annotations) > 1:
                # Try to get text from individual annotations if full text is empty
                individual_texts = [ann.get("description", "") for ann in text_annotations[1:]]
                combined_text = " ".join([t for t in individual_texts if t])
                logger.debug(f"Full text empty, trying individual annotations: {len(combined_text)} chars")
                if combined_text:
                    full_text = combined_text
            
            # Calculate average confidence from individual annotations
            confidences = []
            for annotation in text_annotations[1:]:  # Skip full text annotation
                # Try both 'score' and 'confidence' fields
                confidence = annotation.get("score", annotation.get("confidence", 0.0))
                if confidence > 0:
                    confidences.append(confidence)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Try to detect language from response
            language = None
            if "fullTextAnnotation" in response:
                pages = response["fullTextAnnotation"].get("pages", [])
                if pages and "property" in pages[0]:
                    detected_langs = pages[0]["property"].get("detectedLanguages", [])
                    if detected_langs:
                        language = detected_langs[0].get("languageCode")
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "language": language
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse text detection response: {str(e)}")
            return {"text": "", "confidence": 0.0, "language": None}
    
    def _parse_document_text_detection_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse document text detection API response"""
        try:
            responses = response_data.get("responses", [])
            if not responses:
                logger.warning("No responses in Google Vision API response")
                return {"text": "", "confidence": 0.0, "language": None, "page_count": 0}
            
            response = responses[0]
            
            # Debug: Log the response structure
            logger.debug(f"Google Vision API response structure: {list(response.keys())}")
            
            # Extract full text annotation
            full_text_annotation = response.get("fullTextAnnotation", {})
            if not full_text_annotation:
                logger.warning("No fullTextAnnotation in response")
                # Try alternative text extraction methods
                text_annotations = response.get("textAnnotations", [])
                if text_annotations:
                    logger.debug(f"Found {len(text_annotations)} text annotations, trying alternative extraction")
                    full_text = text_annotations[0].get("description", "") if text_annotations else ""
                    return {"text": full_text, "confidence": 0.0, "language": None, "page_count": 1}
                return {"text": "", "confidence": 0.0, "language": None, "page_count": 0}
            
            # Get full text
            full_text = full_text_annotation.get("text", "")
            logger.debug(f"Extracted text length: {len(full_text)}")
            
            # Get page count
            pages = full_text_annotation.get("pages", [])
            page_count = len(pages)
            
            # Calculate average confidence from pages
            confidences = []
            for page in pages:
                blocks = page.get("blocks", [])
                for block in blocks:
                    confidence = block.get("confidence", 0.0)
                    if confidence > 0:
                        confidences.append(confidence)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Try to detect language
            language = None
            if pages and "property" in pages[0]:
                detected_langs = pages[0]["property"].get("detectedLanguages", [])
                if detected_langs:
                    language = detected_langs[0].get("languageCode")
            
            logger.debug(f"Final result: text_length={len(full_text)}, confidence={avg_confidence}, language={language}")
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "language": language,
                "page_count": page_count
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse document text detection response: {str(e)}")
            return {"text": "", "confidence": 0.0, "language": None, "page_count": 0}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Google Vision API
        
        Returns:
            Health check result
        """
        try:
            await self._ensure_session()
            
            # Simple test request with minimal image
            test_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
            request_data = self._build_text_detection_request(test_image, None, 1)
            
            start_time = datetime.utcnow()
            response_data = await self._make_api_request(
                self.TEXT_DETECTION_ENDPOINT,
                request_data
            )
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "api_key_configured": bool(self.api_key),
                "project_id": self.project_id
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_key_configured": bool(self.api_key),
                "project_id": self.project_id
            }
