/**
 * RAG Tab
 * Manages RAG engine configuration and search settings
 */

import React from 'react';
import { Search, Zap, Settings, FileText, Globe } from 'lucide-react';
import { RAGSettings, SearchMode } from '../../types/settings';

interface RAGTabProps {
  settings: RAGSettings;
  onChange: (settings: RAGSettings) => void;
}

const RAGTab: React.FC<RAGTabProps> = ({ settings, onChange }) => {
  const searchModes: { value: SearchMode; label: string; description: string; icon: React.ComponentType<any> }[] = [
    { 
      value: 'naive', 
      label: 'Naive Search', 
      description: 'Simple keyword matching (fastest)',
      icon: Search
    },
    { 
      value: 'local', 
      label: 'Local Search', 
      description: 'Semantic search within documents',
      icon: FileText
    },
    { 
      value: 'global', 
      label: 'Global Search', 
      description: 'Cross-document semantic search',
      icon: Globe
    },
    { 
      value: 'hybrid', 
      label: 'Hybrid Search', 
      description: 'Combines multiple search strategies (recommended)',
      icon: Zap
    }
  ];

  const handleSearchModeChange = (mode: SearchMode) => {
    onChange({
      ...settings,
      search_mode: mode
    });
  };

  const handleTopKChange = (topK: number) => {
    onChange({
      ...settings,
      top_k: Math.max(1, Math.min(20, topK))
    });
  };

  const handleRerankingToggle = (useReranking: boolean) => {
    onChange({
      ...settings,
      use_reranking: useReranking
    });
  };

  const handleOCRToggle = (enableOCR: boolean) => {
    onChange({
      ...settings,
      enable_ocr: enableOCR
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          RAG Configuration
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Configure how the AI searches and processes your documents.
        </p>
      </div>

      {/* Search Mode */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Search className="w-5 h-5 text-blue-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            Search Mode
          </h4>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Choose how the system searches through your documents.
        </p>
        <div className="grid grid-cols-1 gap-3">
          {searchModes.map((mode) => (
            <label
              key={mode.value}
              className={`flex items-start space-x-3 p-4 border rounded-lg cursor-pointer transition-colors ${
                settings.search_mode === mode.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }`}
            >
              <input
                type="radio"
                name="searchMode"
                value={mode.value}
                checked={settings.search_mode === mode.value}
                onChange={() => handleSearchModeChange(mode.value)}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500 mt-1"
              />
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <mode.icon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {mode.label}
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {mode.description}
                </p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Top-K Results */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Zap className="w-5 h-5 text-yellow-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            Number of Results
          </h4>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          How many document chunks to retrieve for each query (1-20).
        </p>
        <div className="flex items-center space-x-4">
          <input
            type="range"
            min="1"
            max="20"
            value={settings.top_k}
            onChange={(e) => handleTopKChange(parseInt(e.target.value))}
            className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="w-12 text-center">
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {settings.top_k}
            </span>
          </div>
        </div>
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Fewer results (faster)</span>
          <span>More results (comprehensive)</span>
        </div>
      </div>

      {/* Advanced Options */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Settings className="w-5 h-5 text-purple-500" />
          <h4 className="text-md font-medium text-gray-900 dark:text-white">
            Advanced Options
          </h4>
        </div>

        {/* Reranking */}
        <div className="flex items-center justify-between p-4 border border-gray-300 dark:border-gray-600 rounded-lg">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Enable Reranking
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                (Requires Cohere API key)
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Improves result relevance by reordering search results
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.use_reranking}
              onChange={(e) => handleRerankingToggle(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* OCR */}
        <div className="flex items-center justify-between p-4 border border-gray-300 dark:border-gray-600 rounded-lg">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Enable OCR
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                (Requires Google Vision API key)
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Extract text from images and scanned documents
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.enable_ocr}
              onChange={(e) => handleOCRToggle(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </div>

      {/* Performance Info */}
      <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
        <div className="flex items-start space-x-3">
          <div className="text-green-500 mt-0.5">💡</div>
          <div>
            <h4 className="text-sm font-medium text-green-800 dark:text-green-200">
              Performance Tips
            </h4>
            <ul className="text-sm text-green-700 dark:text-green-300 mt-1 space-y-1">
              <li>• Hybrid search provides the best balance of speed and accuracy</li>
              <li>• Higher top-K values give more comprehensive results but slower responses</li>
              <li>• Reranking improves relevance but requires additional API calls</li>
              <li>• OCR is useful for scanned documents but increases processing time</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RAGTab;
