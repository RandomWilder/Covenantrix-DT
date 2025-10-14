/**
 * Upgrade Modal Component
 * Shows when user hits tier limits
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  message: string;
  currentTier?: string;
  details?: string;
}

export const UpgradeModal: React.FC<UpgradeModalProps> = ({
  isOpen,
  onClose,
  title,
  message,
  currentTier,
  details
}) => {
  const { t } = useTranslation();
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-6 space-y-4">
          <p className="text-gray-700 dark:text-gray-300">
            {message}
          </p>
          
          {details && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {details}
            </p>
          )}
          
          {currentTier && (
            <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <strong>{t('subscription.current_tier', 'Current Plan')}:</strong>{' '}
                {currentTier.toUpperCase()}
              </p>
            </div>
          )}
        </div>
        
        {/* Actions */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 space-y-3">
          {currentTier === 'trial' && (
            <button 
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              onClick={() => {
                // TODO: Implement upgrade flow
                console.log('Upgrade to Paid clicked');
              }}
            >
              {t('subscription.upgrade_to_paid', 'Upgrade to Paid')}
            </button>
          )}
          
          {currentTier === 'free' && (
            <>
              <button 
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                onClick={() => {
                  // TODO: Implement upgrade flow
                  console.log('Upgrade to Paid clicked');
                }}
              >
                {t('subscription.upgrade_to_paid', 'Upgrade to Paid')}
              </button>
              <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                {t('subscription.continue_with_custom_keys', 'Or continue using your own API keys with current limits')}
              </p>
            </>
          )}
          
          <button 
            onClick={onClose}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            {t('common.close', 'Close')}
          </button>
        </div>
      </div>
    </div>
  );
};

