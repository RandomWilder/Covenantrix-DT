/**
 * GraphControls Component
 * Search bar and action buttons for the knowledge graph
 */

import React from 'react';
import { Search, Download, RefreshCw, X, Filter } from 'lucide-react';

interface GraphControlsProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  onSearch: () => void;
  onExport: () => void;
  onRefresh: () => void;
  loading?: boolean;
  sourceDocuments?: string[];
  selectedSourceDocument?: string;
  onSourceDocumentChange?: (sourceId: string) => void;
}

const GraphControls: React.FC<GraphControlsProps> = ({
  searchTerm,
  onSearchChange,
  onSearch,
  onExport,
  onRefresh,
  loading = false,
  sourceDocuments = [],
  selectedSourceDocument = '',
  onSourceDocumentChange,
}) => {
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onSearch();
    }
  };

  const handleClear = () => {
    onSearchChange('');
    onSearch(); // Trigger search to reset the view
  };

  return (
    <div className="flex flex-col gap-3 mt-4">
      {/* First Row: Search Input and Source Filter */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center gap-3">
        {/* Search Input */}
        <div className="relative flex-1 min-w-0 w-full lg:w-auto">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="w-5 h-5 text-gray-400 dark:text-gray-500" />
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search entities..."
            className="w-full pl-10 pr-10 py-2.5 bg-white dark:bg-gray-800 border border-gray-300 
                     dark:border-gray-600 rounded-lg text-gray-900 dark:text-white 
                     placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 
                     focus:ring-blue-500 focus:border-transparent transition-all duration-200
                     focus:outline-none shadow-sm text-sm"
          />
          {searchTerm && (
            <button
              onClick={handleClear}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 
                       hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="Clear search"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Source Document Filter */}
        {sourceDocuments.length > 0 && (
          <div className="relative w-full lg:w-64">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Filter className="w-4 h-4 text-gray-400 dark:text-gray-500" />
            </div>
            <select
              value={selectedSourceDocument}
              onChange={(e) => onSourceDocumentChange?.(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-300 
                       dark:border-gray-600 rounded-lg text-gray-900 dark:text-white 
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent 
                       transition-all duration-200 focus:outline-none shadow-sm text-sm
                       appearance-none cursor-pointer"
            >
              <option value="">All Documents</option>
              {sourceDocuments.map((sourceId) => (
                <option key={sourceId} value={sourceId}>
                  {sourceId}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Second Row: Action Buttons */}
      <div className="flex items-center gap-2 w-full lg:w-auto">
        <button
          onClick={onExport}
          disabled={loading}
          className="inline-flex items-center justify-center px-4 py-2.5 bg-white dark:bg-gray-800 
                   border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 
                   dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 
                   disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200
                   text-sm font-medium shadow-sm hover:shadow focus:outline-none 
                   focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 
                   dark:focus:ring-offset-gray-800 flex-1 lg:flex-initial"
        >
          <Download className="w-4 h-4 mr-2" />
          Export JSON
        </button>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="inline-flex items-center justify-center px-4 py-2.5 bg-blue-600 hover:bg-blue-700 
                   text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed 
                   transition-all duration-200 text-sm font-medium shadow-sm hover:shadow
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 
                   dark:focus:ring-offset-gray-800 flex-1 lg:flex-initial"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Reload
        </button>
      </div>
    </div>
  );
};

export default GraphControls;

