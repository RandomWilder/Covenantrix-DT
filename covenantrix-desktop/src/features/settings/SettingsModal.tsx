/**
 * Settings Modal
 * Main settings interface with tabbed navigation
 */

import React, { useState, useEffect } from 'react';
import { X, Save, RotateCcw, AlertCircle, CheckCircle, Key, Globe, Bot, Palette } from 'lucide-react';
import { useSettings } from '../../hooks/useSettings';
import { useToast } from '../../hooks/useToast';
import { UserSettings } from '../../types/settings';
import ApiKeysTab from './ApiKeysTab';
import LanguageTab from './LanguageTab';
import RAGTab from './RAGTab';
import AppearanceTab from './AppearanceTab';
import SettingsBackup from './SettingsBackup';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'api-keys' | 'language' | 'rag' | 'appearance' | 'backup';

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const { 
    settings, 
    updateSettingsWithValidation, 
    resetToDefaults, 
    applySettings, 
    isLoading, 
    validation,
    apiKeyValidation,
    validateAllApiKeys
  } = useSettings();
  
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<TabType>('api-keys');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [localSettings, setLocalSettings] = useState<UserSettings | null>(null);

  const handleSave = async () => {
    if (!localSettings) return;
    
    try {
      setError(null);
      setIsValidating(true);
      
      // Validate API keys if in custom mode
      if (localSettings.api_keys?.mode === 'custom') {
        const validationResults = await validateAllApiKeys();
        const hasInvalidKeys = Object.values(validationResults).some(result => result === false);
        
        if (hasInvalidKeys) {
          showToast('Please fix invalid API keys before saving', 'error');
          return;
        }
      }
      
      // Save the local settings
      await updateSettingsWithValidation(localSettings);
      await applySettings();
      showToast('Settings saved and applied successfully', 'success');
      setHasUnsavedChanges(false);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to save settings';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsValidating(false);
    }
  };

  const handleReset = async () => {
    try {
      await resetToDefaults();
      // Update local settings to match the reset
      if (settings) {
        setLocalSettings(settings);
      }
      showToast('Settings reset to defaults', 'success');
      setHasUnsavedChanges(false);
    } catch (error) {
      showToast('Failed to reset settings', 'error');
    }
  };

  const handleSettingsChange = (updates: Partial<UserSettings>) => {
    setHasUnsavedChanges(true);
    setLocalSettings(prev => prev ? { ...prev, ...updates } : null);
  };

  const handleClose = () => {
    if (hasUnsavedChanges) {
      const confirmed = window.confirm('You have unsaved changes. Are you sure you want to close without saving?');
      if (!confirmed) return;
    }
    setLocalSettings(null);
    setHasUnsavedChanges(false);
    onClose();
  };

  // Initialize local settings when modal opens
  useEffect(() => {
    if (isOpen && settings && !localSettings) {
      setLocalSettings(settings);
    }
  }, [isOpen, settings, localSettings]);

  // Auto-validate API keys when switching to API keys tab
  useEffect(() => {
    if (activeTab === 'api-keys' && localSettings?.api_keys?.mode === 'custom') {
      validateAllApiKeys();
    }
  }, [activeTab, localSettings?.api_keys?.mode, validateAllApiKeys]);

  // Early return after all hooks
  if (!isOpen) {
    return null;
  }

  const tabs = [
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'language', label: 'Language', icon: Globe },
    { id: 'rag', label: 'RAG Config', icon: Bot },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'backup', label: 'Backup', icon: Save }
  ] as const;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Settings
          </h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleReset}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
              title="Reset to defaults"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
            <button
              onClick={handleClose}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 dark:bg-gray-700 border-r border-gray-200 dark:border-gray-600">
            <nav className="p-4 space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto p-6">
              {/* Validation Status */}
              {validation && (validation.errors.length > 0 || validation.warnings.length > 0) && (
                <div className="mb-4 space-y-2">
                  {validation.errors.map((error, index) => (
                    <div key={index} className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <AlertCircle className="w-4 h-4 text-red-500" />
                        <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                      </div>
                    </div>
                  ))}
                  {validation.warnings.map((warning, index) => (
                    <div key={index} className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <AlertCircle className="w-4 h-4 text-yellow-500" />
                        <p className="text-sm text-yellow-700 dark:text-yellow-300">{warning}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* API Key Validation Status */}
              {activeTab === 'api-keys' && settings?.api_keys?.mode === 'custom' && (
                <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">API Key Status</h4>
                  <div className="space-y-1 text-sm">
                    {settings.api_keys.openai && (
                      <div className="flex items-center space-x-2">
                        {apiKeyValidation.openai === true ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : apiKeyValidation.openai === false ? (
                          <AlertCircle className="w-4 h-4 text-red-500" />
                        ) : (
                          <div className="w-4 h-4 border-2 border-gray-300 rounded-full" />
                        )}
                        <span className="text-blue-800 dark:text-blue-200">OpenAI: {apiKeyValidation.openai === true ? 'Valid' : apiKeyValidation.openai === false ? 'Invalid' : 'Not validated'}</span>
                      </div>
                    )}
                    {settings.api_keys.cohere && (
                      <div className="flex items-center space-x-2">
                        {apiKeyValidation.cohere === true ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : apiKeyValidation.cohere === false ? (
                          <AlertCircle className="w-4 h-4 text-red-500" />
                        ) : (
                          <div className="w-4 h-4 border-2 border-gray-300 rounded-full" />
                        )}
                        <span className="text-blue-800 dark:text-blue-200">Cohere: {apiKeyValidation.cohere === true ? 'Valid' : apiKeyValidation.cohere === false ? 'Invalid' : 'Not validated'}</span>
                      </div>
                    )}
                    {settings.api_keys.google && (
                      <div className="flex items-center space-x-2">
                        {apiKeyValidation.google === true ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : apiKeyValidation.google === false ? (
                          <AlertCircle className="w-4 h-4 text-red-500" />
                        ) : (
                          <div className="w-4 h-4 border-2 border-gray-300 rounded-full" />
                        )}
                        <span className="text-blue-800 dark:text-blue-200">Google Cloud: {apiKeyValidation.google === true ? 'Valid' : apiKeyValidation.google === false ? 'Invalid' : 'Not validated'}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {error && (
                <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 text-red-500" />
                    <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                  </div>
                </div>
              )}
              
              {/* Debug info - remove in production */}
              {process.env.NODE_ENV === 'development' && settings && (
                <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                  <details>
                    <summary className="cursor-pointer text-gray-600 dark:text-gray-400">Debug: Settings Structure</summary>
                    <pre className="mt-2 text-xs overflow-auto max-h-32">
                      {JSON.stringify(settings, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
              
              {localSettings ? (
                <>
                  {activeTab === 'api-keys' && (
                    <ApiKeysTab
                      settings={localSettings.api_keys || { mode: 'default' }}
                      onChange={(updates: any) => handleSettingsChange({ api_keys: updates })}
                    />
                  )}
                  {activeTab === 'language' && (
                    <LanguageTab
                      settings={localSettings.language || { preferred: 'en', agent_language: 'auto', ui_language: 'auto' }}
                      onChange={(updates: any) => handleSettingsChange({ language: updates })}
                    />
                  )}
                  {activeTab === 'rag' && (
                    <RAGTab
                      settings={localSettings.rag || { search_mode: 'hybrid', top_k: 5, use_reranking: true, enable_ocr: true }}
                      onChange={(updates: any) => handleSettingsChange({ rag: updates })}
                    />
                  )}
                  {activeTab === 'appearance' && (
                    <AppearanceTab
                      settings={localSettings.ui || { theme: 'system', compact_mode: false, font_size: 'medium' }}
                      onChange={(updates: any) => handleSettingsChange({ ui: updates })}
                    />
                  )}
                  {activeTab === 'backup' && (
                    <SettingsBackup
                      onImport={(importedSettings) => {
                        handleSettingsChange(importedSettings);
                        setHasUnsavedChanges(true);
                      }}
                    />
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-500 dark:text-gray-400">Loading settings...</p>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {hasUnsavedChanges && 'You have unsaved changes'}
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={isLoading || isValidating || !hasUnsavedChanges || (validation && !validation.isValid)}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isValidating ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Validating...</span>
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        <span>{isLoading ? 'Saving...' : 'Save & Apply'}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
