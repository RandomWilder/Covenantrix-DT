/**
 * NodeDetailsPanel Component
 * Slide-out panel showing detailed information about a selected graph node
 */

import React, { useMemo } from 'react';
import { X, FileText, Network, ExternalLink } from 'lucide-react';
import type { GraphNode, GraphEdge } from '../../../types/graph';
import { useTheme } from '../../../hooks/useTheme';

interface NodeDetailsPanelProps {
  node: GraphNode | null;
  edges: GraphEdge[];
  allNodes: GraphNode[];
  onClose: () => void;
  onNavigateToDocument?: (documentId: string) => void;
}

const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({
  node,
  edges,
  allNodes,
  onClose,
  onNavigateToDocument,
}) => {
  const { isDark } = useTheme();

  // Calculate related entities (connected nodes)
  const relatedEntities = useMemo(() => {
    if (!node) return [];
    
    const relatedIds = new Set<string>();
    edges.forEach(edge => {
      if (edge.source === node.id) {
        relatedIds.add(edge.target);
      } else if (edge.target === node.id) {
        relatedIds.add(edge.source);
      }
    });

    return allNodes
      .filter(n => relatedIds.has(n.id))
      .slice(0, 10); // Limit to 10 related entities
  }, [node, edges, allNodes]);

  // Find relationships involving this node
  const relationships = useMemo(() => {
    if (!node) return [];
    
    return edges
      .filter(edge => edge.source === node.id || edge.target === node.id)
      .slice(0, 15); // Limit to 15 relationships
  }, [node, edges]);

  if (!node) return null;

  const handleDocumentClick = () => {
    if (node.source_id && onNavigateToDocument) {
      onNavigateToDocument(node.source_id);
    }
  };

  // Get entity type color (matching the graph node colors)
  const getTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      person: '#3b82f6',
      organization: '#10b981',
      geo: '#f59e0b',
      location: '#f59e0b',
      event: '#ef4444',
      category: '#8b5cf6',
      concept: '#8b5cf6',
      'economic policy': '#ec4899',
      'economic_policy': '#ec4899',
      unknown: '#6b7280',
    };
    return colors[type.toLowerCase()] || colors.unknown;
  };

  return (
    <>
      {/* Backdrop overlay */}
      <div 
        className="fixed inset-0 bg-black/30 dark:bg-black/50 z-40 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Slide-out panel */}
      <div 
        className={`fixed right-0 top-0 bottom-0 w-full sm:w-96 z-50 
                   ${isDark ? 'bg-gray-800' : 'bg-white'} 
                   shadow-2xl transform transition-transform duration-300 ease-in-out
                   flex flex-col overflow-hidden`}
      >
        {/* Header */}
        <div className={`flex items-start justify-between p-6 border-b 
                        ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
          <div className="flex-1 min-w-0 mr-4">
            <h2 className={`text-xl font-bold mb-2 break-words
                          ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {node.label}
            </h2>
            <div 
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white"
              style={{ backgroundColor: getTypeColor(node.type) }}
            >
              {node.type}
            </div>
          </div>
          <button
            onClick={onClose}
            className={`flex-shrink-0 p-2 rounded-lg transition-colors
                       ${isDark 
                         ? 'hover:bg-gray-700 text-gray-400 hover:text-white' 
                         : 'hover:bg-gray-100 text-gray-500 hover:text-gray-900'}`}
            aria-label="Close panel"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Description Section */}
          {node.description && (
            <div>
              <h3 className={`text-sm font-semibold uppercase tracking-wider mb-2
                            ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Description
              </h3>
              <p className={`text-sm leading-relaxed
                           ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                {node.description}
              </p>
            </div>
          )}

          {/* Source Document Section */}
          {node.source_id && (
            <div>
              <h3 className={`text-sm font-semibold uppercase tracking-wider mb-2
                            ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Source Document
              </h3>
              <button
                onClick={handleDocumentClick}
                className={`w-full flex items-center justify-between p-3 rounded-lg 
                           transition-all duration-200 group
                           ${isDark 
                             ? 'bg-gray-700 hover:bg-gray-600 text-gray-200' 
                             : 'bg-gray-50 hover:bg-gray-100 text-gray-700'}`}
              >
                <div className="flex items-center min-w-0 flex-1">
                  <FileText className="w-5 h-5 mr-3 flex-shrink-0" />
                  <span className="text-sm font-medium truncate">
                    {node.source_id}
                  </span>
                </div>
                <ExternalLink className={`w-4 h-4 ml-2 flex-shrink-0 transition-transform 
                                         group-hover:translate-x-0.5 group-hover:-translate-y-0.5
                                         ${isDark ? 'text-gray-400' : 'text-gray-500'}`} />
              </button>
            </div>
          )}

          {/* Relationships Section */}
          {relationships.length > 0 && (
            <div>
              <h3 className={`text-sm font-semibold uppercase tracking-wider mb-3
                            ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Relationships ({relationships.length})
              </h3>
              <div className="space-y-2">
                {relationships.map((rel, idx) => {
                  const isSource = rel.source === node.id;
                  const otherNodeId = isSource ? rel.target : rel.source;
                  const otherNode = allNodes.find(n => n.id === otherNodeId);
                  
                  return (
                    <div 
                      key={idx}
                      className={`p-3 rounded-lg text-sm
                                 ${isDark ? 'bg-gray-700' : 'bg-gray-50'}`}
                    >
                      <div className="flex items-center mb-1">
                        <Network className={`w-4 h-4 mr-2 flex-shrink-0
                                           ${isDark ? 'text-gray-400' : 'text-gray-500'}`} />
                        <span className={`font-medium
                                        ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>
                          {isSource ? '→' : '←'} {otherNode?.label || otherNodeId}
                        </span>
                      </div>
                      {rel.description && (
                        <p className={`text-xs ml-6
                                      ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                          {rel.description}
                        </p>
                      )}
                      {rel.keywords && (
                        <p className={`text-xs ml-6 mt-1
                                      ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                          Keywords: {rel.keywords}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Related Entities Section */}
          {relatedEntities.length > 0 && (
            <div>
              <h3 className={`text-sm font-semibold uppercase tracking-wider mb-3
                            ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Related Entities ({relatedEntities.length})
              </h3>
              <div className="space-y-2">
                {relatedEntities.map((relatedNode) => (
                  <div 
                    key={relatedNode.id}
                    className={`p-3 rounded-lg
                               ${isDark ? 'bg-gray-700' : 'bg-gray-50'}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-sm font-medium
                                       ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>
                        {relatedNode.label}
                      </span>
                      <span 
                        className="text-xs px-2 py-0.5 rounded text-white"
                        style={{ backgroundColor: getTypeColor(relatedNode.type) }}
                      >
                        {relatedNode.type}
                      </span>
                    </div>
                    {relatedNode.description && (
                      <p className={`text-xs
                                    ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        {relatedNode.description.slice(0, 100)}
                        {relatedNode.description.length > 100 ? '...' : ''}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default NodeDetailsPanel;

