"""
Enhanced Geocoding Service
OpenStreetMap Nominatim integration for address geocoding
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import lru_cache
import httpx
import re

from core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class GeocodingResult:
    """Geocoding result structure"""
    latitude: float
    longitude: float
    address: str
    city: Optional[str] = None
    country: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    confidence: float = 0.0
    source: str = "nominatim"


class GeocodingError(Exception):
    """Geocoding specific errors"""
    pass


class GeocodingService:
    """
    Enhanced geocoding service using OpenStreetMap Nominatim
    Provides free geocoding with caching and address normalization
    """
    
    NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
    RATE_LIMIT_DELAY = 1.0  # 1 second between requests (Nominatim requirement)
    CACHE_TTL_HOURS = 24
    
    def __init__(self):
        """Initialize geocoding service"""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_time = 0.0
        
        # Rate limiting
        self._rate_limit_semaphore = asyncio.Semaphore(1)
    
    async def _rate_limit(self):
        """Apply rate limiting to Nominatim API calls"""
        async with self._rate_limit_semaphore:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
            
            self._last_request_time = asyncio.get_event_loop().time()
    
    def _normalize_address(self, address: str) -> str:
        """
        Normalize address for consistent processing
        
        Args:
            address: Raw address string
            
        Returns:
            Normalized address
        """
        if not address:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = address.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Common address abbreviations
        abbreviations = {
            'street': 'st',
            'avenue': 'ave',
            'road': 'rd',
            'boulevard': 'blvd',
            'drive': 'dr',
            'lane': 'ln',
            'court': 'ct',
            'place': 'pl',
            'apartment': 'apt',
            'suite': 'ste',
            'unit': 'unit'
        }
        
        for full, abbrev in abbreviations.items():
            normalized = normalized.replace(f' {full} ', f' {abbrev} ')
            normalized = normalized.replace(f' {full}.', f' {abbrev}.')
        
        return normalized
    
    def _get_cache_key(self, address: str) -> str:
        """Generate cache key for address"""
        return self._normalize_address(address)
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        
        cached_time = cache_entry.get('cached_at')
        if not cached_time:
            return False
        
        cache_age = datetime.utcnow() - cached_time
        return cache_age < timedelta(hours=self.CACHE_TTL_HOURS)
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Make HTTP request to Nominatim API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            GeocodingError: API request failed
        """
        await self._rate_limit()
        
        url = f"{self.NOMINATIM_BASE_URL}/{endpoint}"
        headers = {
            "User-Agent": "Covenantrix/2.0.0 (Real Estate Analysis)",
            "Accept": "application/json"
        }
        
        # Add default parameters
        params.update({
            "format": "json",
            "addressdetails": "1",
            "limit": "5"
        })
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if not isinstance(data, list):
                    raise GeocodingError("Invalid response format from Nominatim")
                
                return data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise GeocodingError("Rate limit exceeded. Please try again later.")
            elif e.response.status_code == 404:
                raise GeocodingError("Address not found")
            else:
                raise GeocodingError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise GeocodingError(f"Request failed: {str(e)}")
        except Exception as e:
            raise GeocodingError(f"Unexpected error: {str(e)}")
    
    async def geocode(self, address: str) -> Optional[GeocodingResult]:
        """
        Geocode address to coordinates
        
        Args:
            address: Address string to geocode
            
        Returns:
            Geocoding result or None if not found
            
        Raises:
            GeocodingError: Geocoding failed
        """
        if not address or not address.strip():
            return None
        
        cache_key = self._get_cache_key(address)
        
        # Check cache first
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                self.logger.debug(f"Geocoding cache hit for: {address}")
                return cache_entry['data']
        
        try:
            # Geocode using Nominatim
            params = {"q": address}
            results = await self._make_request("search", params)
            
            if not results:
                self.logger.warning(f"No geocoding results for: {address}")
                return None
            
            # Select best result
            best_result = self._select_best_result(results, address)
            if not best_result:
                return None
            
            # Parse result
            geocoding_result = self._parse_geocoding_result(best_result, address)
            
            # Cache the result
            self._cache[cache_key] = {
                'data': geocoding_result,
                'cached_at': datetime.utcnow()
            }
            
            return geocoding_result
            
        except GeocodingError:
            raise
        except Exception as e:
            raise GeocodingError(f"Failed to geocode address: {str(e)}")
    
    def _select_best_result(self, results: List[Dict[str, Any]], original_address: str) -> Optional[Dict[str, Any]]:
        """
        Select best geocoding result from multiple options
        
        Args:
            results: List of geocoding results
            original_address: Original address string
            
        Returns:
            Best matching result or None
        """
        if not results:
            return None
        
        # Score results based on relevance
        scored_results = []
        original_lower = original_address.lower()
        
        for result in results:
            score = 0.0
            
            # Check display name similarity
            display_name = result.get("display_name", "").lower()
            if original_lower in display_name:
                score += 0.5
            
            # Check importance (higher is better)
            importance = result.get("importance", 0.0)
            score += importance * 0.3
            
            # Check address type (prefer house, building, etc.)
            address_type = result.get("type", "").lower()
            if address_type in ["house", "building", "residential"]:
                score += 0.2
            
            scored_results.append((score, result))
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return scored_results[0][1] if scored_results else None
    
    def _parse_geocoding_result(self, result: Dict[str, Any], original_address: str) -> GeocodingResult:
        """
        Parse Nominatim result into GeocodingResult
        
        Args:
            result: Nominatim API result
            original_address: Original address string
            
        Returns:
            Parsed geocoding result
        """
        # Extract coordinates
        lat = float(result.get("lat", 0))
        lng = float(result.get("lon", 0))
        
        # Extract address components
        address_parts = result.get("address", {})
        
        city = address_parts.get("city") or address_parts.get("town") or address_parts.get("village")
        country = address_parts.get("country")
        street = address_parts.get("road") or address_parts.get("street")
        postal_code = address_parts.get("postcode")
        
        # Calculate confidence based on result quality
        confidence = self._calculate_confidence(result, original_address)
        
        return GeocodingResult(
            latitude=lat,
            longitude=lng,
            address=result.get("display_name", original_address),
            city=city,
            country=country,
            street=street,
            postal_code=postal_code,
            confidence=confidence,
            source="nominatim"
        )
    
    def _calculate_confidence(self, result: Dict[str, Any], original_address: str) -> float:
        """
        Calculate confidence score for geocoding result
        
        Args:
            result: Nominatim result
            original_address: Original address
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.5  # Base score
        
        # Importance score (0.0 to 1.0)
        importance = result.get("importance", 0.0)
        score += importance * 0.3
        
        # Address type bonus
        address_type = result.get("type", "").lower()
        if address_type in ["house", "building", "residential"]:
            score += 0.1
        
        # Address component completeness
        address_parts = result.get("address", {})
        if address_parts.get("city"):
            score += 0.05
        if address_parts.get("country"):
            score += 0.05
        
        return min(1.0, score)
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[GeocodingResult]:
        """
        Reverse geocode coordinates to address
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Geocoding result or None if not found
        """
        try:
            params = {
                "lat": latitude,
                "lon": longitude
            }
            
            results = await self._make_request("reverse", params)
            
            if not results:
                return None
            
            result = results[0]
            return self._parse_geocoding_result(result, f"{latitude}, {longitude}")
            
        except Exception as e:
            self.logger.warning(f"Reverse geocoding failed: {e}")
            return None
    
    async def validate_address(self, address: str) -> bool:
        """
        Validate if address exists and is geocodable
        
        Args:
            address: Address to validate
            
        Returns:
            True if address is valid, False otherwise
        """
        try:
            result = await self.geocode(address)
            return result is not None and result.confidence > 0.3
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear geocoding cache"""
        self._cache.clear()
        self.logger.info("Geocoding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "cache_entries": list(self._cache.keys())
        }
