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
      }>;
      validateApiKeys: (apiKeys: any) => Promise<{
        success: boolean;
        error?: string;
      }>;
      applySettings: (settings: any) => Promise<{
        success: boolean;
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
      
      // Event listeners
      onDocumentProcessed: (callback: (event: any, data: any) => void) => void;
      onSettingsChanged: (callback: (event: any, data: any) => void) => void;
      
      // Remove listeners
      removeAllListeners: (channel: string) => void;
    };
  }
}

export {};
