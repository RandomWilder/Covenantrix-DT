/**
 * EmptyGraphState Component
 * Displays when no knowledge graph data is available
 */

import React from 'react';
import { Network, Upload } from 'lucide-react';

interface EmptyGraphStateProps {
  onUploadClick?: () => void;
}

const EmptyGraphState: React.FC<EmptyGraphStateProps> = ({ onUploadClick }) => {
  return (
    <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
      <div className="text-center px-6 py-12 max-w-lg">
        <div className="mb-6 inline-flex p-5 bg-gray-100 dark:bg-gray-800 rounded-full">
          <Network className="w-20 h-20 text-gray-400 dark:text-gray-600" />
        </div>
        
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
          No Knowledge Graph Data Available
        </h3>
        
        <p className="text-gray-600 dark:text-gray-400 mb-8 leading-relaxed text-sm">
          Upload and process documents to build your knowledge graph. 
          The system will automatically extract entities and relationships from your documents,
          creating an interactive visualization of your data.
        </p>
        
        {onUploadClick && (
          <button
            onClick={onUploadClick}
            className="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 
                     text-white font-medium rounded-lg transition-all duration-200
                     shadow-sm hover:shadow-md focus:outline-none focus:ring-2 
                     focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
          >
            <Upload className="w-5 h-5 mr-2" />
            Upload Documents
          </button>
        )}
      </div>
    </div>
  );
};

export default EmptyGraphState;

