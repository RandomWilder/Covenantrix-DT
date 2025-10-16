/**
 * Settings Context
 * Manages user settings state and IPC communication
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { UserSettings, SettingsContextValue, SettingsError } from '../types/settings';
import type { ServiceStatus } from '../types/services';
import { isElectron, envLog, envWarn } from '../utils/environment';

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined);

interface SettingsProviderProps {
  children: React.ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<SettingsError | null>(null);
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null);

  // Load settings on mount
  useEffect(() => {
    if (!isElectron()) {
      envLog('SettingsContext: Running in browser mode, using default settings');
      const defaultSettings = getDefaultSettings();
      setSettings(defaultSettings);
      setIsLoading(false);
      return;
    }
    loadSettings();
  }, []);

  const loadSettings = useCallback(async () => {
    if (!isElectron()) {
      envWarn('loadSettings: Not in Electron environment, using defaults');
      const defaultSettings = getDefaultSettings();
      setSettings(defaultSettings);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      envLog('Loading settings...');
      const response = await window.electronAPI.getSettings();
      envLog('Settings response:', response);
      
      if (response.success) {
        envLog('Settings loaded successfully:', response.settings);
        const validatedSettings = validateAndNormalizeSettings(response.settings);
        envLog('Validated settings:', validatedSettings);
        setSettings(validatedSettings);
      } else {
        console.error('Failed to load settings:', response.error);
        // Set default settings if loading fails
        const defaultSettings = getDefaultSettings();
        envLog('Using default settings:', defaultSettings);
        setSettings(defaultSettings);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      const defaultSettings = getDefaultSettings();
      envLog('Using default settings due to error:', defaultSettings);
      setSettings(defaultSettings);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateSettings = useCallback(async (updates: Partial<UserSettings>) => {
    if (!isElectron()) {
      envWarn('updateSettings: Not in Electron environment, only updating local state');
      // Deep merge for nested objects to prevent data loss
      const updatedSettings: UserSettings = {
        ...settings,
        ...updates,
        // Explicitly merge nested objects
        api_keys: updates.api_keys ? { ...settings?.api_keys, ...updates.api_keys } : settings?.api_keys,
        rag: updates.rag ? { ...settings?.rag, ...updates.rag } : settings?.rag,
        language: updates.language ? { ...settings?.language, ...updates.language } : settings?.language,
        ui: updates.ui ? { ...settings?.ui, ...updates.ui } : settings?.ui,
        privacy: updates.privacy ? { ...settings?.privacy, ...updates.privacy } : settings?.privacy,
        profile: updates.profile ? { ...settings?.profile, ...updates.profile } : settings?.profile,
        google_accounts: updates.google_accounts || settings?.google_accounts || [],
        last_updated: new Date().toISOString(),
        version: '1.0'
      } as UserSettings;
      setSettings(updatedSettings);
      return;
    }

    try {
      setIsLoading(true);
      setError(null); // Clear previous errors
      
      // Deep merge for nested objects to prevent data loss
      const updatedSettings: UserSettings = {
        ...settings,
        ...updates,
        // Explicitly merge nested objects
        api_keys: updates.api_keys ? { ...settings?.api_keys, ...updates.api_keys } : settings?.api_keys,
        rag: updates.rag ? { ...settings?.rag, ...updates.rag } : settings?.rag,
        language: updates.language ? { ...settings?.language, ...updates.language } : settings?.language,
        ui: updates.ui ? { ...settings?.ui, ...updates.ui } : settings?.ui,
        privacy: updates.privacy ? { ...settings?.privacy, ...updates.privacy } : settings?.privacy,
        profile: updates.profile ? { ...settings?.profile, ...updates.profile } : settings?.profile,
        google_accounts: updates.google_accounts || settings?.google_accounts || [],
        last_updated: new Date().toISOString(),
        version: '1.0'
      } as UserSettings;

      const response = await window.electronAPI.updateSettings(updatedSettings);
      
      if (response.success) {
        setSettings(updatedSettings);
        setError(null);
      } else {
        const settingsError: SettingsError = {
          message: response.error || 'Failed to update settings',
          validationErrors: response.validationErrors
        };
        setError(settingsError);
        throw new Error(settingsError.message);
      }
    } catch (error) {
      console.error('Error updating settings:', error);
      // Error state is already set above
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [settings]);

  const resetSettings = useCallback(async () => {
    const defaultSettings = getDefaultSettings();
    
    if (!isElectron()) {
      envWarn('resetSettings: Not in Electron environment, only resetting local state');
      setSettings(defaultSettings);
      return;
    }

    try {
      setIsLoading(true);
      
      const response = await window.electronAPI.updateSettings(defaultSettings);
      
      if (response.success) {
        setSettings(defaultSettings);
      } else {
        throw new Error(response.error || 'Failed to reset settings');
      }
    } catch (error) {
      console.error('Error resetting settings:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const validateApiKeys = useCallback(async (): Promise<boolean> => {
    if (!settings?.api_keys) return false;
    
    if (!isElectron()) {
      envWarn('validateApiKeys: Not in Electron environment, returning false');
      return false;
    }
    
    try {
      const response = await window.electronAPI.validateApiKeys(settings.api_keys);
      return response.success;
    } catch (error) {
      console.error('Error validating API keys:', error);
      return false;
    }
  }, [settings?.api_keys]);

  const fetchServiceStatus = useCallback(async () => {
    if (!isElectron()) {
      envWarn('fetchServiceStatus: Not in Electron environment, setting unavailable status');
      setServiceStatus({
        openai_available: false,
        cohere_available: false,
        google_available: false,
        features: {
          chat: false,
          upload: false,
          reranking: false,
          ocr: false
        }
      });
      return;
    }

    try {
      const response = await window.electronAPI.getServicesStatus();
      if (response.success && response.data) {
        setServiceStatus(response.data);
      } else {
        console.error('Failed to fetch service status:', response.error);
        // Set default unavailable status
        setServiceStatus({
          openai_available: false,
          cohere_available: false,
          google_available: false,
          features: {
            chat: false,
            upload: false,
            reranking: false,
            ocr: false
          }
        });
      }
    } catch (error) {
      console.error('Error fetching service status:', error);
      // Set default unavailable status on error
      setServiceStatus({
        openai_available: false,
        cohere_available: false,
        google_available: false,
        features: {
          chat: false,
          upload: false,
          reranking: false,
          ocr: false
        }
      });
    }
  }, []);

  const applySettings = useCallback(async () => {
    if (!settings) return;
    
    if (!isElectron()) {
      envWarn('applySettings: Not in Electron environment, skipping');
      return;
    }
    
    try {
      const response = await window.electronAPI.applySettings(settings);
      if (!response.success) {
        throw new Error(response.error || 'Failed to apply settings');
      }
      
      // Check if services were reloaded
      if (response.restart_required) {
        envLog('Services reload required, notifying user...');
        // Note: Services will reload automatically, no action needed
        // The backend handles RAG engine reinitialization
      } else if (response.applied_services?.includes('rag_engine_reloaded')) {
        envLog('Services successfully reloaded with new configuration');
      }
      
      // Fetch updated service status after applying settings
      await fetchServiceStatus();
    } catch (error) {
      console.error('Error applying settings:', error);
      throw error;
    }
  }, [settings, fetchServiceStatus]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Fetch service status on mount
  useEffect(() => {
    if (!isElectron()) {
      envLog('SettingsContext: Skipping service status fetch in browser mode');
      return;
    }
    fetchServiceStatus();
  }, [fetchServiceStatus]);

  const value: SettingsContextValue = {
    settings,
    isLoading,
    error,
    serviceStatus,
    updateSettings,
    resetSettings,
    validateApiKeys,
    applySettings,
    fetchServiceStatus,
    clearError
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = (): SettingsContextValue => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

// Default settings factory
function getDefaultSettings(): UserSettings {
  return {
    onboarding_completed: false,
    api_keys: {
      mode: 'default'
    },
    rag: {
      search_mode: 'hybrid',
      top_k: 5,
      use_reranking: true,
      enable_ocr: true,
      llm_model: 'gpt-4o-mini'
    },
    language: {
      preferred: 'en',
      agent_language: 'auto',
      ui_language: 'auto'
    },
    ui: {
      theme: 'system',
      compact_mode: false,
      font_size: 'medium',
      zoom_level: 0.8 // Default to 80% zoom for better laptop fit
    },
    privacy: {
      enable_telemetry: false,
      enable_cloud_backup: false,
      retain_history: true
    },
    profile: {
      first_name: undefined,
      last_name: undefined,
      email: undefined
    },
    google_accounts: [],
    version: '1.0',
    last_updated: new Date().toISOString()
  };
}

// Settings validation and normalization
function validateAndNormalizeSettings(settings: any): UserSettings {
  const defaults = getDefaultSettings();
  
  // Ensure all required sections exist with proper structure
  return {
    onboarding_completed: settings?.onboarding_completed ?? defaults.onboarding_completed,
    api_keys: {
      mode: settings?.api_keys?.mode || defaults.api_keys.mode,
      openai: settings?.api_keys?.openai,
      cohere: settings?.api_keys?.cohere,
      google: settings?.api_keys?.google
    },
    rag: {
      search_mode: settings?.rag?.search_mode || defaults.rag.search_mode,
      top_k: settings?.rag?.top_k || defaults.rag.top_k,
      use_reranking: settings?.rag?.use_reranking ?? defaults.rag.use_reranking,
      enable_ocr: settings?.rag?.enable_ocr ?? defaults.rag.enable_ocr,
      llm_model: settings?.rag?.llm_model || defaults.rag.llm_model
    },
    language: {
      preferred: settings?.language?.preferred || defaults.language.preferred,
      agent_language: settings?.language?.agent_language || defaults.language.agent_language,
      ui_language: settings?.language?.ui_language || defaults.language.ui_language
    },
    ui: {
      theme: settings?.ui?.theme || defaults.ui.theme,
      compact_mode: settings?.ui?.compact_mode ?? defaults.ui.compact_mode,
      font_size: settings?.ui?.font_size || defaults.ui.font_size,
      zoom_level: settings?.ui?.zoom_level ?? defaults.ui.zoom_level
    },
    privacy: {
      enable_telemetry: settings?.privacy?.enable_telemetry ?? defaults.privacy.enable_telemetry,
      enable_cloud_backup: settings?.privacy?.enable_cloud_backup ?? defaults.privacy.enable_cloud_backup,
      retain_history: settings?.privacy?.retain_history ?? defaults.privacy.retain_history
    },
    profile: {
      first_name: settings?.profile?.first_name,
      last_name: settings?.profile?.last_name,
      email: settings?.profile?.email
    },
    google_accounts: Array.isArray(settings?.google_accounts) ? settings.google_accounts : [],
    version: settings?.version || defaults.version,
    last_updated: settings?.last_updated || new Date().toISOString()
  };
}
