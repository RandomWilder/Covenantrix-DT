"""
JWT License Validator
Validates JWT-based subscription licenses
"""
import jwt
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from api.schemas.settings import SubscriptionSettings, FeatureFlags

logger = logging.getLogger(__name__)

# Public key for JWT verification (RS256)
# In production, this would be the actual RSA public key
# For now, using a placeholder - this will be replaced with actual public key
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z7thqYjrqOlLYdWpQQE
VlKbhEGh8XB7z5nVnGJK9xXKN9i7IK1uKCq8x9Zx4F3Z7f0YG3qQz8Lx0P2Xq4zZ
-----END PUBLIC KEY-----"""


class LicenseValidator:
    """
    JWT license validator for subscription management
    Validates license tokens and extracts subscription information
    """
    
    def __init__(self, public_key: Optional[str] = None):
        """
        Initialize license validator
        
        Args:
            public_key: Optional RSA public key for JWT verification
        """
        self.public_key = public_key or PUBLIC_KEY
    
    def validate_jwt(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT license token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded JWT payload
            
        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            # Decode JWT with signature verification
            # Support both RS256 (production) and HS256 (development/testing)
            # ALWAYS verify signatures for security
            
            # First, decode header to determine algorithm
            unverified_header = jwt.get_unverified_header(token)
            algorithm = unverified_header.get("alg")
            
            if algorithm == "HS256":
                # Test tokens use HS256 with shared secret
                payload = jwt.decode(
                    token,
                    "test-secret",  # Shared secret for test tokens
                    algorithms=["HS256"],
                    options={"verify_signature": True}
                )
                logger.info("Validated HS256 test token with signature verification")
            elif algorithm == "RS256":
                # Production tokens use RS256 with public key
                payload = jwt.decode(
                    token,
                    self.public_key,
                    algorithms=["RS256"],
                    options={"verify_signature": True}
                )
                logger.info("Validated RS256 production token with signature verification")
            else:
                raise ValueError(f"Unsupported JWT algorithm: {algorithm}")
            
            # Validate required fields
            required_fields = ["tier", "issued", "expiry", "license_id"]
            for field in required_fields:
                if field not in payload:
                    raise ValueError(f"Missing required field in JWT: {field}")
            
            # Check expiry (timestamp in milliseconds)
            expiry_ms = payload["expiry"]
            expiry_dt = datetime.fromtimestamp(expiry_ms / 1000)
            now = datetime.utcnow()
            
            if now >= expiry_dt:
                raise ValueError(f"License expired on {expiry_dt.isoformat()}")
            
            # Validate tier
            valid_tiers = ["trial", "free", "paid", "paid_limited"]
            if payload["tier"] not in valid_tiers:
                raise ValueError(f"Invalid tier: {payload['tier']}")
            
            logger.info(f"Successfully validated license: {payload['license_id'][:8]}... (tier: {payload['tier']})")
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ValueError("License token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid license token: {str(e)}")
        except Exception as e:
            logger.error(f"License validation error: {e}")
            raise ValueError(f"Failed to validate license: {str(e)}")
    
    def extract_tier_info(self, payload: Dict[str, Any]) -> SubscriptionSettings:
        """
        Extract subscription settings from JWT payload
        
        Args:
            payload: Decoded JWT payload
            
        Returns:
            SubscriptionSettings object
        """
        try:
            # Extract expiry as ISO datetime
            expiry_ms = payload["expiry"]
            expiry_dt = datetime.fromtimestamp(expiry_ms / 1000)
            
            # Extract issued timestamp
            issued_ms = payload["issued"]
            issued_dt = datetime.fromtimestamp(issued_ms / 1000)
            
            # Determine expiry field based on tier
            tier = payload["tier"]
            
            # Features are now computed from tier, not stored in JWT
            # We'll let the SubscriptionSettings model compute features from tier
            # This ensures single source of truth
            trial_expires_at = None
            grace_period_expires_at = None
            
            if tier == "trial":
                trial_expires_at = expiry_dt.isoformat()
            elif tier == "paid_limited":
                grace_period_expires_at = expiry_dt.isoformat()
            
            # Build subscription settings
            subscription = SubscriptionSettings(
                tier=tier,
                license_key=payload.get("license_key"),  # Store original token
                trial_started_at=None,  # Keep existing trial tracking
                trial_expires_at=trial_expires_at,
                grace_period_started_at=None,  # Will be set by service
                grace_period_expires_at=grace_period_expires_at,
                features=None,  # Features are now computed from tier
                last_tier_change=datetime.utcnow().isoformat()
            )
            
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to extract tier info from JWT: {e}")
            raise ValueError(f"Failed to extract subscription info: {str(e)}")
    
    def generate_test_token(
        self,
        tier: str,
        duration_days: int = 365
    ) -> str:
        """
        Generate a test JWT token (for development/testing only)
        In production, tokens should be generated by a secure backend service
        
        Args:
            tier: Subscription tier
            duration_days: License duration in days
            
        Returns:
            JWT token string
        """
        import uuid
        
        now = datetime.utcnow()
        issued_ms = int(now.timestamp() * 1000)
        expiry_ms = int((now.timestamp() + (duration_days * 24 * 60 * 60)) * 1000)
        
        payload = {
            "tier": tier,
            "issued": issued_ms,
            "expiry": expiry_ms,
            "license_id": str(uuid.uuid4())
        }
        
        # Generate unverified token (for testing)
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        logger.info(f"Generated test token for tier {tier} (expires in {duration_days} days)")
        return token

