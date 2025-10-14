import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Notification, NotificationContextValue } from '../types/notification';
import { notificationService } from '../services/api/notificationService';
import { isElectron, envLog, envWarn } from '../utils/environment';

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedNotifications, setExpandedNotifications] = useState<Set<string>>(new Set());

  const fetchNotifications = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await notificationService.getAll();
      setNotifications(data);
      
      // Calculate unread count
      const count = data.filter(n => !n.read && !n.dismissed).length;
      setUnreadCount(count);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const markAsRead = useCallback(async (id: string) => {
    try {
      await notificationService.markAsRead(id);
      
      // Update local state
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }, []);

  const dismissNotification = useCallback(async (id: string) => {
    try {
      await notificationService.dismiss(id);
      
      // Remove from local state
      setNotifications(prev => prev.filter(n => n.id !== id));
      
      // Update unread count if notification was unread
      const notification = notifications.find(n => n.id === id);
      if (notification && !notification.read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Failed to dismiss notification:', error);
    }
  }, [notifications]);

  const toggleExpanded = useCallback((id: string) => {
    setExpandedNotifications(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
        // Auto-mark as read when expanding
        const notification = notifications.find(n => n.id === id);
        if (notification && !notification.read) {
          markAsRead(id);
        }
      }
      return newSet;
    });
  }, [notifications, markAsRead]);

  const handleAction = useCallback(async (notificationId: string, action: string) => {
    if (!isElectron()) {
      envWarn('handleAction: Not in Electron environment, action ignored', { notificationId, action });
      return;
    }

    try {
      switch (action) {
        case 'download_update':
          // Trigger update download via IPC
          await window.electronAPI.update.download();
          
          // Keep notification open and mark as downloading
          setNotifications(prev => 
            prev.map(n => n.id === notificationId ? {
              ...n,
              downloadProgress: {
                percent: 0,
                transferred: 0,
                total: 0,
                isDownloading: true
              }
            } : n)
          );
          
          // Keep notification expanded to show progress
          setExpandedNotifications(prev => {
            const newSet = new Set(prev);
            newSet.add(notificationId);
            return newSet;
          });
          break;

        case 'install_update':
          // Trigger update install via IPC (app will restart)
          await window.electronAPI.update.install();
          // Dismiss notification (app will quit immediately)
          await dismissNotification(notificationId);
          break;

        case 'dismiss':
          // Mark notification as read and collapse it
          await markAsRead(notificationId);
          // Collapse the notification
          setExpandedNotifications(prev => {
            const newSet = new Set(prev);
            newSet.delete(notificationId);
            return newSet;
          });
          break;

        default:
          console.warn('Unknown action:', action);
      }
    } catch (error) {
      console.error('Failed to handle action:', { notificationId, action, error });
    }
  }, [dismissNotification, markAsRead]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    if (!isElectron()) {
      envLog('NotificationContext: Skipping auto-refresh in browser mode');
      return;
    }
    
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Listen for update notification events from Electron
  useEffect(() => {
    if (!isElectron()) {
      envLog('NotificationContext: Skipping Electron event listeners in browser mode');
      return;
    }

    // Register listeners for update notification creation
    const cleanupUpdateNotificationCreated = window.electronAPI.onUpdateNotificationCreated(() => {
      envLog('Update notification created, refreshing notifications...');
      fetchNotifications();
    });

    const cleanupUpdateReadyNotificationCreated = window.electronAPI.onUpdateReadyNotificationCreated(() => {
      envLog('Update ready notification created, refreshing notifications...');
      fetchNotifications();
    });

    // Listen for update download progress
    const cleanupUpdateStatus = window.electronAPI.onUpdateStatus((updateData) => {
      const { status, data } = updateData;
      
      if (status === 'downloading' && data) {
        // Update the version_update notification with download progress
        setNotifications(prev => 
          prev.map(n => {
            // Find the update notification (version_update type)
            if (n.type === 'version_update' && n.downloadProgress?.isDownloading) {
              return {
                ...n,
                downloadProgress: {
                  percent: data.percent || 0,
                  transferred: data.transferred || 0,
                  total: data.total || 0,
                  isDownloading: true
                }
              };
            }
            return n;
          })
        );
      }
    });

    // Cleanup on unmount
    return () => {
      cleanupUpdateNotificationCreated();
      cleanupUpdateReadyNotificationCreated();
      cleanupUpdateStatus();
    };
  }, [fetchNotifications]);

  const value: NotificationContextValue = {
    notifications,
    unreadCount,
    isLoading,
    expandedNotifications,
    fetchNotifications,
    markAsRead,
    dismissNotification,
    toggleExpanded,
    handleAction,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

