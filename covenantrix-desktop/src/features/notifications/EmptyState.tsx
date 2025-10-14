import { Bell } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="rounded-full bg-gray-100 dark:bg-gray-800 p-6 mb-4">
        <Bell className="w-12 h-12 text-gray-400 dark:text-gray-600" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
        No notifications
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
        You're all caught up! Check back later for updates.
      </p>
    </div>
  );
}

