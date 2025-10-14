import { Notification } from '../../types/notification';
import { isElectron, envWarn } from '../../utils/environment';

export const notificationService = {
  async getAll(): Promise<Notification[]> {
    if (!isElectron()) {
      envWarn('notificationService.getAll: Not in Electron environment, returning empty array');
      return [];
    }
    const result = await window.electronAPI.notifications.getAll();
    return result.notifications || [];
  },

  async getUnreadCount(): Promise<number> {
    if (!isElectron()) {
      envWarn('notificationService.getUnreadCount: Not in Electron environment, returning 0');
      return 0;
    }
    const result = await window.electronAPI.notifications.getUnreadCount();
    return result.count || 0;
  },

  async markAsRead(id: string): Promise<void> {
    if (!isElectron()) {
      envWarn('notificationService.markAsRead: Not in Electron environment, skipping');
      return;
    }
    await window.electronAPI.notifications.markAsRead(id);
  },

  async dismiss(id: string): Promise<void> {
    if (!isElectron()) {
      envWarn('notificationService.dismiss: Not in Electron environment, skipping');
      return;
    }
    await window.electronAPI.notifications.dismiss(id);
  },

  async cleanup(): Promise<void> {
    if (!isElectron()) {
      envWarn('notificationService.cleanup: Not in Electron environment, skipping');
      return;
    }
    await window.electronAPI.notifications.cleanup();
  },
};

