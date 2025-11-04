/**
 * Knowledge Graph Type Definitions
 * 
 * These types match the backend API schemas defined in backend/api/schemas/graph.py
 */

/**
 * Represents a node (entity) in the knowledge graph
 */
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  description: string;
  source_id?: string;
}

/**
 * Represents an edge (relationship) between two nodes in the knowledge graph
 */
export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  description: string;
  keywords: string;
}

/**
 * Complete graph data structure with nodes, edges, and metadata
 */
export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
}

/**
 * Statistical information about the knowledge graph
 */
export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  entity_types: Record<string, number>;
  density: number;
}

/**
 * Response from the entities endpoint
 */
export interface EntityListResponse {
  entities: GraphNode[];
  count: number;
}

/**
 * Response from the relationships endpoint
 */
export interface RelationshipListResponse {
  relationships: GraphEdge[];
  count: number;
}

/**
 * ReactFlow-specific node type for visualization
 */
export interface FlowNode {
  id: string;
  data: {
    label: string;
    type: string;
    description: string;
  };
  position: { x: number; y: number };
  style?: React.CSSProperties;
}

/**
 * ReactFlow-specific edge type for visualization
 */
export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  markerEnd?: any;
  style?: React.CSSProperties;
}

