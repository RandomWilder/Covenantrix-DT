/**
 * GraphVisualization Component
 * Interactive knowledge graph visualization using ReactFlow
 */

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  BackgroundVariant,
  NodeMouseHandler,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { GraphApi } from '../../services/api/GraphApi';
import { useTheme } from '../../hooks/useTheme';
import GraphStats from './components/GraphStats';
import GraphControls from './components/GraphControls';
import EmptyGraphState from './components/EmptyGraphState';
import NodeDetailsPanel from './components/NodeDetailsPanel';
import type { GraphNode, GraphEdge, GraphStats as GraphStatsType } from '../../types/graph';

const GraphVisualization: React.FC = () => {
  const { isDark } = useTheme();
  // Memoize graphApi to prevent recreation on every render
  const graphApi = useMemo(() => new GraphApi(), []);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<GraphStatsType | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [maxNodes] = useState(500);
  const [allNodes, setAllNodes] = useState<Node[]>([]);
  const [allEdges, setAllEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({ nodes: [], edges: [] });
  const [sourceDocuments, setSourceDocuments] = useState<string[]>([]);
  const [selectedSourceDocument, setSelectedSourceDocument] = useState<string>('');

  /**
   * Get node color based on entity type
   */
  const getNodeColor = (type: string): string => {
    const colors: Record<string, string> = {
      person: '#3b82f6',           // blue
      organization: '#10b981',      // green
      geo: '#f59e0b',               // amber
      location: '#f59e0b',          // amber
      event: '#ef4444',             // red
      category: '#8b5cf6',          // purple
      concept: '#8b5cf6',           // purple
      'economic policy': '#ec4899', // pink
      'economic_policy': '#ec4899', // pink
      unknown: '#6b7280',           // gray
    };
    return colors[type.toLowerCase()] || colors.unknown;
  };

  /**
   * Apply force-directed layout to nodes
   * Creates natural clustering of connected entities
   */
  const applyForceLayout = (
    graphNodes: GraphNode[],
    graphEdges: GraphEdge[]
  ): Map<string, { x: number; y: number }> => {
    // Build adjacency map
    const adjacency = new Map<string, Set<string>>();
    graphEdges.forEach(edge => {
      if (!adjacency.has(edge.source)) adjacency.set(edge.source, new Set());
      if (!adjacency.has(edge.target)) adjacency.set(edge.target, new Set());
      adjacency.get(edge.source)!.add(edge.target);
      adjacency.get(edge.target)!.add(edge.source);
    });

    // Initialize random positions in wide area
    const positions = new Map<string, { x: number; y: number }>();
    graphNodes.forEach(node => {
      positions.set(node.id, {
        x: Math.random() * 2000,
        y: Math.random() * 1500,
      });
    });

    // Force simulation parameters
    const iterations = 50;
    const repulsionStrength = 50000;
    const attractionStrength = 0.01;
    const coolingFactor = 0.95;

    // Run force simulation
    for (let iter = 0; iter < iterations; iter++) {
      const forces = new Map<string, { fx: number; fy: number }>();
      graphNodes.forEach(node => forces.set(node.id, { fx: 0, fy: 0 }));

      // Repulsive forces (all nodes push each other apart)
      for (let i = 0; i < graphNodes.length; i++) {
        for (let j = i + 1; j < graphNodes.length; j++) {
          const node1 = graphNodes[i];
          const node2 = graphNodes[j];
          const pos1 = positions.get(node1.id)!;
          const pos2 = positions.get(node2.id)!;

          const dx = pos1.x - pos2.x;
          const dy = pos1.y - pos2.y;
          const distSq = dx * dx + dy * dy + 0.01; // Avoid division by zero
          const dist = Math.sqrt(distSq);

          const force = repulsionStrength / distSq;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          forces.get(node1.id)!.fx += fx;
          forces.get(node1.id)!.fy += fy;
          forces.get(node2.id)!.fx -= fx;
          forces.get(node2.id)!.fy -= fy;
        }
      }

      // Attractive forces (connected nodes pull together)
      graphEdges.forEach(edge => {
        const pos1 = positions.get(edge.source);
        const pos2 = positions.get(edge.target);
        if (!pos1 || !pos2) return;

        const dx = pos2.x - pos1.x;
        const dy = pos2.y - pos1.y;
        const dist = Math.sqrt(dx * dx + dy * dy + 0.01);

        const force = attractionStrength * dist;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        forces.get(edge.source)!.fx += fx;
        forces.get(edge.source)!.fy += fy;
        forces.get(edge.target)!.fx -= fx;
        forces.get(edge.target)!.fy -= fy;
      });

      // Apply forces with cooling
      const cooling = Math.pow(coolingFactor, iter);
      graphNodes.forEach(node => {
        const pos = positions.get(node.id)!;
        const force = forces.get(node.id)!;
        pos.x += force.fx * cooling;
        pos.y += force.fy * cooling;
      });
    }

    // Center the graph
    const avgX = Array.from(positions.values()).reduce((sum, pos) => sum + pos.x, 0) / positions.size;
    const avgY = Array.from(positions.values()).reduce((sum, pos) => sum + pos.y, 0) / positions.size;
    const offsetX = 500 - avgX;
    const offsetY = 300 - avgY;

    positions.forEach(pos => {
      pos.x += offsetX;
      pos.y += offsetY;
    });

    return positions;
  };

  /**
   * Transform backend graph data to ReactFlow format
   */
  const transformGraphData = useCallback(
    (graphNodes: GraphNode[], graphEdges: GraphEdge[]) => {
      // Apply force-directed layout
      const positions = applyForceLayout(graphNodes, graphEdges);

      // Transform nodes
      const flowNodes: Node[] = graphNodes.map(node => {
        const position = positions.get(node.id) || { x: 0, y: 0 };
        const bgColor = getNodeColor(node.type);
        return {
          id: node.id,
          type: 'default',
          data: {
            label: node.label,
            type: node.type,
            description: node.description,
          },
          position,
          style: {
            background: bgColor,
            color: '#fff',
            border: `2px solid ${isDark ? '#1f2937' : '#f3f4f6'}`,
            borderRadius: '8px',
            padding: '10px 14px',
            fontSize: '12px',
            fontWeight: '500',
            boxShadow: isDark 
              ? '0 2px 8px rgba(0, 0, 0, 0.4)' 
              : '0 2px 8px rgba(0, 0, 0, 0.1)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          },
        };
      });

      // Transform edges
      const flowEdges: Edge[] = graphEdges.map(edge => ({
        id: `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        label: edge.description || undefined,
        animated: false,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: isDark ? '#9ca3af' : '#6b7280',
        },
        style: {
          strokeWidth: Math.max(1.5, edge.weight / 2),
          stroke: isDark ? '#9ca3af' : '#6b7280',
          opacity: 0.6,
        },
        labelStyle: {
          fill: isDark ? '#d1d5db' : '#374151',
          fontSize: 10,
          fontWeight: 500,
        },
        labelBgStyle: {
          fill: isDark ? '#1f2937' : '#ffffff',
          fillOpacity: 0.9,
        },
      }));

      return { flowNodes, flowEdges };
    },
    [isDark]
  );

  /**
   * Load graph data from API
   */
  const loadGraphData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await graphApi.getFullGraph(maxNodes);

      if (data.nodes.length === 0) {
        setNodes([]);
        setEdges([]);
        setAllNodes([]);
        setAllEdges([]);
        setLoading(false);
        return;
      }

      const { flowNodes, flowEdges } = transformGraphData(data.nodes, data.edges);
      setNodes(flowNodes);
      setEdges(flowEdges);
      setAllNodes(flowNodes);
      setAllEdges(flowEdges);
      setGraphData({ nodes: data.nodes, edges: data.edges });
    } catch (err) {
      console.error('Error loading graph data:', err);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [maxNodes, transformGraphData, graphApi]);

  /**
   * Load graph statistics
   */
  const loadStats = useCallback(async () => {
    try {
      const statsData = await graphApi.getStats();
      setStats(statsData);
    } catch (err) {
      console.error('Error loading graph stats:', err);
    }
  }, [graphApi]);

  /**
   * Load source documents for filtering
   */
  const loadSourceDocuments = useCallback(async () => {
    try {
      const sources = await graphApi.getSourceDocuments();
      setSourceDocuments(sources);
    } catch (err) {
      console.error('Error loading source documents:', err);
    }
  }, [graphApi]);

  /**
   * Apply filters (search term and source document)
   */
  const applyFilters = useCallback(() => {
    let filteredNodes = [...allNodes];
    
    // Apply search term filter
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filteredNodes = filteredNodes.map(node => ({
        ...node,
        hidden: !node.data.label.toLowerCase().includes(searchLower),
      }));
    }
    
    // Apply source document filter
    if (selectedSourceDocument) {
      filteredNodes = filteredNodes.map(node => {
        // Find the original graph node to check source_id
        const graphNode = graphData.nodes.find(gn => gn.id === node.id);
        const matchesSource = graphNode?.source_id === selectedSourceDocument;
        
        return {
          ...node,
          hidden: node.hidden || !matchesSource, // Combine with existing hidden state
        };
      });
    }

    // Only show edges between visible nodes
    const visibleNodeIds = new Set(
      filteredNodes.filter(n => !n.hidden).map(n => n.id)
    );
    const filteredEdges = allEdges.map(edge => ({
      ...edge,
      hidden: !visibleNodeIds.has(edge.source) || !visibleNodeIds.has(edge.target),
    }));

    setNodes(filteredNodes);
    setEdges(filteredEdges);
  }, [searchTerm, selectedSourceDocument, allNodes, allEdges, graphData.nodes]);

  /**
   * Export graph as JSON
   */
  const exportGraph = useCallback(() => {
    const exportData = {
      nodes: allNodes.map(n => ({
        id: n.id,
        label: n.data.label,
        type: n.data.type,
        description: n.data.description,
        position: n.position,
      })),
      edges: allEdges.map(e => ({
        source: e.source,
        target: e.target,
        label: e.label,
      })),
      metadata: {
        exportDate: new Date().toISOString(),
        totalNodes: allNodes.length,
        totalEdges: allEdges.length,
      },
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `knowledge-graph-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [allNodes, allEdges]);

  /**
   * Navigate to upload screen
   */
  const handleUploadClick = () => {
    // This would use navigation context or router
    window.dispatchEvent(new CustomEvent('navigate', { detail: { screen: 'upload' } }));
  };

  /**
   * Handle node click to show details panel
   */
  const handleNodeClick: NodeMouseHandler = useCallback((_event, node) => {
    // Find the original graph node data
    const graphNode = graphData.nodes.find(n => n.id === node.id);
    if (graphNode) {
      setSelectedNode(graphNode);
    }
  }, [graphData.nodes]);

  /**
   * Handle navigation to documents screen with document ID
   */
  const handleNavigateToDocument = useCallback((documentId: string) => {
    // Close the panel
    setSelectedNode(null);
    
    // Dispatch navigation event to Documents screen
    // Note: DocumentsScreen doesn't currently support pre-selecting a document,
    // but we navigate there so user can find it
    window.dispatchEvent(new CustomEvent('navigate', { 
      detail: { 
        screen: 'documents',
        documentId // Pass document ID for future enhancement
      } 
    }));
  }, []);

  // Load data on mount
  useEffect(() => {
    loadGraphData();
    loadStats();
    loadSourceDocuments();
  }, [loadGraphData, loadStats, loadSourceDocuments]);

  // Apply filters when search term or source document changes
  useEffect(() => {
    if (allNodes.length > 0) {
      applyFilters();
    }
  }, [searchTerm, selectedSourceDocument, applyFilters, allNodes.length]);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="relative inline-flex">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-200 dark:border-gray-700" />
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-transparent border-t-blue-600 absolute top-0 left-0" />
          </div>
          <p className="mt-6 text-gray-600 dark:text-gray-400 font-medium">
            Loading knowledge graph...
          </p>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-500">
            Analyzing entities and relationships
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
        <div className="text-center px-4 max-w-md">
          <div className="mb-4 inline-flex p-4 bg-red-100 dark:bg-red-900/20 rounded-full">
            <AlertCircle className="w-12 h-12 text-red-500 dark:text-red-400" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Failed to Load Graph
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6 text-sm leading-relaxed">
            {error}
          </p>
          <button
            onClick={loadGraphData}
            className="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 
                     text-white font-medium rounded-lg transition-all duration-200
                     shadow-sm hover:shadow-md focus:outline-none focus:ring-2 
                     focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (allNodes.length === 0) {
    return <EmptyGraphState onUploadClick={handleUploadClick} />;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with stats and controls */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Knowledge Graph
        </h2>
        <GraphStats stats={stats} />
        <GraphControls
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onSearch={applyFilters}
          onExport={exportGraph}
          onRefresh={loadGraphData}
          loading={loading}
          sourceDocuments={sourceDocuments}
          selectedSourceDocument={selectedSourceDocument}
          onSourceDocumentChange={setSelectedSourceDocument}
        />
      </div>

      {/* Graph canvas */}
      <div className={`flex-1 ${isDark ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          fitView
          fitViewOptions={{
            padding: 0.2,
            minZoom: 0.1,
            maxZoom: 2,
          }}
          minZoom={0.05}
          maxZoom={4}
          attributionPosition="bottom-left"
          proOptions={{ hideAttribution: true }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={20}
            size={1}
            color={isDark ? '#374151' : '#e5e7eb'}
          />
          <Controls 
            className={isDark ? 'dark' : ''}
            showInteractive={false}
          />
          <MiniMap
            nodeColor={(node) => node.style?.background as string || '#6b7280'}
            maskColor={isDark ? 'rgba(17, 24, 39, 0.85)' : 'rgba(249, 250, 251, 0.85)'}
            className={isDark ? 'dark' : ''}
            style={{
              backgroundColor: isDark ? '#1f2937' : '#ffffff',
              border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
              borderRadius: '8px',
            }}
          />
        </ReactFlow>
      </div>

      {/* Node Details Panel */}
      <NodeDetailsPanel
        node={selectedNode}
        edges={graphData.edges}
        allNodes={graphData.nodes}
        onClose={() => setSelectedNode(null)}
        onNavigateToDocument={handleNavigateToDocument}
      />
    </div>
  );
};

export default GraphVisualization;

