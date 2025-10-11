/**
 * useSettings Hook
 * Custom hook for settings management with additional utilities
 */

import { useCallback, useEffect, useState } from 'react';
import { useSettings as useSettingsContext } from '../contexts/SettingsContext';
import { UserSettings, ApiKeySettings } from '../types/settings';

export interface SettingsValidation {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface ApiKeyValidation {
  openai: boolean | null;
  cohere: boolean | null;
  google: boolean | null;
}

export const useSettings = () => {
  const context = useSettingsContext();
  const [validation, setValidation] = useState<SettingsValidation>({
    isValid: true,
    errors: [],
    warnings: []
  });
  const [apiKeyValidation, setApiKeyValidation] = useState<ApiKeyValidation>({
    openai: null,
    cohere: null,
    google: null
  });
  const [isFirstRun, setIsFirstRun] = useState(false);

  // Check if this is the first run
  useEffect(() => {
    const checkFirstRun = async () => {
      try {
        // Check if settings exist and have default values
        if (context.settings) {
          const hasCustomApiKeys = context.settings.api_keys.mode === 'custom' && 
            (context.settings.api_keys.openai || context.settings.api_keys.cohere || context.settings.api_keys.google);
          
          const hasNonDefaultSettings = 
            context.settings.language.preferred !== 'en' ||
            context.settings.language.agent_language !== 'auto' ||
            context.settings.language.ui_language !== 'auto' ||
            context.settings.rag.search_mode !== 'hybrid' ||
            context.settings.rag.top_k !== 5 ||
            context.settings.rag.use_reranking !== true ||
            context.settings.rag.enable_ocr !== true ||
            context.settings.ui.theme !== 'system' ||
            context.settings.ui.compact_mode !== false ||
            context.settings.ui.font_size !== 'medium';

          setIsFirstRun(!hasCustomApiKeys && !hasNonDefaultSettings);
        }
      } catch (error) {
        console.error('Error checking first run status:', error);
        setIsFirstRun(true);
      }
    };

    checkFirstRun();
  }, [context.settings]);

  // Validate settings
  const validateSettings = useCallback((settings: UserSettings): SettingsValidation => {
    const errors: string[] = [];
    const warnings: string[] = [];

    // API Keys validation
    if (settings.api_keys.mode === 'custom') {
      if (!settings.api_keys.openai) {
        errors.push('OpenAI API key is required for custom mode');
      }
      if (!settings.api_keys.cohere && settings.rag.use_reranking) {
        warnings.push('Cohere API key recommended for reranking feature');
      }
      if (!settings.api_keys.google && settings.rag.enable_ocr) {
        warnings.push('Google Cloud API key required for OCR feature');
      }
    }

    // RAG settings validation
    if (settings.rag.top_k < 1 || settings.rag.top_k > 20) {
      errors.push('Top-K must be between 1 and 20');
    }

    // Language validation
    if (settings.language.preferred === 'he' && settings.language.agent_language === 'auto') {
      warnings.push('Consider setting agent language to Hebrew for better RTL support');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }, []);

  // Validate individual API key
  const validateApiKey = useCallback(async (keyType: keyof ApiKeySettings, apiKey: string): Promise<boolean> => {
    if (!apiKey) return false;

    try {
      // Use the context's validation method
      const isValid = await context.validateApiKeys();
      
      // Update validation state
      setApiKeyValidation(prev => ({
        ...prev,
        [keyType]: isValid
      }));

      return isValid;
    } catch (error) {
      console.error(`Error validating ${keyType} key:`, error);
      setApiKeyValidation(prev => ({
        ...prev,
        [keyType]: false
      }));
      return false;
    }
  }, [context]);

  // Validate all API keys
  const validateAllApiKeys = useCallback(async (): Promise<ApiKeyValidation> => {
    if (!context.settings?.api_keys || context.settings.api_keys.mode === 'default') {
      return { openai: null, cohere: null, google: null };
    }

    const results: ApiKeyValidation = {
      openai: null,
      cohere: null,
      google: null
    };

    try {
      // Validate OpenAI key
      if (context.settings.api_keys.openai) {
        results.openai = await validateApiKey('openai', context.settings.api_keys.openai);
      }

      // Validate Cohere key
      if (context.settings.api_keys.cohere) {
        results.cohere = await validateApiKey('cohere', context.settings.api_keys.cohere);
      }

      // Validate Google Cloud key
      if (context.settings.api_keys.google) {
        results.google = await validateApiKey('google', context.settings.api_keys.google);
      }

      setApiKeyValidation(results);
      return results;
    } catch (error) {
      console.error('Error validating API keys:', error);
      return results;
    }
  }, [context.settings?.api_keys, validateApiKey]);

  // Update settings with validation
  const updateSettingsWithValidation = useCallback(async (updates: Partial<UserSettings>) => {
    try {
      await context.updateSettings(updates);
      
      // Re-validate settings after update
      if (context.settings) {
        const validationResult = validateSettings({ ...context.settings, ...updates });
        setValidation(validationResult);
      }
    } catch (error) {
      console.error('Error updating settings:', error);
      throw error;
    }
  }, [context, validateSettings]);

  // Reset to defaults
  const resetToDefaults = useCallback(async () => {
    try {
      await context.resetSettings();
      setValidation({ isValid: true, errors: [], warnings: [] });
      setApiKeyValidation({ openai: null, cohere: null, google: null });
    } catch (error) {
      console.error('Error resetting settings:', error);
      throw error;
    }
  }, [context]);

  // Export settings
  const exportSettings = useCallback((): string => {
    if (!context.settings) return '';
    
    // Create exportable settings (remove sensitive data)
    const exportableSettings = {
      ...context.settings,
      api_keys: {
        mode: context.settings.api_keys.mode,
        // Don't export actual API keys
        openai: context.settings.api_keys.openai ? '***' : undefined,
        cohere: context.settings.api_keys.cohere ? '***' : undefined,
        google: context.settings.api_keys.google ? '***' : undefined
      }
    };

    return JSON.stringify(exportableSettings, null, 2);
  }, [context.settings]);

  // Import settings
  const importSettings = useCallback(async (settingsJson: string) => {
    try {
      const importedSettings = JSON.parse(settingsJson);
      
      // Validate imported settings structure
      const validationResult = validateSettings(importedSettings);
      if (!validationResult.isValid) {
        throw new Error(`Invalid settings: ${validationResult.errors.join(', ')}`);
      }

      await context.updateSettings(importedSettings);
      setValidation(validationResult);
    } catch (error) {
      console.error('Error importing settings:', error);
      throw error;
    }
  }, [context, validateSettings]);

  // Get settings summary
  const getSettingsSummary = useCallback(() => {
    if (!context.settings) return null;

    return {
      apiKeys: {
        mode: context.settings.api_keys.mode,
        hasCustomKeys: context.settings.api_keys.mode === 'custom' && 
          (context.settings.api_keys.openai || context.settings.api_keys.cohere || context.settings.api_keys.google)
      },
      language: {
        ui: context.settings.language.ui_language,
        agent: context.settings.language.agent_language,
        preferred: context.settings.language.preferred
      },
      rag: {
        searchMode: context.settings.rag.search_mode,
        topK: context.settings.rag.top_k,
        reranking: context.settings.rag.use_reranking,
        ocr: context.settings.rag.enable_ocr
      },
      ui: {
        theme: context.settings.ui.theme,
        compact: context.settings.ui.compact_mode,
        fontSize: context.settings.ui.font_size
      }
    };
  }, [context.settings]);

  return {
    ...context,
    validation,
    apiKeyValidation,
    isFirstRun,
    validateSettings,
    validateApiKey,
    validateAllApiKeys,
    updateSettingsWithValidation,
    resetToDefaults,
    exportSettings,
    importSettings,
    getSettingsSummary
  };
};
