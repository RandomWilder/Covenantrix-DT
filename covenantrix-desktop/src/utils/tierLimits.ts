/**
 * Tier Limits Configuration
 * Client-side copy of TIER_LIMITS for feature computation
 * This ensures frontend can compute features from tier without API calls
 */

export interface FeatureFlags {
  max_documents: number;
  max_doc_size_mb: number;
  max_total_storage_mb: number;
  max_queries_monthly: number;
  max_queries_daily: number;
  use_default_keys: boolean;
}

// Tier limits configuration - must match backend TIER_LIMITS
export const TIER_LIMITS: Record<string, FeatureFlags> = {
  trial: {
    max_documents: 3,
    max_doc_size_mb: 10,
    max_total_storage_mb: 30,
    max_queries_monthly: -1,  // Unlimited
    max_queries_daily: -1,    // Unlimited
    use_default_keys: true
  },
  free: {
    max_documents: 3,
    max_doc_size_mb: 10,
    max_total_storage_mb: 30,
    max_queries_monthly: 50,
    max_queries_daily: 20,
    use_default_keys: false
  },
  paid: {
    max_documents: -1,        // Unlimited
    max_doc_size_mb: 100,
    max_total_storage_mb: -1,  // Unlimited
    max_queries_monthly: -1,   // Unlimited
    max_queries_daily: -1,     // Unlimited
    use_default_keys: true
  },
  paid_limited: {
    max_documents: 3,  // Show only first 3
    max_doc_size_mb: 10,
    max_total_storage_mb: 30,
    max_queries_monthly: 50,
    max_queries_daily: 20,
    use_default_keys: false
  }
};

/**
 * Get tier limits for a given tier
 * 
 * @param tier - Subscription tier name
 * @returns Feature flags for the tier
 */
export const getTierLimits = (tier: string): FeatureFlags => {
  if (!tier || !TIER_LIMITS[tier]) {
    console.warn(`Invalid tier: ${tier}, falling back to free tier`);
    return TIER_LIMITS.free;
  }
  
  return TIER_LIMITS[tier];
};

/**
 * Check if a tier has unlimited access for a specific feature
 * 
 * @param tier - Subscription tier name
 * @param feature - Feature to check
 * @returns True if unlimited, false otherwise
 */
export const isUnlimited = (tier: string, feature: keyof FeatureFlags): boolean => {
  const limits = getTierLimits(tier);
  return limits[feature] === -1;
};

/**
 * Get display value for a feature limit
 * 
 * @param tier - Subscription tier name
 * @param feature - Feature to get display value for
 * @returns Display string (∞ for unlimited, number otherwise)
 */
export const getDisplayLimit = (tier: string, feature: keyof FeatureFlags): string => {
  const limits = getTierLimits(tier);
  const value = limits[feature];
  return value === -1 ? '∞' : value.toString();
};
