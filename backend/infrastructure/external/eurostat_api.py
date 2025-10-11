"""
Eurostat API Integration
EU housing statistics and rent data
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import httpx
import json

from core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class EurostatHousingData:
    """Eurostat housing data structure"""
    country: str
    region: Optional[str] = None
    average_rent: Optional[float] = None
    rent_index: Optional[float] = None
    housing_costs: Optional[float] = None
    data_year: Optional[int] = None
    data_quality: float = 0.0
    source: str = "eurostat"


class EurostatAPIError(Exception):
    """Eurostat API specific errors"""
    pass


class EurostatAPIService:
    """
    Eurostat API service for EU housing statistics
    Provides access to official EU housing and rent data
    """
    
    BASE_URL = "https://ec.europa.eu/eurostat/api"
    CACHE_TTL_HOURS = 168  # 1 week (EU data updates slowly)
    
    def __init__(self):
        """Initialize Eurostat API service"""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Country code mapping
        self.country_codes = {
            "austria": "AT",
            "belgium": "BE", 
            "bulgaria": "BG",
            "croatia": "HR",
            "cyprus": "CY",
            "czech republic": "CZ",
            "czechia": "CZ",
            "denmark": "DK",
            "estonia": "EE",
            "finland": "FI",
            "france": "FR",
            "germany": "DE",
            "greece": "GR",
            "hungary": "HU",
            "ireland": "IE",
            "italy": "IT",
            "latvia": "LV",
            "lithuania": "LT",
            "luxembourg": "LU",
            "malta": "MT",
            "netherlands": "NL",
            "poland": "PL",
            "portugal": "PT",
            "romania": "RO",
            "slovakia": "SK",
            "slovenia": "SI",
            "spain": "ES",
            "sweden": "SE"
        }
    
    def _get_cache_key(self, country: str, region: Optional[str] = None) -> str:
        """Generate cache key for country/region combination"""
        key = country.lower()
        if region:
            key += f"_{region.lower()}"
        return key
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        
        cached_time = cache_entry.get('cached_at')
        if not cached_time:
            return False
        
        cache_age = datetime.utcnow() - cached_time
        return cache_age < timedelta(hours=self.CACHE_TTL_HOURS)
    
    def _normalize_country_name(self, country: str) -> str:
        """
        Normalize country name for Eurostat lookup
        
        Args:
            country: Country name
            
        Returns:
            Normalized country name
        """
        country_lower = country.lower().strip()
        
        # Direct mapping
        if country_lower in self.country_codes:
            return country_lower
        
        # Handle common variations
        variations = {
            "united kingdom": "uk",
            "great britain": "uk",
            "britain": "uk",
            "czech republic": "czechia",
            "slovak republic": "slovakia"
        }
        
        if country_lower in variations:
            return variations[country_lower]
        
        return country_lower
    
    def _get_country_code(self, country: str) -> Optional[str]:
        """
        Get ISO country code for Eurostat API
        
        Args:
            country: Country name
            
        Returns:
            ISO country code or None
        """
        normalized = self._normalize_country_name(country)
        return self.country_codes.get(normalized)
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to Eurostat API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            EurostatAPIError: API request failed
        """
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "User-Agent": "Covenantrix/2.0.0",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if not data:
                    raise EurostatAPIError("Empty response from Eurostat API")
                
                return data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise EurostatAPIError("Data not found for specified country/region")
            elif e.response.status_code == 429:
                raise EurostatAPIError("Rate limit exceeded. Please try again later.")
            else:
                raise EurostatAPIError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise EurostatAPIError(f"Request failed: {str(e)}")
        except Exception as e:
            raise EurostatAPIError(f"Unexpected error: {str(e)}")
    
    async def get_housing_data(self, country: str, region: Optional[str] = None) -> EurostatHousingData:
        """
        Get housing data for a specific country/region
        
        Args:
            country: Country name
            region: Region name (optional)
            
        Returns:
            Eurostat housing data
            
        Raises:
            EurostatAPIError: API request failed
        """
        cache_key = self._get_cache_key(country, region)
        
        # Check cache first
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                self.logger.debug(f"Cache hit for {country}, {region}")
                return cache_entry['data']
        
        try:
            # Get country code
            country_code = self._get_country_code(country)
            if not country_code:
                raise EurostatAPIError(f"Country '{country}' not supported by Eurostat")
            
            # Fetch housing cost data
            housing_data = await self._fetch_housing_costs(country_code, region)
            
            # Fetch rent data if available
            rent_data = await self._fetch_rent_data(country_code, region)
            
            # Combine data
            combined_data = self._combine_housing_data(
                country, region, housing_data, rent_data
            )
            
            # Cache the result
            self._cache[cache_key] = {
                'data': combined_data,
                'cached_at': datetime.utcnow()
            }
            
            return combined_data
            
        except EurostatAPIError:
            raise
        except Exception as e:
            raise EurostatAPIError(f"Failed to get housing data: {str(e)}")
    
    async def _fetch_housing_costs(self, country_code: str, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch housing cost data from Eurostat
        
        Args:
            country_code: ISO country code
            region: Region name (optional)
            
        Returns:
            Housing cost data
        """
        try:
            # Housing cost dataset
            params = {
                "format": "json",
                "lang": "en",
                "geo": country_code
            }
            
            if region:
                params["geo"] = f"{country_code}_{region}"
            
            data = await self._make_request("dissemination/statistics/1.0/data/housing_costs", params)
            
            return self._parse_housing_costs_data(data)
            
        except Exception as e:
            self.logger.warning(f"Housing costs data fetch failed: {e}")
            return {}
    
    async def _fetch_rent_data(self, country_code: str, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch rent data from Eurostat
        
        Args:
            country_code: ISO country code
            region: Region name (optional)
            
        Returns:
            Rent data
        """
        try:
            # Rent dataset (if available)
            params = {
                "format": "json",
                "lang": "en",
                "geo": country_code
            }
            
            if region:
                params["geo"] = f"{country_code}_{region}"
            
            data = await self._make_request("dissemination/statistics/1.0/data/rent_prices", params)
            
            return self._parse_rent_data(data)
            
        except Exception as e:
            self.logger.warning(f"Rent data fetch failed: {e}")
            return {}
    
    def _parse_housing_costs_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse housing costs data from Eurostat response
        
        Args:
            data: Raw Eurostat data
            
        Returns:
            Parsed housing costs data
        """
        try:
            # Extract relevant housing cost indicators
            housing_costs = {}
            
            if "value" in data:
                values = data["value"]
                if isinstance(values, dict):
                    # Get latest available data
                    latest_year = max(values.keys()) if values else None
                    if latest_year:
                        housing_costs["average_cost"] = values[latest_year]
                        housing_costs["data_year"] = int(latest_year)
            
            return housing_costs
            
        except Exception as e:
            self.logger.warning(f"Failed to parse housing costs data: {e}")
            return {}
    
    def _parse_rent_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse rent data from Eurostat response
        
        Args:
            data: Raw Eurostat data
            
        Returns:
            Parsed rent data
        """
        try:
            rent_data = {}
            
            if "value" in data:
                values = data["value"]
                if isinstance(values, dict):
                    # Get latest available data
                    latest_year = max(values.keys()) if values else None
                    if latest_year:
                        rent_data["average_rent"] = values[latest_year]
                        rent_data["data_year"] = int(latest_year)
            
            return rent_data
            
        except Exception as e:
            self.logger.warning(f"Failed to parse rent data: {e}")
            return {}
    
    def _combine_housing_data(
        self,
        country: str,
        region: Optional[str],
        housing_data: Dict[str, Any],
        rent_data: Dict[str, Any]
    ) -> EurostatHousingData:
        """
        Combine housing and rent data into EurostatHousingData
        
        Args:
            country: Country name
            region: Region name
            housing_data: Housing cost data
            rent_data: Rent data
            
        Returns:
            Combined housing data
        """
        # Calculate data quality score
        data_quality = 0.0
        if housing_data.get("average_cost"):
            data_quality += 0.5
        if rent_data.get("average_rent"):
            data_quality += 0.5
        
        # Get most recent data year
        data_year = None
        if housing_data.get("data_year"):
            data_year = housing_data["data_year"]
        elif rent_data.get("data_year"):
            data_year = rent_data["data_year"]
        
        return EurostatHousingData(
            country=country,
            region=region,
            average_rent=rent_data.get("average_rent"),
            housing_costs=housing_data.get("average_cost"),
            data_year=data_year,
            data_quality=data_quality,
            source="eurostat"
        )
    
    async def get_available_countries(self) -> List[str]:
        """
        Get list of available countries in Eurostat
        
        Returns:
            List of country names
        """
        try:
            params = {"format": "json", "lang": "en"}
            data = await self._make_request("dissemination/statistics/1.0/data/geo", params)
            
            if "value" in data and isinstance(data["value"], dict):
                return list(data["value"].keys())
            
            return []
            
        except Exception as e:
            self.logger.warning(f"Failed to get available countries: {e}")
            return []
    
    def clear_cache(self):
        """Clear Eurostat API cache"""
        self._cache.clear()
        self.logger.info("Eurostat API cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "cache_entries": list(self._cache.keys())
        }
