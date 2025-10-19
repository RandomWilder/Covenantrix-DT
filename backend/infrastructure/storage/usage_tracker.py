"""
Usage Tracking Storage
Tracks query and document usage for subscription limits
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from core.exceptions import StorageError

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Tracks usage statistics for subscription limits
    Stores query counts (daily/monthly) and document counts
    """
    
    def __init__(self, working_dir: Path):
        """
        Initialize usage tracker
        
        Args:
            working_dir: Storage directory path
        """
        self.storage_path = working_dir / "usage_tracking.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage if not exists
        if not self.storage_path.exists():
            self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize usage tracking storage file"""
        from core.config import get_settings
        settings = get_settings()        
        default_data = {
            "version": "1.2",
            "license": {
                "current_tier": "trial",
                "tier_history": [],
                "validation": {
                    "last_validated": None,
                    "next_validation": None,
                    "last_online_check": None
                }
            },
            "usage": {
                "queries": {
                    "monthly": {
                        "count": 0,
                        "reset_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                        "history": [],
                        "period_start": datetime.utcnow().isoformat(),
                        "tier_at_period_start": "trial"
                    },
                    "daily": {
                        "count": 0,
                        "reset_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                        "history": [],
                        "period_start": datetime.utcnow().isoformat(),
                        "tier_at_period_start": "trial"
                    }
                },
                "documents": {
                    "total_count": 0,
                    "current_visible": 0,
                    "upload_history": []
                },
                "enforcement": {
                    "violations": [],
                    "grace_periods": {
                        "query_overage_remaining": 10,
                        "last_grace_reset": datetime.utcnow().isoformat()
                    }
                },
                "features": {
                    "advanced_search_used": False,
                    "export_used": False,
                    "api_access_used": False,
                    "last_feature_audit": datetime.utcnow().isoformat()
                }
            },
            "analytics": {
                "tier_upgrade_signals": {
                    "limit_hits_last_30_days": 0,
                    "avg_queries_per_day": 0.0,
                    "trending_up": False
                }
            },
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "schema_version": "1.2"
            }
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Initialized usage tracking storage at {self.storage_path}")
    
    def _load_data(self) -> Dict[str, Any]:
        """Load usage data from storage"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Check if migration is needed
                if data.get("version", "1.0") != "1.2":
                    data = self._migrate_schema(data)
                return data
        except Exception as e:
            logger.error(f"Failed to load usage data: {e}")
            raise StorageError(f"Failed to load usage tracking data: {str(e)}")
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save usage data to storage"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
            raise StorageError(f"Failed to save usage tracking data: {str(e)}")
    
    def reset_if_expired(self) -> None:
        """Check and reset monthly/daily counters if expired"""
        data = self._load_data()
        usage = data["usage"]
        now = datetime.utcnow()
        
        # Check monthly reset
        monthly_reset = datetime.fromisoformat(usage["queries"]["monthly"]["reset_date"])
        if now >= monthly_reset:
            logger.info("Resetting monthly query counter")
            usage["queries"]["monthly"]["count"] = 0
            usage["queries"]["monthly"]["reset_date"] = (now + timedelta(days=30)).isoformat()
            usage["queries"]["monthly"]["history"] = []
        
        # Check daily reset
        daily_reset = datetime.fromisoformat(usage["queries"]["daily"]["reset_date"])
        if now >= daily_reset:
            logger.info("Resetting daily query counter")
            usage["queries"]["daily"]["count"] = 0
            usage["queries"]["daily"]["reset_date"] = (now + timedelta(days=1)).isoformat()
            usage["queries"]["daily"]["history"] = []
        
        self._save_data(data)
    
    async def record_query(
        self, 
        tier: str, 
        session_id: Optional[str] = None,  # Deprecated, kept for backward compatibility
        query_type: Optional[str] = None,
        success: bool = True,
        tokens_used: Optional[int] = None
    ) -> bool:
        """
        Record a query execution
        
        Args:
            tier: Current subscription tier
            session_id: Session identifier (DEPRECATED - kept for backward compatibility)
            query_type: Type of query (optional)
            success: Whether query was successful (optional)
            tokens_used: Number of tokens used (optional)
            
        Returns:
            True if query was recorded, False if limit would be exceeded
        """
        # Log deprecation warning if session_id is provided
        if session_id is not None:
            logger.warning("session_id parameter is deprecated in record_query(). Session tracking moved to application level.")
        # Reset counters if needed
        self.reset_if_expired()
        
        data = self._load_data()
        usage = data["usage"]
        
        # Increment counters
        usage["queries"]["monthly"]["count"] += 1
        usage["queries"]["daily"]["count"] += 1
        
        # Add to history with enhanced fields
        timestamp = datetime.utcnow().isoformat()
        history_entry = {
            "timestamp": timestamp, 
            "tier": tier,
            "session_id": session_id,
            "query_type": query_type,
            "success": success,
            "tokens_used": tokens_used
        }
        usage["queries"]["monthly"]["history"].append(history_entry)
        usage["queries"]["daily"]["history"].append(history_entry)
        
        # Note: Session tracking removed - session_id parameter is deprecated
        
        data["metadata"]["last_updated"] = timestamp
        self._save_data(data)
        logger.debug(f"Recorded query for tier {tier}")
        return True
    
    async def get_remaining_queries(self, tier: str, tier_limits: Dict[str, int]) -> Dict[str, Any]:
        """
        Get remaining query quotas
        
        Args:
            tier: Current subscription tier
            tier_limits: Tier limits configuration
            
        Returns:
            Dictionary with remaining counts and reset dates
        """
        # Reset counters if needed
        self.reset_if_expired()
        
        data = self._load_data()
        usage = data["usage"]
        
        monthly_limit = tier_limits.get("max_queries_monthly", -1)
        daily_limit = tier_limits.get("max_queries_daily", -1)
        
        monthly_used = usage["queries"]["monthly"]["count"]
        daily_used = usage["queries"]["daily"]["count"]
        
        return {
            "monthly_remaining": monthly_limit - monthly_used if monthly_limit != -1 else -1,
            "daily_remaining": daily_limit - daily_used if daily_limit != -1 else -1,
            "monthly_used": monthly_used,
            "daily_used": daily_used,
            "reset_dates": {
                "monthly": usage["queries"]["monthly"]["reset_date"],
                "daily": usage["queries"]["daily"]["reset_date"]
            }
        }
    
    async def check_query_limit(self, tier_limits: Dict[str, int]) -> tuple[bool, Optional[str]]:
        """
        Check if query is allowed under current limits
        
        Args:
            tier_limits: Tier limits configuration
            
        Returns:
            Tuple of (allowed, reason if not allowed)
        """
        # Reset counters if needed
        self.reset_if_expired()
        
        data = self._load_data()
        usage = data["usage"]
        
        monthly_limit = tier_limits.get("max_queries_monthly", -1)
        daily_limit = tier_limits.get("max_queries_daily", -1)
        
        # Check monthly limit
        if monthly_limit != -1:
            if usage["queries"]["monthly"]["count"] >= monthly_limit:
                return False, f"Monthly query limit of {monthly_limit} reached"
        
        # Check daily limit
        if daily_limit != -1:
            if usage["queries"]["daily"]["count"] >= daily_limit:
                return False, f"Daily query limit of {daily_limit} reached"
        
        return True, None
    
    async def record_document_upload(
        self, 
        doc_id: str, 
        size_mb: float, 
        tier_at_upload: Optional[str] = None,
        format: Optional[str] = None
    ) -> None:
        """
        Record a document upload
        
        Args:
            doc_id: Document ID
            size_mb: Document size in MB
            tier_at_upload: Tier at time of upload (optional)
            format: Document format (optional)
        """
        data = self._load_data()
        usage = data["usage"]
        
        # Increment total count
        usage["documents"]["total_count"] += 1
        usage["documents"]["current_visible"] += 1
        
        # Add to history with enhanced fields
        history_entry = {
            "doc_id": doc_id,
            "size_mb": size_mb,
            "timestamp": datetime.utcnow().isoformat(),
            "tier_at_upload": tier_at_upload,
            "format": format
        }
        usage["documents"]["upload_history"].append(history_entry)
        
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        self._save_data(data)
        logger.debug(f"Recorded document upload: {doc_id} ({size_mb}MB)")
    
    async def record_document_deletion(self, doc_id: str) -> None:
        """
        Record a document deletion
        
        Args:
            doc_id: Document ID
        """
        data = self._load_data()
        usage = data["usage"]
        
        # Decrement visible count
        usage["documents"]["current_visible"] = max(0, usage["documents"]["current_visible"] - 1)
        
        self._save_data(data)
        logger.debug(f"Recorded document deletion: {doc_id}")
    
    async def get_document_count(self) -> int:
        """
        Get current visible document count
        
        Returns:
            Number of currently visible documents
        """
        data = self._load_data()
        return data["usage"]["documents"]["current_visible"]
    
    async def sync_document_count(self, actual_count: int) -> None:
        """
        Synchronize document count with actual registry count
        
        Args:
            actual_count: Actual document count from registry
        """
        data = self._load_data()
        data["usage"]["documents"]["current_visible"] = actual_count
        self._save_data(data)
        logger.info(f"Synced document count to {actual_count}")
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get complete usage statistics
        
        Returns:
            Dictionary of usage stats
        """
        # Reset counters if needed
        self.reset_if_expired()
        
        data = self._load_data()
        return data["usage"]
    
    def _migrate_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate schema from v1.0 to v1.2
        
        Args:
            data: Existing data structure
            
        Returns:
            Migrated data structure
        """
        current_version = data.get("version", "1.0")
        logger.info(f"Migrating usage tracking schema from v{current_version} to v1.2")
        
        # Add missing sections if they don't exist
        if "license" not in data:
            data["license"] = {
                "current_tier": "trial",
                "tier_history": [],
                "validation": {
                    "last_validated": None,
                    "next_validation": None,
                    "last_online_check": None
                }
            }
        
        if "enforcement" not in data.get("usage", {}):
            data["usage"]["enforcement"] = {
                "violations": [],
                "grace_periods": {
                    "query_overage_remaining": 10,
                    "last_grace_reset": datetime.utcnow().isoformat()
                }
            }
        
        if "features" not in data.get("usage", {}):
            data["usage"]["features"] = {
                "advanced_search_used": False,
                "export_used": False,
                "api_access_used": False,
                "last_feature_audit": datetime.utcnow().isoformat()
            }
        
        if "analytics" not in data:
            data["analytics"] = {
                "sessions": [],
                "tier_upgrade_signals": {
                    "limit_hits_last_30_days": 0,
                    "avg_queries_per_day": 0.0,
                    "trending_up": False
                }
            }
        
        if "metadata" not in data:
            data["metadata"] = {
                "last_updated": datetime.utcnow().isoformat(),
                "schema_version": "1.1"
            }
        
        # Add new fields to existing structures
        if "period_start" not in data["usage"]["queries"]["monthly"]:
            data["usage"]["queries"]["monthly"]["period_start"] = datetime.utcnow().isoformat()
            data["usage"]["queries"]["monthly"]["tier_at_period_start"] = "trial"
        
        if "period_start" not in data["usage"]["queries"]["daily"]:
            data["usage"]["queries"]["daily"]["period_start"] = datetime.utcnow().isoformat()
            data["usage"]["queries"]["daily"]["tier_at_period_start"] = "trial"
        
        # Migrate from 1.1 to 1.2: Remove sessions array
        if data.get("version") == "1.1":
            if "sessions" in data.get("analytics", {}):
                # Backup session count for reference
                session_count = len(data["analytics"]["sessions"])
                logger.info(f"Removing {session_count} deprecated session records")
                data["analytics"]["sessions"] = []
        
        # Update version
        data["version"] = "1.2"
        data["metadata"]["schema_version"] = "1.2"
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        # Save migrated data
        self._save_data(data)
        logger.info("Schema migration completed successfully")
        
        return data
    
    # License Section Management Methods
    async def record_tier_change(
        self,
        old_tier: str,
        new_tier: str, 
        reason: str,
        license_key: Optional[str] = None,
        expiration_date: Optional[str] = None
    ) -> None:
        """
        Record a tier change in license history
        
        Args:
            old_tier: Previous tier
            new_tier: New tier
            reason: Reason for change
            license_key: License key if applicable
            expiration_date: Expiration date if applicable
        """
        data = self._load_data()
        now = datetime.utcnow().isoformat()
        
        # Update end_date on last entry if exists
        if data["license"]["tier_history"]:
            data["license"]["tier_history"][-1]["end_date"] = now
        
        # Add new entry
        new_entry = {
            "tier": new_tier,
            "start_date": now,
            "end_date": None,
            "reason": reason
        }
        
        if license_key:
            new_entry["license_key"] = license_key
        if expiration_date:
            new_entry["expiration_date"] = expiration_date
            
        data["license"]["tier_history"].append(new_entry)
        data["license"]["current_tier"] = new_tier
        data["metadata"]["last_updated"] = now
        
        self._save_data(data)
        logger.info(f"Recorded tier change: {old_tier} -> {new_tier} ({reason})")
    
    async def update_validation_status(
        self,
        last_validated: str,
        next_validation: str,
        last_online_check: str
    ) -> None:
        """
        Update license validation status
        
        Args:
            last_validated: Last validation timestamp
            next_validation: Next validation timestamp
            last_online_check: Last online check timestamp
        """
        data = self._load_data()
        data["license"]["validation"]["last_validated"] = last_validated
        data["license"]["validation"]["next_validation"] = next_validation
        data["license"]["validation"]["last_online_check"] = last_online_check
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        self._save_data(data)
        logger.debug("Updated license validation status")
    
    async def get_license_history(self) -> list[Dict[str, Any]]:
        """
        Get complete tier history
        
        Returns:
            List of tier history entries sorted by date
        """
        data = self._load_data()
        return data["license"]["tier_history"]
    
    # Enforcement & Violations Tracking Methods
    async def record_violation(
        self,
        violation_type: str,
        tier: str,
        limit: int,
        attempted: int,
        action_taken: str,
        grace_used: bool = False
    ) -> None:
        """
        Record a violation
        
        Args:
            violation_type: Type of violation
            tier: Current tier
            limit: Limit that was exceeded
            attempted: Amount attempted
            action_taken: Action taken
            grace_used: Whether grace period was used
        """
        data = self._load_data()
        now = datetime.utcnow().isoformat()
        
        violation_entry = {
            "timestamp": now,
            "type": violation_type,
            "tier": tier,
            "limit": limit,
            "attempted": attempted,
            "action_taken": action_taken,
            "grace_used": grace_used
        }
        
        data["usage"]["enforcement"]["violations"].append(violation_entry)
        data["metadata"]["last_updated"] = now
        
        self._save_data(data)
        logger.warning(f"Recorded violation: {violation_type} (tier: {tier}, limit: {limit}, attempted: {attempted})")
    
    async def update_grace_periods(
        self,
        query_overage_remaining: int,
        last_grace_reset: str
    ) -> None:
        """
        Update grace period allowances
        
        Args:
            query_overage_remaining: Remaining grace allowances
            last_grace_reset: Last grace reset timestamp
        """
        data = self._load_data()
        data["usage"]["enforcement"]["grace_periods"]["query_overage_remaining"] = query_overage_remaining
        data["usage"]["enforcement"]["grace_periods"]["last_grace_reset"] = last_grace_reset
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        self._save_data(data)
        logger.debug(f"Updated grace periods: {query_overage_remaining} remaining")
    
    async def get_violation_history(
        self,
        violation_type: Optional[str] = None,
        days: int = 30
    ) -> list[Dict[str, Any]]:
        """
        Get violation history
        
        Args:
            violation_type: Filter by violation type
            days: Number of days to look back
            
        Returns:
            List of violations
        """
        data = self._load_data()
        violations = data["usage"]["enforcement"]["violations"]
        
        # Filter by time range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        filtered_violations = []
        
        for violation in violations:
            violation_date = datetime.fromisoformat(violation["timestamp"])
            if violation_date >= cutoff_date:
                if violation_type is None or violation["type"] == violation_type:
                    filtered_violations.append(violation)
        
        return filtered_violations
    
    # Feature Usage Tracking Methods
    async def record_feature_usage(self, feature_name: str) -> None:
        """
        Record feature usage
        
        Args:
            feature_name: Name of feature used
        """
        data = self._load_data()
        now = datetime.utcnow().isoformat()
        
        # Update feature flag
        feature_key = f"{feature_name}_used"
        if feature_key in data["usage"]["features"]:
            data["usage"]["features"][feature_key] = True
        
        data["usage"]["features"]["last_feature_audit"] = now
        data["metadata"]["last_updated"] = now
        
        self._save_data(data)
        logger.debug(f"Recorded feature usage: {feature_name}")
    
    async def get_feature_usage_stats(self) -> Dict[str, bool]:
        """
        Get feature usage statistics
        
        Returns:
            Dictionary of feature usage flags
        """
        data = self._load_data()
        features = data["usage"]["features"]
        
        return {
            "advanced_search_used": features.get("advanced_search_used", False),
            "export_used": features.get("export_used", False),
            "api_access_used": features.get("api_access_used", False)
        }
    
    # Session-Based Analytics Methods
    async def start_session(self, session_id: str, tier: str) -> None:
        """
        DEPRECATED: Session tracking moved to application level
        
        Start a new session
        
        Args:
            session_id: Unique session identifier
            tier: Current tier
        """
        logger.warning("start_session() is deprecated. Session tracking moved to application level.")
        data = self._load_data()
        now = datetime.utcnow().isoformat()
        
        session_entry = {
            "session_id": session_id,
            "start_time": now,
            "end_time": None,
            "tier": tier,
            "queries_count": 0
        }
        
        data["analytics"]["sessions"].append(session_entry)
        data["metadata"]["last_updated"] = now
        
        self._save_data(data)
        logger.debug(f"Started session: {session_id} (tier: {tier})")
    
    async def end_session(self, session_id: str) -> None:
        """
        DEPRECATED: Session tracking moved to application level
        
        End a session
        
        Args:
            session_id: Session identifier
        """
        logger.warning("end_session() is deprecated. Session tracking moved to application level.")
        data = self._load_data()
        now = datetime.utcnow().isoformat()
        
        # Find and update session
        for session in data["analytics"]["sessions"]:
            if session["session_id"] == session_id and session["end_time"] is None:
                session["end_time"] = now
                break
        
        data["metadata"]["last_updated"] = now
        self._save_data(data)
        logger.debug(f"Ended session: {session_id}")
    
    async def increment_session_queries(self, session_id: str) -> None:
        """
        DEPRECATED: Session tracking moved to application level
        
        Increment query count for session
        
        Args:
            session_id: Session identifier
        """
        logger.warning("increment_session_queries() is deprecated. Session tracking moved to application level.")
        data = self._load_data()
        
        # Find and update session
        for session in data["analytics"]["sessions"]:
            if session["session_id"] == session_id and session["end_time"] is None:
                session["queries_count"] += 1
                break
        
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        self._save_data(data)
    
    async def get_session_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        DEPRECATED: Session tracking moved to application level
        
        Get session analytics (returns zero values for backward compatibility)
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Session analytics data (zero values)
        """
        logger.warning("get_session_analytics() is deprecated. Session tracking moved to application level.")
        
        # Return zero values for backward compatibility
        return {
            "sessions_count": 0,
            "avg_queries_per_session": 0.0,
            "avg_session_duration_minutes": 0.0
        }
    
    async def get_conversation_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get conversation-based analytics
        Uses chat storage to calculate real conversation metrics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics based on actual conversations
        """
        try:
            from core.dependencies import get_chat_service
            from datetime import datetime, timedelta
            
            # Get chat service
            chat_service = get_chat_service()
            conversations = await chat_service.list_conversations()
            
            # Filter conversations from last N days
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_conversations = [
                c for c in conversations 
                if c.updated_at >= cutoff_date
            ]
            
            # Calculate metrics
            conversations_count = len(recent_conversations)
            
            if conversations_count == 0:
                return {
                    "conversations_count": 0,
                    "avg_queries_per_conversation": 0.0,
                    "total_queries": 0,
                    "active_conversations": 0
                }
            
            # Count user messages (queries) across all conversations
            total_queries = 0
            active_conversations = 0
            
            for conversation in recent_conversations:
                user_messages = [msg for msg in conversation.messages if msg.role == "user"]
                query_count = len(user_messages)
                total_queries += query_count
                
                if query_count > 0:
                    active_conversations += 1
            
            avg_queries_per_conversation = total_queries / conversations_count if conversations_count > 0 else 0.0
            
            return {
                "conversations_count": conversations_count,
                "avg_queries_per_conversation": avg_queries_per_conversation,
                "total_queries": total_queries,
                "active_conversations": active_conversations
            }
            
        except Exception as e:
            logger.error(f"Error calculating conversation analytics: {e}")
            return {
                "conversations_count": 0,
                "avg_queries_per_conversation": 0.0,
                "total_queries": 0,
                "active_conversations": 0
            }
    
    # Upgrade Signals & Analytics Methods
    async def calculate_upgrade_signals(self) -> Dict[str, Any]:
        """
        Calculate upgrade signals
        
        Returns:
            Dictionary of upgrade signals
        """
        data = self._load_data()
        
        # Get violations from last 30 days
        violations = await self.get_violation_history(days=30)
        limit_hits = len([v for v in violations if v["action_taken"] == "blocked"])
        
        # Calculate average queries per day
        query_history = data["usage"]["queries"]["monthly"]["history"]
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        recent_queries = [q for q in query_history 
                         if datetime.fromisoformat(q["timestamp"]) >= cutoff_date]
        
        avg_queries_per_day = len(recent_queries) / 30.0
        
        # Calculate trending up (compare last 7 days to previous 7 days)
        now = datetime.utcnow()
        last_7_days = [q for q in recent_queries 
                      if datetime.fromisoformat(q["timestamp"]) >= now - timedelta(days=7)]
        previous_7_days = [q for q in recent_queries 
                          if now - timedelta(days=14) <= datetime.fromisoformat(q["timestamp"]) < now - timedelta(days=7)]
        
        current_avg = len(last_7_days) / 7.0
        previous_avg = len(previous_7_days) / 7.0
        trending_up = current_avg > previous_avg
        
        signals = {
            "limit_hits_last_30_days": limit_hits,
            "avg_queries_per_day": avg_queries_per_day,
            "trending_up": trending_up
        }
        
        # Update stored signals
        data["analytics"]["tier_upgrade_signals"] = signals
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        self._save_data(data)
        
        return signals
    
    async def get_complete_analytics(self) -> Dict[str, Any]:
        """
        Get complete analytics data
        
        Returns:
            Complete analytics dictionary
        """
        data = self._load_data()
        
        # Calculate upgrade signals
        upgrade_signals = await self.calculate_upgrade_signals()
        
        # Get session analytics
        session_analytics = await self.get_session_analytics()
        
        # Get violation history
        violations = await self.get_violation_history()
        
        # Get feature usage
        feature_usage = await self.get_feature_usage_stats()
        
        return {
            "tier_history": data["license"]["tier_history"],
            "violations": violations,
            "feature_usage": feature_usage,
            "upgrade_signals": upgrade_signals,
            "session_analytics": session_analytics,
            "usage_stats": data["usage"]
        }

