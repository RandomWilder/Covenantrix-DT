"""
Analytics Domain Models
Pure Python models for document analytics and classification
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class DocumentCategory(str, Enum):
    """Universal document categories"""
    AGREEMENTS_CONTRACTS = "Agreements & Contracts"
    FINANCIAL_RECORDS = "Financial Records"
    LEGAL_COMPLIANCE = "Legal & Compliance"
    PROPERTY_ASSETS = "Property & Assets"
    OPERATIONAL_DOCUMENTS = "Operational Documents"
    CORRESPONDENCE_OTHER = "Correspondence & Other"


@dataclass
class Classification:
    """Document classification result"""
    category: DocumentCategory
    sub_type: str
    confidence: float
    detected_language: str
    reasoning: str
    classified_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "sub_type": self.sub_type,
            "confidence": self.confidence,
            "detected_language": self.detected_language,
            "reasoning": self.reasoning,
            "classified_at": self.classified_at.isoformat()
        }


@dataclass
class ExtractedDate:
    """Extracted date with context"""
    value: str  # ISO 8601 format
    context: str  # e.g., "contract_start", "payment_due"
    confidence: float
    source_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "context": self.context,
            "confidence": self.confidence,
            "source_text": self.source_text
        }


@dataclass
class MonetaryValue:
    """Extracted monetary value"""
    amount: float
    currency: str  # ISO 4217 code
    context: str  # e.g., "monthly_rent", "deposit"
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": self.amount,
            "currency": self.currency,
            "context": self.context,
            "confidence": self.confidence
        }


@dataclass
class Entity:
    """Extracted entity (person, organization, location)"""
    name: str
    type: str  # "person", "organization", "address", "location"
    role: str  # "tenant", "landlord", "party_a", etc.
    confidence: float
    coordinates: Optional[Dict[str, float]] = None  # lat, lon for addresses
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "type": self.type,
            "role": self.role,
            "confidence": self.confidence
        }
        if self.coordinates:
            result["coordinates"] = self.coordinates
        return result


@dataclass
class KeyTerm:
    """Important term or clause"""
    term: str
    category: str  # "clause", "condition", "obligation", etc.
    context: str
    importance: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "term": self.term,
            "category": self.category,
            "context": self.context,
            "importance": self.importance
        }


@dataclass
class ExtractedMetadata:
    """Complete extracted metadata from document"""
    dates: List[ExtractedDate] = field(default_factory=list)
    monetary_values: List[MonetaryValue] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    key_terms: List[KeyTerm] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    extraction_method: str = "llm"
    chunks_processed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dates": [d.to_dict() for d in self.dates],
            "monetary_values": [m.to_dict() for m in self.monetary_values],
            "entities": [e.to_dict() for e in self.entities],
            "key_terms": [k.to_dict() for k in self.key_terms],
            "extracted_at": self.extracted_at.isoformat(),
            "extraction_method": self.extraction_method,
            "chunks_processed": self.chunks_processed
        }
    
    @property
    def is_empty(self) -> bool:
        """Check if any metadata was extracted"""
        return not any([
            self.dates,
            self.monetary_values,
            self.entities,
            self.key_terms
        ])


@dataclass
class DocumentAnalytics:
    """Complete analytics for a document"""
    document_id: str
    classification: Classification
    metadata: ExtractedMetadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "classification": self.classification.to_dict(),
            "metadata": self.metadata.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class PortfolioSummary:
    """Portfolio-wide analytics summary"""
    total_documents: int
    by_category: Dict[str, int]
    total_monetary_value: Dict[str, float]  # by currency
    date_range: Optional[Dict[str, str]] = None  # earliest, latest
    top_entities: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_documents": self.total_documents,
            "by_category": self.by_category,
            "total_monetary_value": self.total_monetary_value,
            "date_range": self.date_range,
            "top_entities": self.top_entities
        }