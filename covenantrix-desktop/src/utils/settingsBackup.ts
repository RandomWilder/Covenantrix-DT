/**
 * Settings Backup/Restore Utilities
 * Handle settings export/import and backup functionality
 */

import { UserSettings } from '../types/settings'
import { createTimestamp } from './dateUtils';
import { sanitizeSettingsForExport, validateAndNormalizeSettings } from './settings';

export interface BackupMetadata {
  version: string;
  timestamp: string;
  appVersion: string;
  description?: string;
}

export interface SettingsBackup {
  metadata: BackupMetadata;
  settings: Partial<UserSettings>;
}

/**
 * Create a settings backup
 */
export const createSettingsBackup = (
  settings: UserSettings,
  description?: string
): SettingsBackup => {
  const metadata: BackupMetadata = {
    version: '1.0',
    timestamp: createTimestamp(),
    appVersion: '1.0.0', // This should match package.json version
    description
  };

  return {
    metadata,
    settings: sanitizeSettingsForExport(settings)
  };
};

/**
 * Export settings to JSON string
 */
export const exportSettingsToJSON = (
  settings: UserSettings,
  description?: string
): string => {
  const backup = createSettingsBackup(settings, description);
  return JSON.stringify(backup, null, 2);
};

/**
 * Import settings from JSON string
 */
export const importSettingsFromJSON = (jsonString: string): Partial<UserSettings> => {
  try {
    const backup: SettingsBackup = JSON.parse(jsonString);
    
    // Validate backup structure
    if (!backup.metadata || !backup.settings) {
      throw new Error('Invalid backup format');
    }

    // Check version compatibility
    if (backup.metadata.version !== '1.0') {
      throw new Error(`Unsupported backup version: ${backup.metadata.version}`);
    }

    // Validate and normalize settings
    const normalizedSettings = validateAndNormalizeSettings(backup.settings);
    
    return normalizedSettings;
  } catch (error) {
    console.error('Error importing settings:', error);
    throw new Error(`Failed to import settings: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

/**
 * Download settings as file
 */
export const downloadSettingsFile = (
  settings: UserSettings,
  filename?: string
): void => {
  const jsonString = exportSettingsToJSON(settings);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename || `covenantrix-settings-${createTimestamp().split('T')[0]}.json`;
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
};

/**
 * Read settings file from input
 */
export const readSettingsFile = (file: File): Promise<Partial<UserSettings>> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const jsonString = event.target?.result as string;
        const settings = importSettingsFromJSON(jsonString);
        resolve(settings);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsText(file);
  });
};

/**
 * Validate backup file before import
 */
export const validateBackupFile = (file: File): Promise<{ valid: boolean; error?: string }> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const jsonString = event.target?.result as string;
        const backup: SettingsBackup = JSON.parse(jsonString);
        
        // Basic validation
        if (!backup.metadata || !backup.settings) {
          resolve({ valid: false, error: 'Invalid backup format' });
          return;
        }
        
        if (backup.metadata.version !== '1.0') {
          resolve({ valid: false, error: `Unsupported version: ${backup.metadata.version}` });
          return;
        }
        
        // Try to normalize settings
        validateAndNormalizeSettings(backup.settings);
        
        resolve({ valid: true });
      } catch (error) {
        resolve({ 
          valid: false, 
          error: error instanceof Error ? error.message : 'Invalid file format' 
        });
      }
    };
    
    reader.onerror = () => {
      resolve({ valid: false, error: 'Failed to read file' });
    };
    
    reader.readAsText(file);
  });
};

/**
 * Get backup metadata from file
 */
export const getBackupMetadata = (file: File): Promise<BackupMetadata | null> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const jsonString = event.target?.result as string;
        const backup: SettingsBackup = JSON.parse(jsonString);
        resolve(backup.metadata || null);
      } catch (error) {
        resolve(null);
      }
    };
    
    reader.onerror = () => {
      resolve(null);
    };
    
    reader.readAsText(file);
  });
};

/**
 * Create settings comparison
 */
export const compareSettings = (
  current: UserSettings,
  backup: Partial<UserSettings>
): { changed: string[]; added: string[]; removed: string[] } => {
  const changed: string[] = [];
  const added: string[] = [];
  const removed: string[] = [];

  // Compare API keys
  if (backup.api_keys) {
    if (backup.api_keys.mode !== current.api_keys.mode) {
      changed.push('API Key Mode');
    }
    if (backup.api_keys.openai !== current.api_keys.openai) {
      changed.push('OpenAI API Key');
    }
    if (backup.api_keys.cohere !== current.api_keys.cohere) {
      changed.push('Cohere API Key');
    }
    if (backup.api_keys.google !== current.api_keys.google) {
      changed.push('Google API Key');
    }
  }

  // Compare RAG settings
  if (backup.rag) {
    if (backup.rag.search_mode !== current.rag.search_mode) {
      changed.push('Search Mode');
    }
    if (backup.rag.top_k !== current.rag.top_k) {
      changed.push('Top-K Results');
    }
    if (backup.rag.use_reranking !== current.rag.use_reranking) {
      changed.push('Reranking');
    }
    if (backup.rag.enable_ocr !== current.rag.enable_ocr) {
      changed.push('OCR');
    }
  }

  // Compare language settings
  if (backup.language) {
    if (backup.language.preferred !== current.language.preferred) {
      changed.push('Preferred Language');
    }
    if (backup.language.agent_language !== current.language.agent_language) {
      changed.push('Agent Language');
    }
    if (backup.language.ui_language !== current.language.ui_language) {
      changed.push('UI Language');
    }
  }

  // Compare UI settings
  if (backup.ui) {
    if (backup.ui.theme !== current.ui.theme) {
      changed.push('Theme');
    }
    if (backup.ui.compact_mode !== current.ui.compact_mode) {
      changed.push('Compact Mode');
    }
    if (backup.ui.font_size !== current.ui.font_size) {
      changed.push('Font Size');
    }
  }

  // Compare privacy settings
  if (backup.privacy) {
    if (backup.privacy.enable_telemetry !== current.privacy.enable_telemetry) {
      changed.push('Telemetry');
    }
    if (backup.privacy.retain_history !== current.privacy.retain_history) {
      changed.push('History Retention');
    }
  }

  return { changed, added, removed };
};
