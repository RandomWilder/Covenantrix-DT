/**
 * Environment Detection Utilities
 * Detects runtime environment and provides safe access to Electron APIs
 */

/**
 * Check if running in Electron environment
 */
export const isElectron = (): boolean => {
  return typeof window !== 'undefined' && 
         window.electronAPI !== undefined;
};

/**
 * Check if running in browser (Vite dev server)
 */
export const isBrowser = (): boolean => {
  return !isElectron();
};

/**
 * Safe wrapper for Electron API calls
 * Returns null if not in Electron environment
 */
export const safeElectronAPI = <T>(
  apiCall: () => Promise<T>,
  fallback?: T
): Promise<T | null> => {
  if (!isElectron()) {
    console.warn('Electron API called in browser mode, returning fallback');
    return Promise.resolve(fallback ?? null);
  }
  return apiCall();
};

/**
 * Get environment name for logging
 */
export const getEnvironmentName = (): string => {
  if (isElectron()) return 'Electron';
  if (typeof window !== 'undefined') return 'Browser';
  return 'Server';
};

/**
 * Log with environment context
 */
export const envLog = (message: string, ...args: any[]) => {
  const env = getEnvironmentName();
  console.log(`[${env}] ${message}`, ...args);
};

/**
 * Warn with environment context
 */
export const envWarn = (message: string, ...args: any[]) => {
  const env = getEnvironmentName();
  console.warn(`[${env}] ${message}`, ...args);
};

