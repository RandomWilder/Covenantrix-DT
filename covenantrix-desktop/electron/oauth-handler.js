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
    // Create OAuth window
    const authWindow = new BrowserWindow({
      width: 500,
      height: 600,
      show: false,
      modal: true,
      parent: mainWindow,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        sandbox: true
      },
      title: 'Google Authentication',
      autoHideMenuBar: true
    });

    // Load the OAuth URL
    authWindow.loadURL(authUrl);

    // Show window when ready
    authWindow.once('ready-to-show', () => {
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
        reject(new Error(`Failed to load OAuth page: ${errorDescription}`));
        if (authWindow && !authWindow.isDestroyed()) {
          authWindow.close();
        }
      }
    });
  });
}

module.exports = {
  openOAuthWindow
};

