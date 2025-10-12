/**
 * Settings Type Definitions
 * User preferences and API key configuration
 */

import type { ServiceStatus } from './services';

export type ApiKeyMode = 'default' | 'custom';
export type SearchMode = 'naive' | 'local' | 'global' | 'hybrid';
export type Language = 'en' | 'es' | 'fr' | 'he' | 'de';
export type Theme = 'light' | 'dark' | 'system';
export type FontSize = 'small' | 'medium' | 'large';

export interface ApiKeySettings {
  mode: ApiKeyMode;
  openai?: string;        // Only if mode === 'custom'
  cohere?: string;        // Only if mode === 'custom'  
  google?: string;        // Only if mode === 'custom'
  google_vision?: string; // Only if mode === 'custom' (for OCR)
}

export interface RAGSettings {
  search_mode: SearchMode;
  top_k: number;           // 1-20
  use_reranking: boolean;
  enable_ocr: boolean;
}

export interface LanguageSettings {
  preferred: Language;
  agent_language: 'auto' | Language;
  ui_language: 'auto' | 'en' | 'es';
}

export interface UISettings {
  theme: Theme;
  compact_mode: boolean;
  font_size: FontSize;
  zoom_level: number; // 0.5 to 2.0 (50% to 200%)
}

export interface PrivacySettings {
  enable_telemetry: boolean;
  enable_cloud_backup: boolean;  // future
  retain_history: boolean;
}

export interface UserSettings {
  api_keys: ApiKeySettings;
  rag: RAGSettings;
  language: LanguageSettings;
  ui: UISettings;
  privacy: PrivacySettings;
  version: string;
  last_updated?: string;
}

export interface ValidationError {
  field: string;
  message: string;
  type: string;
}

export interface SettingsError {
  message: string;
  validationErrors?: ValidationError[];
}

export interface KeyStatusResponse {
  has_valid_key: boolean;
  mode: ApiKeyMode | null;
  message: string;
}

export interface SettingsContextValue {
  settings: UserSettings | null;
  isLoading: boolean;
  error: SettingsError | null;
  serviceStatus: ServiceStatus | null;
  updateSettings: (updates: Partial<UserSettings>) => Promise<void>;
  resetSettings: () => Promise<void>;
  validateApiKeys: () => Promise<boolean>;
  applySettings: () => Promise<void>;
  fetchServiceStatus: () => Promise<void>;
  clearError: () => void;
}