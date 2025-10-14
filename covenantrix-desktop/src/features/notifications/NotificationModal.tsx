import { X } from 'lucide-react';
import { useNotifications } from '../../contexts/NotificationContext';
import { EmptyState } from './EmptyState';
import { NotificationCard } from './NotificationCard';

interface NotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotificationModal({ isOpen, onClose }: NotificationModalProps) {
  const {
    notifications,
    expandedNotifications,
    toggleExpanded,
    dismissNotification,
    handleAction,
  } = useNotifications();

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="fixed inset-0 flex items-start justify-center z-50 pointer-events-none">
        <div className="pointer-events-auto w-full max-w-2xl mt-20 mx-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-h-[70vh] flex flex-col border border-gray-200 dark:border-gray-800">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Notifications
              </h2>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto">
              {notifications.length === 0 ? (
                <EmptyState />
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-800">
                  {notifications.map((notification) => (
                    <NotificationCard
                      key={notification.id}
                      notification={notification}
                      isExpanded={expandedNotifications.has(notification.id)}
                      onToggle={() => toggleExpanded(notification.id)}
                      onDismiss={dismissNotification}
                      onAction={handleAction}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

