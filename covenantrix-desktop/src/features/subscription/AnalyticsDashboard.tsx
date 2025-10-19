/**
 * Analytics Dashboard Component
 * Displays comprehensive subscription analytics and usage insights
 */

import React, { useState, useEffect } from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { useTranslation } from 'react-i18next';
import { 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Activity,
  Zap,
  Target,
  Calendar
} from 'lucide-react';
import type { SubscriptionAnalytics, TierHistoryEntry } from '../../types/subscription';

export const AnalyticsDashboard: React.FC = () => {
  const { getAnalytics, getLicenseHistory, getUpgradeRecommendations } = useSubscription();
  const { t } = useTranslation();
  const [analytics, setAnalytics] = useState<SubscriptionAnalytics | null>(null);
  const [licenseHistory, setLicenseHistory] = useState<TierHistoryEntry[]>([]);
  const [upgradeRecommendations, setUpgradeRecommendations] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [analyticsData, historyData, recommendationsData] = await Promise.all([
        getAnalytics().catch(err => {
          console.error('Failed to get analytics:', err);
          return {
            tier_history: [],
            violations: [],
            feature_usage: {
              advanced_search_used: false,
              export_used: false,
              api_access_used: false,
              last_feature_audit: new Date().toISOString()
            },
            upgrade_signals: {
              limit_hits_last_30_days: 0,
              avg_queries_per_day: 0,
              trending_up: false
            },
            conversations_last_30_days: 0,
            avg_queries_per_conversation: 0,
            // Deprecated aliases for backward compatibility
            sessions_last_30_days: 0,
            avg_queries_per_session: 0
          };
        }),
        getLicenseHistory().catch(err => {
          console.error('Failed to get license history:', err);
          return [];
        }),
        getUpgradeRecommendations().catch(err => {
          console.error('Failed to get upgrade recommendations:', err);
          return [];
        })
      ]);

      setAnalytics(analyticsData);
      setLicenseHistory(historyData);
      setUpgradeRecommendations(recommendationsData);
    } catch (err: any) {
      console.error('Failed to load analytics data:', err);
      setError(err.message || 'Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString();
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'Invalid Date';
    }
  };

  const getTierColor = (tier: string) => {
    if (!tier) return 'text-gray-600 bg-gray-100';
    
    switch (tier.toLowerCase()) {
      case 'trial': return 'text-blue-600 bg-blue-100';
      case 'free': return 'text-gray-600 bg-gray-100';
      case 'paid': return 'text-green-600 bg-green-100';
      case 'paid_limited': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getViolationTypeColor = (type: string) => {
    if (!type) return 'text-gray-600 bg-gray-100';
    
    switch (type.toLowerCase()) {
      case 'daily_query_limit': return 'text-orange-600 bg-orange-100';
      case 'monthly_query_limit': return 'text-red-600 bg-red-100';
      case 'document_limit': return 'text-purple-600 bg-purple-100';
      case 'file_size_limit': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        {t('analytics.loading', 'Loading analytics...')}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-2" />
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button
          onClick={loadAnalyticsData}
          className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {t('common.retry', 'Retry')}
        </button>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        {t('analytics.no_data', 'No analytics data available')}
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            {t('analytics.title', 'Analytics Dashboard')}
          </h2>
        </div>
        <button
          onClick={loadAnalyticsData}
          className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
        >
          {t('common.refresh', 'Refresh')}
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {t('analytics.conversations_30_days', 'Conversations (30 days)')}
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {analytics.conversations_last_30_days || 0}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {t('analytics.avg_queries_per_conversation', 'Avg Queries/Conversation')}
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {analytics.avg_queries_per_conversation ? analytics.avg_queries_per_conversation.toFixed(1) : '0.0'}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {t('analytics.violations_30_days', 'Violations (30 days)')}
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {analytics.violations?.length || 0}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-purple-600" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {t('analytics.upgrade_signals', 'Upgrade Signals')}
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {analytics.upgrade_signals?.limit_hits_last_30_days || 0}
          </p>
        </div>
      </div>

      {/* Tier History Timeline */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {t('analytics.tier_history', 'Tier History')}
          </h3>
        </div>
        
        {licenseHistory && licenseHistory.length > 0 ? (
          <div className="space-y-3">
            {licenseHistory.map((entry, index) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className={`px-2 py-1 rounded text-xs font-medium ${getTierColor(entry.tier)}`}>
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
            {t('analytics.no_tier_history', 'No tier history available')}
          </p>
        )}
      </div>

      {/* Violations Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-orange-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {t('analytics.recent_violations', 'Recent Violations')}
          </h3>
        </div>
        
        {analytics.violations && analytics.violations.length > 0 ? (
          <div className="space-y-3">
            {analytics.violations.slice(0, 10).map((violation, index) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className={`px-2 py-1 rounded text-xs font-medium ${getViolationTypeColor(violation.type)}`}>
                  {violation.type.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    {violation.attempted} / {violation.limit} ({violation.action_taken})
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {formatDate(violation.timestamp)} • {violation.tier}
                  </p>
                </div>
                {violation.grace_used && (
                  <div className="text-xs text-orange-600 dark:text-orange-400">
                    Grace Used
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400 text-center py-4">
            {t('analytics.no_violations', 'No violations in the last 30 days')}
          </p>
        )}
      </div>

      {/* Feature Usage */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-4">
          <Target className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {t('analytics.feature_usage', 'Feature Usage')}
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <CheckCircle className={`w-5 h-5 ${analytics.feature_usage?.advanced_search_used ? 'text-green-600' : 'text-gray-400'}`} />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {t('analytics.advanced_search', 'Advanced Search')}
            </span>
          </div>
          
          <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <CheckCircle className={`w-5 h-5 ${analytics.feature_usage?.export_used ? 'text-green-600' : 'text-gray-400'}`} />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {t('analytics.export', 'Export')}
            </span>
          </div>
          
          <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <CheckCircle className={`w-5 h-5 ${analytics.feature_usage?.api_access_used ? 'text-green-600' : 'text-gray-400'}`} />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {t('analytics.api_access', 'API Access')}
            </span>
          </div>
        </div>
      </div>

      {/* Upgrade Recommendations */}
      {upgradeRecommendations && upgradeRecommendations.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-700">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
              {t('analytics.upgrade_recommendations', 'Upgrade Recommendations')}
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

      {/* Upgrade Signals */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {t('analytics.upgrade_signals', 'Upgrade Signals')}
          </h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {analytics.upgrade_signals?.limit_hits_last_30_days || 0}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('analytics.limit_hits', 'Limit Hits (30 days)')}
            </p>
          </div>
          
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {analytics.upgrade_signals?.avg_queries_per_day ? analytics.upgrade_signals.avg_queries_per_day.toFixed(1) : '0.0'}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('analytics.avg_queries_per_day', 'Avg Queries/Day')}
            </p>
          </div>
          
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center justify-center gap-2">
              {analytics.upgrade_signals?.trending_up ? (
                <TrendingUp className="w-5 h-5 text-green-600" />
              ) : (
                <Activity className="w-5 h-5 text-gray-400" />
              )}
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {analytics.upgrade_signals?.trending_up ? t('analytics.trending_up', 'Trending Up') : t('analytics.stable', 'Stable')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
