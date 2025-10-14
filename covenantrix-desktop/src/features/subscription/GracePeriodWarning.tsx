/**
 * Grace Period Warning Component
 * Displays warning banner during grace period (paid_limited tier)
 */

import React from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { useTranslation } from 'react-i18next';

export const GracePeriodWarning: React.FC = () => {
  const { subscription, getDaysRemaining } = useSubscription();
  const { t } = useTranslation();
  
  if (!subscription || subscription.tier !== 'paid_limited') return null;
  
  const daysLeft = getDaysRemaining('grace');
  if (daysLeft === null) return null;
  
  return (
    <div className="bg-red-50 dark:bg-red-900/30 border-b border-red-200 dark:border-red-700 px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <p className="text-sm text-red-800 dark:text-red-200">
          <strong>{t('subscription.payment_issue', 'Payment Issue')}:</strong>{' '}
          {t('subscription.grace_period_warning', {
            count: daysLeft,
            defaultValue: `${daysLeft} days to resolve payment or data will be lost`
          })}
        </p>
        <button 
          className="text-sm font-medium text-red-800 dark:text-red-200 underline hover:no-underline"
          onClick={() => {
            // TODO: Implement payment resolution flow
            console.log('Resolve payment clicked');
          }}
        >
          {t('subscription.resolve_payment', 'Resolve Payment')}
        </button>
      </div>
    </div>
  );
};

