"""
Agent Orchestrator
Manages agent lifecycle and task distribution
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from domain.agents.models import (
    Agent, Task, TaskRequest, TaskStatus, AgentStatus, AgentSystemStatus
)
from domain.agents.base import BaseAgent
from domain.agents.exceptions import (
    AgentNotFoundError, AgentExecutionError, TaskNotFoundError
)

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for managing available agent types and instances
    """
    
    def __init__(self):
        """Initialize agent registry"""
        self._agent_types: Dict[str, type] = {}
        self._agents: Dict[str, BaseAgent] = {}
    
    def register_agent_type(self, agent_type: str, agent_class: type) -> None:
        """
        Register an agent type
        
        Args:
            agent_type: Agent type identifier
            agent_class: Agent class (must inherit from BaseAgent)
        """
        if not issubclass(agent_class, BaseAgent):
            raise ValueError(f"Agent class must inherit from BaseAgent")
        
        self._agent_types[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")
    
    def create_agent(
        self,
        agent_type: str,
        agent_id: str,
        **kwargs
    ) -> BaseAgent:
        """
        Create an agent instance
        
        Args:
            agent_type: Type of agent to create
            agent_id: Unique agent identifier
            **kwargs: Additional arguments for agent constructor
            
        Returns:
            Created agent instance
        """
        if agent_type not in self._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = self._agent_types[agent_type]
        agent = agent_class(agent_id=agent_id, **kwargs)
        self._agents[agent_id] = agent
        
        logger.info(f"Created agent: {agent_id} ({agent_type})")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[BaseAgent]:
        """List all agent instances"""
        return list(self._agents.values())
    
    def list_agent_types(self) -> List[str]:
        """List available agent types"""
        return list(self._agent_types.keys())
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove agent from registry"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Removed agent: {agent_id}")
            return True
        return False


class AgentOrchestrator:
    """
    Agent orchestrator
    Coordinates agent execution and task management
    """
    
    def __init__(
        self, 
        registry: AgentRegistry,
        data_access_service: Optional[Any] = None,
        external_data_service: Optional[Any] = None
    ):
        """
        Initialize orchestrator
        
        Args:
            registry: Agent registry
            data_access_service: Agent data access service
            external_data_service: External data service
        """
        self.registry = registry
        self.data_access_service = data_access_service
        self.external_data_service = external_data_service
        self._tasks: Dict[str, Task] = {}
        self._task_lock = asyncio.Lock()
    
    async def create_agent(
        self,
        agent_type: str,
        name: str,
        description: str,
        config: Optional[Dict] = None
    ) -> Agent:
        """
        Create a new agent
        
        Args:
            agent_type: Type of agent
            name: Agent name
            description: Agent description
            config: Optional configuration
            
        Returns:
            Created agent
        """
        import uuid
        agent_id = str(uuid.uuid4())
        
        agent = self.registry.create_agent(
            agent_type=agent_type,
            agent_id=agent_id,
            name=name,
            description=description
        )
        
        # Inject data services if available
        if self.data_access_service and self.external_data_service:
            agent.set_data_services(
                data_access=self.data_access_service,
                external_data=self.external_data_service
            )
        
        return agent.agent
    
    async def submit_task(self, request: TaskRequest) -> Task:
        """
        Submit a task for execution
        
        Args:
            request: Task request
            
        Returns:
            Created task
            
        Raises:
            AgentNotFoundError: Agent not found
        """
        # Validate request
        request.validate()
        
        # Get agent
        agent = self.registry.get_agent(request.agent_id)
        if not agent:
            raise AgentNotFoundError(request.agent_id)
        
        # Create task
        task = Task.create_new(
            agent_id=request.agent_id,
            task_type=request.task_type,
            parameters=request.parameters
        )
        
        # Store task
        async with self._task_lock:
            self._tasks[task.id] = task
        
        # Execute task asynchronously (don't wait)
        asyncio.create_task(self._execute_task(task, agent))
        
        logger.info(f"Task submitted: {task.id} to agent {agent.agent.name}")
        return task
    
    async def _execute_task(self, task: Task, agent: BaseAgent) -> None:
        """
        Execute task (internal)
        
        Args:
            task: Task to execute
            agent: Agent to execute task
        """
        try:
            # Mark as running
            task.start()
            agent.set_status(AgentStatus.BUSY)
            
            logger.info(f"Executing task: {task.id}")
            
            # Execute
            result = await agent.execute_task(task)
            
            # Mark as completed
            task.complete(result)
            agent.set_status(AgentStatus.IDLE)
            
            logger.info(f"Task completed: {task.id}")
            
        except Exception as e:
            # Mark as failed
            task.fail(str(e))
            agent.set_status(AgentStatus.ERROR)
            
            logger.error(f"Task failed: {task.id} - {e}")
    
    async def get_task_status(self, task_id: str) -> Task:
        """
        Get task status
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task
            
        Raises:
            TaskNotFoundError: Task not found
        """
        task = self._tasks.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        return task
    
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get task result
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task result
            
        Raises:
            TaskNotFoundError: Task not found
            AgentExecutionError: Task not completed
        """
        task = await self.get_task_status(task_id)
        
        if task.status != TaskStatus.COMPLETED:
            raise AgentExecutionError(
                f"Task not completed: {task.status.value}",
                agent_id=task.agent_id
            )
        
        return task.result or {}
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents"""
        agents = self.registry.list_agents()
        return [agent.get_info() for agent in agents]
    
    async def list_agent_types(self) -> List[str]:
        """List available agent types"""
        return self.registry.list_agent_types()
    
    async def get_system_status(self) -> AgentSystemStatus:
        """Get overall system status"""
        agents = self.registry.list_agents()
        
        active_agents = sum(
            1 for agent in agents
            if agent.agent.status == AgentStatus.BUSY
        )
        
        tasks = list(self._tasks.values())
        
        return AgentSystemStatus(
            total_agents=len(agents),
            active_agents=active_agents,
            total_tasks=len(tasks),
            pending_tasks=sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            running_tasks=sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
            completed_tasks=sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            failed_tasks=sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        )
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed/failed tasks
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of tasks cleaned up
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        async with self._task_lock:
            tasks_to_remove = [
                task_id for task_id, task in self._tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
                and task.completed_at
                and task.completed_at < cutoff
            ]
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
        
        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
        return len(tasks_to_remove)