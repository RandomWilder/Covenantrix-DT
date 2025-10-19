/**
 * Subscription and Tier Management Types
 */

export type SubscriptionTier = 'trial' | 'free' | 'paid' | 'paid_limited';

export interface FeatureFlags {
  max_documents: number;
  max_doc_size_mb: number;
  max_total_storage_mb: number;
  max_queries_monthly: number;
  max_queries_daily: number;
  use_default_keys: boolean;
}

export interface SubscriptionSettings {
  tier: SubscriptionTier;
  license_key?: string;
  trial_started_at?: string;
  trial_expires_at?: string;
  grace_period_started_at?: string;
  grace_period_expires_at?: string;
  features: FeatureFlags;
  last_tier_change?: string;
}

export interface UsageStats {
  documents_uploaded: number;
  queries_this_month: number;
  queries_today: number;
  monthly_remaining: number;
  daily_remaining: number;
  monthly_reset_date: string;
  daily_reset_date: string;
}

export interface SubscriptionStatusResponse {
  subscription: SubscriptionSettings;
  usage: UsageStats;
}

export interface LicenseActivationResponse {
  success: boolean;
  new_tier: string;
  message: string;
}

export interface TierStatus {
  tier: string;
  features: Record<string, any>;
  usage_stats: UsageStats;
  remaining: Record<string, any>;
  usage_percentages: {
    monthly_queries: number;
    daily_queries: number;
    documents: number;
  };
  warnings: string[];
  upgrade_prompts: string[];
  trial_info: {
    started_at?: string;
    expires_at?: string;
    is_active: boolean;
  };
  grace_period_info: {
    started_at?: string;
    expires_at?: string;
    is_active: boolean;
  };
}

export interface TierHistoryEntry {
  tier: SubscriptionTier;
  start_date: string;
  end_date: string | null;
  reason: string;
  license_key?: string;
  expiration_date?: string;
}

export interface ViolationRecord {
  timestamp: string;
  type: string;
  tier: string;
  limit: number;
  attempted: number;
  action_taken: string;
  grace_used: boolean;
}

export interface FeatureUsageStats {
  advanced_search_used: boolean;
  export_used: boolean;
  api_access_used: boolean;
  last_feature_audit: string;
}

export interface UpgradeSignals {
  limit_hits_last_30_days: number;
  avg_queries_per_day: number;
  trending_up: boolean;
}

export interface SubscriptionAnalytics {
  tier_history: TierHistoryEntry[];
  violations: ViolationRecord[];
  feature_usage: FeatureUsageStats;
  upgrade_signals: UpgradeSignals;
  conversations_last_30_days: number;
  avg_queries_per_conversation: number;
  
  // Deprecated aliases for backward compatibility
  /** @deprecated Use conversations_last_30_days instead */
  sessions_last_30_days: number;
  /** @deprecated Use avg_queries_per_conversation instead */
  avg_queries_per_session: number;
}

export interface SubscriptionContextValue {
  subscription: SubscriptionSettings | null;
  usage: UsageStats | null;
  isLoading: boolean;
  canUploadDocument: () => boolean;
  canSendQuery: () => Promise<boolean>;
  getRemainingQuota: (resource: 'documents' | 'queries') => number;
  activateLicense: (key: string) => Promise<void>;
  getDaysRemaining: (type: 'trial' | 'grace') => number | null;
  refreshSubscription: () => Promise<void>;
  triggerConfetti: boolean;
  resetConfetti: () => void;
  getAnalytics: () => Promise<SubscriptionAnalytics>;
  getLicenseHistory: () => Promise<TierHistoryEntry[]>;
  getUpgradeRecommendations: () => Promise<string[]>;
}
