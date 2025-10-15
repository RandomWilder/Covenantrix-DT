"""
Subscription Service
Core business logic for subscription management, tier transitions, and limit enforcement
"""
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from api.schemas.settings import SubscriptionSettings, FeatureFlags, UserSettings
from infrastructure.storage.user_settings_storage import UserSettingsStorage
from infrastructure.storage.usage_tracker import UsageTracker
from domain.subscription.license_validator import LicenseValidator
from domain.subscription.tier_config import TIER_LIMITS, get_tier_features
from domain.notifications.service import NotificationService

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Subscription management service
    Handles tier activation, expiry checking, limit enforcement, and transitions
    """
    
    def __init__(
        self,
        settings_storage: UserSettingsStorage,
        usage_tracker: UsageTracker,
        license_validator: LicenseValidator,
        notification_service: NotificationService
    ):
        """
        Initialize subscription service
        
        Args:
            settings_storage: User settings storage instance
            usage_tracker: Usage tracking storage instance
            license_validator: JWT license validator instance
            notification_service: Notification service instance
        """
        self.settings_storage = settings_storage
        self.usage_tracker = usage_tracker
        self.license_validator = license_validator
        self.notification_service = notification_service
    
    def get_current_subscription(self) -> SubscriptionSettings:
        """
        Get current subscription settings (synchronous version for dependencies)
        
        Returns:
            Current subscription settings
        """
        import asyncio
        try:
            # Get event loop or create new one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run async method
            settings = loop.run_until_complete(self.settings_storage.load_settings())
            return settings.subscription
        except Exception as e:
            logger.error(f"Failed to load subscription: {e}")
            # Return default trial subscription
            return SubscriptionSettings()
    
    async def get_current_subscription_async(self) -> SubscriptionSettings:
        """
        Get current subscription settings (async version)
        
        Returns:
            Current subscription settings
        """
        settings = await self.settings_storage.load_settings()
        return settings.subscription
    
    async def activate_license(self, jwt_token: str) -> SubscriptionSettings:
        """
        Activate a license key (JWT token)
        
        Args:
            jwt_token: JWT license token
            
        Returns:
            Updated subscription settings
            
        Raises:
            ValueError: If license validation fails
        """
        try:
            # Validate JWT
            payload = self.license_validator.validate_jwt(jwt_token)
            
            # Extract subscription info
            new_subscription = self.license_validator.extract_tier_info(payload)
            
            # Store the JWT token
            new_subscription.license_key = jwt_token
            
            # Load current settings
            settings = await self.settings_storage.load_settings()
            old_tier = settings.subscription.tier
            new_tier = new_subscription.tier
            
            # Update subscription
            settings.subscription = new_subscription
            await self.settings_storage.save_settings(settings)
            
            # Handle tier transition
            await self.transition_tier(new_tier, reason=f"license_activated_from_{old_tier}")
            
            logger.info(f"License activated successfully: {old_tier} -> {new_tier}")
            return new_subscription
            
        except Exception as e:
            logger.error(f"License activation failed: {e}")
            raise
    
    async def check_tier_expiry(self) -> bool:
        """
        Check if current tier has expired and handle transitions
        Called on backend startup
        
        Returns:
            True if tier changed, False otherwise
        """
        settings = await self.settings_storage.load_settings()
        subscription = settings.subscription
        now = datetime.utcnow()
        changed = False
        
        # CRITICAL: Sync feature flags with tier config on every startup
        # This ensures stored features always match current tier configuration
        current_features = subscription.features.model_dump()
        expected_features = get_tier_features(subscription.tier)
        
        if current_features != expected_features:
            logger.info(f"Feature flags out of sync for {subscription.tier} tier, updating...")
            settings.subscription.features = FeatureFlags(**expected_features)
            await self.settings_storage.save_settings(settings)
            logger.info(f"Feature flags synced: {expected_features}")
            changed = True
        
        # Initialize trial if first launch
        if subscription.tier == "trial" and subscription.trial_started_at is None:
            logger.info("Trial tier detected without start date, calling _initialize_trial()")
            await self._initialize_trial()
            changed = True
        else:
            logger.debug(f"Trial status: tier={subscription.tier}, started_at={subscription.trial_started_at}")
        
        # Check trial expiry
        if subscription.tier == "trial" and subscription.trial_expires_at:
            expiry = datetime.fromisoformat(subscription.trial_expires_at)
            if now >= expiry:
                logger.info("Trial period expired, transitioning to FREE tier")
                await self.transition_tier("free", reason="trial_expired")
                changed = True
        
        # Check grace period expiry
        if subscription.tier == "paid_limited" and subscription.grace_period_expires_at:
            expiry = datetime.fromisoformat(subscription.grace_period_expires_at)
            if now >= expiry:
                logger.warning("Grace period expired, transitioning to FREE tier")
                await self.transition_tier("free", reason="grace_period_expired")
                changed = True
        
        return changed
    
    async def transition_tier(self, new_tier: str, reason: str) -> None:
        """
        Handle tier transitions with proper cleanup and notifications
        
        Args:
            new_tier: Target tier
            reason: Reason for transition
        """
        settings = await self.settings_storage.load_settings()
        old_tier = settings.subscription.tier
        
        if old_tier == new_tier:
            logger.info(f"Already on tier {new_tier}, no transition needed")
            return
        
        logger.info(f"Tier transition: {old_tier} -> {new_tier} (reason: {reason})")
        
        # Update tier and features
        settings.subscription.tier = new_tier
        settings.subscription.features = FeatureFlags(**get_tier_features(new_tier))
        settings.subscription.last_tier_change = datetime.utcnow().isoformat()
        
        # Handle specific transitions
        if old_tier == "trial" and new_tier == "free":
            # Force custom API key mode
            settings.api_keys.mode = "custom"
            await self.notification_service.create_notification(
                type="warning",
                source="subscription",
                title="Trial Ended",
                summary="Your 7-day trial has ended. Please configure your own API keys in Settings to continue using the app."
            )
        
        elif old_tier == "paid" and new_tier == "paid_limited":
            # Start grace period
            now = datetime.utcnow()
            settings.subscription.grace_period_started_at = now.isoformat()
            settings.subscription.grace_period_expires_at = (now + timedelta(days=7)).isoformat()
            
            # Force custom API key mode
            settings.api_keys.mode = "custom"
            
            await self.notification_service.create_notification(
                type="error",
                source="subscription",
                title="Payment Issue Detected",
                summary="You have 7 days to resolve payment. Access limited to first 3 documents."
            )
        
        elif old_tier == "paid_limited" and new_tier == "free":
            # End grace period, delete hidden documents
            settings.subscription.grace_period_started_at = None
            settings.subscription.grace_period_expires_at = None
            
            await self._delete_hidden_documents()
            
            await self.notification_service.create_notification(
                type="info",
                source="subscription",
                title="Downgraded to Free Tier",
                summary="Documents beyond the first 3 have been permanently deleted."
            )
        
        elif old_tier == "paid_limited" and new_tier == "paid":
            # Restore full access
            settings.subscription.grace_period_started_at = None
            settings.subscription.grace_period_expires_at = None
            
            await self.notification_service.create_notification(
                type="success",
                source="subscription",
                title="Subscription Restored",
                summary="Full access restored. All documents are now visible."
            )
        
        elif new_tier == "free" and old_tier in ["trial", "free"]:
            # Force custom mode for free tier
            settings.api_keys.mode = "custom"
        
        # Save updated settings
        await self.settings_storage.save_settings(settings)
        
        logger.info(f"Tier transition complete: {old_tier} -> {new_tier}")
    
    async def check_upload_allowed(self) -> Tuple[bool, str]:
        """
        Check if document upload is allowed under current limits
        
        Returns:
            Tuple of (allowed, reason if not allowed)
        """
        subscription = await self.get_current_subscription_async()
        max_documents = subscription.features.max_documents
        
        # Unlimited documents
        if max_documents == -1:
            return True, ""
        
        # Check current document count
        doc_count = await self.usage_tracker.get_document_count()
        
        if doc_count >= max_documents:
            return False, f"Document limit of {max_documents} reached for {subscription.tier} tier"
        
        return True, ""
    
    async def check_query_allowed(self) -> Tuple[bool, str]:
        """
        Check if query is allowed under current limits
        
        Returns:
            Tuple of (allowed, reason if not allowed)
        """
        subscription = await self.get_current_subscription_async()
        tier_limits = {
            "max_queries_monthly": subscription.features.max_queries_monthly,
            "max_queries_daily": subscription.features.max_queries_daily
        }
        
        return await self.usage_tracker.check_query_limit(tier_limits)
    
    async def record_query(self) -> None:
        """Record a query execution"""
        subscription = await self.get_current_subscription_async()
        await self.usage_tracker.record_query(subscription.tier)
    
    async def record_document_upload(self, filename: str, size_mb: float) -> None:
        """
        Record a document upload
        
        Args:
            filename: Document filename (used as doc_id for now)
            size_mb: Document size in MB
        """
        await self.usage_tracker.record_document_upload(filename, size_mb)
    
    def get_current_limits(self) -> Dict[str, Any]:
        """
        Get feature flags for current tier
        
        Returns:
            Feature flags dictionary
        """
        subscription = self.get_current_subscription()
        return subscription.features.model_dump()
    
    async def get_remaining_queries(self) -> Dict[str, Any]:
        """
        Get remaining query quotas
        
        Returns:
            Dictionary with remaining counts and reset dates
        """
        subscription = await self.get_current_subscription_async()
        tier_limits = {
            "max_queries_monthly": subscription.features.max_queries_monthly,
            "max_queries_daily": subscription.features.max_queries_daily
        }
        
        return await self.usage_tracker.get_remaining_queries(subscription.tier, tier_limits)
    
    async def _initialize_trial(self) -> None:
        """Initialize trial period on first launch"""
        logger.info("_initialize_trial() called - checking if trial needs initialization")
        settings = await self.settings_storage.load_settings()
        
        if settings.subscription.trial_started_at is not None:
            logger.info("Trial already initialized, skipping")
            return
        
        now = datetime.utcnow()
        trial_duration = TIER_LIMITS["trial"]["duration_days"]
        
        settings.subscription.tier = "trial"
        settings.subscription.trial_started_at = now.isoformat()
        settings.subscription.trial_expires_at = (now + timedelta(days=trial_duration)).isoformat()
        settings.subscription.features = FeatureFlags(**get_tier_features("trial"))
        
        await self.settings_storage.save_settings(settings)
        
        logger.info(f"Trial period initialized: {trial_duration} days from {now.isoformat()}")
        
        # Create welcome notification
        await self.notification_service.create_notification(
            type="info",
            source="subscription",
            title="Welcome to Covenantrix!",
            summary=f"Your {trial_duration}-day trial has started. Enjoy unlimited queries with default API keys."
        )
    
    async def _delete_hidden_documents(self) -> None:
        """Delete documents beyond first 3 (called on paid_limited -> free transition)"""
        try:
            from core.dependencies import get_document_service
            from infrastructure.storage.document_registry import DocumentRegistry
            
            # Get document service
            doc_registry = DocumentRegistry()
            all_docs = await doc_registry.list_documents(include_deleted=False)
            
            # Sort by creation date and get docs to delete
            docs_sorted = sorted(all_docs, key=lambda d: d.created_at)
            docs_to_delete = docs_sorted[3:]  # Everything after first 3
            
            # Delete documents
            for doc in docs_to_delete:
                try:
                    await doc_registry.delete_document(doc.id, hard_delete=True)
                    await self.usage_tracker.record_document_deletion(doc.id)
                    logger.info(f"Deleted hidden document: {doc.id} ({doc.metadata.filename})")
                except Exception as e:
                    logger.error(f"Failed to delete document {doc.id}: {e}")
            
            logger.info(f"Deleted {len(docs_to_delete)} hidden documents")
            
        except Exception as e:
            logger.error(f"Failed to delete hidden documents: {e}")
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get complete usage statistics
        
        Returns:
            Dictionary with usage stats and subscription info
        """
        subscription = await self.get_current_subscription_async()
        usage_data = await self.usage_tracker.get_usage_stats()
        remaining = await self.get_remaining_queries()
        
        return {
            "tier": subscription.tier,
            "documents_uploaded": usage_data["documents"]["current_visible"],
            "queries_this_month": usage_data["queries"]["monthly"]["count"],
            "queries_today": usage_data["queries"]["daily"]["count"],
            "monthly_remaining": remaining["monthly_remaining"],
            "daily_remaining": remaining["daily_remaining"],
            "monthly_reset_date": remaining["reset_dates"]["monthly"],
            "daily_reset_date": remaining["reset_dates"]["daily"]
        }

