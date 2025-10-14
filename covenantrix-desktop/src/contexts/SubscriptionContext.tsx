/**
 * Subscription Context
 * Manages subscription state and usage tracking
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { SubscriptionSettings, UsageStats, SubscriptionContextValue } from '../types/subscription';
import { isElectron } from '../utils/environment';

const SubscriptionContext = createContext<SubscriptionContextValue | undefined>(undefined);

export const SubscriptionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [subscription, setSubscription] = useState<SubscriptionSettings | null>(null);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSubscription();
  }, []);

  const loadSubscription = useCallback(async () => {
    if (!isElectron()) return;
    
    try {
      const response = await window.electronAPI.subscription.getStatus();
      if (response.success && response.data) {
        setSubscription(response.data.subscription);
        setUsage(response.data.usage);
      }
    } catch (error) {
      console.error('Failed to load subscription:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshSubscription = useCallback(async () => {
    await loadSubscription();
  }, [loadSubscription]);

  const canUploadDocument = useCallback((): boolean => {
    if (!subscription || !usage) return false;
    
    const { max_documents } = subscription.features;
    if (max_documents === -1) return true;
    
    return usage.documents_uploaded < max_documents;
  }, [subscription, usage]);

  const canSendQuery = useCallback(async (): Promise<boolean> => {
    if (!subscription || !usage) return false;
    
    const { max_queries_monthly, max_queries_daily } = subscription.features;
    
    if (max_queries_monthly !== -1 && usage.monthly_remaining <= 0) return false;
    if (max_queries_daily !== -1 && usage.daily_remaining <= 0) return false;
    
    return true;
  }, [subscription, usage]);

  const getRemainingQuota = useCallback((resource: 'documents' | 'queries'): number => {
    if (!subscription || !usage) return 0;
    
    if (resource === 'documents') {
      const max = subscription.features.max_documents;
      if (max === -1) return -1;
      return Math.max(0, max - usage.documents_uploaded);
    } else {
      const monthlyRemaining = usage.monthly_remaining !== -1 ? usage.monthly_remaining : Infinity;
      const dailyRemaining = usage.daily_remaining !== -1 ? usage.daily_remaining : Infinity;
      
      const minimum = Math.min(monthlyRemaining, dailyRemaining);
      return minimum === Infinity ? -1 : minimum;
    }
  }, [subscription, usage]);

  const activateLicense = useCallback(async (key: string): Promise<void> => {
    if (!isElectron()) throw new Error('License activation only available in desktop app');
    
    const response = await window.electronAPI.subscription.activateLicense(key);
    if (response.success) {
      await loadSubscription();
    } else {
      throw new Error(response.error || 'License activation failed');
    }
  }, [loadSubscription]);

  const getDaysRemaining = useCallback((type: 'trial' | 'grace'): number | null => {
    if (!subscription) return null;
    
    const expiryField = type === 'trial' ? subscription.trial_expires_at : subscription.grace_period_expires_at;
    if (!expiryField) return null;
    
    const expiry = new Date(expiryField);
    const now = new Date();
    const diff = expiry.getTime() - now.getTime();
    
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  }, [subscription]);

  const value: SubscriptionContextValue = {
    subscription,
    usage,
    isLoading,
    canUploadDocument,
    canSendQuery,
    getRemainingQuota,
    activateLicense,
    getDaysRemaining,
    refreshSubscription
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};

export const useSubscription = (): SubscriptionContextValue => {
  const context = useContext(SubscriptionContext);
  if (!context) {
    throw new Error('useSubscription must be used within SubscriptionProvider');
  }
  return context;
};

