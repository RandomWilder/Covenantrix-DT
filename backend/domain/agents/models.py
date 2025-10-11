"""
Agent Domain Models
Pure Python models for agent system
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid


class AgentType(str, Enum):
    """Types of agents"""
    MARKET_RESEARCH = "market_research"
    COMPLIANCE = "compliance"
    FINANCIAL_ANALYSIS = "financial_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    DOCUMENT_GENERATION = "document_generation"


class AgentStatus(str, Enum):
    """Agent status"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentCapability:
    """Agent capability description"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


@dataclass
class Agent:
    """
    Agent entity
    Represents an AI agent with specific capabilities
    """
    id: str
    type: AgentType
    name: str
    description: str
    capabilities: List[AgentCapability]
    status: AgentStatus = AgentStatus.IDLE
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create_new(
        cls,
        agent_type: AgentType,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        config: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None
    ) -> "Agent":
        """Create a new agent instance"""
        return cls(
            id=agent_id or str(uuid.uuid4()),
            type=agent_type,
            name=name,
            description=description,
            capabilities=capabilities,
            config=config or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description
                }
                for cap in self.capabilities
            ],
            "created_at": self.created_at.isoformat()
        }


@dataclass
class TaskRequest:
    """Request to execute agent task"""
    agent_id: str
    task_type: str
    parameters: Dict[str, Any]
    requested_by: Optional[str] = None
    priority: int = 5  # 1-10, higher = more important
    
    def validate(self) -> None:
        """Validate task request"""
        if not self.task_type:
            raise ValueError("task_type is required")
        
        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be a dictionary")
        
        if not 1 <= self.priority <= 10:
            raise ValueError("priority must be between 1 and 10")


@dataclass
class Task:
    """
    Agent task
    Represents a unit of work for an agent
    """
    id: str
    agent_id: str
    task_type: str
    parameters: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    
    @classmethod
    def create_new(
        cls,
        agent_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> "Task":
        """Create a new task instance"""
        return cls(
            id=task_id or str(uuid.uuid4()),
            agent_id=agent_id,
            task_type=task_type,
            parameters=parameters,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )
    
    def start(self) -> None:
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result: Dict[str, Any]) -> None:
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
        self.progress = 1.0
    
    def fail(self, error: str) -> None:
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error
    
    def update_progress(self, progress: float) -> None:
        """Update task progress"""
        self.progress = max(0.0, min(1.0, progress))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }


@dataclass
class AgentSystemStatus:
    """Overall agent system status"""
    total_agents: int
    active_agents: int
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_agents": self.total_agents,
            "active_agents": self.active_agents,
            "total_tasks": self.total_tasks,
            "pending_tasks": self.pending_tasks,
            "running_tasks": self.running_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks
        }