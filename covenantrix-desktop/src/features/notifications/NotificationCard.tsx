import { X } from 'lucide-react';
import { Notification } from '../../types/notification';
import { formatRelativeTime } from '../../utils/dateUtils';

interface NotificationCardProps {
  notification: Notification;
  isExpanded: boolean;
  onToggle: () => void;
  onDismiss: (id: string) => void;
  onAction: (id: string, action: string) => void;
}


function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

export function NotificationCard({
  notification,
  isExpanded,
  onToggle,
  onDismiss,
  onAction,
}: NotificationCardProps) {
  const isUnread = !notification.read && !notification.dismissed;

  return (
    <div
      className={`
        notification-card ${isExpanded ? 'notification-card-expanded' : ''} border-b border-gray-200 dark:border-gray-700 
        ${isUnread ? 'notification-card-unread bg-blue-50/50 dark:bg-blue-900/10' : 'bg-white dark:bg-gray-900'}
        transition-colors duration-200
      `}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Unread indicator */}
          {isUnread && (
            <div className="flex-shrink-0 mt-1">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
            </div>
          )}

          {/* Content */}
          <div className="flex-1 min-w-0 cursor-pointer" onClick={onToggle}>
            <h4
              className={`text-sm mb-1 ${
                isUnread
                  ? 'font-semibold text-gray-900 dark:text-gray-100'
                  : 'font-medium text-gray-800 dark:text-gray-200'
              }`}
            >
              {notification.title}
            </h4>

            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              {notification.summary}
            </p>

            {/* Expanded content */}
            {isExpanded && notification.content && !notification.downloadProgress?.isDownloading && (
              <div className="mt-3 mb-3 max-h-[200px] overflow-y-auto rounded border border-gray-200 dark:border-gray-700 p-3 bg-gray-50 dark:bg-gray-800/50">
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {notification.content}
                </p>
              </div>
            )}

            {/* Download progress */}
            {isExpanded && notification.downloadProgress?.isDownloading && (
              <div className="mt-3 mb-3">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700 dark:text-gray-300 font-medium flex items-center gap-2">
                      {notification.downloadProgress.percent === 0 ? (
                        <>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                          Starting download...
                        </>
                      ) : notification.downloadProgress.percent === 100 ? (
                        <>
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          Download completed
                        </>
                      ) : (
                        <>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                          Downloading update...
                        </>
                      )}
                    </span>
                    <span className="text-gray-600 dark:text-gray-400 font-mono">
                      {Math.round(notification.downloadProgress.percent)}%
                    </span>
                  </div>
                  
                  {/* Progress bar */}
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out relative"
                      style={{ width: `${notification.downloadProgress.percent}%` }}
                    >
                      {/* Animated shimmer effect */}
                      {notification.downloadProgress.percent > 0 && notification.downloadProgress.percent < 100 && (
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
                      )}
                    </div>
                  </div>
                  
                  {/* Download stats */}
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>
                      {formatBytes(notification.downloadProgress.transferred)} / {formatBytes(notification.downloadProgress.total)}
                    </span>
                    {notification.downloadProgress.percent > 0 && notification.downloadProgress.percent < 100 && (
                      <span>
                        {formatBytes(notification.downloadProgress.total - notification.downloadProgress.transferred)} remaining
                      </span>
                    )}
                    {notification.downloadProgress.percent === 100 && (
                      <span className="text-green-600 dark:text-green-400 font-medium">
                        Ready to install
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Action buttons - hide during download */}
            {isExpanded && notification.actions && notification.actions.length > 0 && !notification.downloadProgress?.isDownloading && (
              <div className="flex gap-2 mt-3">
                {notification.actions.map((action, index) => (
                  <button
                    key={index}
                    onClick={(e) => {
                      e.stopPropagation();
                      console.log('[NotificationCard] Action button clicked', { 
                        notificationId: notification.id, 
                        action: action.action,
                        actionLabel: action.label 
                      });
                      onAction(notification.id, action.action);
                    }}
                    className="px-4 py-2 text-sm font-medium rounded-lg transition-colors
                      bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}

            <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">
              {formatRelativeTime(notification.timestamp)}
            </div>
          </div>

          {/* Dismiss button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDismiss(notification.id);
            }}
            className="flex-shrink-0 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Dismiss notification"
          >
            <X className="w-4 h-4 text-gray-400 dark:text-gray-600" />
          </button>
        </div>
      </div>
    </div>
  );
}

