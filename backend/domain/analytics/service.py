"""
Analytics Service
Orchestrates classification and metadata extraction
"""
import logging
from typing import Callable, Awaitable

from domain.analytics.models import DocumentAnalytics, Classification, ExtractedMetadata
from domain.analytics.classifier import DocumentClassifier
from domain.analytics.extractor import MetadataExtractor
from domain.analytics.validator import DataValidator
from domain.analytics.exceptions import AnalyticsError

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analytics domain service
    Orchestrates document classification and metadata extraction
    """
    
    def __init__(
        self,
        llm_func: Callable[[str, str], Awaitable[str]],
        min_confidence: float = 0.6
    ):
        """
        Initialize analytics service
        
        Args:
            llm_func: Async LLM function
            min_confidence: Minimum confidence for validation
        """
        self.classifier = DocumentClassifier(llm_func)
        self.extractor = MetadataExtractor(llm_func)
        self.validator = DataValidator(min_confidence)
    
    async def analyze_document(
        self,
        document_id: str,
        content: str,
        filename: str
    ) -> DocumentAnalytics:
        """
        Complete document analysis: classification + extraction
        
        Args:
            document_id: Document identifier
            content: Document text content
            filename: Original filename
            
        Returns:
            Complete document analytics
            
        Raises:
            AnalyticsError: Analysis failed
        """
        try:
            logger.info(f"Analyzing document: {document_id}")
            
            # Run classification and extraction in parallel
            import asyncio
            
            classification_task = self.classifier.classify(content, filename)
            extraction_task = self.extractor.extract(content, filename)
            
            classification, raw_metadata = await asyncio.gather(
                classification_task,
                extraction_task
            )
            
            # Validate extracted metadata
            validated_metadata = self._validate_metadata(raw_metadata)
            
            # Create analytics object
            analytics = DocumentAnalytics(
                document_id=document_id,
                classification=classification,
                metadata=validated_metadata
            )
            
            logger.info(
                f"Document analyzed: {document_id} - "
                f"{classification.category.value} - "
                f"{len(validated_metadata.dates)} dates, "
                f"{len(validated_metadata.monetary_values)} monetary values"
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Document analysis failed: {document_id} - {e}")
            raise AnalyticsError(f"Analysis failed: {str(e)}")
    
    async def classify_only(
        self,
        content: str,
        filename: str
    ) -> Classification:
        """
        Classify document only (no extraction)
        
        Args:
            content: Document text content
            filename: Original filename
            
        Returns:
            Classification result
        """
        return await self.classifier.classify(content, filename)
    
    async def extract_only(
        self,
        content: str,
        filename: str
    ) -> ExtractedMetadata:
        """
        Extract metadata only (no classification)
        
        Args:
            content: Document text content
            filename: Original filename
            
        Returns:
            Extracted and validated metadata
        """
        raw_metadata = await self.extractor.extract(content, filename)
        return self._validate_metadata(raw_metadata)
    
    def _validate_metadata(self, metadata: ExtractedMetadata) -> ExtractedMetadata:
        """Validate and clean extracted metadata"""
        validated = ExtractedMetadata(
            dates=self.validator.validate_dates(metadata.dates),
            monetary_values=self.validator.validate_monetary_values(metadata.monetary_values),
            entities=self.validator.validate_entities(metadata.entities),
            key_terms=self.validator.validate_key_terms(metadata.key_terms),
            extracted_at=metadata.extracted_at,
            extraction_method=metadata.extraction_method,
            chunks_processed=metadata.chunks_processed
        )
        
        return validated
    
    def get_taxonomy(self):
        """Get classification taxonomy"""
        return self.classifier.get_taxonomy()