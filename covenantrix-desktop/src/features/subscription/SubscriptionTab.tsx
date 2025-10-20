/**
 * Subscription Tab Component
 * Shows subscription status and license activation
 */

import React, { useState, useEffect } from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { useTranslation } from 'react-i18next';
import { AlertCircle, CheckCircle, Clock, Key, TrendingUp, AlertTriangle, BarChart3, History, ChevronDown, ChevronUp } from 'lucide-react';
import { ConfettiEffect } from '../../components/ui/ConfettiEffect';
import { AnalyticsDashboard } from './AnalyticsDashboard';
import { getTierLimits, getDisplayLimit } from '../../utils/tierLimits';
import type { TierStatus, TierHistoryEntry } from '../../types/subscription';

export const SubscriptionTab: React.FC = () => {
  const { subscription, usage, activateLicense, triggerConfetti, resetConfetti, getLicenseHistory, getUpgradeRecommendations, refreshSubscription } = useSubscription();
  const { t } = useTranslation();
  const [licenseKey, setLicenseKey] = useState('');
  const [isActivating, setIsActivating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tierStatus, setTierStatus] = useState<TierStatus | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [showTierHistory, setShowTierHistory] = useState(false);
  const [tierHistory, setTierHistory] = useState<TierHistoryEntry[]>([]);
  const [upgradeRecommendations, setUpgradeRecommendations] = useState<string[]>([]);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
  
  // Load tier status on mount
  useEffect(() => {
    loadTierStatus();
    // Refresh subscription data on mount to ensure fresh data
    refreshSubscription();
  }, [refreshSubscription]);

  // Add data refresh on component mount and debug logging
  useEffect(() => {
    console.log('Usage data:', usage);
    console.log('Daily queries:', usage?.queries_today);
  }, [usage]);

  // Refresh data when tab becomes visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadAnalyticsData();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  const loadTierStatus = async () => {
    try {
      const response = await (window.electronAPI.subscription as any).getTierStatus();
      if (response.success && response.data) {
        setTierStatus(response.data);
      }
    } catch (error) {
      console.error('Failed to load tier status:', error);
    }
  };

  const loadAnalyticsData = async () => {
    try {
      setIsLoadingAnalytics(true);
      const [history, recommendations] = await Promise.all([
        getLicenseHistory(),
        getUpgradeRecommendations()
      ]);
      setTierHistory(history);
      setUpgradeRecommendations(recommendations);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setIsLoadingAnalytics(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getTierColorForHistory = (tier: string) => {
    switch (tier) {
      case 'trial': return 'text-blue-600 bg-blue-100';
      case 'free': return 'text-gray-600 bg-gray-100';
      case 'paid': return 'text-green-600 bg-green-100';
      case 'paid_limited': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

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
      {/* Confetti Effect */}
      <ConfettiEffect 
        trigger={triggerConfetti} 
        onComplete={resetConfetti} 
      />
      {/* Warnings and Upgrade Prompts */}
      {tierStatus && (tierStatus.warnings.length > 0 || tierStatus.upgrade_prompts.length > 0) && (
        <div className="space-y-3">
          {/* Warnings */}
          {tierStatus.warnings.length > 0 && (
            <div className="border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 bg-yellow-50 dark:bg-yellow-900/20">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                    {t('subscription.warnings', 'Usage Warnings')}
                  </h4>
                  <ul className="space-y-1">
                    {tierStatus.warnings.map((warning: string, index: number) => (
                      <li key={index} className="text-sm text-yellow-700 dark:text-yellow-300">
                        • {warning}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
          
          {/* Upgrade Prompts */}
          {tierStatus.upgrade_prompts.length > 0 && (
            <div className="border border-blue-200 dark:border-blue-700 rounded-lg p-4 bg-blue-50 dark:bg-blue-900/20">
              <div className="flex items-start gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
                    {t('subscription.upgrade_suggestions', 'Upgrade Suggestions')}
                  </h4>
                  <ul className="space-y-1">
                    {tierStatus.upgrade_prompts.map((prompt: string, index: number) => (
                      <li key={index} className="text-sm text-blue-700 dark:text-blue-300">
                        • {prompt}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

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
              {usage.documents_uploaded} / {getDisplayLimit(subscription.tier, 'max_documents')}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-gray-700 dark:text-gray-300">
              {t('subscription.queries_monthly', 'Queries (Monthly)')}:
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {usage.queries_this_month} / {getDisplayLimit(subscription.tier, 'max_queries_monthly')}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-gray-700 dark:text-gray-300">
              {t('subscription.queries_daily', 'Queries (Daily)')}:
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {usage.queries_today} / {getDisplayLimit(subscription.tier, 'max_queries_daily')}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <span className="text-gray-700 dark:text-gray-300">
              {t('subscription.max_file_size', 'Max File Size')}:
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {getTierLimits(subscription.tier).max_doc_size_mb}MB
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2">
            <span className="text-gray-700 dark:text-gray-300">
              {t('subscription.default_api_keys', 'Default API Keys')}:
            </span>
            <span className={`font-medium ${getTierLimits(subscription.tier).use_default_keys ? 'text-green-600' : 'text-gray-500'}`}>
              {getTierLimits(subscription.tier).use_default_keys ? t('common.available', 'Available') : t('common.not_available', 'Not Available')}
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
      
      {/* Analytics Dashboard Toggle */}
      <div className="border rounded-lg p-6 bg-white dark:bg-gray-800">
        <button
          onClick={() => {
            setShowAnalytics(!showAnalytics);
            if (!showAnalytics) {
              loadAnalyticsData();
            }
          }}
          className="flex items-center justify-between w-full text-left"
        >
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {t('subscription.analytics', 'Analytics Dashboard')}
            </h3>
          </div>
          {showAnalytics ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
        </button>
        
        {showAnalytics && (
          <div className="mt-4">
            <AnalyticsDashboard />
          </div>
        )}
      </div>

      {/* Tier History */}
      <div className="border rounded-lg p-6 bg-white dark:bg-gray-800">
        <button
          onClick={() => {
            setShowTierHistory(!showTierHistory);
            if (!showTierHistory && tierHistory.length === 0) {
              loadAnalyticsData();
            }
          }}
          className="flex items-center justify-between w-full text-left"
        >
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {t('subscription.tier_history', 'Tier History')}
            </h3>
          </div>
          {showTierHistory ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
        </button>
        
        {showTierHistory && (
          <div className="mt-4">
            {isLoadingAnalytics ? (
              <div className="text-center text-gray-500 dark:text-gray-400 py-4">
                {t('common.loading', 'Loading...')}
              </div>
            ) : tierHistory.length > 0 ? (
              <div className="space-y-3">
                {tierHistory.map((entry, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className={`px-2 py-1 rounded text-xs font-medium ${getTierColorForHistory(entry.tier)}`}>
                      {entry.tier.toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {entry.reason}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDate(entry.start_date)} - {entry.end_date ? formatDate(entry.end_date) : 'Current'}
                      </p>
                    </div>
                    {entry.license_key && (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {entry.license_key.substring(0, 8)}...
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                {t('subscription.no_tier_history', 'No tier history available')}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Upgrade Recommendations */}
      {upgradeRecommendations.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-700">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
              {t('subscription.upgrade_recommendations', 'Upgrade Recommendations')}
            </h3>
          </div>
          
          <div className="space-y-2">
            {upgradeRecommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start gap-2">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  {recommendation}
                </p>
              </div>
            ))}
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

