/**
 * Global Type Declarations
 * Defines types for global objects and APIs
 */

declare global {
  interface Window {
    electronAPI: {
      // App info
      getVersion: () => Promise<string>;
      
      // Document operations
      openDocument: (filePath: string) => Promise<any>;
      saveDocument: (data: any) => Promise<any>;
      
      // Settings
      getSettings: () => Promise<{
        success: boolean;
        settings?: any;
        error?: string;
      }>;
      updateSettings: (settings: any) => Promise<{
        success: boolean;
        error?: string;
        validationErrors?: Array<{
          field: string;
          message: string;
          type: string;
        }>;
        settings?: any;
      }>;
      validateApiKeys: (apiKeys: any) => Promise<{
        success: boolean;
        openai_valid?: boolean | null;
        cohere_valid?: boolean | null;
        google_valid?: boolean | null;
        message?: string;
        errors?: Record<string, string>;
      }>;
      applySettings: (settings: any) => Promise<{
        success: boolean;
        error?: string;
        restart_required?: boolean;
        applied_services?: string[];
      }>;
      getKeyStatus: () => Promise<{
        success: boolean;
        has_valid_key: boolean;
        mode: string | null;
        message: string;
        error?: string;
      }>;
      getServicesStatus: () => Promise<{
        success: boolean;
        data?: {
          openai_available: boolean;
          cohere_available: boolean;
          google_available: boolean;
          features: {
            chat: boolean;
            upload: boolean;
            reranking: boolean;
            ocr: boolean;
          };
        };
        error?: string;
      }>;
      
      // Zoom level management
      setZoomLevel: (zoomLevel: number) => Promise<{
        success: boolean;
        zoomLevel?: number;
        error?: string;
      }>;
      getZoomLevel: () => Promise<{
        success: boolean;
        zoomLevel?: number;
        error?: string;
      }>;
      
      // File operations
      selectFile: (options: any) => Promise<any>;
      selectFiles: (options: any) => Promise<any>;
      selectFolder: (options: any) => Promise<any>;
      validateFiles: (filePaths: string[]) => Promise<any>;
      getFileInfo: (filePath: string) => Promise<any>;
      readFilePreview: (filePath: string, maxSize: number) => Promise<any>;
      
      // System
      showMessageBox: (options: any) => Promise<any>;
      showOpenDialog: (options: any) => Promise<any>;
      showSaveDialog: (options: any) => Promise<any>;
      
      // Storage management
      getStoragePath: () => Promise<string>;
      validateStorageDirectory: () => Promise<any>;
      
      // Google OAuth
      startGoogleOAuth: () => Promise<void>;
      onOAuthCallback: (callback: (data: { code: string; state: string }) => void) => void;
      
      // Event listeners
      onDocumentProcessed: (callback: (event: any, data: any) => void) => void;
      onSettingsChanged: (callback: (event: any, data: any) => void) => void;
      
      // Remove listeners
      removeAllListeners: (channel: string) => void;
    };
  }
}

export {};
