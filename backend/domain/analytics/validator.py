"""
Data Validator
Validates and normalizes extracted metadata
"""
import logging
import re
from typing import List
from datetime import datetime
from dateutil import parser as date_parser

from domain.analytics.models import (
    ExtractedDate, MonetaryValue, Entity, KeyTerm
)

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates and normalizes extracted data
    Ensures data quality and consistency
    """
    
    # ISO 4217 currency codes
    VALID_CURRENCIES = {
        'USD', 'EUR', 'GBP', 'ILS', 'JPY', 'CNY', 'CHF', 'CAD', 'AUD',
        'NZD', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RON'
    }
    
    # Standard entity roles (English only)
    STANDARD_ROLES = {
        'tenant', 'landlord', 'owner', 'buyer', 'seller', 'employer',
        'employee', 'contractor', 'client', 'vendor', 'partner', 'party_a',
        'party_b', 'insurer', 'insured', 'lender', 'borrower'
    }
    
    def __init__(self, min_confidence: float = 0.6):
        """
        Initialize validator
        
        Args:
            min_confidence: Minimum confidence threshold
        """
        self.min_confidence = min_confidence
    
    def validate_dates(self, dates: List[ExtractedDate]) -> List[ExtractedDate]:
        """Validate and normalize dates"""
        validated = []
        
        for date in dates:
            # Skip low confidence
            if date.confidence < self.min_confidence:
                continue
            
            # Validate ISO format
            try:
                datetime.fromisoformat(date.value)
                validated.append(date)
            except ValueError:
                logger.warning(f"Invalid date format: {date.value}")
        
        return validated
    
    def validate_monetary_values(
        self,
        values: List[MonetaryValue]
    ) -> List[MonetaryValue]:
        """Validate and normalize monetary values"""
        validated = []
        
        for value in values:
            # Skip low confidence
            if value.confidence < self.min_confidence:
                continue
            
            # Skip negative amounts
            if value.amount < 0:
                continue
            
            # Normalize currency code
            currency = value.currency.upper()
            if currency not in self.VALID_CURRENCIES:
                # Try to map common variants
                currency = self._normalize_currency(currency)
            
            validated.append(MonetaryValue(
                amount=value.amount,
                currency=currency,
                context=value.context,
                confidence=value.confidence
            ))
        
        return validated
    
    def validate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Validate and normalize entities"""
        validated = []
        
        for entity in entities:
            # Skip low confidence
            if entity.confidence < self.min_confidence:
                continue
            
            # Skip generic names
            if self._is_generic_name(entity.name):
                continue
            
            # Normalize role to English
            role = self._normalize_role(entity.role)
            
            validated.append(Entity(
                name=entity.name,
                type=entity.type,
                role=role,
                confidence=entity.confidence,
                coordinates=entity.coordinates
            ))
        
        return validated
    
    def validate_key_terms(self, terms: List[KeyTerm]) -> List[KeyTerm]:
        """Validate key terms"""
        validated = []
        
        for term in terms:
            # Skip if importance too low
            if term.importance < 0.4:
                continue
            
            # Skip very short terms
            if len(term.term) < 5:
                continue
            
            validated.append(term)
        
        return validated
    
    def _normalize_currency(self, currency: str) -> str:
        """Normalize currency code"""
        # Common mappings
        mappings = {
            'DOLLAR': 'USD',
            'DOLLARS': 'USD',
            '$': 'USD',
            'EURO': 'EUR',
            'EUROS': 'EUR',
            '€': 'EUR',
            'SHEKEL': 'ILS',
            'SHEKELS': 'ILS',
            '₪': 'ILS',
            'POUND': 'GBP',
            'POUNDS': 'GBP',
            '£': 'GBP'
        }
        
        return mappings.get(currency.upper(), 'UNKNOWN')
    
    def _normalize_role(self, role: str) -> str:
        """Normalize entity role to English standard"""
        role_lower = role.lower().strip()
        
        # Already standard
        if role_lower in self.STANDARD_ROLES:
            return role_lower
        
        # Common mappings (Hebrew to English)
        mappings = {
            'שוכר': 'tenant',
            'משכיר': 'landlord',
            'בעלים': 'owner',
            'קונה': 'buyer',
            'מוכר': 'seller',
            'מעסיק': 'employer',
            'עובד': 'employee',
            'קבלן': 'contractor',
            'לקוח': 'client',
            'ספק': 'vendor',
            'שותף': 'partner'
        }
        
        return mappings.get(role, role_lower)
    
    def _is_generic_name(self, name: str) -> bool:
        """Check if name is too generic"""
        generic = [
            'unknown', 'לא ידוע', 'המושכר', 'סניף', 'branch',
            'location', 'address', 'מיקום', 'כתובת', 'company',
            'person', 'entity'
        ]
        
        return name.lower().strip() in generic