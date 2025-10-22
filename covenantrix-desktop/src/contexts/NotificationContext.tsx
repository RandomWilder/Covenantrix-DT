import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { Notification, NotificationContextValue, DownloadProgress } from '../types/notification';
import { notificationService } from '../services/api/notificationService';
import { isElectron, envLog, envWarn } from '../utils/environment';

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  // ✅ ARCHITECTURAL FIX: Separate persistent and transient state
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [downloadStates, setDownloadStates] = useState<Map<string, DownloadProgress>>(new Map());
  
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedNotifications, setExpandedNotifications] = useState<Set<string>>(new Set());

  // ✅ Combine notifications with download states for rendering
  const notificationsWithProgress = useMemo(() => {
    return notifications.map(n => {
      const downloadProgress = downloadStates.get(n.id);
      return downloadProgress ? { ...n, downloadProgress } : n;
    });
  }, [notifications, downloadStates]);

  // ✅ SIMPLIFIED: No more preservation logic needed
  const fetchNotifications = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await notificationService.getAll();
      
      // Just set notifications - download states are separate
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
      
      // Clean up download state if exists
      setDownloadStates(prev => {
        const next = new Map(prev);
        next.delete(id);
        return next;
      });
      
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
          console.log('[NotificationContext] Download update triggered', { notificationId });
          
          try {
            // ✅ CRITICAL FIX: Set download state BEFORE triggering download
            setDownloadStates(prev => {
              const next = new Map(prev);
              next.set(notificationId, {
                percent: 0,
                transferred: 0,
                total: 0,
                isDownloading: true
              });
              console.log('[NotificationContext] Download state set for notification:', notificationId);
              return next;
            });
            
            // Keep notification expanded to show progress
            setExpandedNotifications(prev => {
              const newSet = new Set(prev);
              newSet.add(notificationId);
              return newSet;
            });
            
            // Now trigger the download
            const result = await window.electronAPI.update.download();
            console.log('[NotificationContext] Download initiated', result);
            
            if (!result.success) {
              console.error('[NotificationContext] Download failed:', result.error);
              // Clear download state on failure
              setDownloadStates(prev => {
                const next = new Map(prev);
                next.delete(notificationId);
                return next;
              });
              return;
            }
          } catch (error) {
            console.error('[NotificationContext] Download exception:', error);
            // Clear download state on error
            setDownloadStates(prev => {
              const next = new Map(prev);
              next.delete(notificationId);
              return next;
            });
          }
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

  // ✅ SIMPLIFIED: Auto-refresh just works
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
      
      // ✅ Clear download states when update is ready
      setDownloadStates(prev => {
        const next = new Map(prev);
        // Clear all download states for version_update notifications
        notifications.forEach(n => {
          if (n.type === 'version_update') {
            next.delete(n.id);
          }
        });
        return next;
      });
      
      fetchNotifications();
    });

    // ✅ FIXED: Handle all update status events including completion
    const cleanupUpdateStatus = window.electronAPI.onUpdateStatus((updateData) => {
      const { status, data } = updateData;
      
      // Handle download progress updates
      if (status === 'downloading' && data) {
        console.log('[NotificationContext] Processing download progress:', {
          percent: data.percent,
          transferred: data.transferred,
          total: data.total
        });
        
        // Find the downloading notification by checking if it exists in downloadStates
        const downloadingNotification = notifications.find(
          n => n.type === 'version_update' && downloadStates.has(n.id)
        );
        
        if (downloadingNotification) {
          console.log('[NotificationContext] Updating progress for notification:', downloadingNotification.id);
          // Update download state
          setDownloadStates(prev => {
            const next = new Map(prev);
            next.set(downloadingNotification.id, {
              percent: data.percent || 0,
              transferred: data.transferred || 0,
              total: data.total || 0,
              isDownloading: true
            });
            return next;
          });
        } else {
          console.warn('[NotificationContext] No downloading notification found in downloadStates');
        }
      }
      
      // ✅ Handle download completion
      if (status === 'Update downloaded') {
        console.log('[NotificationContext] Download completed, clearing download states');
        
        // Clear all download states
        setDownloadStates(new Map());
        
        // Refresh notifications to get the "Update Ready" notification
        fetchNotifications();
      }
      
      // ✅ Handle update ready notification created
      if (status === 'update-ready-notification-created') {
        console.log('[NotificationContext] Update ready notification created, clearing download states');
        
        // Clear all download states
        setDownloadStates(new Map());
        
        // Refresh notifications
        fetchNotifications();
      }
    });

    // Cleanup on unmount
    return () => {
      cleanupUpdateNotificationCreated();
      cleanupUpdateReadyNotificationCreated();
      cleanupUpdateStatus();
    };
  }, [fetchNotifications, notifications, downloadStates]);

  const value: NotificationContextValue = {
    notifications: notificationsWithProgress, // ✅ Expose combined data
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