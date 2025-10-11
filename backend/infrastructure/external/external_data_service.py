"""
External Data Service
Implements IExternalDataService interface for external API integration
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from domain.agents.base import IExternalDataService
from infrastructure.external.market_data_service import MarketDataService, MarketDataServiceError

logger = logging.getLogger(__name__)


@dataclass
class MarketDataResult:
    """Market data result structure"""
    average_rent: Optional[float] = None
    median_rent: Optional[float] = None
    min_rent: Optional[float] = None
    max_rent: Optional[float] = None
    sample_size: int = 0
    data_quality: float = 0.0
    confidence: float = 0.0
    source: str = "unknown"
    location: Optional[str] = None
    last_updated: Optional[datetime] = None
    market_factors: Dict[str, Any] = None


class ExternalDataServiceError(Exception):
    """External data service errors"""
    pass


class ExternalDataService(IExternalDataService):
    """
    External data service implementation
    Orchestrates multiple external APIs with fallback logic
    """
    
    def __init__(self):
        """Initialize external data service"""
        self.market_data_service = MarketDataService()
        self.logger = logging.getLogger(__name__)
    
    async def fetch_market_data(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch market data from external sources
        
        Args:
            query: Market data query parameters
            
        Returns:
            Market data dictionary
        """
        try:
            location = query.get("location")
            property_type = query.get("property_type", "apartment")
            bedrooms = query.get("bedrooms")
            size_sqm = query.get("size_sqm")
            
            if not location:
                raise ExternalDataServiceError("Location is required for market data")
            
            # Use unified market data service
            market_data_result = await self.market_data_service.get_market_data(
                location=location,
                property_type=property_type,
                bedrooms=bedrooms,
                size_sqm=size_sqm
            )
            
            # Convert to dictionary format for agent compatibility
            return {
                "average_rent": market_data_result.average_rent,
                "median_rent": market_data_result.median_rent,
                "min_rent": market_data_result.min_rent,
                "max_rent": market_data_result.max_rent,
                "sample_size": market_data_result.sample_size,
                "data_quality": market_data_result.data_quality,
                "confidence": market_data_result.confidence,
                "source": market_data_result.source,
                "location": market_data_result.location,
                "city": market_data_result.city,
                "country": market_data_result.country,
                "last_updated": market_data_result.last_updated.isoformat() if market_data_result.last_updated else None,
                "market_factors": market_data_result.market_factors or {},
                "source_chain": market_data_result.source_chain or []
            }
            
        except MarketDataServiceError as e:
            raise ExternalDataServiceError(f"Market data service error: {str(e)}")
        except Exception as e:
            raise ExternalDataServiceError(f"Failed to fetch market data: {str(e)}")
    
    async def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Geocode address to coordinates
        
        Args:
            address: Address string
            
        Returns:
            Coordinates dict with 'lat' and 'lng' or None
        """
        try:
            result = await self.market_data_service.geocoding_service.geocode(address)
            if not result:
                return None
            
            return {
                "lat": result.latitude,
                "lng": result.longitude,
                "address": result.address,
                "city": result.city,
                "country": result.country,
                "confidence": result.confidence
            }
            
        except Exception as e:
            self.logger.warning(f"Geocoding failed: {e}")
            return None
    
    async def validate_location(self, location: str) -> bool:
        """
        Validate if location can be geocoded and has market data
        
        Args:
            location: Location string
            
        Returns:
            True if location is valid, False otherwise
        """
        try:
            return await self.market_data_service.validate_location(location)
        except Exception:
            return False
    
    def clear_caches(self):
        """Clear all external service caches"""
        self.market_data_service.clear_caches()
        self.logger.info("All external service caches cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for all services"""
        return self.market_data_service.get_cache_stats()
