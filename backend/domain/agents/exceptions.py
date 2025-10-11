"""
Agent Domain Exceptions
"""
from typing import Optional
from core.exceptions import CovenantrixException
from fastapi import status


class AgentError(CovenantrixException):
    """Base agent error"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AgentNotFoundError(AgentError):
    """Agent not found"""
    
    def __init__(self, agent_id: str):
        super().__init__(f"Agent not found: {agent_id}")
        self.details = {"agent_id": agent_id}


class AgentExecutionError(AgentError):
    """Agent execution failed"""
    
    def __init__(self, message: str, agent_id: Optional[str] = None):
        super().__init__(f"Agent execution error: {message}")
        if agent_id:
            self.details = {"agent_id": agent_id}


class TaskNotFoundError(AgentError):
    """Task not found"""
    
    def __init__(self, task_id: str):
        super().__init__(f"Task not found: {task_id}")
        self.details = {"task_id": task_id}


class InvalidTaskParametersError(AgentError):
    """Invalid task parameters"""
    
    def __init__(self, message: str):
        super().__init__(f"Invalid task parameters: {message}")