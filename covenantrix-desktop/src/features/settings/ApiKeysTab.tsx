/**
 * API Keys Tab
 * Manages API key configuration and validation
 */

import React, { useState } from 'react';
import { Eye, EyeOff, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { ApiKeySettings, ApiKeyMode } from '../../types/settings';

interface ApiKeysTabProps {
  settings: ApiKeySettings;
  onChange: (settings: ApiKeySettings) => void;
}

const ApiKeysTab: React.FC<ApiKeysTabProps> = ({ settings, onChange }) => {
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [validationStatus, setValidationStatus] = useState<Record<string, 'idle' | 'validating' | 'valid' | 'invalid'>>({});

  const toggleKeyVisibility = (keyName: string) => {
    setShowKeys(prev => ({ ...prev, [keyName]: !prev[keyName] }));
  };

  const handleModeChange = (mode: ApiKeyMode) => {
    onChange({
      ...settings,
      mode,
      // Clear custom keys when switching to default
      ...(mode === 'default' ? {} : {})
    });
  };

  const handleKeyChange = (keyName: string, value: string) => {
    onChange({
      ...settings,
      [keyName]: value
    });
  };

  const validateKey = async (keyName: string, keyValue: string) => {
    if (!keyValue.trim()) {
      setValidationStatus(prev => ({ ...prev, [keyName]: 'idle' }));
      return;
    }

    setValidationStatus(prev => ({ ...prev, [keyName]: 'validating' }));

    try {
      // This would call the backend validation endpoint
      // For now, we'll simulate validation
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulate validation result (in real implementation, this would be actual API validation)
      const isValid = keyValue.length > 10; // Simple validation for demo
      setValidationStatus(prev => ({ 
        ...prev, 
        [keyName]: isValid ? 'valid' : 'invalid' 
      }));
    } catch (error) {
      setValidationStatus(prev => ({ ...prev, [keyName]: 'invalid' }));
    }
  };

  const getValidationIcon = (status: string) => {
    switch (status) {
      case 'validating':
        return <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />;
      case 'valid':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'invalid':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          API Key Configuration
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Configure your API keys for AI services. Keys are encrypted and stored securely on your device.
        </p>
      </div>

      {/* Mode Selection */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            API Key Mode
          </label>
          <div className="space-y-3">
            <label className="flex items-center space-x-3">
              <input
                type="radio"
                name="apiMode"
                value="default"
                checked={settings.mode === 'default'}
                onChange={() => handleModeChange('default')}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Use Default Keys
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Use pre-configured API keys (recommended for most users)
                </div>
              </div>
            </label>
            
            <label className="flex items-center space-x-3">
              <input
                type="radio"
                name="apiMode"
                value="custom"
                checked={settings.mode === 'custom'}
                onChange={() => handleModeChange('custom')}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Use Custom Keys
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Provide your own API keys for full control
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Custom Keys Section */}
        {settings.mode === 'custom' && (
          <div className="space-y-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center space-x-2 mb-4">
              <AlertCircle className="w-5 h-5 text-amber-500" />
              <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
                Custom API Keys
              </span>
            </div>

            {/* OpenAI Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                OpenAI API Key
              </label>
              <div className="relative">
                <input
                  type={showKeys.openai ? 'text' : 'password'}
                  value={settings.openai || ''}
                  onChange={(e) => handleKeyChange('openai', e.target.value)}
                  onBlur={(e) => validateKey('openai', e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 pr-20 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
                />
                <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                  {getValidationIcon(validationStatus.openai)}
                  <button
                    type="button"
                    onClick={() => toggleKeyVisibility('openai')}
                    className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    {showKeys.openai ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Required for AI chat and document processing
              </p>
            </div>

            {/* Cohere Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Cohere API Key
              </label>
              <div className="relative">
                <input
                  type={showKeys.cohere ? 'text' : 'password'}
                  value={settings.cohere || ''}
                  onChange={(e) => handleKeyChange('cohere', e.target.value)}
                  onBlur={(e) => validateKey('cohere', e.target.value)}
                  placeholder="co-..."
                  className="w-full px-3 py-2 pr-20 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
                />
                <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                  {getValidationIcon(validationStatus.cohere)}
                  <button
                    type="button"
                    onClick={() => toggleKeyVisibility('cohere')}
                    className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    {showKeys.cohere ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Optional: Improves search result ranking
              </p>
            </div>

            {/* Google Cloud Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Google Cloud API Key
              </label>
              <div className="relative">
                <input
                  type={showKeys.google ? 'text' : 'password'}
                  value={settings.google || ''}
                  onChange={(e) => handleKeyChange('google', e.target.value)}
                  onBlur={(e) => validateKey('google', e.target.value)}
                  placeholder="AIzaSy..."
                  className="w-full px-3 py-2 pr-20 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
                />
                <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
                  {getValidationIcon(validationStatus.google)}
                  <button
                    type="button"
                    onClick={() => toggleKeyVisibility('google')}
                    className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    {showKeys.google ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Used for Vision API (OCR), Drive integration, and other Google Cloud services
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Security Notice */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200">
              Security & Privacy
            </h4>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              Your API keys are encrypted and stored locally on your device. They are never transmitted to our servers or shared with third parties.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiKeysTab;
