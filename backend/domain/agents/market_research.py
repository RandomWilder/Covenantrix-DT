"""
Market Research Agent
Analyzes rental properties and provides market recommendations
"""
import logging
from typing import Dict, Any, List, Optional

from domain.agents.base import BaseAgent, IAgentDataAccess, IExternalDataService
from domain.agents.models import (
    AgentType, AgentCapability, Task, TaskStatus
)
from domain.agents.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)


class MarketResearchAgent(BaseAgent):
    """
    Market Research Agent
    Analyzes lease documents and provides rent recommendations
    based on market data and property characteristics
    """
    
    TASK_TYPE_RENT_ANALYSIS = "rent_analysis"
    
    def __init__(
        self,
        agent_id: str,
        name: str = "Market Research Agent",
        description: str = "Analyzes rental market and provides recommendations"
    ):
        """Initialize market research agent"""
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            agent_type=AgentType.MARKET_RESEARCH
        )
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get agent capabilities"""
        return [
            AgentCapability(
                name="rent_analysis",
                description="Analyze property and provide rent recommendations",
                input_schema={
                    "type": "object",
                    "properties": {
                        "document_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Document IDs to analyze (lease agreements)"
                        },
                        "property_address": {
                            "type": "string",
                            "description": "Property address (optional)"
                        }
                    },
                    "required": ["document_ids"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "current_rent": {"type": "number"},
                        "recommended_rent": {"type": "number"},
                        "market_average": {"type": "number"},
                        "confidence": {"type": "number"},
                        "reasoning": {"type": "string"},
                        "market_factors": {"type": "object"}
                    }
                }
            )
        ]
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute market research task
        
        Args:
            task: Task to execute
            
        Returns:
            Analysis result
        """
        self.logger.info(f"Executing task: {task.task_type}")
        
        if task.task_type == self.TASK_TYPE_RENT_ANALYSIS:
            return await self._execute_rent_analysis(task)
        else:
            raise AgentExecutionError(
                f"Unknown task type: {task.task_type}",
                agent_id=self.agent.id
            )
    
    async def _execute_rent_analysis(self, task: Task) -> Dict[str, Any]:
        """
        Execute rent analysis
        
        Args:
            task: Task with parameters
            
        Returns:
            Rent analysis result
        """
        # Validate data access
        if not self.data_access or not self.external_data:
            raise AgentExecutionError(
                "Data access services not configured",
                agent_id=self.agent.id
            )
        
        # Validate parameters
        self.validate_task_parameters(
            task.parameters,
            required_fields=["document_ids"]
        )
        
        document_ids = task.parameters["document_ids"]
        
        try:
            # Step 1: Extract property information from documents (20%)
            task.update_progress(0.1)
            property_info = await self._extract_property_info(document_ids)
            
            # Step 2: Get current rent from documents (40%)
            task.update_progress(0.3)
            current_rent = await self._extract_current_rent(document_ids)
            
            # Step 3: Fetch market data (60%)
            task.update_progress(0.5)
            market_data = await self._fetch_market_data(property_info)
            
            # Step 4: Calculate recommendation (80%)
            task.update_progress(0.7)
            recommendation = self._calculate_recommendation(
                property_info,
                current_rent,
                market_data
            )
            
            # Step 5: Generate reasoning (100%)
            task.update_progress(0.9)
            reasoning = self._generate_reasoning(
                property_info,
                current_rent,
                market_data,
                recommendation
            )
            
            result = {
                "property_info": property_info,
                "current_rent": current_rent,
                "recommended_rent": recommendation["recommended_rent"],
                "market_average": recommendation["market_average"],
                "confidence": recommendation["confidence"],
                "reasoning": reasoning,
                "market_factors": market_data,
                "analysis_date": task.created_at.isoformat()
            }
            
            self.logger.info(
                f"Rent analysis completed: Current ${current_rent} -> "
                f"Recommended ${recommendation['recommended_rent']}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Rent analysis failed: {e}")
            raise AgentExecutionError(
                f"Rent analysis failed: {str(e)}",
                agent_id=self.agent.id
            )
    
    async def _extract_property_info(
        self,
        document_ids: List[str]
    ) -> Dict[str, Any]:
        """Extract property information from documents"""
        property_info = {
            "address": None,
            "size_sqm": None,
            "bedrooms": None,
            "bathrooms": None,
            "property_type": "apartment",
            "floor": None,
            "amenities": []
        }
        
        # Get analytics for each document
        for doc_id in document_ids:
            analytics = await self.data_access.get_document_analytics(doc_id)
            if not analytics:
                continue
            
            # Extract from entities
            if "metadata" in analytics:
                metadata = analytics["metadata"]
                
                # Look for address
                for entity in metadata.get("entities", []):
                    if entity.get("type") == "address" and not property_info["address"]:
                        property_info["address"] = entity.get("name")
        
        # Query for additional property details
        if document_ids:
            query_result = await self.data_access.query_documents(
                query="property size, bedrooms, bathrooms, floor, amenities",
                document_ids=document_ids
            )
            
            # Parse query response for property details
            # (simplified - real implementation would use LLM to extract structured data)
            response = query_result.get("response", "")
            
            # Extract numbers from response (very basic)
            import re
            numbers = re.findall(r'\d+', response)
            if len(numbers) >= 2:
                property_info["size_sqm"] = int(numbers[0])
                property_info["bedrooms"] = int(numbers[1])
        
        return property_info
    
    async def _extract_current_rent(
        self,
        document_ids: List[str]
    ) -> Optional[float]:
        """Extract current rent from documents"""
        # Look for rent in analytics
        for doc_id in document_ids:
            analytics = await self.data_access.get_document_analytics(doc_id)
            if not analytics:
                continue
            
            metadata = analytics.get("metadata", {})
            
            # Look for monthly rent in monetary values
            for value in metadata.get("monetary_values", []):
                context = value.get("context", "").lower()
                if "rent" in context or "monthly" in context:
                    return float(value.get("amount", 0))
        
        return None
    
    async def _fetch_market_data(
        self,
        property_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch market data from external sources"""
        try:
            # Fetch market data using external data service
            market_data = await self.external_data.fetch_market_data({
                "location": property_info.get("address"),
                "property_type": property_info.get("property_type", "apartment"),
                "bedrooms": property_info.get("bedrooms"),
                "size_sqm": property_info.get("size_sqm")
            })
            
            self.logger.info(f"Market data fetched from source: {market_data.get('source', 'unknown')}")
            return market_data
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch market data: {e}")
            # Return fallback data with low confidence
            return {
                "average_rent": 2500.0,
                "median_rent": 2400.0,
                "min_rent": 1800.0,
                "max_rent": 3500.0,
                "sample_size": 0,
                "data_quality": 0.1,
                "confidence": 0.3,
                "source": "fallback",
                "source_chain": [f"external_data_failed: {str(e)}"]
            }
    
    def _calculate_recommendation(
        self,
        property_info: Dict[str, Any],
        current_rent: Optional[float],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate rent recommendation with enhanced algorithm"""
        market_avg = market_data.get("average_rent", 2500.0)
        
        # Start with market average
        recommended_rent = market_avg
        
        # Adjust for property size (size_sqm > 100: +10%, < 60: -10%)
        size_sqm = property_info.get("size_sqm")
        if size_sqm:
            if size_sqm > 100:
                recommended_rent *= 1.1
            elif size_sqm < 60:
                recommended_rent *= 0.9
        
        # Adjust for bedroom count
        bedrooms = property_info.get("bedrooms")
        if bedrooms:
            if bedrooms == 1:
                recommended_rent *= 0.8
            elif bedrooms == 2:
                recommended_rent *= 1.0
            elif bedrooms == 3:
                recommended_rent *= 1.2
            elif bedrooms >= 4:
                recommended_rent *= 1.4
        
        # Use external data confidence if available, otherwise calculate
        if "confidence" in market_data:
            confidence = market_data["confidence"]
        else:
            # Calculate confidence based on data availability
            confidence = 0.5
            if market_data.get("sample_size", 0) > 10:
                confidence += 0.3
            if property_info.get("address"):
                confidence += 0.1
            if size_sqm:
                confidence += 0.1
            confidence = min(1.0, confidence)
        
        return {
            "recommended_rent": round(recommended_rent, 2),
            "market_average": market_avg,
            "confidence": confidence
        }
    
    def _generate_reasoning(
        self,
        property_info: Dict[str, Any],
        current_rent: Optional[float],
        market_data: Dict[str, Any],
        recommendation: Dict[str, Any]
    ) -> str:
        """Generate human-readable reasoning"""
        lines = []
        
        lines.append("Market Analysis Summary:")
        lines.append("")
        
        # Current rent
        if current_rent:
            lines.append(f"Current Rent: ${current_rent:,.2f}/month")
        else:
            lines.append("Current Rent: Not available in documents")
        
        # Recommendation
        lines.append(f"Recommended Rent: ${recommendation['recommended_rent']:,.2f}/month")
        lines.append(f"Market Average: ${recommendation['market_average']:,.2f}/month")
        
        # Confidence
        confidence_pct = recommendation['confidence'] * 100
        lines.append(f"Confidence: {confidence_pct:.0f}%")
        lines.append("")
        
        # Factors
        lines.append("Analysis Factors:")
        if property_info.get("size_sqm"):
            lines.append(f"- Property size: {property_info['size_sqm']} sqm")
        if property_info.get("bedrooms"):
            lines.append(f"- Bedrooms: {property_info['bedrooms']}")
        if market_data.get("sample_size"):
            lines.append(f"- Market sample size: {market_data['sample_size']} properties")
        
        # Data source information
        source = market_data.get("source", "unknown")
        lines.append(f"- Data source: {source}")
        
        if "source_chain" in market_data:
            source_chain = market_data["source_chain"]
            if len(source_chain) > 1:
                lines.append(f"- Data sources tried: {', '.join(source_chain)}")
        
        # Market factors if available
        market_factors = market_data.get("market_factors", {})
        if market_factors:
            lines.append("- Market factors:")
            for key, value in market_factors.items():
                if value is not None:
                    lines.append(f"  * {key}: {value}")
        
        return "\n".join(lines)