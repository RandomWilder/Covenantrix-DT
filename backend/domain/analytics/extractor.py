"""
Metadata Extractor
Pure business logic for extracting structured data from documents
"""
import logging
from typing import Dict, Any, List, Callable, Awaitable
from domain.analytics.models import (
    ExtractedMetadata, ExtractedDate, MonetaryValue, Entity, KeyTerm
)
from domain.analytics.exceptions import ExtractionError

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Metadata extraction service
    Extracts structured information from document content
    """
    
    # Chunking configuration
    CHUNK_SIZE = 2000  # characters
    CHUNK_OVERLAP = 500  # characters
    
    def __init__(self, llm_func: Callable[[str, str], Awaitable[str]]):
        """
        Initialize extractor with LLM function
        
        Args:
            llm_func: Async LLM function (prompt, system_prompt) -> response
        """
        self.llm_func = llm_func
    
    async def extract(
        self,
        content: str,
        filename: str
    ) -> ExtractedMetadata:
        """
        Extract metadata from document content
        
        Args:
            content: Document text content
            filename: Original filename
            
        Returns:
            Extracted metadata
            
        Raises:
            ExtractionError: Extraction failed
        """
        try:
            # Split into chunks for processing
            chunks = self._split_into_chunks(content)
            
            logger.info(f"Extracting metadata from {len(chunks)} chunks")
            
            # Process each chunk
            all_dates = []
            all_monetary = []
            all_entities = []
            all_terms = []
            
            for i, chunk in enumerate(chunks):
                chunk_result = await self._extract_from_chunk(chunk, filename, i+1)
                
                all_dates.extend(chunk_result.get("dates", []))
                all_monetary.extend(chunk_result.get("monetary_values", []))
                all_entities.extend(chunk_result.get("entities", []))
                all_terms.extend(chunk_result.get("key_terms", []))
            
            # Deduplicate and create metadata object
            metadata = ExtractedMetadata(
                dates=self._deduplicate_dates(all_dates),
                monetary_values=self._deduplicate_monetary(all_monetary),
                entities=self._deduplicate_entities(all_entities),
                key_terms=self._deduplicate_terms(all_terms),
                chunks_processed=len(chunks)
            )
            
            logger.info(
                f"Metadata extracted: {len(metadata.dates)} dates, "
                f"{len(metadata.monetary_values)} monetary values, "
                f"{len(metadata.entities)} entities"
            )
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            raise ExtractionError(f"Extraction failed: {str(e)}")
    
    def _split_into_chunks(self, content: str) -> List[str]:
        """Split content into overlapping chunks"""
        if len(content) <= self.CHUNK_SIZE:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.CHUNK_SIZE
            
            # Try to break at sentence boundary
            if end < len(content):
                for i in range(end - 1, max(start + self.CHUNK_SIZE - 200, start), -1):
                    if content[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start with overlap
            start = end - self.CHUNK_OVERLAP
            if start >= len(content):
                break
        
        return chunks
    
    async def _extract_from_chunk(
        self,
        chunk: str,
        filename: str,
        chunk_num: int
    ) -> Dict[str, Any]:
        """Extract metadata from a single chunk"""
        prompt = f"""Extract structured information from this document section.
Work with ANY language - extract data regardless of language.

Extract:
1. **Dates** with context (contract dates, deadlines, etc.)
2. **Monetary Values** with ISO currency codes (USD, EUR, ILS, etc.)
3. **Entities** (people, organizations, addresses) with roles in ENGLISH
4. **Key Terms** (important clauses, conditions)

Document: {filename}
Chunk: {chunk_num}

Content:
{chunk}

Respond in JSON:
{{
    "dates": [
        {{"value": "YYYY-MM-DD", "context": "contract_start", "confidence": 0.9}}
    ],
    "monetary_values": [
        {{"amount": 1000.0, "currency": "USD", "context": "monthly_rent", "confidence": 0.9}}
    ],
    "entities": [
        {{"name": "Entity Name", "type": "person|organization|address", "role": "tenant|landlord|party", "confidence": 0.9}}
    ],
    "key_terms": [
        {{"term": "Important clause", "category": "obligation", "context": "Brief context", "importance": 0.8}}
    ]
}}

IMPORTANT:
- Use ISO 4217 currency codes only (USD, EUR, ILS, GBP, etc.)
- Entity roles must be in ENGLISH
- Only extract high-confidence information
- Return empty arrays if nothing found"""
        
        system_prompt = """You are a precise data extraction expert. Extract only factual information.
Return ONLY valid JSON. Use standard formats (ISO dates, currency codes).
Entity roles must be in English regardless of document language."""
        
        response = await self.llm_func(prompt, system_prompt)
        
        # Parse response
        return self._parse_extraction_response(response)
    
    def _parse_extraction_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM extraction response"""
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
        
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse extraction response, returning empty")
            return {"dates": [], "monetary_values": [], "entities": [], "key_terms": []}
        
        return data
    
    def _deduplicate_dates(self, dates: List[Dict]) -> List[ExtractedDate]:
        """Deduplicate and convert dates"""
        seen = set()
        result = []
        
        for d in dates:
            key = (d.get("value"), d.get("context"))
            if key not in seen and d.get("value"):
                seen.add(key)
                result.append(ExtractedDate(
                    value=d["value"],
                    context=d.get("context", "unknown"),
                    confidence=float(d.get("confidence", 0.7)),
                    source_text=d.get("source_text")
                ))
        
        return result
    
    def _deduplicate_monetary(self, values: List[Dict]) -> List[MonetaryValue]:
        """Deduplicate and convert monetary values"""
        seen = set()
        result = []
        
        for m in values:
            key = (m.get("amount"), m.get("currency"), m.get("context"))
            if key not in seen and m.get("amount") is not None:
                seen.add(key)
                result.append(MonetaryValue(
                    amount=float(m["amount"]),
                    currency=m.get("currency", "UNKNOWN"),
                    context=m.get("context", "unknown"),
                    confidence=float(m.get("confidence", 0.7))
                ))
        
        return result
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Entity]:
        """Deduplicate and convert entities"""
        seen = set()
        result = []
        
        for e in entities:
            name = e.get("name", "").strip()
            if not name or len(name) < 3:
                continue
            
            key = (name.lower(), e.get("type"))
            if key not in seen:
                seen.add(key)
                result.append(Entity(
                    name=name,
                    type=e.get("type", "unknown"),
                    role=e.get("role", "unknown"),
                    confidence=float(e.get("confidence", 0.7))
                ))
        
        return result
    
    def _deduplicate_terms(self, terms: List[Dict]) -> List[KeyTerm]:
        """Deduplicate and convert key terms"""
        seen = set()
        result = []
        
        for t in terms:
            term = t.get("term", "").strip()
            if not term:
                continue
            
            if term.lower() not in seen:
                seen.add(term.lower())
                result.append(KeyTerm(
                    term=term,
                    category=t.get("category", "unknown"),
                    context=t.get("context", ""),
                    importance=float(t.get("importance", 0.5))
                ))
        
        return result