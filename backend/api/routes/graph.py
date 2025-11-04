"""
Knowledge Graph Routes
Expose LightRAG's knowledge graph data for visualization
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, List, Any, Optional
import logging

from core.dependencies import get_rag_engine
from infrastructure.ai.rag_engine import RAGEngine
from api.schemas.graph import (
    GraphNode, GraphEdge, GraphData, GraphStats,
    EntityListResponse, RelationshipListResponse
)

router = APIRouter(prefix="/api/graph", tags=["graph"])
logger = logging.getLogger(__name__)


def _get_graph_storage_from_rag(rag_engine: RAGEngine):
    """
    Extract NetworkXStorage instance from LightRAG
    
    Args:
        rag_engine: Initialized RAG engine
        
    Returns:
        NetworkXStorage object or None if not available
    """
    try:
        # Access LightRAG instance (private attribute)
        if not hasattr(rag_engine, '_rag') or rag_engine._rag is None:
            logger.warning("RAG engine not initialized or _rag is None")
            return None
        
        # Access the knowledge graph storage (NetworkXStorage wrapper)
        lightrag_instance = rag_engine._rag
        if not hasattr(lightrag_instance, 'chunk_entity_relation_graph'):
            logger.warning("LightRAG instance does not have chunk_entity_relation_graph")
            return None
            
        graph_storage = lightrag_instance.chunk_entity_relation_graph
        
        if graph_storage is None:
            logger.warning("chunk_entity_relation_graph is None")
            return None
            
        return graph_storage
    except Exception as e:
        logger.error(f"Error accessing graph storage from RAG engine: {e}")
        return None


@router.get("/entities", response_model=EntityListResponse)
async def get_entities(
    limit: Optional[int] = Query(None, description="Maximum number of entities to return"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    rag_engine: RAGEngine = Depends(get_rag_engine)
) -> EntityListResponse:
    """
    Get list of entities from the knowledge graph
    
    Args:
        limit: Optional limit on number of entities
        entity_type: Optional filter by entity type
        rag_engine: RAG engine dependency
        
    Returns:
        List of entities with metadata
    """
    try:
        graph_storage = _get_graph_storage_from_rag(rag_engine)
        
        if graph_storage is None:
            logger.warning("No graph data available")
            return EntityListResponse(entities=[], count=0)
        
        # Get all nodes from NetworkXStorage
        all_nodes = await graph_storage.get_all_nodes()
        
        if not all_nodes:
            logger.warning("No nodes found in graph")
            return EntityListResponse(entities=[], count=0)
        
        # Extract entities with data
        entities = []
        for node_data in all_nodes:
            # Filter by entity type if specified
            node_type = node_data.get('entity_type', node_data.get('type', 'unknown'))
            if entity_type and node_type != entity_type:
                continue
            
            entity = GraphNode(
                id=str(node_data.get('id', node_data.get('entity_name', ''))),
                label=node_data.get('entity_name', node_data.get('label', '')),
                type=node_type,
                description=node_data.get('description', ''),
                source_id=node_data.get('source_id')
            )
            entities.append(entity)
            
            # Apply limit if specified
            if limit and len(entities) >= limit:
                break
        
        logger.info(f"Retrieved {len(entities)} entities")
        return EntityListResponse(entities=entities, count=len(entities))
        
    except Exception as e:
        logger.error(f"Error retrieving entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve entities: {str(e)}"
        )


@router.get("/relationships", response_model=RelationshipListResponse)
async def get_relationships(
    rag_engine: RAGEngine = Depends(get_rag_engine)
) -> RelationshipListResponse:
    """
    Get list of relationships (edges) from the knowledge graph
    
    Args:
        rag_engine: RAG engine dependency
        
    Returns:
        List of relationships with metadata
    """
    try:
        graph_storage = _get_graph_storage_from_rag(rag_engine)
        
        if graph_storage is None:
            logger.warning("No graph data available")
            return RelationshipListResponse(relationships=[], count=0)
        
        # Get all edges from NetworkXStorage
        all_edges = await graph_storage.get_all_edges()
        
        if not all_edges:
            logger.warning("No edges found in graph")
            return RelationshipListResponse(relationships=[], count=0)
        
        # Extract relationships with data
        # CRITICAL: GraphML uses 'source' and 'target' attributes, not 'source_id'/'target_id'
        relationships = []
        for edge_data in all_edges:
            relationship = GraphEdge(
                source=str(edge_data.get('source', edge_data.get('source_id', ''))),
                target=str(edge_data.get('target', edge_data.get('target_id', ''))),
                weight=edge_data.get('weight', 1.0),
                description=edge_data.get('description', ''),
                keywords=edge_data.get('keywords', '')
            )
            relationships.append(relationship)
        
        logger.info(f"Retrieved {len(relationships)} relationships")
        return RelationshipListResponse(relationships=relationships, count=len(relationships))
        
    except Exception as e:
        logger.error(f"Error retrieving relationships: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve relationships: {str(e)}"
        )


@router.get("/graph", response_model=GraphData)
async def get_full_graph(
    max_nodes: int = Query(500, description="Maximum number of nodes to return"),
    rag_engine: RAGEngine = Depends(get_rag_engine)
) -> GraphData:
    """
    Get complete graph structure with nodes and edges
    
    Args:
        max_nodes: Maximum number of nodes to return (default 500)
        rag_engine: RAG engine dependency
        
    Returns:
        Complete graph with nodes and edges arrays
    """
    try:
        graph_storage = _get_graph_storage_from_rag(rag_engine)
        
        if graph_storage is None:
            logger.warning("No graph data available")
            return GraphData(
                nodes=[],
                edges=[],
                total_nodes=0,
                total_edges=0
            )
        
        # Get all nodes and edges
        all_nodes = await graph_storage.get_all_nodes()
        all_edges = await graph_storage.get_all_edges()
        
        if not all_nodes:
            logger.warning("No nodes found in graph")
            return GraphData(
                nodes=[],
                edges=[],
                total_nodes=0,
                total_edges=0
            )
        
        # Get total counts
        total_nodes = len(all_nodes)
        total_edges = len(all_edges) if all_edges else 0
        
        logger.info(f"Full graph has {total_nodes} nodes and {total_edges} edges")
        
        # Extract nodes (limited to max_nodes)
        nodes = []
        node_ids = set()
        
        for node_data in all_nodes[:max_nodes]:
            node_id = str(node_data.get('id', node_data.get('entity_name', '')))
            node_ids.add(node_id)
            
            node = GraphNode(
                id=node_id,
                label=node_data.get('entity_name', node_data.get('label', node_id)),
                type=node_data.get('entity_type', node_data.get('type', 'unknown')),
                description=node_data.get('description', ''),
                source_id=node_data.get('source_id')
            )
            nodes.append(node)
        
        # Extract edges (only between nodes in the limited set)
        # CRITICAL: GraphML uses 'source' and 'target' attributes, not 'source_id'/'target_id'
        edges = []
        if all_edges:
            for edge_data in all_edges:
                source = str(edge_data.get('source', edge_data.get('source_id', '')))
                target = str(edge_data.get('target', edge_data.get('target_id', '')))
                
                # Only include edges between nodes in our limited set
                if source in node_ids and target in node_ids:
                    edge = GraphEdge(
                        source=source,
                        target=target,
                        weight=edge_data.get('weight', 1.0),
                        description=edge_data.get('description', ''),
                        keywords=edge_data.get('keywords', '')
                    )
                    edges.append(edge)
        
        logger.info(f"Returning {len(nodes)} nodes and {len(edges)} edges (limited from {total_nodes}/{total_edges})")
        
        return GraphData(
            nodes=nodes,
            edges=edges,
            total_nodes=total_nodes,
            total_edges=total_edges
        )
        
    except Exception as e:
        logger.error(f"Error retrieving graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve graph: {str(e)}"
        )


@router.get("/sources", response_model=List[str])
async def get_source_documents(
    rag_engine: RAGEngine = Depends(get_rag_engine)
) -> List[str]:
    """
    Get list of unique source document IDs from the knowledge graph
    
    Args:
        rag_engine: RAG engine dependency
        
    Returns:
        List of unique source document IDs
    """
    try:
        graph_storage = _get_graph_storage_from_rag(rag_engine)
        
        if graph_storage is None:
            logger.warning("No graph data available")
            return []
        
        # Get all nodes from NetworkXStorage
        all_nodes = await graph_storage.get_all_nodes()
        
        if not all_nodes:
            logger.warning("No nodes found in graph")
            return []
        
        # Extract unique source IDs
        source_ids = set()
        for node_data in all_nodes:
            source_id = node_data.get('source_id')
            if source_id:
                source_ids.add(str(source_id))
        
        # Convert to sorted list
        result = sorted(list(source_ids))
        logger.info(f"Retrieved {len(result)} unique source documents")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving source documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve source documents: {str(e)}"
        )


@router.get("/stats", response_model=GraphStats)
async def get_graph_stats(
    rag_engine: RAGEngine = Depends(get_rag_engine)
) -> GraphStats:
    """
    Get statistical overview of the knowledge graph
    
    Args:
        rag_engine: RAG engine dependency
        
    Returns:
        Graph statistics including node count, edge count, entity types, and density
    """
    try:
        graph_storage = _get_graph_storage_from_rag(rag_engine)
        
        if graph_storage is None:
            logger.warning("No graph data available")
            return GraphStats(
                total_nodes=0,
                total_edges=0,
                entity_types={},
                density=0.0
            )
        
        # Get all nodes and edges
        all_nodes = await graph_storage.get_all_nodes()
        all_edges = await graph_storage.get_all_edges()
        
        # Calculate basic stats
        total_nodes = len(all_nodes) if all_nodes else 0
        total_edges = len(all_edges) if all_edges else 0
        
        # Calculate density
        # Density = actual_edges / possible_edges
        # For directed graph: possible_edges = n * (n-1)
        # For undirected graph: possible_edges = n * (n-1) / 2
        density = 0.0
        if total_nodes > 1:
            # Assume undirected graph (typical for knowledge graphs)
            possible_edges = (total_nodes * (total_nodes - 1)) / 2
            density = total_edges / possible_edges if possible_edges > 0 else 0.0
        
        # Count entity types
        entity_types: Dict[str, int] = {}
        if all_nodes:
            for node_data in all_nodes:
                entity_type = node_data.get('entity_type', node_data.get('type', 'unknown'))
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        logger.info(f"Graph stats: {total_nodes} nodes, {total_edges} edges, density {density:.4f}")
        
        return GraphStats(
            total_nodes=total_nodes,
            total_edges=total_edges,
            entity_types=entity_types,
            density=density
        )
        
    except Exception as e:
        logger.error(f"Error retrieving graph stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve graph statistics: {str(e)}"
        )

