"""
Numbeo API Integration
Real estate market data from Numbeo API
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx
from dataclasses import dataclass

from core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class NumbeoPropertyData:
    """Numbeo property data structure"""
    city: str
    country: str
    average_rent_1br: Optional[float] = None
    average_rent_2br: Optional[float] = None
    average_rent_3br: Optional[float] = None
    average_rent_center: Optional[float] = None
    average_rent_outside: Optional[float] = None
    data_quality: float = 0.0
    sample_size: int = 0
    last_updated: Optional[datetime] = None


class NumbeoAPIError(Exception):
    """Numbeo API specific errors"""
    pass


class NumbeoAPIService:
    """
    Numbeo API service for real estate data
    Provides access to global real estate market data
    """
    
    BASE_URL = "https://www.numbeo.com/api"
    RATE_LIMIT_DELAY = 1.0  # 1 second between requests
    CACHE_TTL_HOURS = 24
    
    def __init__(self):
        """Initialize Numbeo API service"""
        self.settings = get_settings()
        self.api_key = getattr(self.settings, 'numbeo_api_key', None)
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_time = 0.0
        
        # Rate limiting
        self._rate_limit_semaphore = asyncio.Semaphore(1)
    
    async def _rate_limit(self):
        """Apply rate limiting to API calls"""
        async with self._rate_limit_semaphore:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - time_since_last)
            
            self._last_request_time = asyncio.get_event_loop().time()
    
    def _get_cache_key(self, city: str, country: str) -> str:
        """Generate cache key for city/country combination"""
        return f"{city.lower()}_{country.lower()}"
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        
        cached_time = cache_entry.get('cached_at')
        if not cached_time:
            return False
        
        cache_age = datetime.utcnow() - cached_time
        return cache_age < timedelta(hours=self.CACHE_TTL_HOURS)
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to Numbeo API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            NumbeoAPIError: API request failed
        """
        await self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "User-Agent": "Covenantrix/2.0.0",
            "Accept": "application/json"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if not data or "error" in data:
                    raise NumbeoAPIError(f"API error: {data.get('error', 'Unknown error')}")
                
                return data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise NumbeoAPIError("Rate limit exceeded. Please try again later.")
            elif e.response.status_code == 404:
                raise NumbeoAPIError("City not found in Numbeo database")
            else:
                raise NumbeoAPIError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise NumbeoAPIError(f"Request failed: {str(e)}")
        except Exception as e:
            raise NumbeoAPIError(f"Unexpected error: {str(e)}")
    
    async def get_city_data(self, city: str, country: str) -> NumbeoPropertyData:
        """
        Get real estate data for a specific city
        
        Args:
            city: City name
            country: Country name
            
        Returns:
            Numbeo property data
            
        Raises:
            NumbeoAPIError: API request failed
        """
        cache_key = self._get_cache_key(city, country)
        
        # Check cache first
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                self.logger.debug(f"Cache hit for {city}, {country}")
                return cache_entry['data']
        
        try:
            # Fetch from API
            params = {
                "query": f"{city}, {country}",
                "api_key": self.api_key
            }
            
            data = await self._make_request("cities", params)
            
            if not data or "cities" not in data:
                raise NumbeoAPIError("No city data returned from API")
            
            cities = data["cities"]
            if not cities:
                raise NumbeoAPIError(f"City '{city}, {country}' not found")
            
            # Find best matching city
            city_data = self._find_best_city_match(cities, city, country)
            if not city_data:
                raise NumbeoAPIError(f"No matching city found for '{city}, {country}'")
            
            # Get property data for the city
            property_data = await self._get_property_data(city_data["city_id"])
            
            # Cache the result
            self._cache[cache_key] = {
                'data': property_data,
                'cached_at': datetime.utcnow()
            }
            
            return property_data
            
        except NumbeoAPIError:
            raise
        except Exception as e:
            raise NumbeoAPIError(f"Failed to get city data: {str(e)}")
    
    def _find_best_city_match(self, cities: List[Dict], target_city: str, target_country: str) -> Optional[Dict]:
        """
        Find best matching city from API results
        
        Args:
            cities: List of cities from API
            target_city: Target city name
            target_country: Target country name
            
        Returns:
            Best matching city data or None
        """
        target_city_lower = target_city.lower()
        target_country_lower = target_country.lower()
        
        # Exact match first
        for city in cities:
            if (city.get("city", "").lower() == target_city_lower and 
                city.get("country", "").lower() == target_country_lower):
                return city
        
        # Partial match
        for city in cities:
            city_name = city.get("city", "").lower()
            country_name = city.get("country", "").lower()
            
            if (target_city_lower in city_name or city_name in target_city_lower) and \
               (target_country_lower in country_name or country_name in target_country_lower):
                return city
        
        # Return first city if no match found
        return cities[0] if cities else None
    
    async def _get_property_data(self, city_id: int) -> NumbeoPropertyData:
        """
        Get property data for a specific city ID
        
        Args:
            city_id: Numbeo city ID
            
        Returns:
            Property data for the city
        """
        try:
            params = {"city_id": city_id}
            data = await self._make_request("city_prices", params)
            
            if not data or "prices" not in data:
                raise NumbeoAPIError("No property data returned")
            
            prices = data["prices"]
            
            # Extract rent data
            rent_data = {}
            for price in prices:
                item_name = price.get("item_name", "").lower()
                price_value = price.get("average_price")
                
                if "rent" in item_name and "1 bedroom" in item_name:
                    rent_data["1br"] = price_value
                elif "rent" in item_name and "2 bedroom" in item_name:
                    rent_data["2br"] = price_value
                elif "rent" in item_name and "3 bedroom" in item_name:
                    rent_data["3br"] = price_value
                elif "rent" in item_name and "city center" in item_name:
                    rent_data["center"] = price_value
                elif "rent" in item_name and "outside" in item_name:
                    rent_data["outside"] = price_value
            
            # Calculate data quality score
            data_quality = self._calculate_data_quality(rent_data)
            
            return NumbeoPropertyData(
                city=data.get("city", ""),
                country=data.get("country", ""),
                average_rent_1br=rent_data.get("1br"),
                average_rent_2br=rent_data.get("2br"),
                average_rent_3br=rent_data.get("3br"),
                average_rent_center=rent_data.get("center"),
                average_rent_outside=rent_data.get("outside"),
                data_quality=data_quality,
                sample_size=len(prices),
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            raise NumbeoAPIError(f"Failed to get property data: {str(e)}")
    
    def _calculate_data_quality(self, rent_data: Dict[str, Any]) -> float:
        """
        Calculate data quality score (0.0 to 1.0)
        
        Args:
            rent_data: Raw rent data from API
            
        Returns:
            Data quality score
        """
        score = 0.0
        total_checks = 5
        
        # Check for different rent types
        if rent_data.get("1br"):
            score += 0.2
        if rent_data.get("2br"):
            score += 0.2
        if rent_data.get("3br"):
            score += 0.2
        if rent_data.get("center"):
            score += 0.2
        if rent_data.get("outside"):
            score += 0.2
        
        return min(1.0, score)
    
    async def search_cities(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for cities matching query
        
        Args:
            query: Search query
            
        Returns:
            List of matching cities
        """
        try:
            params = {"query": query}
            data = await self._make_request("cities", params)
            
            if not data or "cities" not in data:
                return []
            
            return data["cities"]
            
        except Exception as e:
            self.logger.warning(f"City search failed: {e}")
            return []
    
    def clear_cache(self):
        """Clear API cache"""
        self._cache.clear()
        self.logger.info("Numbeo API cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "cache_entries": list(self._cache.keys())
        }
