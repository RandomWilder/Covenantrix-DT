"""
Agent Routes
Agent management and task execution
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging

from domain.agents.orchestrator import AgentOrchestrator, AgentRegistry
from domain.agents.models import TaskRequest, AgentType
from domain.agents.market_research import MarketResearchAgent
from core.dependencies import get_agent_orchestrator
from api.schemas.agents import (
    AgentListResponse, AgentCreateRequest, AgentResponse,
    TaskSubmitRequest, TaskResponse, TaskStatusResponse
)

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> AgentListResponse:
    """
    List all available agents
    
    Returns:
        List of agents
    """
    try:
        agents = await orchestrator.list_agents()
        
        return AgentListResponse(
            success=True,
            agents=agents,
            total_count=len(agents)
        )
        
    except Exception as e:
        logger.error(f"List agents failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=AgentResponse)
async def create_agent(
    request: AgentCreateRequest,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> AgentResponse:
    """
    Create a new agent
    
    Args:
        request: Agent creation request
        orchestrator: Agent orchestrator
        
    Returns:
        Created agent
    """
    try:
        agent = await orchestrator.create_agent(
            agent_type=request.agent_type,
            name=request.name,
            description=request.description,
            config=request.config
        )
        
        return AgentResponse(
            success=True,
            agent=agent.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Create agent failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks", response_model=TaskResponse)
async def submit_task(
    request: TaskSubmitRequest,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> TaskResponse:
    """
    Submit a task for agent execution
    
    Args:
        request: Task request
        orchestrator: Agent orchestrator
        
    Returns:
        Created task
    """
    try:
        task_request = TaskRequest(
            agent_id=request.agent_id,
            task_type=request.task_type,
            parameters=request.parameters
        )
        
        task = await orchestrator.submit_task(task_request)
        
        return TaskResponse(
            success=True,
            task=task.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Submit task failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> TaskStatusResponse:
    """
    Get task status
    
    Args:
        task_id: Task identifier
        orchestrator: Agent orchestrator
        
    Returns:
        Task status
    """
    try:
        task = await orchestrator.get_task_status(task_id)
        
        return TaskStatusResponse(
            success=True,
            task=task.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Get task status failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Get task result
    
    Args:
        task_id: Task identifier
        orchestrator: Agent orchestrator
        
    Returns:
        Task result
    """
    try:
        result = await orchestrator.get_task_result(task_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Get task result failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status")
async def get_system_status(
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Get agent system status
    
    Returns:
        System status
    """
    try:
        status = await orchestrator.get_system_status()
        
        return {
            "success": True,
            "status": status.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Get system status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))