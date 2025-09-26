"""
Advanced API Key Management Service for EstateCore API Gateway
Comprehensive API key lifecycle management, security, and monitoring
"""

import os
import secrets
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIKeyStatus(Enum):
    """API key status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"

class APIKeyType(Enum):
    """API key types"""
    FULL_ACCESS = "full_access"
    READ_ONLY = "read_only"
    WRITE_ONLY = "write_only"
    SANDBOX = "sandbox"
    WEBHOOK = "webhook"
    INTEGRATION = "integration"

class KeyRotationPolicy(Enum):
    """Key rotation policies"""
    MANUAL = "manual"
    AUTOMATIC_30_DAYS = "automatic_30_days"
    AUTOMATIC_60_DAYS = "automatic_60_days"
    AUTOMATIC_90_DAYS = "automatic_90_days"
    AUTOMATIC_365_DAYS = "automatic_365_days"

@dataclass
class APIKeyPermissions:
    """API key permissions configuration"""
    endpoints: List[str] = field(default_factory=list)  # Allowed endpoints
    methods: List[str] = field(default_factory=list)    # Allowed HTTP methods
    rate_limits: Dict[str, int] = field(default_factory=dict)  # Custom rate limits
    ip_whitelist: List[str] = field(default_factory=list)  # IP restrictions
    time_restrictions: Dict[str, Any] = field(default_factory=dict)  # Time-based access
    data_access_level: str = "standard"  # Data access level
    can_create_webhooks: bool = False
    can_manage_users: bool = False
    can_access_analytics: bool = False

@dataclass
class APIKey:
    """API key data structure"""
    key_id: str
    key_hash: str  # Hashed version of the actual key
    key_prefix: str  # First 8 characters for identification
    client_id: str
    organization_id: str
    name: str
    description: str
    key_type: APIKeyType
    permissions: APIKeyPermissions
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    rotation_policy: KeyRotationPolicy = KeyRotationPolicy.MANUAL
    next_rotation_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    encrypted_key: Optional[str] = None  # Encrypted version for secure storage

@dataclass
class APIKeyUsageLog:
    """API key usage logging"""
    log_id: str
    key_id: str
    client_id: str
    endpoint: str
    method: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    response_status: int
    response_time: float
    request_size: int
    response_size: int
    error_message: Optional[str] = None

class APIKeyGenerator:
    """Secure API key generation"""
    
    @staticmethod
    def generate_api_key(prefix: str = "ec") -> Tuple[str, str, str]:
        """
        Generate a secure API key with prefix
        Returns: (full_key, key_hash, key_prefix)
        """
        # Generate random bytes for the key
        key_bytes = secrets.token_bytes(32)
        key_string = base64.urlsafe_b64encode(key_bytes).decode('utf-8').rstrip('=')
        
        # Create full key with prefix
        full_key = f"{prefix}_{key_string}"
        
        # Generate hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        # Extract prefix for identification
        key_prefix = full_key[:12]  # prefix + first 8 chars
        
        return full_key, key_hash, key_prefix
    
    @staticmethod
    def validate_api_key_format(api_key: str) -> bool:
        """Validate API key format"""
        if not api_key or len(api_key) < 16:
            return False
        
        if not api_key.startswith('ec_'):
            return False
        
        # Check if the key contains only valid base64url characters
        key_part = api_key[3:]  # Remove prefix
        try:
            base64.urlsafe_b64decode(key_part + '===')  # Add padding
            return True
        except Exception:
            return False

class APIKeyEncryption:
    """API key encryption for secure storage"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.environ.get('API_KEY_MASTER_KEY')
        if not self.master_key:
            raise ValueError("Master key is required for API key encryption")
        
        # Derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'estatecore_api_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        self.fernet = Fernet(key)
    
    def encrypt_key(self, api_key: str) -> str:
        """Encrypt API key for storage"""
        return self.fernet.encrypt(api_key.encode()).decode()
    
    def decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt API key from storage"""
        return self.fernet.decrypt(encrypted_key.encode()).decode()

class APIKeyValidation:
    """API key validation and verification"""
    
    @staticmethod
    def validate_permissions(api_key: APIKey, endpoint: str, method: str, 
                           ip_address: str) -> Tuple[bool, Optional[str]]:
        """Validate API key permissions for request"""
        
        # Check key status
        if api_key.status != APIKeyStatus.ACTIVE:
            return False, f"API key is {api_key.status.value}"
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return False, "API key has expired"
        
        # Check endpoint permissions
        if api_key.permissions.endpoints:
            if not any(endpoint.startswith(allowed) for allowed in api_key.permissions.endpoints):
                return False, "Endpoint not allowed for this API key"
        
        # Check method permissions
        if api_key.permissions.methods:
            if method not in api_key.permissions.methods:
                return False, f"HTTP method {method} not allowed for this API key"
        
        # Check IP whitelist
        if api_key.permissions.ip_whitelist:
            if ip_address not in api_key.permissions.ip_whitelist:
                return False, "IP address not in whitelist"
        
        # Check time restrictions
        if api_key.permissions.time_restrictions:
            current_time = datetime.utcnow()
            restrictions = api_key.permissions.time_restrictions
            
            if 'start_time' in restrictions and 'end_time' in restrictions:
                start_time = datetime.fromisoformat(restrictions['start_time'])
                end_time = datetime.fromisoformat(restrictions['end_time'])
                if not (start_time <= current_time <= end_time):
                    return False, "Access restricted by time constraints"
            
            if 'allowed_hours' in restrictions:
                current_hour = current_time.hour
                if current_hour not in restrictions['allowed_hours']:
                    return False, "Access not allowed at this time"
            
            if 'allowed_days' in restrictions:
                current_day = current_time.weekday()  # 0=Monday, 6=Sunday
                if current_day not in restrictions['allowed_days']:
                    return False, "Access not allowed on this day"
        
        return True, None

class APIKeyManagementService:
    """Main API key management service"""
    
    def __init__(self):
        self.api_keys: Dict[str, APIKey] = {}
        self.key_hash_lookup: Dict[str, str] = {}  # hash -> key_id mapping
        self.usage_logs: List[APIKeyUsageLog] = []
        self.encryption = None
        
        # Initialize encryption if master key is available
        try:
            self.encryption = APIKeyEncryption()
        except ValueError as e:
            logger.warning(f"API key encryption not available: {str(e)}")
        
        # Load existing keys
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from storage"""
        # In a real implementation, this would load from database
        # For now, we'll use a simple file-based storage
        storage_path = os.environ.get('API_KEYS_STORAGE_PATH', 'api_keys.json')
        if os.path.exists(storage_path):
            try:
                with open(storage_path, 'r') as f:
                    data = json.load(f)
                    for key_data in data.get('api_keys', []):
                        # Convert datetime strings back to datetime objects
                        if key_data.get('created_at'):
                            key_data['created_at'] = datetime.fromisoformat(key_data['created_at'])
                        if key_data.get('expires_at'):
                            key_data['expires_at'] = datetime.fromisoformat(key_data['expires_at'])
                        if key_data.get('last_used_at'):
                            key_data['last_used_at'] = datetime.fromisoformat(key_data['last_used_at'])
                        if key_data.get('next_rotation_date'):
                            key_data['next_rotation_date'] = datetime.fromisoformat(key_data['next_rotation_date'])
                        
                        # Convert enums
                        key_data['key_type'] = APIKeyType(key_data['key_type'])
                        key_data['status'] = APIKeyStatus(key_data['status'])
                        key_data['rotation_policy'] = KeyRotationPolicy(key_data['rotation_policy'])
                        
                        # Convert permissions
                        if key_data.get('permissions'):
                            key_data['permissions'] = APIKeyPermissions(**key_data['permissions'])
                        
                        api_key = APIKey(**key_data)
                        self.api_keys[api_key.key_id] = api_key
                        self.key_hash_lookup[api_key.key_hash] = api_key.key_id
                        
            except Exception as e:
                logger.error(f"Failed to load API keys: {str(e)}")
    
    def _save_api_keys(self):
        """Save API keys to storage"""
        storage_path = os.environ.get('API_KEYS_STORAGE_PATH', 'api_keys.json')
        try:
            data = {'api_keys': []}
            for api_key in self.api_keys.values():
                key_data = {
                    'key_id': api_key.key_id,
                    'key_hash': api_key.key_hash,
                    'key_prefix': api_key.key_prefix,
                    'client_id': api_key.client_id,
                    'organization_id': api_key.organization_id,
                    'name': api_key.name,
                    'description': api_key.description,
                    'key_type': api_key.key_type.value,
                    'status': api_key.status.value,
                    'created_at': api_key.created_at.isoformat(),
                    'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
                    'last_used_at': api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                    'usage_count': api_key.usage_count,
                    'rotation_policy': api_key.rotation_policy.value,
                    'next_rotation_date': api_key.next_rotation_date.isoformat() if api_key.next_rotation_date else None,
                    'metadata': api_key.metadata,
                    'encrypted_key': api_key.encrypted_key,
                    'permissions': {
                        'endpoints': api_key.permissions.endpoints,
                        'methods': api_key.permissions.methods,
                        'rate_limits': api_key.permissions.rate_limits,
                        'ip_whitelist': api_key.permissions.ip_whitelist,
                        'time_restrictions': api_key.permissions.time_restrictions,
                        'data_access_level': api_key.permissions.data_access_level,
                        'can_create_webhooks': api_key.permissions.can_create_webhooks,
                        'can_manage_users': api_key.permissions.can_manage_users,
                        'can_access_analytics': api_key.permissions.can_access_analytics
                    }
                }
                data['api_keys'].append(key_data)
            
            with open(storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save API keys: {str(e)}")
    
    def create_api_key(self, client_id: str, organization_id: str, name: str,
                      description: str, key_type: APIKeyType,
                      permissions: APIKeyPermissions,
                      expires_in_days: Optional[int] = None,
                      rotation_policy: KeyRotationPolicy = KeyRotationPolicy.MANUAL) -> Tuple[str, APIKey]:
        """Create a new API key"""
        
        # Generate the API key
        full_key, key_hash, key_prefix = APIKeyGenerator.generate_api_key()
        
        # Calculate expiration date
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Calculate next rotation date
        next_rotation_date = None
        if rotation_policy != KeyRotationPolicy.MANUAL:
            days_map = {
                KeyRotationPolicy.AUTOMATIC_30_DAYS: 30,
                KeyRotationPolicy.AUTOMATIC_60_DAYS: 60,
                KeyRotationPolicy.AUTOMATIC_90_DAYS: 90,
                KeyRotationPolicy.AUTOMATIC_365_DAYS: 365
            }
            rotation_days = days_map.get(rotation_policy, 90)
            next_rotation_date = datetime.utcnow() + timedelta(days=rotation_days)
        
        # Encrypt the key if encryption is available
        encrypted_key = None
        if self.encryption:
            encrypted_key = self.encryption.encrypt_key(full_key)
        
        # Create API key object
        api_key = APIKey(
            key_id=str(uuid.uuid4()),
            key_hash=key_hash,
            key_prefix=key_prefix,
            client_id=client_id,
            organization_id=organization_id,
            name=name,
            description=description,
            key_type=key_type,
            permissions=permissions,
            expires_at=expires_at,
            rotation_policy=rotation_policy,
            next_rotation_date=next_rotation_date,
            encrypted_key=encrypted_key
        )
        
        # Store the API key
        self.api_keys[api_key.key_id] = api_key
        self.key_hash_lookup[key_hash] = api_key.key_id
        
        # Save to persistent storage
        self._save_api_keys()
        
        logger.info(f"Created API key {api_key.key_id} for client {client_id}")
        
        return full_key, api_key
    
    def verify_api_key(self, api_key: str) -> Tuple[bool, Optional[APIKey], Optional[str]]:
        """Verify an API key and return the associated key object"""
        
        # Validate key format
        if not APIKeyGenerator.validate_api_key_format(api_key):
            return False, None, "Invalid API key format"
        
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Look up the key
        if key_hash not in self.key_hash_lookup:
            return False, None, "API key not found"
        
        key_id = self.key_hash_lookup[key_hash]
        api_key_obj = self.api_keys[key_id]
        
        # Check key status
        if api_key_obj.status != APIKeyStatus.ACTIVE:
            return False, api_key_obj, f"API key is {api_key_obj.status.value}"
        
        # Check expiration
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            # Auto-expire the key
            api_key_obj.status = APIKeyStatus.EXPIRED
            self._save_api_keys()
            return False, api_key_obj, "API key has expired"
        
        # Update last used timestamp
        api_key_obj.last_used_at = datetime.utcnow()
        api_key_obj.usage_count += 1
        
        # Save updated usage info
        self._save_api_keys()
        
        return True, api_key_obj, None
    
    def revoke_api_key(self, key_id: str, reason: str = "Revoked by admin") -> bool:
        """Revoke an API key"""
        if key_id not in self.api_keys:
            return False
        
        api_key = self.api_keys[key_id]
        api_key.status = APIKeyStatus.REVOKED
        api_key.metadata['revocation_reason'] = reason
        api_key.metadata['revoked_at'] = datetime.utcnow().isoformat()
        
        # Save changes
        self._save_api_keys()
        
        logger.info(f"Revoked API key {key_id}: {reason}")
        return True
    
    def suspend_api_key(self, key_id: str, reason: str = "Suspended by admin") -> bool:
        """Suspend an API key (can be reactivated)"""
        if key_id not in self.api_keys:
            return False
        
        api_key = self.api_keys[key_id]
        api_key.status = APIKeyStatus.SUSPENDED
        api_key.metadata['suspension_reason'] = reason
        api_key.metadata['suspended_at'] = datetime.utcnow().isoformat()
        
        # Save changes
        self._save_api_keys()
        
        logger.info(f"Suspended API key {key_id}: {reason}")
        return True
    
    def reactivate_api_key(self, key_id: str) -> bool:
        """Reactivate a suspended API key"""
        if key_id not in self.api_keys:
            return False
        
        api_key = self.api_keys[key_id]
        if api_key.status != APIKeyStatus.SUSPENDED:
            return False
        
        api_key.status = APIKeyStatus.ACTIVE
        api_key.metadata['reactivated_at'] = datetime.utcnow().isoformat()
        
        # Save changes
        self._save_api_keys()
        
        logger.info(f"Reactivated API key {key_id}")
        return True
    
    def rotate_api_key(self, key_id: str) -> Tuple[bool, Optional[str]]:
        """Rotate an API key (generate new key, keep same permissions)"""
        if key_id not in self.api_keys:
            return False, None
        
        old_api_key = self.api_keys[key_id]
        
        # Generate new key
        new_full_key, new_key_hash, new_key_prefix = APIKeyGenerator.generate_api_key()
        
        # Remove old hash lookup
        del self.key_hash_lookup[old_api_key.key_hash]
        
        # Update API key with new values
        old_api_key.key_hash = new_key_hash
        old_api_key.key_prefix = new_key_prefix
        
        # Encrypt new key if encryption is available
        if self.encryption:
            old_api_key.encrypted_key = self.encryption.encrypt_key(new_full_key)
        
        # Update rotation info
        if old_api_key.rotation_policy != KeyRotationPolicy.MANUAL:
            days_map = {
                KeyRotationPolicy.AUTOMATIC_30_DAYS: 30,
                KeyRotationPolicy.AUTOMATIC_60_DAYS: 60,
                KeyRotationPolicy.AUTOMATIC_90_DAYS: 90,
                KeyRotationPolicy.AUTOMATIC_365_DAYS: 365
            }
            rotation_days = days_map.get(old_api_key.rotation_policy, 90)
            old_api_key.next_rotation_date = datetime.utcnow() + timedelta(days=rotation_days)
        
        old_api_key.metadata['last_rotation'] = datetime.utcnow().isoformat()
        
        # Add new hash lookup
        self.key_hash_lookup[new_key_hash] = key_id
        
        # Save changes
        self._save_api_keys()
        
        logger.info(f"Rotated API key {key_id}")
        return True, new_full_key
    
    def update_permissions(self, key_id: str, permissions: APIKeyPermissions) -> bool:
        """Update API key permissions"""
        if key_id not in self.api_keys:
            return False
        
        api_key = self.api_keys[key_id]
        api_key.permissions = permissions
        api_key.metadata['permissions_updated_at'] = datetime.utcnow().isoformat()
        
        # Save changes
        self._save_api_keys()
        
        logger.info(f"Updated permissions for API key {key_id}")
        return True
    
    def log_usage(self, key_id: str, endpoint: str, method: str, ip_address: str,
                 user_agent: str, response_status: int, response_time: float,
                 request_size: int, response_size: int, error_message: Optional[str] = None):
        """Log API key usage"""
        usage_log = APIKeyUsageLog(
            log_id=str(uuid.uuid4()),
            key_id=key_id,
            client_id=self.api_keys[key_id].client_id if key_id in self.api_keys else 'unknown',
            endpoint=endpoint,
            method=method,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            response_status=response_status,
            response_time=response_time,
            request_size=request_size,
            response_size=response_size,
            error_message=error_message
        )
        
        self.usage_logs.append(usage_log)
        
        # Keep only recent logs (last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        self.usage_logs = [log for log in self.usage_logs if log.timestamp > cutoff_date]
    
    def get_api_keys_for_client(self, client_id: str) -> List[APIKey]:
        """Get all API keys for a specific client"""
        return [key for key in self.api_keys.values() if key.client_id == client_id]
    
    def get_api_key_analytics(self, key_id: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for a specific API key"""
        if key_id not in self.api_keys:
            return {}
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        relevant_logs = [
            log for log in self.usage_logs 
            if log.key_id == key_id and log.timestamp > cutoff_date
        ]
        
        if not relevant_logs:
            return {
                'total_requests': 0,
                'average_response_time': 0,
                'error_rate': 0,
                'most_used_endpoints': [],
                'daily_usage': []
            }
        
        total_requests = len(relevant_logs)
        error_count = len([log for log in relevant_logs if log.response_status >= 400])
        error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
        
        response_times = [log.response_time for log in relevant_logs]
        average_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Endpoint usage
        endpoint_usage = {}
        for log in relevant_logs:
            endpoint_usage[log.endpoint] = endpoint_usage.get(log.endpoint, 0) + 1
        
        most_used_endpoints = sorted(endpoint_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Daily usage
        daily_usage = {}
        for log in relevant_logs:
            date_key = log.timestamp.strftime('%Y-%m-%d')
            daily_usage[date_key] = daily_usage.get(date_key, 0) + 1
        
        return {
            'total_requests': total_requests,
            'average_response_time': average_response_time,
            'error_rate': error_rate,
            'most_used_endpoints': most_used_endpoints,
            'daily_usage': [{'date': date, 'requests': count} for date, count in sorted(daily_usage.items())],
            'bandwidth_usage': sum(log.request_size + log.response_size for log in relevant_logs)
        }
    
    def check_rotation_schedule(self):
        """Check and perform automatic key rotations"""
        now = datetime.utcnow()
        
        for api_key in self.api_keys.values():
            if (api_key.rotation_policy != KeyRotationPolicy.MANUAL and 
                api_key.next_rotation_date and 
                api_key.next_rotation_date <= now and
                api_key.status == APIKeyStatus.ACTIVE):
                
                logger.info(f"Auto-rotating API key {api_key.key_id}")
                success, new_key = self.rotate_api_key(api_key.key_id)
                
                if success:
                    # In a real implementation, you would notify the client about the rotation
                    logger.info(f"API key {api_key.key_id} rotated successfully")
                else:
                    logger.error(f"Failed to rotate API key {api_key.key_id}")

# Global API Key Management service instance
_api_key_service = None

def get_api_key_service() -> APIKeyManagementService:
    """Get or create the API Key Management service instance"""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = APIKeyManagementService()
    return _api_key_service