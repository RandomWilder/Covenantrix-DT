"""
Geocoding Service
Converts addresses to coordinates using external APIs
"""
import logging
from typing import Optional, Dict
from functools import lru_cache
import asyncio

from core.config import get_settings

logger = logging.getLogger(__name__)


class GeocodingService:
    """
    Geocoding service with caching
    """
    
    def __init__(self):
        """Initialize geocoding service"""
        settings = get_settings()
        self.api_key = settings.google_maps_api_key
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Dict[str, float]] = {}
    
    @lru_cache(maxsize=1000)
    def _normalize_address(self, address: str) -> str:
        """Normalize address for cache key"""
        return ' '.join(address.lower().split())
    
    async def geocode(self, address: str) -> Optional[Dict[str, float]]:
        """
        Geocode address to coordinates
        
        Args:
            address: Address string
            
        Returns:
            Dict with 'lat' and 'lng' or None
        """
        if not address:
            return None
        
        # Check cache
        cache_key = self._normalize_address(address)
        if cache_key in self._cache:
            self.logger.debug(f"Geocoding cache hit: {address}")
            return self._cache[cache_key]
        
        # Mock implementation (replace with actual API call)
        self.logger.warning(f"Geocoding not implemented, returning None for: {address}")
        return None
    
    def clear_cache(self):
        """Clear geocoding cache"""
        self._cache.clear()
        self._normalize_address.cache_clear()
        self.logger.info("Geocoding cache cleared")
    
    def get_cache_info(self) -> Dict:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "lru_info": self._normalize_address.cache_info()._asdict()
        }