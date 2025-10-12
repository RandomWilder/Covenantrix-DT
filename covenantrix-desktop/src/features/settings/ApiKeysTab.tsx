/**
 * API Keys Tab
 * Manages API key configuration and validation
 */

import React, { useState } from 'react';
import { Eye, EyeOff, CheckCircle, XCircle, AlertCircle, X } from 'lucide-react';
import { ApiKeySettings, ApiKeyMode, SettingsError } from '../../types/settings';

interface ApiKeysTabProps {
  settings: ApiKeySettings;
  onChange: (settings: ApiKeySettings) => void;
  error?: SettingsError | null;
  onClearError?: () => void;
}

const ApiKeysTab: React.FC<ApiKeysTabProps> = ({ settings, onChange, error, onClearError }) => {
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
      // Call the backend validation endpoint
      const validationRequest: any = {};
      validationRequest[keyName] = keyValue;
      
      const response = await window.electronAPI.validateApiKeys(validationRequest);
      
      // Check the specific key validation result
      let isValid = false;
      if (keyName === 'openai') {
        isValid = response.openai_valid === true;
      } else if (keyName === 'cohere') {
        isValid = response.cohere_valid === true;
      } else if (keyName === 'google') {
        isValid = response.google_valid === true;
      }
      
      setValidationStatus(prev => ({ 
        ...prev, 
        [keyName]: isValid ? 'valid' : 'invalid' 
      }));
      
      if (!isValid && response.errors && response.errors[keyName]) {
        console.error(`${keyName} validation error:`, response.errors[keyName]);
      }
    } catch (error) {
      console.error(`Error validating ${keyName} key:`, error);
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

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
          <div className="flex items-start space-x-3">
            <XCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-red-800 dark:text-red-200 mb-1">
                Validation Error
              </h4>
              <p className="text-sm text-red-700 dark:text-red-300">
                {error.message}
              </p>
              {error.validationErrors && error.validationErrors.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {error.validationErrors.map((err, idx) => (
                    <li key={idx} className="text-xs text-red-600 dark:text-red-400">
                      <strong>{err.field}:</strong> {err.message}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {onClearError && (
              <button
                onClick={onClearError}
                className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-200"
                aria-label="Dismiss error"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}

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
                  Use system keys provided by administrators. Recommended for most users.
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
                  Provide your own API keys. Only your custom keys will be used (no automatic fallback).
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Custom Keys Section */}
        {settings.mode === 'custom' && (
          <div className="space-y-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="space-y-2 mb-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-5 h-5 text-amber-500" />
                <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
                  Custom API Keys - Strict Mode
                </span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-300 pl-7">
                This key will be used exclusively. No automatic fallback will occur. If the key is invalid, services will be disabled until corrected.
              </p>
            </div>

            {/* OpenAI Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                OpenAI API Key <span className="text-red-500">*</span>
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
              <div className="mt-1 space-y-1">
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  Required for AI chat and document processing
                </p>
                {validationStatus.openai === 'invalid' && (
                  <p className="text-xs text-red-600 dark:text-red-400 font-medium">
                    The OpenAI API key you entered is invalid. Please verify your key and try again. No automatic fallback will occur.
                  </p>
                )}
              </div>
            </div>

            {/* Cohere Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Cohere API Key <span className="text-gray-400">(optional)</span>
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
              <div className="mt-1 space-y-1">
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  Optional: Enables reranking features for improved search results
                </p>
                {!settings.cohere && (
                  <p className="text-xs text-amber-600 dark:text-amber-400">
                    ⚠️ Cohere API key not provided. Reranking features will not be available.
                  </p>
                )}
                {validationStatus.cohere === 'invalid' && (
                  <p className="text-xs text-red-600 dark:text-red-400 font-medium">
                    The Cohere API key you entered is invalid. Please verify your key and try again.
                  </p>
                )}
              </div>
            </div>

            {/* Google Cloud Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Google Cloud API Key <span className="text-gray-400">(optional)</span>
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
              <div className="mt-1 space-y-1">
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  Optional: Enables OCR features for scanned documents and image processing
                </p>
                {!settings.google && (
                  <p className="text-xs text-amber-600 dark:text-amber-400">
                    ⚠️ Google API key not provided. OCR features will not be available.
                  </p>
                )}
                {validationStatus.google === 'invalid' && (
                  <p className="text-xs text-red-600 dark:text-red-400 font-medium">
                    The Google API key you entered is invalid. Please verify your key and try again.
                  </p>
                )}
              </div>
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
