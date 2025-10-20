/**
 * Google Account Card Component
 * Displays a single connected Google account with status and actions
 */

import React from 'react';
import { Trash2, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { GoogleAccountSettings } from '../../../types/settings';
import { formatDate, getRelativeTime } from '../../../utils/dateUtils';

interface GoogleAccountCardProps {
  account: GoogleAccountSettings;
  onRemove: (accountId: string) => void;
}

export const GoogleAccountCard: React.FC<GoogleAccountCardProps> = ({ 
  account, 
  onRemove 
}) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'connected':
        return 'text-green-600 dark:text-green-400';
      case 'expired':
        return 'text-red-600 dark:text-red-400';
      case 'revoked':
        return 'text-gray-600 dark:text-gray-400';
      default:
        return 'text-yellow-600 dark:text-yellow-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'connected':
        return <CheckCircle className="w-4 h-4" />;
      case 'expired':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };


  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Email */}
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-lg font-medium text-gray-900 dark:text-white">
              {account.email}
            </span>
            <div className={`flex items-center space-x-1 ${getStatusColor(account.status)}`}>
              {getStatusIcon(account.status)}
              <span className="text-xs font-medium capitalize">{account.status}</span>
            </div>
          </div>

          {/* Display Name */}
          {account.display_name && (
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              {account.display_name}
            </div>
          )}

          {/* Timestamps */}
          <div className="flex flex-col space-y-1 text-xs text-gray-500 dark:text-gray-400">
            <div>
              <span className="font-medium">Connected:</span> {formatDate(account.connected_at)}
            </div>
            <div>
              <span className="font-medium">Last used:</span> {getRelativeTime(account.last_used)}
            </div>
          </div>

          {/* Scopes */}
          {account.scopes && account.scopes.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {account.scopes.map((scope, index) => {
                const scopeName = scope.split('/').pop() || scope;
                return (
                  <span 
                    key={index}
                    className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded"
                  >
                    {scopeName}
                  </span>
                );
              })}
            </div>
          )}
        </div>

        {/* Actions */}
        <button
          onClick={() => onRemove(account.account_id)}
          className="ml-4 p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
          title="Remove account"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

