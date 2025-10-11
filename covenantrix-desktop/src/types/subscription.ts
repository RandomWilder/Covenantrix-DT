/**
 * Subscription Type Definitions
 * Structure for future licensing, stub implementation for MVP
 */

export type SubscriptionTier = 'free' | 'pro' | 'team' | 'enterprise';

export interface Subscription {
  tier: SubscriptionTier;
  features: FeatureFlags;
  validUntil?: Date;
  licenseKey?: string;
}

export interface FeatureFlags {
  maxDocuments: number;
  maxQueriesPerMonth: number;
  cloudSync: boolean;
  collaboration: boolean;
  prioritySupport: boolean;
  useDefaultApiKeys: boolean; // Your keys vs user's own keys
}

export interface SubscriptionContextValue {
  subscription: Subscription | null;
  isLoading: boolean;
  canUseFeature: (feature: keyof FeatureFlags) => boolean;
  getRemainingQuota: (resource: string) => Promise<number>;
  upgradeSubscription: (tier: SubscriptionTier) => Promise<void>;
}