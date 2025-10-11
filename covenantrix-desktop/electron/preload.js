const { contextBridge, ipcRenderer } = require('electron')

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getVersion: () => ipcRenderer.invoke('get-version'),
  
  // Document operations
  openDocument: (filePath) => ipcRenderer.invoke('open-document', filePath),
  saveDocument: (data) => ipcRenderer.invoke('save-document', data),
  
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  updateSettings: (settings) => ipcRenderer.invoke('update-settings', settings),
  validateApiKeys: (apiKeys) => ipcRenderer.invoke('validate-api-keys', apiKeys),
  applySettings: (settings) => ipcRenderer.invoke('apply-settings', settings),
  
  // Zoom level management
  setZoomLevel: (zoomLevel) => ipcRenderer.invoke('set-zoom-level', zoomLevel),
  getZoomLevel: () => ipcRenderer.invoke('get-zoom-level'),
  
  // File operations
  selectFile: (options) => ipcRenderer.invoke('select-file', options),
  selectFiles: (options) => ipcRenderer.invoke('select-files', options),
  selectFolder: (options) => ipcRenderer.invoke('select-directory', options),
  validateFiles: (filePaths) => ipcRenderer.invoke('validate-files', filePaths),
  getFileInfo: (filePath) => ipcRenderer.invoke('get-file-info', filePath),
  readFilePreview: (filePath, maxSize) => ipcRenderer.invoke('read-file-preview', filePath, maxSize),
  
  // System
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  
  // Storage management
  getStoragePath: () => ipcRenderer.invoke('get-storage-path'),
  validateStorageDirectory: () => ipcRenderer.invoke('validate-storage-directory'),
  
  // Event listeners
  onDocumentProcessed: (callback) => ipcRenderer.on('document-processed', callback),
  onSettingsChanged: (callback) => ipcRenderer.on('settings-changed', callback),
  
  // Remove listeners
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
})

// Security: Prevent the renderer from accessing Node.js APIs
window.addEventListener('DOMContentLoaded', () => {
  // Remove any existing Node.js globals
  delete window.require
  delete window.exports
  delete window.module
})
