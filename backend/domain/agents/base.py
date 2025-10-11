"""
Base Agent Interface
Abstract base class for all agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

from domain.agents.models import (
    Agent, AgentCapability, AgentType, AgentStatus, Task
)

logger = logging.getLogger(__name__)


class IAgentDataAccess(ABC):
    """
    Abstract interface for agent data access
    Allows agents to access document data and analytics
    """
    
    @abstractmethod
    async def get_document_content(self, document_id: str) -> Optional[str]:
        """Get document content by ID"""
        pass
    
    @abstractmethod
    async def get_document_analytics(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for document"""
        pass
    
    @abstractmethod
    async def query_documents(
        self,
        query: str,
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Query documents using RAG"""
        pass
    
    @abstractmethod
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents"""
        pass


class IExternalDataService(ABC):
    """
    Abstract interface for external data sources
    Allows agents to access external APIs and data
    """
    
    @abstractmethod
    async def fetch_market_data(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch market data from external sources"""
        pass
    
    @abstractmethod
    async def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """Geocode address to coordinates"""
        pass


class BaseAgent(ABC):
    """
    Abstract base class for all agents
    Defines the interface that all agents must implement
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        agent_type: AgentType
    ):
        """
        Initialize base agent
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            description: Agent description
            agent_type: Type of agent
        """
        self.agent = Agent.create_new(
            agent_type=agent_type,
            name=name,
            description=description,
            capabilities=self.get_capabilities(),
            agent_id=agent_id
        )
        
        # Data access services (injected)
        self.data_access: Optional[IAgentDataAccess] = None
        self.external_data: Optional[IExternalDataService] = None
        
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def set_data_services(
        self,
        data_access: IAgentDataAccess,
        external_data: IExternalDataService
    ) -> None:
        """
        Inject data access services
        
        Args:
            data_access: Document data access service
            external_data: External data service
        """
        self.data_access = data_access
        self.external_data = external_data
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """
        Get list of agent capabilities
        
        Returns:
            List of capabilities this agent can perform
        """
        pass
    
    @abstractmethod
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task
        
        Args:
            task: Task to execute
            
        Returns:
            Task result dictionary
            
        Raises:
            AgentExecutionError: Task execution failed
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return self.agent.to_dict()
    
    def set_status(self, status: AgentStatus) -> None:
        """Update agent status"""
        self.agent.status = status
    
    def validate_task_parameters(
        self,
        parameters: Dict[str, Any],
        required_fields: List[str]
    ) -> None:
        """
        Validate task parameters
        
        Args:
            parameters: Task parameters
            required_fields: Required field names
            
        Raises:
            ValueError: Missing required fields
        """
        missing = [field for field in required_fields if field not in parameters]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")