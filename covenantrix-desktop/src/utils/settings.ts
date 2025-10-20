/**
 * Settings Utilities
 * Helper functions for settings management and validation
 */

import { UserSettings, Language, Theme, FontSize } from '../types/settings';
import { createTimestamp } from './dateUtils';

/**
 * Default settings factory
 */
export const getDefaultSettings = (): UserSettings => {
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
      zoom_level: 1.0
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
    last_updated: createTimestamp()
  };
};

/**
 * Validate and normalize settings
 */
export const validateAndNormalizeSettings = (settings: any): UserSettings => {
  const defaults = getDefaultSettings();
  
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
      top_k: Math.max(1, Math.min(20, settings?.rag?.top_k || defaults.rag.top_k)),
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
};

/**
 * Check if settings are valid
 */
export const isValidSettings = (settings: any): boolean => {
  try {
    const normalized = validateAndNormalizeSettings(settings);
    
    // Check required fields
    if (!normalized.api_keys || !normalized.rag || !normalized.language || !normalized.ui || !normalized.privacy) {
      return false;
    }

    // Check API keys mode
    if (normalized.api_keys.mode !== 'default' && normalized.api_keys.mode !== 'custom') {
      return false;
    }

    // Check RAG settings
    if (normalized.rag.top_k < 1 || normalized.rag.top_k > 20) {
      return false;
    }

    // Check language settings
    const validLanguages: Language[] = ['en', 'es', 'fr', 'he', 'de'];
    if (!validLanguages.includes(normalized.language.preferred)) {
      return false;
    }

    // Check UI settings
    const validThemes: Theme[] = ['light', 'dark', 'system'];
    if (!validThemes.includes(normalized.ui.theme)) {
      return false;
    }

    const validFontSizes: FontSize[] = ['small', 'medium', 'large'];
    if (!validFontSizes.includes(normalized.ui.font_size)) {
      return false;
    }

    return true;
  } catch (error) {
    console.error('Error validating settings:', error);
    return false;
  }
};

/**
 * Get settings validation errors
 */
export const getSettingsValidationErrors = (settings: any): string[] => {
  const errors: string[] = [];

  if (!settings) {
    errors.push('Settings object is required');
    return errors;
  }

  // Check API keys
  if (!settings.api_keys) {
    errors.push('API keys configuration is required');
  } else {
    if (settings.api_keys.mode === 'custom') {
      if (!settings.api_keys.openai) {
        errors.push('OpenAI API key is required for custom mode');
      }
    }
  }

  // Check RAG settings
  if (!settings.rag) {
    errors.push('RAG configuration is required');
  } else {
    if (settings.rag.top_k < 1 || settings.rag.top_k > 20) {
      errors.push('Top-K must be between 1 and 20');
    }
  }

  // Check language settings
  if (!settings.language) {
    errors.push('Language configuration is required');
  }

  // Check UI settings
  if (!settings.ui) {
    errors.push('UI configuration is required');
  }

  // Check privacy settings
  if (!settings.privacy) {
    errors.push('Privacy configuration is required');
  }

  return errors;
};

/**
 * Get settings validation warnings
 */
export const getSettingsValidationWarnings = (settings: any): string[] => {
  const warnings: string[] = [];

  if (!settings) return warnings;

  // Check for potential issues
  if (settings.api_keys?.mode === 'custom' && settings.rag?.use_reranking && !settings.api_keys?.cohere) {
    warnings.push('Cohere API key recommended for reranking feature');
  }

  if (settings.rag?.enable_ocr && !settings.api_keys?.google) {
    warnings.push('Google API key required for OCR feature');
  }

  if (settings.language?.preferred === 'he' && settings.language?.agent_language === 'auto') {
    warnings.push('Consider setting agent language to Hebrew for better RTL support');
  }

  return warnings;
};

/**
 * Sanitize settings for export (remove sensitive data)
 */
export const sanitizeSettingsForExport = (settings: UserSettings): Partial<UserSettings> => {
  return {
    ...settings,
    api_keys: {
      mode: settings.api_keys.mode,
      // Don't export actual API keys
      openai: settings.api_keys.openai ? '***' : undefined,
      cohere: settings.api_keys.cohere ? '***' : undefined,
      google: settings.api_keys.google ? '***' : undefined
    }
  };
};

/**
 * Check if settings have been customized from defaults
 */
export const hasCustomizedSettings = (settings: UserSettings): boolean => {
  const defaults = getDefaultSettings();

  return (
    settings.api_keys.mode !== defaults.api_keys.mode ||
    settings.language.preferred !== defaults.language.preferred ||
    settings.language.agent_language !== defaults.language.agent_language ||
    settings.language.ui_language !== defaults.language.ui_language ||
    settings.rag.search_mode !== defaults.rag.search_mode ||
    settings.rag.top_k !== defaults.rag.top_k ||
    settings.rag.use_reranking !== defaults.rag.use_reranking ||
    settings.rag.enable_ocr !== defaults.rag.enable_ocr ||
    settings.rag.llm_model !== defaults.rag.llm_model ||
    settings.ui.theme !== defaults.ui.theme ||
    settings.ui.compact_mode !== defaults.ui.compact_mode ||
    settings.ui.font_size !== defaults.ui.font_size ||
    settings.privacy.enable_telemetry !== defaults.privacy.enable_telemetry ||
    settings.privacy.retain_history !== defaults.privacy.retain_history
  );
};

/**
 * Get settings summary for display
 */
export const getSettingsSummary = (settings: UserSettings) => {
  return {
    apiKeys: {
      mode: settings.api_keys.mode,
      hasCustomKeys: settings.api_keys.mode === 'custom' && 
        (settings.api_keys.openai || settings.api_keys.cohere || settings.api_keys.google)
    },
    language: {
      ui: settings.language.ui_language,
      agent: settings.language.agent_language,
      preferred: settings.language.preferred
    },
    rag: {
      searchMode: settings.rag.search_mode,
      topK: settings.rag.top_k,
      reranking: settings.rag.use_reranking,
      ocr: settings.rag.enable_ocr,
      llmModel: settings.rag.llm_model
    },
    ui: {
      theme: settings.ui.theme,
      compact: settings.ui.compact_mode,
      fontSize: settings.ui.font_size
    },
    privacy: {
      telemetry: settings.privacy.enable_telemetry,
      history: settings.privacy.retain_history
    }
  };
};

/**
 * Migrate settings from older versions
 */
export const migrateSettings = (settings: any, fromVersion: string): UserSettings => {
  const normalized = validateAndNormalizeSettings(settings);

  // Add migration logic for different versions
  switch (fromVersion) {
    case '0.9':
      // Example migration from 0.9 to 1.0
      if (!normalized.privacy) {
        normalized.privacy = {
          enable_telemetry: false,
          enable_cloud_backup: false,
          retain_history: true
        };
      }
      break;
    
    default:
      // No migration needed
      break;
  }

  return normalized;
};

/**
 * Get language display name
 */
export const getLanguageDisplayName = (language: Language): string => {
  const names: Record<Language, string> = {
    en: 'English',
    es: 'Español',
    fr: 'Français',
    he: 'עברית',
    de: 'Deutsch'
  };
  return names[language] || language;
};

/**
 * Get theme display name
 */
export const getThemeDisplayName = (theme: Theme): string => {
  const names: Record<Theme, string> = {
    light: 'Light',
    dark: 'Dark',
    system: 'System'
  };
  return names[theme] || theme;
};

/**
 * Get font size display name
 */
export const getFontSizeDisplayName = (fontSize: FontSize): string => {
  const names: Record<FontSize, string> = {
    small: 'Small',
    medium: 'Medium',
    large: 'Large'
  };
  return names[fontSize] || fontSize;
};
