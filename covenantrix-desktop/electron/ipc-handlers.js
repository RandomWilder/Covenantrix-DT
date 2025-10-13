const { ipcMain, dialog } = require('electron')
const path = require('path')
const fs = require('fs').promises
const os = require('os')
const axios = require('axios')
const { openOAuthWindow } = require('./oauth-handler')

/**
 * IPC Handlers for File Operations
 * Handles file selection, validation, and upload operations
 */

// Only register handlers if ipcMain is available (in Electron context)
if (ipcMain) {
  // File selection handlers
  ipcMain.handle('select-files', async (event, options = {}) => {
  try {
    const result = await dialog.showOpenDialog({
      title: 'Select Documents to Upload',
      properties: ['openFile', 'multiSelections'],
      filters: [
        {
          name: 'Supported Documents',
          extensions: ['pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg', 'tiff']
        },
        {
          name: 'PDF Files',
          extensions: ['pdf']
        },
        {
          name: 'Word Documents',
          extensions: ['docx', 'doc']
        },
        {
          name: 'Text Files',
          extensions: ['txt']
        },
        {
          name: 'Images',
          extensions: ['png', 'jpg', 'jpeg', 'tiff']
        },
        {
          name: 'All Files',
          extensions: ['*']
        }
      ],
      ...options
    })

    if (result.canceled) {
      return { success: false, files: [] }
    }

    // Validate selected files
    const validatedFiles = []
    const maxSizeBytes = 50 * 1024 * 1024 // 50MB
    const supportedExtensions = ['pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg', 'tiff']

    for (const filePath of result.filePaths) {
      try {
        const stats = await fs.stat(filePath)
        const ext = path.extname(filePath).toLowerCase().substring(1)
        
        // Check file size
        if (stats.size > maxSizeBytes) {
          console.warn(`File too large: ${filePath} (${(stats.size / (1024 * 1024)).toFixed(2)}MB)`)
          continue
        }

        // Check file extension
        if (!supportedExtensions.includes(ext)) {
          console.warn(`Unsupported file type: ${filePath}`)
          continue
        }

        validatedFiles.push({
          path: filePath,
          name: path.basename(filePath),
          size: stats.size,
          extension: ext,
          lastModified: stats.mtime
        })
      } catch (error) {
        console.error(`Error validating file ${filePath}:`, error)
      }
    }

    return {
      success: true,
      files: validatedFiles,
      totalSize: validatedFiles.reduce((sum, file) => sum + file.size, 0)
    }
  } catch (error) {
    console.error('File selection error:', error)
    return { success: false, error: error.message, files: [] }
  }
})

// Single file selection
ipcMain.handle('select-file', async (event, options = {}) => {
  try {
    const result = await dialog.showOpenDialog({
      title: 'Select Document to Upload',
      properties: ['openFile'],
      filters: [
        {
          name: 'Supported Documents',
          extensions: ['pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg', 'tiff']
        }
      ],
      ...options
    })

    if (result.canceled || result.filePaths.length === 0) {
      return { success: false, file: null }
    }

    const filePath = result.filePaths[0]
    const stats = await fs.stat(filePath)
    const ext = path.extname(filePath).toLowerCase().substring(1)
    const maxSizeBytes = 50 * 1024 * 1024 // 50MB

    // Validate file
    if (stats.size > maxSizeBytes) {
      return {
        success: false,
        error: `File too large: ${(stats.size / (1024 * 1024)).toFixed(2)}MB (max: 50MB)`
      }
    }

    return {
      success: true,
      file: {
        path: filePath,
        name: path.basename(filePath),
        size: stats.size,
        extension: ext,
        lastModified: stats.mtime
      }
    }
  } catch (error) {
    console.error('Single file selection error:', error)
    return { success: false, error: error.message, file: null }
  }
})

// File validation
ipcMain.handle('validate-files', async (event, filePaths) => {
  try {
    const validationResults = []
    const maxSizeBytes = 50 * 1024 * 1024 // 50MB
    const supportedExtensions = ['pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg', 'tiff']

    for (const filePath of filePaths) {
      try {
        const stats = await fs.stat(filePath)
        const ext = path.extname(filePath).toLowerCase().substring(1)
        
        const validation = {
          path: filePath,
          name: path.basename(filePath),
          valid: true,
          errors: [],
          size: stats.size,
          extension: ext,
          lastModified: stats.mtime
        }

        // Check file size
        if (stats.size > maxSizeBytes) {
          validation.valid = false
          validation.errors.push(`File too large: ${(stats.size / (1024 * 1024)).toFixed(2)}MB (max: 50MB)`)
        }

        // Check file extension
        if (!supportedExtensions.includes(ext)) {
          validation.valid = false
          validation.errors.push(`Unsupported file type: .${ext}`)
        }

        validationResults.push(validation)
      } catch (error) {
        validationResults.push({
          path: filePath,
          name: path.basename(filePath),
          valid: false,
          errors: [`File access error: ${error.message}`],
          size: 0,
          extension: path.extname(filePath).toLowerCase().substring(1),
          lastModified: new Date()
        })
      }
    }

    return {
      success: true,
      results: validationResults,
      validCount: validationResults.filter(r => r.valid).length,
      invalidCount: validationResults.filter(r => !r.valid).length
    }
  } catch (error) {
    console.error('File validation error:', error)
    return { success: false, error: error.message, results: [] }
  }
})

// Directory selection for batch operations
ipcMain.handle('select-directory', async (event, options = {}) => {
  try {
    const result = await dialog.showOpenDialog({
      title: 'Select Directory',
      properties: ['openDirectory'],
      ...options
    })

    if (result.canceled) {
      return { success: false, directory: null }
    }

    const directoryPath = result.filePaths[0]
    
    // Scan directory for supported files
    const files = await fs.readdir(directoryPath)
    const supportedExtensions = ['pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg', 'tiff']
    const supportedFiles = files.filter(file => {
      const ext = path.extname(file).toLowerCase().substring(1)
      return supportedExtensions.includes(ext)
    })

    return {
      success: true,
      directory: directoryPath,
      supportedFiles: supportedFiles.length,
      totalFiles: files.length
    }
  } catch (error) {
    console.error('Directory selection error:', error)
    return { success: false, error: error.message, directory: null }
  }
})

// File info retrieval
ipcMain.handle('get-file-info', async (event, filePath) => {
  try {
    const stats = await fs.stat(filePath)
    const ext = path.extname(filePath).toLowerCase().substring(1)
    
    return {
      success: true,
      info: {
        path: filePath,
        name: path.basename(filePath),
        size: stats.size,
        extension: ext,
        lastModified: stats.mtime,
        created: stats.birthtime,
        isFile: stats.isFile(),
        isDirectory: stats.isDirectory()
      }
    }
  } catch (error) {
    console.error('File info error:', error)
    return { success: false, error: error.message, info: null }
  }
})

// File reading for preview
ipcMain.handle('read-file-preview', async (event, filePath, maxSize = 1024) => {
  try {
    const stats = await fs.stat(filePath)
    
    if (stats.size > maxSize * 1024) {
      return {
        success: false,
        error: 'File too large for preview',
        preview: null
      }
    }

    const content = await fs.readFile(filePath, 'utf8')
    
    return {
      success: true,
      preview: content.substring(0, maxSize),
      fullSize: stats.size,
      truncated: content.length > maxSize
    }
  } catch (error) {
    console.error('File preview error:', error)
    return { success: false, error: error.message, preview: null }
  }
})

// Storage management handlers
ipcMain.handle('get-storage-path', async (event) => {
  try {
    const userHome = os.homedir()
    const covenantrixDir = path.join(userHome, '.covenantrix')
    const ragStorageDir = path.join(covenantrixDir, 'rag_storage')
    
    return {
      success: true,
      userDataDir: covenantrixDir,
      ragStorageDir: ragStorageDir
    }
  } catch (error) {
    console.error('Failed to get storage path:', error)
    return {
      success: false,
      error: error.message
    }
  }
})

ipcMain.handle('validate-storage-directory', async (event) => {
  try {
    const userHome = os.homedir()
    const covenantrixDir = path.join(userHome, '.covenantrix')
    const ragStorageDir = path.join(covenantrixDir, 'rag_storage')
    
    // Check if directories exist and are writable
    const covenantrixExists = await fs.access(covenantrixDir).then(() => true).catch(() => false)
    const ragStorageExists = await fs.access(ragStorageDir).then(() => true).catch(() => false)
    
    return {
      success: true,
      covenantrixDir: covenantrixDir,
      ragStorageDir: ragStorageDir,
      covenantrixExists: covenantrixExists,
      ragStorageExists: ragStorageExists,
      isWritable: covenantrixExists && ragStorageExists
    }
  } catch (error) {
    console.error('Failed to validate storage directory:', error)
    return {
      success: false,
      error: error.message
    }
  }
})

// Settings handlers
ipcMain.handle('get-settings', async (event) => {
  try {
    const Store = require('electron-store')
    const { machineId } = require('node-machine-id')
    
    // Get machine ID for encryption key
    const machineIdValue = machineId()
    const crypto = require('crypto')
    const encryptionKey = crypto.createHash('sha256')
      .update(machineIdValue + 'covenantrix-settings')
      .digest('hex')
    
    // Initialize secure store
    const secureStore = new Store({
      name: 'covenantrix-settings',
      encryptionKey: encryptionKey
    })
    
    const settings = secureStore.get('settings', {})
    const apiKeys = secureStore.get('apiKeys', {})
    const lastUpdated = secureStore.get('lastUpdated', null)
    
    // Ensure proper structure with defaults
    const defaultSettings = {
      api_keys: { mode: 'default' },
      rag: { search_mode: 'hybrid', top_k: 5, use_reranking: true, enable_ocr: true },
      language: { preferred: 'en', agent_language: 'auto', ui_language: 'auto' },
      ui: { theme: 'system', compact_mode: false, font_size: 'medium' },
      privacy: { enable_telemetry: false, enable_cloud_backup: false, retain_history: true },
      version: '1.0',
      last_updated: lastUpdated
    }
    
    const mergedSettings = {
      ...defaultSettings,
      ...settings,
      api_keys: { ...defaultSettings.api_keys, ...apiKeys },
      last_updated: lastUpdated
    }
    
    console.log('Returning settings:', mergedSettings)
    
    return {
      success: true,
      settings: mergedSettings
    }
  } catch (error) {
    console.error('Failed to get settings:', error)
    return {
      success: false,
      error: error.message,
      settings: null
    }
  }
})

ipcMain.handle('update-settings', async (event, settingsData) => {
  try {
    const Store = require('electron-store')
    const { machineId } = require('node-machine-id')
    
    // Get machine ID for encryption key
    const machineIdValue = machineId()
    const crypto = require('crypto')
    const encryptionKey = crypto.createHash('sha256')
      .update(machineIdValue + 'covenantrix-settings')
      .digest('hex')
    
    // Initialize secure store
    const secureStore = new Store({
      name: 'covenantrix-settings',
      encryptionKey: encryptionKey
    })
    
    // Extract API keys and settings
    const { api_keys, ...settings } = settingsData
    
    console.log('Updating settings:', { api_keys, settings })
    
    // Forward to backend API first to validate
    try {
      const backendUrl = 'http://127.0.0.1:8000/settings'
      const response = await axios.post(backendUrl, {
        settings: settingsData
      })
      
      // If backend validation succeeds, save to local store
      secureStore.set('settings', settings)
      secureStore.set('apiKeys', api_keys)
      secureStore.set('lastUpdated', new Date().toISOString())
      
      return {
        success: true,
        message: 'Settings updated successfully',
        settings: response.data.settings
      }
    } catch (backendError) {
      console.error('Backend validation failed:', backendError.message)
      
      // Extract validation error details if available
      let errorMessage = 'Failed to validate settings'
      let validationErrors = null
      
      if (backendError.response) {
        const status = backendError.response.status
        const data = backendError.response.data
        
        if (status === 422 && data.detail) {
          // Pydantic validation error
          if (Array.isArray(data.detail)) {
            validationErrors = data.detail.map(err => ({
              field: err.loc ? err.loc.join('.') : 'unknown',
              message: err.msg,
              type: err.type
            }))
            errorMessage = validationErrors.map(e => `${e.field}: ${e.message}`).join('; ')
          } else {
            errorMessage = data.detail
          }
        } else if (data.detail) {
          errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
        }
      }
      
      return {
        success: false,
        error: errorMessage,
        validationErrors: validationErrors
      }
    }
  } catch (error) {
    console.error('Failed to update settings:', error)
    return {
      success: false,
      error: error.message
    }
  }
})

ipcMain.handle('validate-api-keys', async (event, apiKeys) => {
  try {
    const backendUrl = 'http://127.0.0.1:8000/settings/api-keys/validate'
    const response = await axios.post(backendUrl, apiKeys)
    
    return {
      success: true,
      validation: response.data
    }
  } catch (error) {
    console.error('API key validation failed:', error)
    return {
      success: false,
      error: error.message,
      validation: null
    }
  }
})

ipcMain.handle('apply-settings', async (event, settingsData) => {
  try {
    const backendUrl = 'http://127.0.0.1:8000/settings/apply'
    const response = await axios.post(backendUrl, {
      settings: settingsData
    })
    
    return {
      success: true,
      result: response.data
    }
  } catch (error) {
    console.error('Failed to apply settings:', error)
    return {
      success: false,
      error: error.message,
      result: null
    }
  }
})

ipcMain.handle('get-default-settings', async (event) => {
  try {
    const backendUrl = 'http://127.0.0.1:8000/settings/defaults'
    const response = await axios.get(backendUrl)
    
    return {
      success: true,
      settings: response.data.settings
    }
  } catch (error) {
    console.error('Failed to get default settings:', error)
    return {
      success: false,
      error: error.message,
      settings: null
    }
  }
})

ipcMain.handle('get-key-status', async (event) => {
  try {
    const backendUrl = 'http://127.0.0.1:8000/settings/key-status'
    const response = await axios.get(backendUrl)
    
    return {
      success: true,
      ...response.data
    }
  } catch (error) {
    console.error('Failed to get key status:', error)
    return {
      success: false,
      error: error.message,
      has_valid_key: false,
      mode: null,
      message: 'Failed to check key status'
    }
  }
})

ipcMain.handle('services:status', async (event) => {
  try {
    const backendUrl = 'http://127.0.0.1:8000/services/status'
    const response = await axios.get(backendUrl)
    
    return {
      success: true,
      data: response.data
    }
  } catch (error) {
    console.error('Failed to get services status:', error)
    return {
      success: false,
      error: error.message,
      data: {
        openai_available: false,
        cohere_available: false,
        google_available: false,
        features: {
          chat: false,
          upload: false,
          reranking: false,
          ocr: false
        }
      }
    }
  }
})

ipcMain.handle('reset-settings', async (event) => {
  try {
    const backendUrl = 'http://127.0.0.1:8000/settings/reset'
    await axios.post(backendUrl)
    
    // Clear local storage
    const Store = require('electron-store')
    const { machineId } = require('node-machine-id')
    
    const machineIdValue = machineId()
    const crypto = require('crypto')
    const encryptionKey = crypto.createHash('sha256')
      .update(machineIdValue + 'covenantrix-settings')
      .digest('hex')
    
    const secureStore = new Store({
      name: 'covenantrix-settings',
      encryptionKey: encryptionKey
    })
    
    secureStore.clear()
    
    return {
      success: true,
      message: 'Settings reset to defaults'
    }
  } catch (error) {
    console.error('Failed to reset settings:', error)
    return {
      success: false,
      error: error.message
    }
  }
})

}

// Zoom level handlers
ipcMain.handle('set-zoom-level', async (event, zoomLevel) => {
  try {
    // Validate zoom level (0.5 to 2.0)
    const validZoomLevel = Math.max(0.5, Math.min(2.0, zoomLevel))
    
    // Apply zoom to main window
    const { BrowserWindow } = require('electron')
    const mainWindow = BrowserWindow.getFocusedWindow()
    if (mainWindow) {
      mainWindow.webContents.setZoomFactor(validZoomLevel)
      console.log(`Zoom level set to: ${(validZoomLevel * 100).toFixed(0)}%`)
    }
    
    return {
      success: true,
      zoomLevel: validZoomLevel
    }
  } catch (error) {
    console.error('Failed to set zoom level:', error)
    return {
      success: false,
      error: error.message
    }
  }
})

ipcMain.handle('get-zoom-level', async (event) => {
  try {
    const { BrowserWindow } = require('electron')
    const mainWindow = BrowserWindow.getFocusedWindow()
    
    if (mainWindow) {
      const zoomLevel = mainWindow.webContents.getZoomFactor()
      return {
        success: true,
        zoomLevel: zoomLevel
      }
    }
    
    return {
      success: false,
      error: 'No active window found'
    }
  } catch (error) {
    console.error('Failed to get zoom level:', error)
    return {
      success: false,
      error: error.message
    }
  }
})

// Google OAuth handlers
ipcMain.handle('google-oauth-start', async (event) => {
  try {
    // Get the main window from the event sender
    const mainWindow = require('electron').BrowserWindow.fromWebContents(event.sender);
    
    // Call backend to get OAuth URL (use 127.0.0.1 to force IPv4)
    const response = await axios.post('http://127.0.0.1:8000/api/google/accounts/connect');
    const { auth_url } = response.data;
    
    // Open OAuth window
    await openOAuthWindow(auth_url, mainWindow);
    
    return { success: true };
  } catch (error) {
    console.error('Error starting OAuth flow:', error);
    return { 
      success: false, 
      error: error.message || 'Failed to start OAuth flow' 
    };
  }
});

module.exports = {
  // Export handlers for registration in main.js
  registerHandlers: () => {
    // Handlers are already registered above
    console.log('File operation, settings, and OAuth IPC handlers registered')
  }
}
