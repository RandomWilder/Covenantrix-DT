/**
 * OAuth Handler for Electron
 * Manages OAuth authentication windows and callbacks
 */

const { BrowserWindow } = require('electron');

/**
 * Open OAuth window for Google authentication
 * @param {string} authUrl - The OAuth authorization URL
 * @param {BrowserWindow} mainWindow - The main application window
 * @returns {Promise<{code: string, state: string}>}
 */
function openOAuthWindow(authUrl, mainWindow) {
  return new Promise((resolve, reject) => {
    // Validate inputs
    if (!authUrl) {
      reject(new Error('OAuth URL is required'));
      return;
    }
    
    if (!mainWindow || mainWindow.isDestroyed()) {
      console.warn('Main window not available, creating standalone OAuth window');
    }
    
    // Create OAuth window configuration
    const windowConfig = {
      width: 500,
      height: 600,
      show: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        sandbox: true
      },
      title: 'Google Authentication',
      autoHideMenuBar: true
    };
    
    // Add parent if mainWindow is valid
    if (mainWindow && !mainWindow.isDestroyed()) {
      windowConfig.modal = true;
      windowConfig.parent = mainWindow;
    }
    
    // Create OAuth window
    const authWindow = new BrowserWindow(windowConfig);

    // Load the OAuth URL
    authWindow.loadURL(authUrl).catch(err => {
      console.error('Failed to load OAuth URL:', err);
      if (!authWindow.isDestroyed()) {
        authWindow.close();
      }
      reject(new Error(`Failed to load OAuth page: ${err.message}`));
    });

    // Show window when ready
    authWindow.once('ready-to-show', () => {
      console.log('OAuth window ready, showing...');
      authWindow.show();
    });

    // Track if callback was handled
    let callbackHandled = false;

    // Intercept callback redirect
    authWindow.webContents.on('will-redirect', (event, url) => {
      handleCallback(url);
    });

    // Also handle navigation (some OAuth providers use this)
    authWindow.webContents.on('did-navigate', (event, url) => {
      handleCallback(url);
    });

    function handleCallback(url) {
      if (callbackHandled) return;

      // Check if this is the callback URL
      if (url.startsWith('http://localhost:8000/oauth/callback') || 
          url.startsWith('http://localhost:8000/api/google/accounts/callback')) {
        callbackHandled = true;

        try {
          const urlObj = new URL(url);
          const code = urlObj.searchParams.get('code');
          const state = urlObj.searchParams.get('state');
          const error = urlObj.searchParams.get('error');

          if (error) {
            reject(new Error(`OAuth error: ${error}`));
          } else if (code && state) {
            // Send to renderer via IPC
            mainWindow.webContents.send('oauth-callback', { code, state });
            resolve({ code, state });
          } else {
            reject(new Error('Missing code or state parameter'));
          }
        } catch (err) {
          reject(err);
        } finally {
          // Close the OAuth window
          if (authWindow && !authWindow.isDestroyed()) {
            authWindow.close();
          }
        }
      }
    }

    // Handle window closed by user
    authWindow.on('closed', () => {
      if (!callbackHandled) {
        reject(new Error('OAuth window was closed by user'));
      }
    });

    // Handle errors
    authWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
      if (!callbackHandled) {
        console.error('OAuth window failed to load:', errorCode, errorDescription);
        reject(new Error(`Failed to load OAuth page: ${errorDescription}`));
        if (authWindow && !authWindow.isDestroyed()) {
          authWindow.close();
        }
      }
    });
    
    // Add timeout protection (5 minutes)
    const timeout = setTimeout(() => {
      if (!callbackHandled && authWindow && !authWindow.isDestroyed()) {
        console.error('OAuth flow timeout - no callback received');
        authWindow.close();
        reject(new Error('OAuth flow timed out'));
      }
    }, 300000);
    
    // Clear timeout when promise settles
    authWindow.once('closed', () => {
      clearTimeout(timeout);
    });
  });
}

module.exports = {
  openOAuthWindow
};

