/**
 * GraphStats Component
 * Displays knowledge graph statistics in a card grid
 */

import React from 'react';
import { Network, GitBranch, Activity } from 'lucide-react';
import type { GraphStats as GraphStatsType } from '../../../types/graph';

interface GraphStatsProps {
  stats: GraphStatsType | null;
}

const GraphStats: React.FC<GraphStatsProps> = ({ stats }) => {
  if (!stats) {
    return null;
  }

  const getNodeColor = (type: string): string => {
    const colors: Record<string, string> = {
      person: 'bg-blue-500',
      organization: 'bg-green-500',
      geo: 'bg-amber-500',
      location: 'bg-amber-500',
      event: 'bg-red-500',
      category: 'bg-purple-500',
      concept: 'bg-purple-500',
      'economic policy': 'bg-pink-500',
      'economic_policy': 'bg-pink-500',
      unknown: 'bg-gray-500',
    };
    return colors[type.toLowerCase()] || colors.unknown;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
      {/* Total Entities */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 
                    dark:border-gray-700 hover:shadow-md transition-shadow duration-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Entities</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {stats.total_nodes.toLocaleString()}
            </p>
          </div>
          <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Network className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </div>

      {/* Total Relationships */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 
                    dark:border-gray-700 hover:shadow-md transition-shadow duration-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Relationships</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {stats.total_edges.toLocaleString()}
            </p>
          </div>
          <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <GitBranch className="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
        </div>
      </div>

      {/* Graph Density */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 
                    dark:border-gray-700 hover:shadow-md transition-shadow duration-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Graph Density</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {(stats.density * 100).toFixed(2)}%
            </p>
          </div>
          <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
            <Activity className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
      </div>

      {/* Entity Types Breakdown */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 
                    dark:border-gray-700 hover:shadow-md transition-shadow duration-200">
        <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Entity Types</p>
        <div className="space-y-1.5 max-h-16 overflow-y-auto custom-scrollbar">
          {Object.entries(stats.entity_types)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 4)
            .map(([type, count]) => (
              <div key={type} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${getNodeColor(type)} flex-shrink-0`} />
                  <span className="text-gray-700 dark:text-gray-300 capitalize font-medium">{type}</span>
                </span>
                <span className="text-gray-600 dark:text-gray-400 font-semibold">{count}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default GraphStats;

