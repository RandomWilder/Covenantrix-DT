"""
Security Utilities
Encryption, hashing, and secure storage utilities
"""
import hashlib
import os
import platform
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json


class APIKeyManager:
    """Secure API key management with machine-derived encryption"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize with encryption key
        
        Args:
            encryption_key: Fernet encryption key (generates if None)
        """
        if encryption_key is None:
            encryption_key = self._generate_machine_key()
        self.cipher = Fernet(encryption_key)
        self._encryption_key = encryption_key
    
    def _generate_machine_key(self) -> bytes:
        """
        Generate machine-derived encryption key
        Uses machine ID and system info for stable key generation
        """
        try:
            # Get machine-specific identifiers
            machine_id = self._get_machine_id()
            system_info = f"{platform.system()}-{platform.machine()}"
            
            # Create deterministic salt
            salt = hashlib.sha256(f"{machine_id}-{system_info}".encode()).digest()
            
            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            return key
            
        except Exception as e:
            # Fallback to random key if machine derivation fails
            return Fernet.generate_key()
    
    def _get_machine_id(self) -> str:
        """Get machine-specific identifier"""
        try:
            # Try to get machine ID from various sources
            if platform.system() == "Windows":
                # Windows: Use computer name and user profile
                computer_name = os.environ.get("COMPUTERNAME", "unknown")
                user_profile = os.environ.get("USERPROFILE", "unknown")
                return f"{computer_name}-{user_profile}"
            elif platform.system() == "Darwin":
                # macOS: Use hostname and user
                hostname = os.uname().nodename
                user = os.environ.get("USER", "unknown")
                return f"{hostname}-{user}"
            else:
                # Linux: Use hostname and user
                hostname = os.uname().nodename
                user = os.environ.get("USER", "unknown")
                return f"{hostname}-{user}"
        except Exception:
            # Fallback to a generic identifier
            return "covenantrix-default"
    
    def encrypt_key(self, api_key: str) -> str:
        """Encrypt API key"""
        try:
            encrypted = self.cipher.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise ValueError(f"Failed to encrypt API key: {str(e)}")
    
    def decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt API key"""
        try:
            if not encrypted_key:
                raise ValueError("Empty encrypted key provided")
            
            decoded = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            raise ValueError(f"Failed to decrypt API key: {str(e)} | Details: {error_details}")
    
    def encrypt_settings(self, settings: Dict[str, Any]) -> str:
        """Encrypt settings dictionary"""
        try:
            settings_json = json.dumps(settings)
            encrypted = self.cipher.encrypt(settings_json.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise ValueError(f"Failed to encrypt settings: {str(e)}")
    
    def decrypt_settings(self, encrypted_settings: str) -> Dict[str, Any]:
        """Decrypt settings dictionary"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_settings.encode())
            decrypted = self.cipher.decrypt(decoded)
            return json.loads(decrypted.decode())
        except Exception as e:
            raise ValueError(f"Failed to decrypt settings: {str(e)}")
    
    def encrypt_oauth_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt OAuth tokens in credential dictionary
        
        Args:
            credentials: Dictionary containing OAuth tokens
            
        Returns:
            Dictionary with encrypted token values
        """
        encrypted_creds = credentials.copy()
        
        # Encrypt access_token if present
        if "access_token" in encrypted_creds and encrypted_creds["access_token"]:
            encrypted_creds["access_token"] = self.encrypt_key(encrypted_creds["access_token"])
        
        # Encrypt refresh_token if present
        if "refresh_token" in encrypted_creds and encrypted_creds["refresh_token"]:
            encrypted_creds["refresh_token"] = self.encrypt_key(encrypted_creds["refresh_token"])
        
        return encrypted_creds
    
    def decrypt_oauth_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt OAuth tokens in credential dictionary
        
        Args:
            credentials: Dictionary containing encrypted OAuth tokens
            
        Returns:
            Dictionary with decrypted token values
        """
        decrypted_creds = credentials.copy()
        
        # Decrypt access_token if present
        if "access_token" in decrypted_creds and decrypted_creds["access_token"]:
            decrypted_creds["access_token"] = self.decrypt_key(decrypted_creds["access_token"])
        
        # Decrypt refresh_token if present
        if "refresh_token" in decrypted_creds and decrypted_creds["refresh_token"]:
            decrypted_creds["refresh_token"] = self.decrypt_key(decrypted_creds["refresh_token"])
        
        return decrypted_creds
    
    def validate_api_key_format(self, api_key: str, key_type: str) -> bool:
        """Validate API key format"""
        if not api_key or not isinstance(api_key, str):
            return False
        
        if key_type == "openai":
            return api_key.startswith("sk-") and len(api_key) > 20
        elif key_type == "cohere":
            return len(api_key) > 20
        elif key_type == "google":
            return len(api_key) > 20
        else:
            return len(api_key) > 10
    
    def sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for logging by masking sensitive fields"""
        sanitized = data.copy()
        sensitive_keys = ["openai", "cohere", "google", "api_key", "key", "token"]
        
        for key, value in sanitized.items():
            if isinstance(value, dict):
                sanitized[key] = self.sanitize_for_logging(value)
            elif key.lower() in sensitive_keys and isinstance(value, str):
                if len(value) > 8:
                    sanitized[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    sanitized[key] = "***"
        
        return sanitized


def hash_string(value: str) -> str:
    """Create SHA256 hash of string"""
    return hashlib.sha256(value.encode()).hexdigest()


def generate_document_id(content: str, filename: str) -> str:
    """Generate deterministic document ID from content and filename"""
    combined = f"{filename}:{content[:1000]}"  # First 1000 chars
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """Check if file extension is allowed"""
    extension = filename.lower().split('.')[-1]
    return extension in [ext.lower() for ext in allowed_extensions]