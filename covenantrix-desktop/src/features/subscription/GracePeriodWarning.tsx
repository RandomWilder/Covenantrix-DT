/**
 * Grace Period Warning Component
 * Displays warning banner during grace period (paid_limited tier)
 */

import React, { useState, useEffect } from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, Clock, TrendingUp, ChevronDown, ChevronUp } from 'lucide-react';
import type { ViolationRecord } from '../../types/subscription';
import { formatDate } from '../../utils/dateUtils';

export const GracePeriodWarning: React.FC = () => {
  const { subscription, getDaysRemaining, getAnalytics } = useSubscription();
  const { t } = useTranslation();
  const [showDetails, setShowDetails] = useState(false);
  const [recentViolations, setRecentViolations] = useState<ViolationRecord[]>([]);
  const [graceRemaining, setGraceRemaining] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  if (!subscription || subscription.tier !== 'paid_limited') return null;
  
  const daysLeft = getDaysRemaining('grace');
  if (daysLeft === null) return null;

  useEffect(() => {
    if (showDetails) {
      loadGraceDetails();
    }
  }, [showDetails]);

  const loadGraceDetails = async () => {
    try {
      setIsLoading(true);
      const analytics = await getAnalytics();
      
      // Filter recent violations that used grace
      const graceViolations = analytics.violations
        .filter(v => v.grace_used)
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, 5);
      
      setRecentViolations(graceViolations);
      
      // Calculate remaining grace (this would come from analytics in a real implementation)
      setGraceRemaining(analytics.upgrade_signals.limit_hits_last_30_days > 0 ? 3 : 5);
    } catch (error) {
      console.error('Failed to load grace details:', error);
    } finally {
      setIsLoading(false);
    }
  };


  const getViolationTypeLabel = (type: string) => {
    switch (type) {
      case 'daily_query_limit': return t('violations.daily_query_limit', 'Daily Query Limit');
      case 'monthly_query_limit': return t('violations.monthly_query_limit', 'Monthly Query Limit');
      case 'document_limit': return t('violations.document_limit', 'Document Limit');
      case 'file_size_limit': return t('violations.file_size_limit', 'File Size Limit');
      default: return type.replace(/_/g, ' ');
    }
  };
  
  return (
    <div className="bg-red-50 dark:bg-red-900/30 border-b border-red-200 dark:border-red-700 px-4 py-3">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <p className="text-sm text-red-800 dark:text-red-200">
              <strong>{t('subscription.payment_issue', 'Payment Issue')}:</strong>{' '}
              {t('subscription.grace_period_warning', {
                count: daysLeft,
                defaultValue: `${daysLeft} days to resolve payment or data will be lost`
              })}
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-1 text-sm font-medium text-red-800 dark:text-red-200 hover:text-red-900 dark:hover:text-red-100"
            >
              {t('subscription.grace_details', 'Grace Details')}
              {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            
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

        {showDetails && (
          <div className="mt-4 pt-4 border-t border-red-200 dark:border-red-700">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Grace Status */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-red-200 dark:border-red-700">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-4 h-4 text-orange-600" />
                  <h4 className="font-medium text-gray-900 dark:text-gray-100">
                    {t('subscription.grace_status', 'Grace Status')}
                  </h4>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {graceRemaining !== null 
                    ? t('subscription.grace_remaining', `${graceRemaining} grace allowances remaining`)
                    : t('subscription.grace_unlimited', 'Unlimited grace during grace period')
                  }
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  {t('subscription.grace_reset_info', 'Grace allowances reset monthly')}
                </p>
              </div>

              {/* Recent Grace Usage */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-red-200 dark:border-red-700">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  <h4 className="font-medium text-gray-900 dark:text-gray-100">
                    {t('subscription.recent_grace_usage', 'Recent Grace Usage')}
                  </h4>
                </div>
                
                {isLoading ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t('common.loading', 'Loading...')}
                  </p>
                ) : recentViolations.length > 0 ? (
                  <div className="space-y-2">
                    {recentViolations.map((violation, index) => (
                      <div key={index} className="text-xs text-gray-600 dark:text-gray-400">
                        <div className="flex items-center justify-between">
                          <span>{getViolationTypeLabel(violation.type)}</span>
                          <span>{formatDate(violation.timestamp)}</span>
                        </div>
                        <div className="text-gray-500 dark:text-gray-500">
                          {violation.attempted}/{violation.limit} ({violation.action_taken})
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t('subscription.no_grace_usage', 'No grace usage in recent activity')}
                  </p>
                )}
              </div>
            </div>

            {/* Upgrade CTA */}
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    {t('subscription.upgrade_to_avoid_restrictions', 'Upgrade to avoid future restrictions')}
                  </p>
                  <p className="text-xs text-blue-700 dark:text-blue-300">
                    {t('subscription.upgrade_benefits', 'Get unlimited access and avoid grace period limitations')}
                  </p>
                </div>
                <button
                  onClick={() => {
                    // TODO: Implement upgrade flow
                    console.log('Upgrade clicked');
                  }}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                >
                  {t('subscription.upgrade_now', 'Upgrade Now')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

