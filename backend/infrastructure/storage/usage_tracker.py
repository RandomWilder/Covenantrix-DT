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
        default_data = {
            "version": "1.0",
            "usage": {
                "queries": {
                    "monthly": {
                        "count": 0,
                        "reset_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                        "history": []
                    },
                    "daily": {
                        "count": 0,
                        "reset_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                        "history": []
                    }
                },
                "documents": {
                    "total_count": 0,
                    "current_visible": 0,
                    "upload_history": []
                }
            }
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Initialized usage tracking storage at {self.storage_path}")
    
    def _load_data(self) -> Dict[str, Any]:
        """Load usage data from storage"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
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
    
    async def record_query(self, tier: str) -> bool:
        """
        Record a query execution
        
        Args:
            tier: Current subscription tier
            
        Returns:
            True if query was recorded, False if limit would be exceeded
        """
        # Reset counters if needed
        self.reset_if_expired()
        
        data = self._load_data()
        usage = data["usage"]
        
        # Increment counters
        usage["queries"]["monthly"]["count"] += 1
        usage["queries"]["daily"]["count"] += 1
        
        # Add to history
        timestamp = datetime.utcnow().isoformat()
        history_entry = {"timestamp": timestamp, "tier": tier}
        usage["queries"]["monthly"]["history"].append(history_entry)
        usage["queries"]["daily"]["history"].append(history_entry)
        
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
    
    async def record_document_upload(self, doc_id: str, size_mb: float) -> None:
        """
        Record a document upload
        
        Args:
            doc_id: Document ID
            size_mb: Document size in MB
        """
        data = self._load_data()
        usage = data["usage"]
        
        # Increment total count
        usage["documents"]["total_count"] += 1
        usage["documents"]["current_visible"] += 1
        
        # Add to history
        history_entry = {
            "doc_id": doc_id,
            "size_mb": size_mb,
            "timestamp": datetime.utcnow().isoformat()
        }
        usage["documents"]["upload_history"].append(history_entry)
        
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

