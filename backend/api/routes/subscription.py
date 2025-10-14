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
            features=subscription.features,
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
            features=new_subscription.features
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
        
        return ValidateLicenseResponse(
            valid=True,
            tier=payload["tier"],
            expiry=expiry_dt.isoformat(),
            features=payload["features"]
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

