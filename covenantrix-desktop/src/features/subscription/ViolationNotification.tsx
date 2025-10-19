/**
 * Violation Notification Component
 * Shows inline notifications when limits are hit
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, X, TrendingUp, Clock, AlertCircle } from 'lucide-react';

export interface ViolationNotificationProps {
  violationType: 'daily_query_limit' | 'monthly_query_limit' | 'document_limit' | 'file_size_limit';
  tier: string;
  limit: number;
  attempted: number;
  actionTaken: 'blocked' | 'warned' | 'grace_allowed';
  graceUsed?: boolean;
  onDismiss?: () => void;
  onUpgrade?: () => void;
  resetTime?: string;
}

export const ViolationNotification: React.FC<ViolationNotificationProps> = ({
  violationType,
  tier,
  limit,
  attempted,
  actionTaken,
  graceUsed = false,
  onDismiss,
  onUpgrade,
  resetTime
}) => {
  const { t } = useTranslation();

  const getViolationTitle = () => {
    switch (violationType) {
      case 'daily_query_limit':
        return t('violations.daily_query_limit', 'Daily Query Limit Reached');
      case 'monthly_query_limit':
        return t('violations.monthly_query_limit', 'Monthly Query Limit Reached');
      case 'document_limit':
        return t('violations.document_limit', 'Document Limit Reached');
      case 'file_size_limit':
        return t('violations.file_size_limit', 'File Size Limit Exceeded');
      default:
        return t('violations.limit_reached', 'Limit Reached');
    }
  };

  const getViolationMessage = () => {
    const limitType = violationType.replace(/_/g, ' ').replace('limit', 'limit');
    
    if (actionTaken === 'blocked') {
      return t('violations.blocked_message', 
        `You've reached your ${limitType} of ${limit}. ${resetTime ? `Limit resets ${resetTime}.` : ''}`, 
        { limitType, limit, resetTime }
      );
    } else if (actionTaken === 'grace_allowed') {
      return t('violations.grace_message', 
        `You've exceeded your ${limitType} but have been granted grace access. ${graceUsed ? 'This uses your grace allowance.' : ''}`, 
        { limitType, graceUsed }
      );
    } else {
      return t('violations.warning_message', 
        `You're approaching your ${limitType} limit (${attempted}/${limit}).`, 
        { limitType, attempted, limit }
      );
    }
  };

  const getNotificationColor = () => {
    if (actionTaken === 'blocked') {
      return 'border-red-200 bg-red-50 dark:border-red-700 dark:bg-red-900/20';
    } else if (actionTaken === 'grace_allowed') {
      return 'border-orange-200 bg-orange-50 dark:border-orange-700 dark:bg-orange-900/20';
    } else {
      return 'border-yellow-200 bg-yellow-50 dark:border-yellow-700 dark:bg-yellow-900/20';
    }
  };

  const getIconColor = () => {
    if (actionTaken === 'blocked') {
      return 'text-red-600';
    } else if (actionTaken === 'grace_allowed') {
      return 'text-orange-600';
    } else {
      return 'text-yellow-600';
    }
  };

  const getIcon = () => {
    if (actionTaken === 'blocked') {
      return <AlertCircle className="w-5 h-5" />;
    } else if (actionTaken === 'grace_allowed') {
      return <Clock className="w-5 h-5" />;
    } else {
      return <AlertTriangle className="w-5 h-5" />;
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${getNotificationColor()}`}>
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 mt-0.5 ${getIconColor()}`}>
          {getIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-2">
            <h4 className={`font-medium ${actionTaken === 'blocked' ? 'text-red-800 dark:text-red-200' : actionTaken === 'grace_allowed' ? 'text-orange-800 dark:text-orange-200' : 'text-yellow-800 dark:text-yellow-200'}`}>
              {getViolationTitle()}
            </h4>
            
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="flex-shrink-0 p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            )}
          </div>
          
          <p className={`text-sm mb-3 ${actionTaken === 'blocked' ? 'text-red-700 dark:text-red-300' : actionTaken === 'grace_allowed' ? 'text-orange-700 dark:text-orange-300' : 'text-yellow-700 dark:text-yellow-300'}`}>
            {getViolationMessage()}
          </p>
          
          <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
            <span>
              {t('violations.tier', 'Tier')}: {tier.toUpperCase()}
            </span>
            <span>•</span>
            <span>
              {t('violations.usage', 'Usage')}: {attempted}/{limit}
            </span>
            {graceUsed && (
              <>
                <span>•</span>
                <span className="text-orange-600 dark:text-orange-400">
                  {t('violations.grace_used', 'Grace Used')}
                </span>
              </>
            )}
          </div>
          
          {actionTaken === 'blocked' && onUpgrade && (
            <div className="mt-3 pt-3 border-t border-red-200 dark:border-red-700">
              <button
                onClick={onUpgrade}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                <TrendingUp className="w-4 h-4" />
                {t('violations.upgrade_now', 'Upgrade Now')}
              </button>
            </div>
          )}
          
          {actionTaken === 'grace_allowed' && (
            <div className="mt-3 pt-3 border-t border-orange-200 dark:border-orange-700">
              <div className="flex items-center gap-2 text-sm text-orange-700 dark:text-orange-300">
                <Clock className="w-4 h-4" />
                <span>
                  {t('violations.grace_period_active', 'Grace period is active. Consider upgrading to avoid future restrictions.')}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
