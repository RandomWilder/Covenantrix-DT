"""
Document Classifier
Pure business logic for document classification
"""
import logging
from typing import Dict, Any, Callable, Awaitable
from domain.analytics.models import Classification, DocumentCategory
from domain.analytics.exceptions import ClassificationError

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """
    Document classification service
    Language-agnostic classification using LLM
    """
    
    # Category descriptions for LLM
    CATEGORY_DESCRIPTIONS = {
        DocumentCategory.AGREEMENTS_CONTRACTS: "Any type of agreement, contract, or binding arrangement",
        DocumentCategory.FINANCIAL_RECORDS: "Invoices, receipts, statements, financial reports",
        DocumentCategory.LEGAL_COMPLIANCE: "Legal documents, policies, regulatory compliance",
        DocumentCategory.PROPERTY_ASSETS: "Real estate, property deeds, asset documentation",
        DocumentCategory.OPERATIONAL_DOCUMENTS: "Procedures, manuals, operational guidelines",
        DocumentCategory.CORRESPONDENCE_OTHER: "Emails, letters, memos, reports, other documents"
    }
    
    # Subtypes by category
    SUBTYPES = {
        DocumentCategory.AGREEMENTS_CONTRACTS: [
            "Service Agreement", "Lease Agreement", "Employment Contract",
            "Partnership Agreement", "Purchase Agreement", "NDA"
        ],
        DocumentCategory.FINANCIAL_RECORDS: [
            "Invoice", "Receipt", "Bank Statement", "Tax Document",
            "Financial Report", "Payment Record"
        ],
        DocumentCategory.LEGAL_COMPLIANCE: [
            "Legal Notice", "Court Document", "Compliance Certificate",
            "Regulatory Filing", "Policy Document"
        ],
        DocumentCategory.PROPERTY_ASSETS: [
            "Property Deed", "Lease Agreement", "Mortgage Document",
            "Asset Inventory", "Property Insurance"
        ],
        DocumentCategory.OPERATIONAL_DOCUMENTS: [
            "Procedure Manual", "Safety Document", "Training Material",
            "Operational Report", "Process Document"
        ],
        DocumentCategory.CORRESPONDENCE_OTHER: [
            "Email", "Letter", "Memo", "Report", "Other Document"
        ]
    }
    
    def __init__(self, llm_func: Callable[[str, str], Awaitable[str]]):
        """
        Initialize classifier with LLM function
        
        Args:
            llm_func: Async LLM function (prompt, system_prompt) -> response
        """
        self.llm_func = llm_func
    
    async def classify(
        self,
        content: str,
        filename: str,
        sample_size: int = 3000
    ) -> Classification:
        """
        Classify document into category and sub-type
        
        Args:
            content: Document text content
            filename: Original filename
            sample_size: Characters to sample for classification
            
        Returns:
            Classification result
            
        Raises:
            ClassificationError: Classification failed
        """
        try:
            # Sample content for classification
            content_sample = content[:sample_size] if len(content) > sample_size else content
            
            # Build classification prompt
            prompt = self._build_classification_prompt(content_sample, filename)
            
            # Call LLM
            response = await self.llm_func(prompt, self._get_system_prompt())
            
            # Parse response
            classification = self._parse_classification_response(response)
            
            logger.info(
                f"Document classified: {classification.category.value} - {classification.sub_type} "
                f"(confidence: {classification.confidence})"
            )
            
            return classification
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise ClassificationError(f"Classification failed: {str(e)}")
    
    def _build_classification_prompt(self, content: str, filename: str) -> str:
        """Build classification prompt"""
        categories_list = "\n".join([
            f"{i+1}. {cat.value} - {desc}"
            for i, (cat, desc) in enumerate(self.CATEGORY_DESCRIPTIONS.items())
        ])
        
        return f"""Analyze this document and classify it into one of these categories:

Categories:
{categories_list}

Document Filename: {filename}

Document Content (first 3000 characters):
{content}

Respond in JSON format:
{{
    "category": "category name exactly as listed",
    "sub_type": "specific document sub-type",
    "confidence": 0.0-1.0,
    "detected_language": "ISO language code",
    "reasoning": "brief explanation"
}}"""
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for classification"""
        return """You are a document classification expert. Analyze documents accurately regardless of language.
Return ONLY valid JSON with no additional text. Be precise and confident in your classifications."""
    
    def _parse_classification_response(self, response: str) -> Classification:
        """Parse LLM response into Classification object"""
        import json
        
        # Clean response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Parse JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            raise ClassificationError(f"Failed to parse classification response: {e}")
        
        # Map category string to enum
        category_name = data.get("category", "")
        category = self._map_category_name(category_name)
        
        return Classification(
            category=category,
            sub_type=data.get("sub_type", "Unknown"),
            confidence=float(data.get("confidence", 0.7)),
            detected_language=data.get("detected_language", "unknown"),
            reasoning=data.get("reasoning", "")
        )
    
    def _map_category_name(self, category_name: str) -> DocumentCategory:
        """Map category name string to enum"""
        for category in DocumentCategory:
            if category.value.lower() == category_name.lower():
                return category
        
        # Default to correspondence if no match
        return DocumentCategory.CORRESPONDENCE_OTHER
    
    def get_taxonomy(self) -> Dict[str, Any]:
        """Get classification taxonomy"""
        return {
            "categories": {
                cat.value: {
                    "description": self.CATEGORY_DESCRIPTIONS[cat],
                    "subtypes": self.SUBTYPES[cat]
                }
                for cat in DocumentCategory
            }
        }