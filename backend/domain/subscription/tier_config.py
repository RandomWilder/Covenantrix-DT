"""
Subscription Tier Configuration
Defines limits and features for each subscription tier
"""
from typing import Dict, Any

# Tier limits configuration
TIER_LIMITS = {
    "trial": {
        "max_documents": 3,
        "max_doc_size_mb": 10,
        "max_total_storage_mb": 30,
        "max_queries_monthly": -1,  # Unlimited
        "max_queries_daily": -1,    # Unlimited
        "use_default_keys": True,
        "duration_days": 7
    },
    "free": {
        "max_documents": 3,
        "max_doc_size_mb": 10,
        "max_total_storage_mb": 30,
        "max_queries_monthly": 50,
        "max_queries_daily": 20,
        "use_default_keys": False,
        "duration_days": None  # Indefinite
    },
    "paid": {
        "max_documents": -1,        # Unlimited
        "max_doc_size_mb": 100,
        "max_total_storage_mb": -1,  # Unlimited
        "max_queries_monthly": -1,   # Unlimited
        "max_queries_daily": -1,     # Unlimited
        "use_default_keys": True,
        "duration_days": None  # Based on license
    },
    "paid_limited": {
        "max_documents": 3,  # Show only first 3
        "max_doc_size_mb": 10,
        "max_total_storage_mb": 30,
        "max_queries_monthly": 50,
        "max_queries_daily": 20,
        "use_default_keys": False,
        "grace_period_days": 7
    }
}


def get_tier_features(tier: str) -> Dict[str, Any]:
    """
    Extract feature flags from tier config
    
    Args:
        tier: Subscription tier name
        
    Returns:
        Dictionary of feature flags (excluding duration/grace period)
    """
    if tier not in TIER_LIMITS:
        raise ValueError(f"Invalid tier: {tier}. Must be one of: {list(TIER_LIMITS.keys())}")
    
    config = TIER_LIMITS[tier]
    
    # Extract only feature-related fields (exclude metadata like duration_days)
    return {
        "max_documents": config["max_documents"],
        "max_doc_size_mb": config["max_doc_size_mb"],
        "max_total_storage_mb": config["max_total_storage_mb"],
        "max_queries_monthly": config["max_queries_monthly"],
        "max_queries_daily": config["max_queries_daily"],
        "use_default_keys": config["use_default_keys"]
    }

