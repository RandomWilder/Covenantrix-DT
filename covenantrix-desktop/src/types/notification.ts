export interface NotificationAction {
  label: string;
  action: string;
  url?: string;
}

// ✅ NEW: Separate type for download progress (transient state)
export interface DownloadProgress {
  percent: number;
  transferred: number;
  total: number;
  isDownloading: boolean;
}

export interface Notification {
  id: string;
  type: string;
  source: 'local' | 'cloud' | 'subscription';
  title: string;
  summary: string;
  content?: string;
  actions?: NotificationAction[];
  timestamp: string;
  read: boolean;
  dismissed: boolean;
  metadata?: Record<string, any>;
  // ✅ Download progress tracking (ephemeral, added by frontend only)
  downloadProgress?: DownloadProgress;
}

export interface NotificationContextValue {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  expandedNotifications: Set<string>;
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  dismissNotification: (id: string) => Promise<void>;
  toggleExpanded: (id: string) => void;
  handleAction: (notificationId: string, action: string) => Promise<void>;
}