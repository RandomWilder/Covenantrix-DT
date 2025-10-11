const { autoUpdater } = require('electron-updater');
const { app, dialog, BrowserWindow } = require('electron');
const log = require('electron-log');

// Configure logging
log.transports.file.level = 'info';
autoUpdater.logger = log;

// Disable auto-download - require user approval
autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;

let updateCheckInProgress = false;
let downloadInProgress = false;

class UpdateManager {
  constructor() {
    this.mainWindow = null;
    this.updateInfo = null;
    this.setupEventListeners();
  }

  setMainWindow(window) {
    this.mainWindow = window;
  }

  setupEventListeners() {
    // Checking for update
    autoUpdater.on('checking-for-update', () => {
      log.info('Checking for updates...');
      updateCheckInProgress = true;
      this.sendStatusToWindow('Checking for updates...');
    });

    // Update available
    autoUpdater.on('update-available', (info) => {
      log.info('Update available:', info);
      updateCheckInProgress = false;
      this.updateInfo = info;
      
      this.sendStatusToWindow('Update available', info);
      this.promptUserToDownload(info);
    });

    // Update not available
    autoUpdater.on('update-not-available', (info) => {
      log.info('Update not available:', info);
      updateCheckInProgress = false;
      this.sendStatusToWindow('App is up to date');
    });

    // Download progress
    autoUpdater.on('download-progress', (progressObj) => {
      const message = `Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent.toFixed(2)}% (${progressObj.transferred}/${progressObj.total})`;
      log.info(message);
      
      this.sendStatusToWindow('downloading', {
        percent: progressObj.percent,
        transferred: progressObj.transferred,
        total: progressObj.total
      });
    });

    // Update downloaded
    autoUpdater.on('update-downloaded', (info) => {
      log.info('Update downloaded:', info);
      downloadInProgress = false;
      
      this.sendStatusToWindow('Update downloaded', info);
      this.promptUserToInstall(info);
    });

    // Error occurred
    autoUpdater.on('error', (err) => {
      log.error('Update error:', err);
      updateCheckInProgress = false;
      downloadInProgress = false;
      
      this.sendStatusToWindow('Error checking for updates', { error: err.message });
      
      // Show error dialog only if it's not a network timeout
      if (!err.message.includes('net::') && !err.message.includes('ETIMEDOUT')) {
        dialog.showErrorBox('Update Error', `Error in auto-updater: ${err.message}`);
      }
    });
  }

  sendStatusToWindow(status, data = null) {
    if (this.mainWindow && this.mainWindow.webContents) {
      this.mainWindow.webContents.send('update-status', { status, data });
    }
  }

  async checkForUpdates(silent = false) {
    if (updateCheckInProgress || downloadInProgress) {
      log.info('Update check already in progress, skipping...');
      return;
    }

    try {
      // Only check for updates in production
      if (process.env.NODE_ENV === 'development') {
        log.info('Skipping update check in development mode');
        return;
      }

      log.info('Starting update check...');
      log.info('Repository: https://github.com/RandomWilder/Covenantrix-DT');
      await autoUpdater.checkForUpdates();
    } catch (error) {
      log.error('Error checking for updates:', error);
      if (!silent) {
        dialog.showErrorBox('Update Check Failed', `Failed to check for updates: ${error.message}`);
      }
    }
  }

  promptUserToDownload(info) {
    const dialogOpts = {
      type: 'info',
      buttons: ['Download Now', 'Later'],
      title: 'Update Available',
      message: `Covenantrix ${info.version} is available`,
      detail: `Current version: ${app.getVersion()}\nNew version: ${info.version}\n\nRelease notes:\n${info.releaseNotes || 'No release notes available'}\n\nWould you like to download it now?`
    };

    dialog.showMessageBox(this.mainWindow, dialogOpts).then((returnValue) => {
      if (returnValue.response === 0) {
        // User clicked "Download Now"
        downloadInProgress = true;
        this.sendStatusToWindow('downloading-started');
        autoUpdater.downloadUpdate();
      }
    });
  }

  promptUserToInstall(info) {
    const dialogOpts = {
      type: 'info',
      buttons: ['Restart Now', 'Later'],
      title: 'Update Ready',
      message: 'Update downloaded',
      detail: `Covenantrix ${info.version} has been downloaded and is ready to install.\n\nThe application will restart to complete the update.\n\nRestart now?`
    };

    dialog.showMessageBox(this.mainWindow, dialogOpts).then((returnValue) => {
      if (returnValue.response === 0) {
        // User clicked "Restart Now"
        setImmediate(() => {
          // Disable beforeunload handler
          app.removeAllListeners('window-all-closed');
          autoUpdater.quitAndInstall(false, true);
        });
      }
    });
  }

  // Manual update check triggered by user
  async manualUpdateCheck() {
    if (updateCheckInProgress || downloadInProgress) {
      dialog.showMessageBox(this.mainWindow, {
        type: 'info',
        title: 'Update in Progress',
        message: 'An update check or download is already in progress.',
        buttons: ['OK']
      });
      return;
    }

    try {
      await this.checkForUpdates(false);
      
      // If no update is available after checking, show a message
      setTimeout(() => {
        if (!updateCheckInProgress && !this.updateInfo) {
          dialog.showMessageBox(this.mainWindow, {
            type: 'info',
            title: 'No Updates',
            message: 'You are using the latest version of Covenantrix.',
            buttons: ['OK']
          });
        }
      }, 3000);
    } catch (error) {
      log.error('Manual update check failed:', error);
    }
  }
}

// Export singleton instance
const updateManager = new UpdateManager();

module.exports = {
  updateManager,
  checkForUpdates: (silent) => updateManager.checkForUpdates(silent),
  manualUpdateCheck: () => updateManager.manualUpdateCheck(),
  setMainWindow: (window) => updateManager.setMainWindow(window)
};