const { app, BrowserWindow, Menu, shell, ipcMain, dialog } = require('electron')
const path = require('path')
const fs = require('fs')
const os = require('os')
const isDev = process.env.NODE_ENV === 'development'

// Import secure storage
const Store = require('electron-store')
const { machineId } = require('node-machine-id')

// Import managers
const { updateManager, checkForUpdates, manualUpdateCheck } = require('./updater')
const { backendManager, startBackend, stopBackend, getBackendStatus } = require('./backend-manager')

// Import IPC handlers
const { registerHandlers: registerFileHandlers } = require('./ipc-handlers')

let mainWindow
let secureStore

function initializeUserDataDirectory() {
  /**
   * Initialize user data directory for Covenantrix
   * Creates ~/.covenantrix/ directory structure
   */
  try {
    const userHome = os.homedir()
    const covenantrixDir = path.join(userHome, '.covenantrix')
    const ragStorageDir = path.join(covenantrixDir, 'rag_storage')
    
    // Create directories if they don't exist
    if (!fs.existsSync(covenantrixDir)) {
      fs.mkdirSync(covenantrixDir, { recursive: true })
      console.log(`Created user data directory: ${covenantrixDir}`)
    }
    
    if (!fs.existsSync(ragStorageDir)) {
      fs.mkdirSync(ragStorageDir, { recursive: true })
      console.log(`Created RAG storage directory: ${ragStorageDir}`)
    }
    
    console.log(`User data directory initialized: ${covenantrixDir}`)
    return covenantrixDir
  } catch (error) {
    console.error('Failed to initialize user data directory:', error)
    throw error
  }
}

function initializeSecureStorage() {
  /**
   * Initialize secure storage with machine-derived encryption
   * Uses electron-store with machine-specific encryption key
   */
  try {
    // Get machine ID for encryption key
    const machineIdValue = machineId()
    
    // Create encryption key from machine ID
    const crypto = require('crypto')
    const encryptionKey = crypto.createHash('sha256')
      .update(machineIdValue + 'covenantrix-settings')
      .digest('hex')
    
    // Initialize secure store
    secureStore = new Store({
      name: 'covenantrix-settings',
      encryptionKey: encryptionKey
    })
    
    console.log('Secure storage initialized with machine-derived encryption')
    return secureStore
  } catch (error) {
    console.error('Failed to initialize secure storage:', error)
    // Fallback to unencrypted store
    secureStore = new Store({
      name: 'covenantrix-settings'
    })
    console.warn('Using fallback unencrypted storage')
    return secureStore
  }
}

async function createWindow() {
  // Get screen dimensions for responsive sizing
  const { screen } = require('electron')
  const primaryDisplay = screen.getPrimaryDisplay()
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize
  
  // Calculate optimal window size (80% of screen or minimum 1000x700)
  const optimalWidth = Math.max(1000, Math.min(1400, Math.floor(screenWidth * 0.8)))
  const optimalHeight = Math.max(700, Math.min(900, Math.floor(screenHeight * 0.8)))
  
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: optimalWidth,
    height: optimalHeight,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    titleBarStyle: 'hiddenInset',
    show: false,
    icon: path.join(__dirname, '../public/icons/icon.png')
  })

  // Set main window for updater
  updateManager.setMainWindow(mainWindow)

  // Start backend before loading the app
  try {
    console.log('Starting backend server...')
    const backendInfo = await startBackend()
    console.log('Backend started successfully:', backendInfo)
    
    // Store backend URL for the renderer
    global.backendUrl = backendInfo.url
  } catch (error) {
    console.error('Failed to start backend:', error)
    
    // Show error dialog
    const choice = await dialog.showMessageBox(mainWindow, {
      type: 'error',
      title: 'Backend Startup Failed',
      message: 'Failed to start the Covenantrix backend server',
      detail: `Error: ${error.message}\n\nThe application cannot function without the backend. Would you like to retry?`,
      buttons: ['Retry', 'Exit'],
      defaultId: 0,
      cancelId: 1
    })
    
    if (choice.response === 0) {
      // Retry
      return createWindow()
    } else {
      // Exit
      app.quit()
      return
    }
  }

  // Load the app
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist-electron/index.html'))
  }

  // Show window when ready
  mainWindow.once('ready-to-show', async () => {
    try {
      // Get saved zoom level from settings, default to 0.8 (80%)
      let zoomLevel = 0.8
      if (secureStore) {
        const settings = secureStore.get('settings', {})
        if (settings.ui && typeof settings.ui.zoom_level === 'number') {
          zoomLevel = Math.max(0.5, Math.min(2.0, settings.ui.zoom_level))
        }
      }
      
      // Apply zoom level
      mainWindow.webContents.setZoomFactor(zoomLevel)
      console.log(`Applied zoom level: ${(zoomLevel * 100).toFixed(0)}%`)
    } catch (error) {
      console.error('Failed to apply zoom level:', error)
      // Fallback to default 80% zoom
      mainWindow.webContents.setZoomFactor(0.8)
    }
    
    mainWindow.show()
    
    // Check for updates after window is shown (silent check)
    setTimeout(() => {
      checkForUpdates(true)
    }, 5000)
  })

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })
}

// Register IPC handlers for updater
function registerUpdaterHandlers() {
  // Manual update check
  ipcMain.handle('check-for-updates', async () => {
    await manualUpdateCheck()
  })
  
  // Get backend status
  ipcMain.handle('get-backend-status', async () => {
    return getBackendStatus()
  })
  
  // Get backend URL
  ipcMain.handle('get-backend-url', async () => {
    return global.backendUrl || null
  })
}

// App event handlers
app.whenReady().then(async () => {
  // Initialize user data directory first
  try {
    initializeUserDataDirectory()
  } catch (error) {
    console.error('Failed to initialize user data directory:', error)
    // Continue with app startup even if directory creation fails
  }
  
  // Initialize secure storage
  try {
    initializeSecureStorage()
  } catch (error) {
    console.error('Failed to initialize secure storage:', error)
    // Continue with app startup even if storage initialization fails
  }
  
  // Register IPC handlers
  registerFileHandlers()
  registerUpdaterHandlers()
  
  // Create window (this will start backend too)
  await createWindow()

  // macOS specific: re-create window when dock icon is clicked
  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  // macOS specific: keep app running even when all windows are closed
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// Clean shutdown
app.on('before-quit', async (event) => {
  if (backendManager.getStatus().running) {
    event.preventDefault()
    
    console.log('Shutting down backend...')
    await stopBackend()
    
    console.log('Backend stopped, quitting app')
    app.exit(0)
  }
})

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault()
    shell.openExternal(navigationUrl)
  })
})

// Create application menu
const template = [
  {
    label: 'File',
    submenu: [
      {
        label: 'New Document',
        accelerator: 'CmdOrCtrl+N',
        click: () => {
          // Handle new document
        }
      },
      {
        label: 'Open Document',
        accelerator: 'CmdOrCtrl+O',
        click: () => {
          // Handle open document
        }
      },
      { type: 'separator' },
      {
        label: 'Exit',
        accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
        click: () => {
          app.quit()
        }
      }
    ]
  },
  {
    label: 'Edit',
    submenu: [
      { role: 'undo' },
      { role: 'redo' },
      { type: 'separator' },
      { role: 'cut' },
      { role: 'copy' },
      { role: 'paste' }
    ]
  },
  {
    label: 'View',
    submenu: [
      { role: 'reload' },
      { role: 'forceReload' },
      { role: 'toggleDevTools' },
      { type: 'separator' },
      { role: 'resetZoom' },
      { role: 'zoomIn' },
      { role: 'zoomOut' },
      { type: 'separator' },
      { role: 'togglefullscreen' }
    ]
  },
  {
    label: 'Help',
    submenu: [
      {
        label: 'Check for Updates',
        click: () => {
          manualUpdateCheck()
        }
      },
      { type: 'separator' },
      {
        label: 'About Covenantrix',
        click: () => {
          dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'About Covenantrix',
            message: 'Covenantrix',
            detail: `Version: ${app.getVersion()}\n\nRAG-powered Document Intelligence Platform`
          })
        }
      }
    ]
  },
  {
    label: 'Window',
    submenu: [
      { role: 'minimize' },
      { role: 'close' }
    ]
  }
]

const menu = Menu.buildFromTemplate(template)
Menu.setApplicationMenu(menu)