"""
Subscription API Routes
Endpoints for subscription management and license activation
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from api.schemas.settings import FeatureFlags
from domain.subscription.service import SubscriptionService
from core.dependencies import get_subscription_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/subscription",
    tags=["subscription"]
)


# Request/Response Models
class SubscriptionStatusResponse(BaseModel):
    """Subscription status response"""
    tier: str
    features: FeatureFlags
    trial_started_at: Optional[str] = None
    trial_expires_at: Optional[str] = None
    grace_period_started_at: Optional[str] = None
    grace_period_expires_at: Optional[str] = None
    usage: Dict[str, Any]
    last_tier_change: Optional[str] = None


class LicenseActivationRequest(BaseModel):
    """License activation request"""
    license_key: str = Field(..., description="JWT license token")


class LicenseActivationResponse(BaseModel):
    """License activation response"""
    success: bool
    new_tier: str
    message: str
    features: Optional[FeatureFlags] = None


class UsageStatsResponse(BaseModel):
    """Usage statistics response"""
    tier: str
    documents_uploaded: int
    queries_this_month: int
    queries_today: int
    monthly_remaining: int
    daily_remaining: int
    monthly_reset_date: str
    daily_reset_date: str


class ValidateLicenseResponse(BaseModel):
    """License validation response"""
    valid: bool
    tier: Optional[str] = None
    expiry: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TierStatusResponse(BaseModel):
    """Tier status response with warnings and upgrade prompts"""
    tier: str
    features: Dict[str, Any]
    usage_stats: Dict[str, Any]
    remaining: Dict[str, Any]
    usage_percentages: Dict[str, float]
    warnings: list[str]
    upgrade_prompts: list[str]
    trial_info: Dict[str, Any]
    grace_period_info: Dict[str, Any]


class AnalyticsResponse(BaseModel):
    """Analytics response with complete usage data"""
    tier_history: list[Dict[str, Any]]
    violations: list[Dict[str, Any]]
    feature_usage: Dict[str, bool]
    upgrade_signals: Dict[str, Any]
    conversations_last_30_days: int
    avg_queries_per_conversation: float
    
    # Deprecated aliases for backward compatibility
    @property
    def sessions_last_30_days(self) -> int:
        """Deprecated: Use conversations_last_30_days instead"""
        return self.conversations_last_30_days
    
    @property
    def avg_queries_per_session(self) -> float:
        """Deprecated: Use avg_queries_per_conversation instead"""
        return self.avg_queries_per_conversation


class LicenseHistoryResponse(BaseModel):
    """License history response"""
    tier_history: list[Dict[str, Any]]


class UpgradeRecommendationsResponse(BaseModel):
    """Upgrade recommendations response"""
    recommendations: list[Dict[str, Any]]
    signals: Dict[str, Any]
    violation_count: int
    feature_usage: Dict[str, bool]


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Get current subscription status
    
    Returns subscription tier, features, and usage statistics
    """
    try:
        subscription = await subscription_service.get_current_subscription_async()
        usage_stats = await subscription_service.get_usage_stats()
        
        return SubscriptionStatusResponse(
            tier=subscription.tier,
            features=subscription.get_features(),  # Use computed features
            trial_started_at=subscription.trial_started_at,
            trial_expires_at=subscription.trial_expires_at,
            grace_period_started_at=subscription.grace_period_started_at,
            grace_period_expires_at=subscription.grace_period_expires_at,
            usage=usage_stats,
            last_tier_change=subscription.last_tier_change
        )
    except Exception as e:
        logger.error(f"Failed to get subscription status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subscription status: {str(e)}"
        )


@router.post("/activate", response_model=LicenseActivationResponse)
async def activate_license(
    request: LicenseActivationRequest,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Activate a license key
    
    Validates JWT token and updates subscription tier
    """
    try:
        new_subscription = await subscription_service.activate_license(request.license_key)
        
        return LicenseActivationResponse(
            success=True,
            new_tier=new_subscription.tier,
            message=f"License activated successfully. Welcome to {new_subscription.tier} tier!",
            features=new_subscription.get_features()  # Use computed features
        )
        
    except ValueError as e:
        # License validation error
        logger.warning(f"License activation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_license",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"License activation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate license: {str(e)}"
        )


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Get usage statistics
    
    Returns remaining quotas and usage counts
    """
    try:
        stats = await subscription_service.get_usage_stats()
        
        return UsageStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage statistics: {str(e)}"
        )


@router.get("/tier-status", response_model=TierStatusResponse)
async def get_tier_status(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Get comprehensive tier status with warnings and upgrade prompts
    
    Returns tier information, usage statistics, warnings, and upgrade recommendations
    """
    try:
        status = await subscription_service.get_tier_status()
        return TierStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Failed to get tier status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tier status: {str(e)}"
        )


@router.post("/validate-license", response_model=ValidateLicenseResponse)
async def validate_license(
    request: LicenseActivationRequest,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Validate a license key without activating it
    
    Used for testing and validation purposes
    """
    try:
        # Validate JWT
        payload = subscription_service.license_validator.validate_jwt(request.license_key)
        
        # Extract expiry
        from datetime import datetime
        expiry_ms = payload["expiry"]
        expiry_dt = datetime.fromtimestamp(expiry_ms / 1000)
        
        # Compute features from tier instead of JWT
        from domain.subscription.tier_config import get_tier_features
        computed_features = get_tier_features(payload["tier"])
        
        return ValidateLicenseResponse(
            valid=True,
            tier=payload["tier"],
            expiry=expiry_dt.isoformat(),
            features=computed_features
        )
        
    except ValueError as e:
        return ValidateLicenseResponse(
            valid=False,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"License validation error: {e}")
        return ValidateLicenseResponse(
            valid=False,
            error=f"Validation error: {str(e)}"
        )


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_subscription_analytics(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Get complete subscription analytics
    
    Returns comprehensive analytics data including tier history, violations, 
    feature usage, upgrade signals, and conversation analytics
    """
    try:
        analytics = await subscription_service.usage_tracker.get_complete_analytics()
        
        # Track API access feature usage
        await subscription_service.usage_tracker.record_feature_usage("api_access")
        
        # Get conversation-based analytics using the new method
        conversation_analytics = await subscription_service.usage_tracker.get_conversation_analytics(days=30)
        
        return AnalyticsResponse(
            tier_history=analytics.get("tier_history", []),
            violations=analytics.get("violations", []),
            feature_usage=analytics.get("feature_usage", {}),
            upgrade_signals=analytics.get("upgrade_signals", {}),
            conversations_last_30_days=conversation_analytics.get("conversations_count", 0),
            avg_queries_per_conversation=conversation_analytics.get("avg_queries_per_conversation", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


@router.get("/license-history", response_model=LicenseHistoryResponse)
async def get_license_history(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Get complete license/tier history
    
    Returns chronological history of all tier transitions
    """
    try:
        tier_history = await subscription_service.usage_tracker.get_license_history()
        
        # Track API access feature usage
        await subscription_service.usage_tracker.record_feature_usage("api_access")
        
        return LicenseHistoryResponse(tier_history=tier_history)
        
    except Exception as e:
        logger.error(f"Failed to get license history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve license history: {str(e)}"
        )


@router.get("/upgrade-recommendations", response_model=UpgradeRecommendationsResponse)
async def get_upgrade_recommendations(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Get personalized upgrade recommendations
    
    Returns upgrade recommendations based on usage patterns and signals
    """
    try:
        recommendations = await subscription_service.get_upgrade_recommendations()
        
        return UpgradeRecommendationsResponse(**recommendations)
        
    except Exception as e:
        logger.error(f"Failed to get upgrade recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve upgrade recommendations: {str(e)}"
        )

