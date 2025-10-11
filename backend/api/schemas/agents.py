"""
Agent API Schemas
Request and response models for agent operations
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class AgentCreateRequest(BaseModel):
    """Agent creation request"""
    agent_type: str = Field(..., description="Type of agent to create")
    name: str = Field(..., min_length=1, description="Agent name")
    description: str = Field(..., description="Agent description")
    config: Optional[Dict[str, Any]] = Field(None, description="Agent configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "market_research",
                "name": "Market Research Agent",
                "description": "Analyzes rental market data",
                "config": {}
            }
        }


class AgentResponse(BaseModel):
    """Agent response"""
    success: bool
    agent: Dict[str, Any]


class AgentListResponse(BaseModel):
    """Agent list response"""
    success: bool
    agents: List[Dict[str, Any]]
    total_count: int


class TaskSubmitRequest(BaseModel):
    """Task submission request"""
    agent_id: str = Field(..., description="Agent ID to execute task")
    task_type: str = Field(..., description="Type of task")
    parameters: Dict[str, Any] = Field(..., description="Task parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent-123",
                "task_type": "rent_analysis",
                "parameters": {
                    "document_ids": ["doc-1", "doc-2"],
                    "property_address": "123 Main St"
                }
            }
        }


class TaskResponse(BaseModel):
    """Task response"""
    success: bool
    task: Dict[str, Any]


class TaskStatusResponse(BaseModel):
    """Task status response"""
    success: bool
    task: Dict[str, Any]


class TaskResultResponse(BaseModel):
    """Task result response"""
    success: bool
    task_id: str
    result: Dict[str, Any]


class SystemStatusResponse(BaseModel):
    """Agent system status response"""
    success: bool
    status: Dict[str, Any]