/**
 * Trial Banner Component
 * Displays trial period countdown banner
 */

import React from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { useTranslation } from 'react-i18next';

export const TrialBanner: React.FC = () => {
  const { subscription, getDaysRemaining } = useSubscription();
  const { t } = useTranslation();
  
  if (!subscription || subscription.tier !== 'trial') return null;
  
  const daysLeft = getDaysRemaining('trial');
  if (daysLeft === null) return null;
  
  return (
    <div className="bg-blue-50 dark:bg-blue-900/30 border-b border-blue-200 dark:border-blue-700 px-4 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>{t('subscription.trial_label', 'Trial')}:</strong>{' '}
          {t('subscription.days_remaining', { count: daysLeft, defaultValue: `${daysLeft} days remaining` })}
        </p>
        <button 
          className="text-sm font-medium text-blue-800 dark:text-blue-200 underline hover:no-underline"
          onClick={() => {
            // TODO: Implement upgrade modal or redirect
            console.log('Upgrade clicked');
          }}
        >
          {t('subscription.upgrade_now', 'Upgrade Now')}
        </button>
      </div>
    </div>
  );
};

