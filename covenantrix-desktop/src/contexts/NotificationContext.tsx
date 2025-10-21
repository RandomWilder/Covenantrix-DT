import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { Notification, NotificationContextValue } from '../types/notification';
import { notificationService } from '../services/api/notificationService';
import { isElectron, envLog, envWarn } from '../utils/environment';

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedNotifications, setExpandedNotifications] = useState<Set<string>>(new Set());

  // ✅ NEW: Ref to hold current notifications for interval checks
  const notificationsRef = useRef<Notification[]>([]);
  
  // Update ref whenever notifications change
  useEffect(() => {
    notificationsRef.current = notifications;
  }, [notifications]);

  // ✅ FIXED: Capture download states directly from ref
  const fetchNotifications = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // ✅ Capture download states DIRECTLY from ref (always current)
      const activeDownloads = new Map();
      notificationsRef.current.forEach(n => {
        if (n.downloadProgress?.isDownloading) {
          activeDownloads.set(n.id, n.downloadProgress);
          console.log('[fetchNotifications] Preserving download state for:', n.id, n.downloadProgress);
        }
      });
      
      const data = await notificationService.getAll();
      
      // Restore download states to fetched data
      const restoredData = data.map(backendNotification => {
        const activeDownload = activeDownloads.get(backendNotification.id);
        if (activeDownload) {
          console.log('[fetchNotifications] Restoring download state to:', backendNotification.id);
          return { ...backendNotification, downloadProgress: activeDownload };
        }
        return backendNotification;
      });
      
      setNotifications(restoredData);
      
      // Calculate unread count
      const count = data.filter(n => !n.read && !n.dismissed).length;
      setUnreadCount(count);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setIsLoading(false);
    }
  }, []); // ✅ Empty dependency array - correct

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
          console.log('[NotificationContext] Download update triggered', { notificationId });
          
          try {
            // Trigger update download via IPC
            const result = await window.electronAPI.update.download();
            console.log('[NotificationContext] Download initiated', result);
            
            if (!result.success) {
              console.error('[NotificationContext] Download failed:', result.error);
              // TODO: Show error to user
              return;
            }
            
            // Keep notification open and mark as downloading
            console.log('[NotificationContext] Setting notification as downloading:', notificationId);
            setNotifications(prev => 
              prev.map(n => {
                if (n.id === notificationId) {
                  console.log('[NotificationContext] Updating notification to downloading state:', {
                    notificationId: n.id,
                    type: n.type,
                    wasDownloading: n.downloadProgress?.isDownloading
                  });
                  return {
                    ...n,
                    downloadProgress: {
                      percent: 0,
                      transferred: 0,
                      total: 0,
                      isDownloading: true
                    }
                  };
                }
                return n;
              })
            );
            
            // Keep notification expanded to show progress
            setExpandedNotifications(prev => {
              const newSet = new Set(prev);
              newSet.add(notificationId);
              return newSet;
            });
          } catch (error) {
            console.error('[NotificationContext] Download exception:', error);
            // TODO: Show error to user
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

  // ✅ FIXED: Auto-refresh with ref-based download check
  useEffect(() => {
    if (!isElectron()) {
      envLog('NotificationContext: Skipping auto-refresh in browser mode');
      return;
    }
    
    fetchNotifications();
    
    const interval = setInterval(() => {
      // Check from ref - always current, no stale closure
      const hasActiveDownload = notificationsRef.current.some(
        n => n.downloadProgress?.isDownloading
      );
      
      if (!hasActiveDownload) {
        fetchNotifications();
      } else {
        console.log('[NotificationContext] Skipping auto-refresh - download in progress');
      }
    }, 60000);
    
    return () => clearInterval(interval);
  }, [fetchNotifications]); // ✅ Only fetchNotifications in dependencies

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
      // ✅ This naturally clears download state when update is ready
      fetchNotifications();
    });

    // Listen for update download progress
    const cleanupUpdateStatus = window.electronAPI.onUpdateStatus((updateData) => {
      console.log('[NotificationContext] onUpdateStatus received:', updateData);
      const { status, data } = updateData;
      
      if (status === 'downloading' && data) {
        console.log('[NotificationContext] Processing download progress:', {
          percent: data.percent,
          transferred: data.transferred,
          total: data.total,
          status
        });
        
        // Update the version_update notification with download progress
        setNotifications(prev => {
          const updated = prev.map(n => {
            // Find the update notification (version_update type)
            if (n.type === 'version_update' && n.downloadProgress?.isDownloading) {
              console.log('[NotificationContext] Updating notification progress:', {
                notificationId: n.id,
                oldPercent: n.downloadProgress?.percent,
                newPercent: data.percent,
                oldTransferred: n.downloadProgress?.transferred,
                newTransferred: data.transferred
              });
              
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
          });
          
          console.log('[NotificationContext] Notifications updated, found downloading notifications:', 
            updated.filter(n => n.downloadProgress?.isDownloading).length
          );
          
          return updated;
        });
      } else {
        console.log('[NotificationContext] Ignoring update status:', { status, hasData: !!data });
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