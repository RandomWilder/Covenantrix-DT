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
    autoUpdater.on('update-available', async (info) => {
      log.info('Update available:', info);
      updateCheckInProgress = false;
      this.updateInfo = info;
      
      this.sendStatusToWindow('Update available', info);
      
      // Create notification via backend API
      try {
        await this.createUpdateNotification(info, 'update_available');
        this.sendStatusToWindow('update-notification-created');
      } catch (error) {
        log.error('Failed to create notification, falling back to dialog:', error);
        // Fallback to original dialog method
        this.promptUserToDownload(info);
      }
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
    autoUpdater.on('update-downloaded', async (info) => {
      log.info('Update downloaded:', info);
      downloadInProgress = false;
      
      this.sendStatusToWindow('Update downloaded', info);
      
      // Create notification via backend API
      try {
        await this.createUpdateNotification(info, 'update_ready');
        this.sendStatusToWindow('update-ready-notification-created');
      } catch (error) {
        log.error('Failed to create notification, falling back to dialog:', error);
        // Fallback to original dialog method
        this.promptUserToInstall(info);
      }
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

  /**
   * Format bytes to MB string
   * @param {number} bytes - Bytes to format
   * @returns {string} Formatted string (e.g., "145.8 MB")
   */
  formatBytes(bytes) {
    if (bytes == null || bytes === undefined) {
      return 'Unknown';
    }
    const mb = bytes / 1024 / 1024;
    return `${mb.toFixed(2)} MB`;
  }

  /**
   * Format release notes with version comparison and download size
   * @param {object} info - Update info from autoUpdater
   * @returns {string} Formatted markdown string
   */
  formatReleaseNotes(info) {
    // Extract release notes (may be string or HTML)
    let notes = info.releaseNotes || 'No release notes available';
    
    // Strip HTML tags if present
    if (typeof notes === 'string') {
      notes = notes.replace(/<[^>]*>/g, '');
    }

    // Get download size from first file
    const downloadSize = info.files && info.files[0] 
      ? this.formatBytes(info.files[0].size) 
      : 'Unknown';

    // Format structure
    const formatted = `**Current Version:** ${app.getVersion()}\n**New Version:** ${info.version}\n\n**Release Notes:**\n${notes}\n\n**Download Size:** ${downloadSize}`;
    
    return formatted;
  }

  /**
   * Create update notification via backend API
   * @param {object} info - Update info from autoUpdater
   * @param {string} notificationType - 'update_available' or 'update_ready'
   */
  async createUpdateNotification(info, notificationType) {
    const backendUrl = global.backendUrl || 'http://localhost:8000';
    const currentVersion = app.getVersion();

    let notificationData;

    if (notificationType === 'update_available') {
      // Update Available Notification
      notificationData = {
        type: 'version_update',
        source: 'local',
        title: `Version ${info.version} Available`,
        summary: `Update to Covenantrix ${info.version}`,
        content: this.formatReleaseNotes(info),
        actions: [
          { label: 'Download Now', action: 'download_update' },
          { label: 'Later', action: 'dismiss' }
        ],
        metadata: {
          version: info.version,
          current_version: currentVersion,
          release_date: info.releaseDate || new Date().toISOString().split('T')[0],
          download_size: info.files && info.files[0] ? info.files[0].size : null,
          dedup_key: `version_update_${info.version}`
        }
      };
    } else if (notificationType === 'update_ready') {
      // Update Ready Notification
      notificationData = {
        type: 'version_ready',
        source: 'local',
        title: 'Update Ready to Install',
        summary: `Version ${info.version} is ready`,
        content: `Covenantrix ${info.version} has been downloaded and is ready to install.\n\nThe application will restart to complete the update.\n\nClick 'Restart Now' when ready.`,
        actions: [
          { label: 'Restart Now', action: 'install_update' },
          { label: 'Later', action: 'dismiss' }
        ],
        metadata: {
          version: info.version,
          current_version: currentVersion,
          dedup_key: `version_ready_${info.version}`
        }
      };
    } else {
      throw new Error(`Unknown notification type: ${notificationType}`);
    }

    // Call backend API
    try {
      const response = await fetch(`${backendUrl}/api/notifications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(notificationData)
      });

      if (!response.ok) {
        throw new Error(`Failed to create notification: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      log.info(`Notification created successfully: ${notificationType}`, result);
      return result;
    } catch (error) {
      log.error(`Failed to create notification: ${notificationType}`, error);
      throw error;
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

  /**
   * Fallback method: Dialog prompt for download (used if notification creation fails)
   * @param {object} info - Update info
   */
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

  /**
   * Fallback method: Dialog prompt for install (used if notification creation fails)
   * @param {object} info - Update info
   */
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