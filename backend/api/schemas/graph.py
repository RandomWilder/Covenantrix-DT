"""
Knowledge Graph Pydantic Schemas
Response models for graph API endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class GraphNode(BaseModel):
    """Represents a node (entity) in the knowledge graph"""
    id: str = Field(..., description="Unique identifier for the node")
    label: str = Field(..., description="Display label for the node")
    type: str = Field(..., description="Entity type (person, organization, location, etc.)")
    description: str = Field(default="", description="Description of the entity")
    source_id: Optional[str] = Field(default=None, description="Source document ID")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "entity_123",
                "label": "John Doe",
                "type": "person",
                "description": "CEO of Example Corp",
                "source_id": "doc_456"
            }
        }


class GraphEdge(BaseModel):
    """Represents an edge (relationship) between two nodes"""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    weight: float = Field(default=1.0, description="Relationship weight/strength")
    description: str = Field(default="", description="Description of the relationship")
    keywords: str = Field(default="", description="Keywords associated with the relationship")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "entity_123",
                "target": "entity_456",
                "weight": 5.0,
                "description": "Works with",
                "keywords": "collaboration, partnership"
            }
        }


class GraphData(BaseModel):
    """Complete graph data structure with nodes and edges"""
    nodes: List[GraphNode] = Field(..., description="List of nodes in the graph")
    edges: List[GraphEdge] = Field(..., description="List of edges in the graph")
    total_nodes: int = Field(..., description="Total number of nodes available")
    total_edges: int = Field(..., description="Total number of edges available")

    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [],
                "edges": [],
                "total_nodes": 100,
                "total_edges": 150
            }
        }


class GraphStats(BaseModel):
    """Statistical information about the knowledge graph"""
    total_nodes: int = Field(..., description="Total number of nodes")
    total_edges: int = Field(..., description="Total number of edges")
    entity_types: Dict[str, int] = Field(..., description="Count of entities by type")
    density: float = Field(..., description="Graph density (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_nodes": 100,
                "total_edges": 150,
                "entity_types": {
                    "person": 30,
                    "organization": 25,
                    "location": 20,
                    "event": 15,
                    "concept": 10
                },
                "density": 0.0303
            }
        }


class EntityListResponse(BaseModel):
    """Response from the entities endpoint"""
    entities: List[GraphNode] = Field(..., description="List of entities")
    count: int = Field(..., description="Number of entities returned")

    class Config:
        json_schema_extra = {
            "example": {
                "entities": [],
                "count": 10
            }
        }


class RelationshipListResponse(BaseModel):
    """Response from the relationships endpoint"""
    relationships: List[GraphEdge] = Field(..., description="List of relationships")
    count: int = Field(..., description="Number of relationships returned")

    class Config:
        json_schema_extra = {
            "example": {
                "relationships": [],
                "count": 15
            }
        }
