/**
 * Subscription Tab Component
 * Shows subscription status and license activation
 */

import React, { useState } from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { useTranslation } from 'react-i18next';
import { AlertCircle, CheckCircle, Clock, Key } from 'lucide-react';

export const SubscriptionTab: React.FC = () => {
  const { subscription, usage, activateLicense } = useSubscription();
  const { t } = useTranslation();
  const [licenseKey, setLicenseKey] = useState('');
  const [isActivating, setIsActivating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  if (!subscription || !usage) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        {t('subscription.loading', 'Loading subscription information...')}
      </div>
    );
  }
  
  const handleActivate = async () => {
    if (!licenseKey.trim()) {
      setError(t('subscription.enter_license_key', 'Please enter a license key'));
      return;
    }
    
    setIsActivating(true);
    setError(null);
    setSuccess(null);
    
    try {
      await activateLicense(licenseKey);
      setLicenseKey('');
      setSuccess(t('subscription.activation_success', 'License activated successfully!'));
    } catch (err: any) {
      setError(err.message || t('subscription.activation_failed', 'License activation failed'));
    } finally {
      setIsActivating(false);
    }
  };
  
  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'trial': return 'blue';
      case 'free': return 'gray';
      case 'paid': return 'green';
      case 'paid_limited': return 'red';
      default: return 'gray';
    }
  };
  
  const tierColor = getTierColor(subscription.tier);
  
  return (
    <div className="space-y-6 p-6">
      {/* Current Tier Display */}
      <div className={`border rounded-lg p-6 bg-${tierColor}-50 dark:bg-${tierColor}-900/20 border-${tierColor}-200 dark:border-${tierColor}-700`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-semibold text-${tierColor}-900 dark:text-${tierColor}-100`}>
            {t('subscription.current_plan', 'Current Plan')}: {subscription.tier.toUpperCase()}
          </h3>
          {subscription.tier === 'paid' && (
            <CheckCircle className={`w-6 h-6 text-${tierColor}-600`} />
          )}
          {subscription.tier === 'trial' && (
            <Clock className={`w-6 h-6 text-${tierColor}-600`} />
          )}
          {subscription.tier === 'paid_limited' && (
            <AlertCircle className={`w-6 h-6 text-${tierColor}-600`} />
          )}
        </div>
        
        {/* Feature Limits Display */}
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-gray-700 dark:text-gray-300">
              {t('subscription.documents', 'Documents')}:
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {usage.documents_uploaded} / {subscription.features.max_documents === -1 ? '∞' : subscription.features.max_documents}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-gray-700 dark:text-gray-300">
              {t('subscription.queries_monthly', 'Queries (Monthly)')}:
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {usage.queries_this_month} / {subscription.features.max_queries_monthly === -1 ? '∞' : subscription.features.max_queries_monthly}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-gray-700 dark:text-gray-300">
              {t('subscription.queries_daily', 'Queries (Daily)')}:
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {usage.queries_today} / {subscription.features.max_queries_daily === -1 ? '∞' : subscription.features.max_queries_daily}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-gray-700 dark:text-gray-300">
              {t('subscription.max_file_size', 'Max File Size')}:
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {subscription.features.max_doc_size_mb}MB
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2">
            <span className="text-gray-700 dark:text-gray-300">
              {t('subscription.default_api_keys', 'Default API Keys')}:
            </span>
            <span className={`font-medium ${subscription.features.use_default_keys ? 'text-green-600' : 'text-gray-500'}`}>
              {subscription.features.use_default_keys ? t('common.available', 'Available') : t('common.not_available', 'Not Available')}
            </span>
          </div>
        </div>
      </div>
      
      {/* License Activation */}
      {subscription.tier !== 'paid' && (
        <div className="border rounded-lg p-6 bg-white dark:bg-gray-800">
          <div className="flex items-center gap-2 mb-4">
            <Key className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {t('subscription.activate_license', 'Activate License')}
            </h3>
          </div>
          
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {t('subscription.activate_description', 'Enter your license key to upgrade your subscription')}
          </p>
          
          <div className="space-y-3">
            <input
              type="text"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value)}
              placeholder={t('subscription.license_key_placeholder', 'Paste license key here')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isActivating}
            />
            
            <button
              onClick={handleActivate}
              disabled={!licenseKey.trim() || isActivating}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isActivating 
                ? t('subscription.activating', 'Activating...')
                : t('subscription.activate_button', 'Activate License')
              }
            </button>
            
            {error && (
              <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            )}
            
            {success && (
              <div className="flex items-start gap-2 p-3 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-green-800 dark:text-green-200">{success}</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Tier Information */}
      <div className="border rounded-lg p-6 bg-gray-50 dark:bg-gray-800/50">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
          {t('subscription.about_tiers', 'Subscription Tiers')}
        </h3>
        <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
          <div>
            <strong className="text-gray-900 dark:text-gray-100">TRIAL:</strong>{' '}
            {t('subscription.trial_description', '7 days, 3 docs, 10MB per doc, unlimited queries, default API keys')}
          </div>
          <div>
            <strong className="text-gray-900 dark:text-gray-100">FREE:</strong>{' '}
            {t('subscription.free_description', 'Indefinite, 3 docs, 10MB per doc, 50 queries/month + 20/day, custom keys only')}
          </div>
          <div>
            <strong className="text-gray-900 dark:text-gray-100">PAID:</strong>{' '}
            {t('subscription.paid_description', 'Unlimited docs/queries, 100MB per doc, default keys available')}
          </div>
        </div>
      </div>
    </div>
  );
};

