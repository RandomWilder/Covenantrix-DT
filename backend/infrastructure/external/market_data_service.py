"""
Unified Market Data Service
Combines multiple external APIs for comprehensive market data
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from infrastructure.external.numbeo_api import NumbeoAPIService, NumbeoAPIError
from infrastructure.external.geocoding_service import GeocodingService, GeocodingError
from infrastructure.external.eurostat_api import EurostatAPIService, EurostatAPIError

logger = logging.getLogger(__name__)


@dataclass
class MarketDataResult:
    """Unified market data result"""
    average_rent: Optional[float] = None
    median_rent: Optional[float] = None
    min_rent: Optional[float] = None
    max_rent: Optional[float] = None
    sample_size: int = 0
    data_quality: float = 0.0
    confidence: float = 0.0
    source: str = "unknown"
    location: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    last_updated: Optional[datetime] = None
    market_factors: Dict[str, Any] = None
    source_chain: List[str] = None


class MarketDataServiceError(Exception):
    """Market data service errors"""
    pass


class MarketDataService:
    """
    Unified market data service
    Combines Numbeo, Eurostat, and geocoding services for comprehensive market analysis
    """
    
    def __init__(self):
        """Initialize market data service"""
        self.numbeo_service = NumbeoAPIService()
        self.geocoding_service = GeocodingService()
        self.eurostat_service = EurostatAPIService()
        self.logger = logging.getLogger(__name__)
    
    async def get_market_data(
        self,
        location: str,
        property_type: str = "apartment",
        bedrooms: Optional[int] = None,
        size_sqm: Optional[float] = None
    ) -> MarketDataResult:
        """
        Get comprehensive market data for a location
        
        Args:
            location: Property location
            property_type: Type of property
            bedrooms: Number of bedrooms
            size_sqm: Property size in square meters
            
        Returns:
            Unified market data result
        """
        try:
            # Step 1: Geocode the location for geographic intelligence
            geocoding_result = await self.geocoding_service.geocode(location)
            if not geocoding_result:
                raise MarketDataServiceError(f"Could not geocode location: {location}")
            
            # Step 2: Try multiple data sources with intelligent fallback
            market_data = await self._fetch_market_data_with_intelligence(
                location=location,
                geocoding_result=geocoding_result,
                property_type=property_type,
                bedrooms=bedrooms,
                size_sqm=size_sqm
            )
            
            return market_data
            
        except MarketDataServiceError:
            raise
        except Exception as e:
            raise MarketDataServiceError(f"Failed to get market data: {str(e)}")
    
    async def _fetch_market_data_with_intelligence(
        self,
        location: str,
        geocoding_result,
        property_type: str,
        bedrooms: Optional[int],
        size_sqm: Optional[float]
    ) -> MarketDataResult:
        """
        Fetch market data with geographic intelligence and multi-source strategy
        
        Args:
            location: Original location string
            geocoding_result: Geocoding result with coordinates and address components
            property_type: Property type
            bedrooms: Number of bedrooms
            size_sqm: Property size
            
        Returns:
            Market data result with source attribution
        """
        source_chain = []
        best_result = None
        best_confidence = 0.0
        
        # Try Numbeo first (global coverage, high quality)
        if geocoding_result.city and geocoding_result.country:
            try:
                self.logger.info(f"Trying Numbeo API for {geocoding_result.city}, {geocoding_result.country}")
                numbeo_data = await self.numbeo_service.get_city_data(
                    geocoding_result.city, 
                    geocoding_result.country
                )
                
                if numbeo_data and numbeo_data.data_quality > 0.3:
                    numbeo_result = self._convert_numbeo_to_result(
                        numbeo_data, geocoding_result, property_type, bedrooms, size_sqm
                    )
                    
                    if numbeo_result.confidence > best_confidence:
                        best_result = numbeo_result
                        best_confidence = numbeo_result.confidence
                    
                    source_chain.append("numbeo")
                    self.logger.info(f"Numbeo data retrieved with confidence: {numbeo_result.confidence}")
                
            except NumbeoAPIError as e:
                self.logger.warning(f"Numbeo API failed: {e}")
                source_chain.append(f"numbeo_failed: {str(e)}")
        
        # Try Eurostat for EU countries (official statistics)
        if geocoding_result.country and self._is_eu_country(geocoding_result.country):
            try:
                self.logger.info(f"Trying Eurostat API for {geocoding_result.country}")
                eurostat_data = await self.eurostat_service.get_housing_data(geocoding_result.country)
                
                if eurostat_data and eurostat_data.data_quality > 0.2:
                    eurostat_result = self._convert_eurostat_to_result(
                        eurostat_data, geocoding_result, property_type, bedrooms, size_sqm
                    )
                    
                    if eurostat_result.confidence > best_confidence:
                        best_result = eurostat_result
                        best_confidence = eurostat_result.confidence
                    
                    source_chain.append("eurostat")
                    self.logger.info(f"Eurostat data retrieved with confidence: {eurostat_result.confidence}")
                
            except EurostatAPIError as e:
                self.logger.warning(f"Eurostat API failed: {e}")
                source_chain.append(f"eurostat_failed: {str(e)}")
        
        # Fallback to generic data if no sources worked
        if not best_result:
            self.logger.warning("All external APIs failed, using fallback data")
            best_result = self._get_fallback_result(location, geocoding_result, property_type, bedrooms)
            source_chain.append("fallback")
        
        # Add source chain to result
        best_result.source_chain = source_chain
        best_result.location = location
        
        return best_result
    
    def _convert_numbeo_to_result(
        self,
        numbeo_data,
        geocoding_result,
        property_type: str,
        bedrooms: Optional[int],
        size_sqm: Optional[float]
    ) -> MarketDataResult:
        """
        Convert Numbeo data to unified result format
        
        Args:
            numbeo_data: Numbeo property data
            geocoding_result: Geocoding result
            property_type: Property type
            bedrooms: Number of bedrooms
            size_sqm: Property size
            
        Returns:
            Market data result
        """
        # Select appropriate rent based on bedrooms and location
        rent_value = self._select_best_rent_value(numbeo_data, bedrooms, geocoding_result)
        
        # Calculate confidence based on data quality and geographic accuracy
        confidence = numbeo_data.data_quality
        if rent_value:
            confidence += 0.2
        if bedrooms and bedrooms <= 3:
            confidence += 0.1
        if geocoding_result.confidence > 0.7:
            confidence += 0.1
        
        confidence = min(1.0, confidence)
        
        # Calculate rent range estimates
        min_rent = rent_value * 0.8 if rent_value else None
        max_rent = rent_value * 1.2 if rent_value else None
        
        return MarketDataResult(
            average_rent=rent_value,
            median_rent=rent_value,  # Use average as median approximation
            min_rent=min_rent,
            max_rent=max_rent,
            sample_size=numbeo_data.sample_size,
            data_quality=numbeo_data.data_quality,
            confidence=confidence,
            source="numbeo",
            city=geocoding_result.city,
            country=geocoding_result.country,
            last_updated=datetime.utcnow(),
            market_factors={
                "city": numbeo_data.city,
                "country": numbeo_data.country,
                "rent_1br": numbeo_data.average_rent_1br,
                "rent_2br": numbeo_data.average_rent_2br,
                "rent_3br": numbeo_data.average_rent_3br,
                "rent_center": numbeo_data.average_rent_center,
                "rent_outside": numbeo_data.average_rent_outside,
                "geocoding_confidence": geocoding_result.confidence
            }
        )
    
    def _convert_eurostat_to_result(
        self,
        eurostat_data,
        geocoding_result,
        property_type: str,
        bedrooms: Optional[int],
        size_sqm: Optional[float]
    ) -> MarketDataResult:
        """
        Convert Eurostat data to unified result format
        
        Args:
            eurostat_data: Eurostat housing data
            geocoding_result: Geocoding result
            property_type: Property type
            bedrooms: Number of bedrooms
            size_sqm: Property size
            
        Returns:
            Market data result
        """
        # Use Eurostat rent data if available
        rent_value = eurostat_data.average_rent
        
        # Calculate confidence based on data quality and geographic accuracy
        confidence = eurostat_data.data_quality
        if rent_value:
            confidence += 0.3
        if geocoding_result.confidence > 0.7:
            confidence += 0.1
        
        confidence = min(1.0, confidence)
        
        # Calculate rent range estimates
        min_rent = rent_value * 0.8 if rent_value else None
        max_rent = rent_value * 1.2 if rent_value else None
        
        return MarketDataResult(
            average_rent=rent_value,
            median_rent=rent_value,  # Use average as median approximation
            min_rent=min_rent,
            max_rent=max_rent,
            sample_size=0,  # Eurostat doesn't provide sample size
            data_quality=eurostat_data.data_quality,
            confidence=confidence,
            source="eurostat",
            city=geocoding_result.city,
            country=geocoding_result.country,
            last_updated=datetime.utcnow(),
            market_factors={
                "country": eurostat_data.country,
                "region": eurostat_data.region,
                "housing_costs": eurostat_data.housing_costs,
                "data_year": eurostat_data.data_year,
                "geocoding_confidence": geocoding_result.confidence
            }
        )
    
    def _select_best_rent_value(self, numbeo_data, bedrooms: Optional[int], geocoding_result) -> Optional[float]:
        """
        Select the best rent value from Numbeo data based on bedrooms and location
        
        Args:
            numbeo_data: Numbeo property data
            bedrooms: Number of bedrooms
            geocoding_result: Geocoding result
            
        Returns:
            Best rent value or None
        """
        # Priority order for rent selection
        rent_options = []
        
        # Add bedroom-specific rents
        if bedrooms == 1 and numbeo_data.average_rent_1br:
            rent_options.append(("1br", numbeo_data.average_rent_1br, 0.9))
        elif bedrooms == 2 and numbeo_data.average_rent_2br:
            rent_options.append(("2br", numbeo_data.average_rent_2br, 0.9))
        elif bedrooms == 3 and numbeo_data.average_rent_3br:
            rent_options.append(("3br", numbeo_data.average_rent_3br, 0.9))
        
        # Add location-specific rents (center vs outside)
        if numbeo_data.average_rent_center:
            # Prefer center if geocoding confidence is high (likely city center)
            center_priority = 0.8 if geocoding_result.confidence > 0.7 else 0.6
            rent_options.append(("center", numbeo_data.average_rent_center, center_priority))
        
        if numbeo_data.average_rent_outside:
            # Prefer outside if geocoding confidence is lower (likely suburban)
            outside_priority = 0.7 if geocoding_result.confidence < 0.6 else 0.5
            rent_options.append(("outside", numbeo_data.average_rent_outside, outside_priority))
        
        # Select best option based on priority
        if rent_options:
            rent_options.sort(key=lambda x: x[2], reverse=True)
            return rent_options[0][1]
        
        return None
    
    def _is_eu_country(self, country: str) -> bool:
        """
        Check if country is in the European Union
        
        Args:
            country: Country name
            
        Returns:
            True if EU country, False otherwise
        """
        eu_countries = {
            "austria", "belgium", "bulgaria", "croatia", "cyprus", "czech republic", "czechia",
            "denmark", "estonia", "finland", "france", "germany", "greece", "hungary",
            "ireland", "italy", "latvia", "lithuania", "luxembourg", "malta", "netherlands",
            "poland", "portugal", "romania", "slovakia", "slovenia", "spain", "sweden"
        }
        
        return country.lower() in eu_countries
    
    def _get_fallback_result(
        self,
        location: str,
        geocoding_result,
        property_type: str,
        bedrooms: Optional[int]
    ) -> MarketDataResult:
        """
        Get fallback market data when external APIs fail
        
        Args:
            location: Property location
            geocoding_result: Geocoding result
            property_type: Property type
            bedrooms: Number of bedrooms
            
        Returns:
            Fallback market data result
        """
        # Basic fallback based on property type and bedrooms
        base_rent = 2000.0  # Default base rent
        
        # Adjust for bedrooms
        if bedrooms:
            if bedrooms == 1:
                base_rent = 1500.0
            elif bedrooms == 2:
                base_rent = 2000.0
            elif bedrooms == 3:
                base_rent = 2500.0
            elif bedrooms >= 4:
                base_rent = 3000.0
        
        # Adjust for property type
        if property_type.lower() == "house":
            base_rent *= 1.2
        elif property_type.lower() == "studio":
            base_rent *= 0.7
        
        return MarketDataResult(
            average_rent=base_rent,
            median_rent=base_rent,
            min_rent=base_rent * 0.7,
            max_rent=base_rent * 1.3,
            sample_size=0,
            data_quality=0.1,  # Very low quality for fallback
            confidence=0.3,  # Low confidence
            source="fallback",
            city=geocoding_result.city,
            country=geocoding_result.country,
            last_updated=datetime.utcnow(),
            market_factors={
                "location": location,
                "property_type": property_type,
                "bedrooms": bedrooms,
                "note": "Fallback data - external APIs unavailable",
                "geocoding_confidence": geocoding_result.confidence
            }
        )
    
    async def validate_location(self, location: str) -> bool:
        """
        Validate if location can be geocoded and has market data
        
        Args:
            location: Location string
            
        Returns:
            True if location is valid, False otherwise
        """
        try:
            # Check if location can be geocoded
            geocoding_result = await self.geocoding_service.geocode(location)
            if not geocoding_result:
                return False
            
            # Check if we have market data for this location
            market_data = await self.get_market_data(location)
            return market_data.confidence > 0.3
            
        except Exception:
            return False
    
    def clear_caches(self):
        """Clear all service caches"""
        self.numbeo_service.clear_cache()
        self.geocoding_service.clear_cache()
        self.eurostat_service.clear_cache()
        self.logger.info("All market data service caches cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for all services"""
        return {
            "numbeo": self.numbeo_service.get_cache_stats(),
            "geocoding": self.geocoding_service.get_cache_stats(),
            "eurostat": self.eurostat_service.get_cache_stats()
        }
