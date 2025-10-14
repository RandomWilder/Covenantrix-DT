/**
 * Usage Stats Widget Component
 * Displays remaining quotas in a compact widget
 */

import React from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { useTranslation } from 'react-i18next';

export const UsageStatsWidget: React.FC = () => {
  const { usage, subscription, getRemainingQuota } = useSubscription();
  const { t } = useTranslation();
  
  if (!subscription || subscription.tier === 'paid') return null;
  if (!usage) return null;
  
  const docsRemaining = getRemainingQuota('documents');
  const queriesRemaining = getRemainingQuota('queries');
  
  return (
    <div className="px-4 py-2 text-xs text-gray-600 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700">
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span>{t('subscription.documents_remaining', 'Documents')}:</span>
          <span className="font-medium">
            {docsRemaining === -1 ? '∞' : docsRemaining} {t('subscription.left', 'left')}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>{t('subscription.queries_remaining', 'Queries')}:</span>
          <span className="font-medium">
            {queriesRemaining === -1 ? '∞' : queriesRemaining} {t('subscription.left', 'left')}
          </span>
        </div>
      </div>
    </div>
  );
};

