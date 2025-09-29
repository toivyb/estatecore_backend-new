#!/usr/bin/env python3
"""
Zero-Trust Authentication System for EstateCore Phase 8D
Advanced security with continuous verification, risk assessment, and adaptive authentication
"""

import os
import json
import hashlib
import hmac
import secrets
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import jwt
import bcrypt
import pyotp
import sqlite3
import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthMethod(Enum):
    PASSWORD = "password"
    MFA_TOTP = "mfa_totp"
    MFA_SMS = "mfa_sms"
    MFA_EMAIL = "mfa_email"
    BIOMETRIC = "biometric"
    SSO_SAML = "sso_saml"
    SSO_OAUTH = "sso_oauth"
    API_KEY = "api_key"
    CERTIFICATE = "certificate"

class RiskLevel(Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuthResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    REQUIRES_MFA = "requires_mfa"
    REQUIRES_STEP_UP = "requires_step_up"
    BLOCKED = "blocked"
    EXPIRED = "expired"

class DeviceType(Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    API_CLIENT = "api_client"
    UNKNOWN = "unknown"

@dataclass
class AuthenticationRequest:
    """Authentication request details"""
    request_id: str
    user_identifier: str
    auth_method: AuthMethod
    credentials: Dict[str, Any]
    device_info: Dict[str, Any]
    location_info: Dict[str, Any]
    timestamp: datetime
    ip_address: str
    user_agent: str
    session_id: Optional[str]

@dataclass
class AuthenticationResult:
    """Authentication result"""
    request_id: str
    user_id: Optional[str]
    result: AuthResult
    risk_score: float
    confidence_level: float
    required_methods: List[AuthMethod]
    session_token: Optional[str]
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_at: Optional[datetime]
    next_verification: Optional[datetime]
    restrictions: List[str]
    metadata: Dict[str, Any]

@dataclass
class SecurityContext:
    """Security context for requests"""
    user_id: str
    session_id: str
    auth_level: int
    permissions: List[str]
    device_id: str
    device_trusted: bool
    location_verified: bool
    last_verification: datetime
    risk_factors: List[str]
    active_sessions: List[str]

@dataclass
class DeviceProfile:
    """Device fingerprint and profile"""
    device_id: str
    user_id: str
    device_type: DeviceType
    browser_fingerprint: str
    screen_resolution: str
    timezone: str
    language: str
    platform: str
    first_seen: datetime
    last_seen: datetime
    trusted: bool
    risk_score: float
    characteristics: Dict[str, Any]

@dataclass
class SecurityEvent:
    """Security event for monitoring"""
    event_id: str
    event_type: str
    user_id: Optional[str]
    device_id: Optional[str]
    ip_address: str
    location: Dict[str, Any]
    risk_level: RiskLevel
    description: str
    metadata: Dict[str, Any]
    timestamp: datetime
    resolved: bool

class ZeroTrustAuthenticator:
    """Zero-Trust Authentication System"""
    
    def __init__(self, database_path: str = "zero_trust_auth.db"):
        self.database_path = database_path
        self.encryption_key = self._load_or_generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # JWT configuration
        self.jwt_secret = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
        self.jwt_algorithm = 'HS256'
        
        # Risk thresholds
        self.risk_thresholds = {
            'require_mfa': 0.3,
            'require_step_up': 0.6,
            'block_access': 0.8,
            'require_admin_approval': 0.9
        }
        
        # Initialize database
        self._initialize_database()
        
        logger.info("Zero-Trust Authenticator initialized")
    
    def _load_or_generate_key(self) -> bytes:
        """Load or generate encryption key"""
        key_file = "encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _initialize_database(self):
        """Initialize authentication database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                mfa_secret TEXT,
                backup_codes TEXT,
                security_questions TEXT,
                account_locked BOOLEAN DEFAULT 0,
                failed_attempts INTEGER DEFAULT 0,
                last_login TEXT,
                password_changed TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                location TEXT,
                active BOOLEAN DEFAULT 1,
                risk_score REAL DEFAULT 0,
                auth_methods TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Device profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_profiles (
                device_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_type TEXT NOT NULL,
                browser_fingerprint TEXT,
                screen_resolution TEXT,
                timezone TEXT,
                language TEXT,
                platform TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                trusted BOOLEAN DEFAULT 0,
                risk_score REAL DEFAULT 0,
                characteristics TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Authentication attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_attempts (
                attempt_id TEXT PRIMARY KEY,
                user_identifier TEXT NOT NULL,
                auth_method TEXT NOT NULL,
                result TEXT NOT NULL,
                risk_score REAL NOT NULL,
                ip_address TEXT,
                device_id TEXT,
                location TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Security events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                user_id TEXT,
                device_id TEXT,
                ip_address TEXT,
                location TEXT,
                risk_level TEXT NOT NULL,
                description TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0
            )
        """)
        
        # MFA tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mfa_tokens (
                token_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_type TEXT NOT NULL,
                token_value TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_active ON sessions (user_id, active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_attempts_user_time ON auth_attempts (user_identifier, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_events_time ON security_events (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_profiles_user ON device_profiles (user_id)")
        
        conn.commit()
        conn.close()
    
    async def authenticate(self, request: AuthenticationRequest) -> AuthenticationResult:
        """Main authentication entry point with zero-trust verification"""
        try:
            logger.info(f"Authentication request: {request.user_identifier} via {request.auth_method.value}")
            
            # Initial risk assessment
            risk_score = await self._assess_initial_risk(request)
            
            # Device fingerprinting
            device_id = await self._fingerprint_device(request)
            
            # Perform authentication
            auth_result = await self._perform_authentication(request, risk_score)
            
            # Post-auth risk assessment
            final_risk_score = await self._assess_post_auth_risk(request, auth_result, risk_score)
            
            # Create security context if successful
            if auth_result.result == AuthResult.SUCCESS:
                security_context = await self._create_security_context(
                    auth_result.user_id, device_id, request, final_risk_score
                )
                
                # Generate tokens
                session_token, access_token, refresh_token = await self._generate_tokens(
                    security_context, final_risk_score
                )
                
                auth_result.session_token = session_token
                auth_result.access_token = access_token
                auth_result.refresh_token = refresh_token
                
                # Update device profile
                await self._update_device_profile(device_id, auth_result.user_id, request)
            
            # Log authentication attempt
            await self._log_authentication_attempt(request, auth_result, final_risk_score)
            
            # Generate security events if needed
            await self._generate_security_events(request, auth_result, final_risk_score)
            
            auth_result.risk_score = final_risk_score
            return auth_result
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthenticationResult(
                request_id=request.request_id,
                user_id=None,
                result=AuthResult.FAILED,
                risk_score=1.0,
                confidence_level=0.0,
                required_methods=[],
                session_token=None,
                access_token=None,
                refresh_token=None,
                expires_at=None,
                next_verification=None,
                restrictions=[],
                metadata={'error': str(e)}
            )
    
    async def _assess_initial_risk(self, request: AuthenticationRequest) -> float:
        """Assess initial risk based on request characteristics"""
        risk_factors = []
        risk_score = 0.0
        
        # IP address risk
        ip_risk = await self._assess_ip_risk(request.ip_address)
        risk_score += ip_risk * 0.3
        if ip_risk > 0.5:
            risk_factors.append("suspicious_ip")
        
        # Location risk
        location_risk = await self._assess_location_risk(request.user_identifier, request.location_info)
        risk_score += location_risk * 0.2
        if location_risk > 0.5:
            risk_factors.append("unusual_location")
        
        # Device risk
        device_risk = await self._assess_device_risk(request.device_info, request.user_identifier)
        risk_score += device_risk * 0.3
        if device_risk > 0.5:
            risk_factors.append("unknown_device")
        
        # Time-based risk
        time_risk = await self._assess_time_risk(request.user_identifier, request.timestamp)
        risk_score += time_risk * 0.1
        if time_risk > 0.5:
            risk_factors.append("unusual_time")
        
        # Behavioral risk
        behavioral_risk = await self._assess_behavioral_risk(request.user_identifier, request)
        risk_score += behavioral_risk * 0.1
        if behavioral_risk > 0.5:
            risk_factors.append("unusual_behavior")
        
        return min(risk_score, 1.0)
    
    async def _perform_authentication(self, request: AuthenticationRequest, 
                                   risk_score: float) -> AuthenticationResult:
        """Perform the actual authentication"""
        
        if request.auth_method == AuthMethod.PASSWORD:
            return await self._authenticate_password(request, risk_score)
        elif request.auth_method == AuthMethod.MFA_TOTP:
            return await self._authenticate_mfa_totp(request, risk_score)
        elif request.auth_method == AuthMethod.MFA_SMS:
            return await self._authenticate_mfa_sms(request, risk_score)
        elif request.auth_method == AuthMethod.BIOMETRIC:
            return await self._authenticate_biometric(request, risk_score)
        elif request.auth_method == AuthMethod.SSO_SAML:
            return await self._authenticate_sso_saml(request, risk_score)
        elif request.auth_method == AuthMethod.API_KEY:
            return await self._authenticate_api_key(request, risk_score)
        else:
            raise ValueError(f"Unsupported authentication method: {request.auth_method}")
    
    async def _authenticate_password(self, request: AuthenticationRequest, 
                                   risk_score: float) -> AuthenticationResult:
        """Authenticate with username/password"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get user
            cursor.execute("""
                SELECT user_id, password_hash, salt, account_locked, failed_attempts, mfa_secret
                FROM users 
                WHERE username = ? OR email = ?
            """, (request.user_identifier, request.user_identifier))
            
            user_row = cursor.fetchone()
            conn.close()
            
            if not user_row:
                # User not found - still hash password to prevent timing attacks
                bcrypt.hashpw(b"dummy", bcrypt.gensalt())
                return AuthenticationResult(
                    request_id=request.request_id,
                    user_id=None,
                    result=AuthResult.FAILED,
                    risk_score=risk_score,
                    confidence_level=0.0,
                    required_methods=[],
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    next_verification=None,
                    restrictions=[],
                    metadata={'reason': 'invalid_credentials'}
                )
            
            user_id, password_hash, salt, account_locked, failed_attempts, mfa_secret = user_row
            
            # Check if account is locked
            if account_locked:
                return AuthenticationResult(
                    request_id=request.request_id,
                    user_id=user_id,
                    result=AuthResult.BLOCKED,
                    risk_score=1.0,
                    confidence_level=0.0,
                    required_methods=[],
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    next_verification=None,
                    restrictions=['account_locked'],
                    metadata={'reason': 'account_locked'}
                )
            
            # Verify password
            password = request.credentials.get('password', '')
            password_bytes = password.encode('utf-8')
            
            if bcrypt.checkpw(password_bytes, password_hash.encode('utf-8')):
                # Password correct - reset failed attempts
                await self._reset_failed_attempts(user_id)
                
                # Determine if MFA is required
                required_methods = []
                
                if mfa_secret or risk_score > self.risk_thresholds['require_mfa']:
                    required_methods.append(AuthMethod.MFA_TOTP)
                    result = AuthResult.REQUIRES_MFA
                else:
                    result = AuthResult.SUCCESS
                
                return AuthenticationResult(
                    request_id=request.request_id,
                    user_id=user_id,
                    result=result,
                    risk_score=risk_score,
                    confidence_level=0.8,
                    required_methods=required_methods,
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    next_verification=None,
                    restrictions=[],
                    metadata={'auth_method': 'password'}
                )
            else:
                # Password incorrect - increment failed attempts
                await self._increment_failed_attempts(user_id)
                
                return AuthenticationResult(
                    request_id=request.request_id,
                    user_id=user_id,
                    result=AuthResult.FAILED,
                    risk_score=min(risk_score + 0.2, 1.0),
                    confidence_level=0.0,
                    required_methods=[],
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    next_verification=None,
                    restrictions=[],
                    metadata={'reason': 'invalid_credentials'}
                )
                
        except Exception as e:
            logger.error(f"Password authentication error: {e}")
            raise
    
    async def _authenticate_mfa_totp(self, request: AuthenticationRequest,
                                   risk_score: float) -> AuthenticationResult:
        """Authenticate with TOTP MFA"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get user MFA secret
            cursor.execute("""
                SELECT user_id, mfa_secret FROM users 
                WHERE username = ? OR email = ?
            """, (request.user_identifier, request.user_identifier))
            
            user_row = cursor.fetchone()
            conn.close()
            
            if not user_row:
                return AuthenticationResult(
                    request_id=request.request_id,
                    user_id=None,
                    result=AuthResult.FAILED,
                    risk_score=risk_score,
                    confidence_level=0.0,
                    required_methods=[],
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    next_verification=None,
                    restrictions=[],
                    metadata={'reason': 'user_not_found'}
                )
            
            user_id, mfa_secret = user_row
            
            if not mfa_secret:
                return AuthenticationResult(
                    request_id=request.request_id,
                    user_id=user_id,
                    result=AuthResult.FAILED,
                    risk_score=risk_score,
                    confidence_level=0.0,
                    required_methods=[],
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    next_verification=None,
                    restrictions=[],
                    metadata={'reason': 'mfa_not_configured'}
                )
            
            # Verify TOTP code
            totp_code = request.credentials.get('totp_code', '')
            totp = pyotp.TOTP(mfa_secret)
            
            if totp.verify(totp_code, valid_window=1):  # Allow 30 second window
                return AuthenticationResult(
                    request_id=request.request_id,
                    user_id=user_id,
                    result=AuthResult.SUCCESS,
                    risk_score=max(risk_score - 0.3, 0.0),  # Reduce risk after MFA
                    confidence_level=0.95,
                    required_methods=[],
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    next_verification=None,
                    restrictions=[],
                    metadata={'auth_method': 'mfa_totp'}
                )
            else:
                return AuthenticationResult(
                    request_id=request.request_id,
                    user_id=user_id,
                    result=AuthResult.FAILED,
                    risk_score=min(risk_score + 0.3, 1.0),
                    confidence_level=0.0,
                    required_methods=[],
                    session_token=None,
                    access_token=None,
                    refresh_token=None,
                    expires_at=None,
                    next_verification=None,
                    restrictions=[],
                    metadata={'reason': 'invalid_totp_code'}
                )
                
        except Exception as e:
            logger.error(f"MFA TOTP authentication error: {e}")
            raise
    
    async def _generate_tokens(self, security_context: SecurityContext, 
                             risk_score: float) -> Tuple[str, str, str]:
        """Generate session, access, and refresh tokens"""
        
        # Session token (long-lived, encrypted)
        session_payload = {
            'user_id': security_context.user_id,
            'session_id': security_context.session_id,
            'device_id': security_context.device_id,
            'auth_level': security_context.auth_level,
            'risk_score': risk_score,
            'issued_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        session_token_data = json.dumps(session_payload).encode()
        session_token = base64.urlsafe_b64encode(
            self.cipher_suite.encrypt(session_token_data)
        ).decode()
        
        # Access token (short-lived, JWT)
        access_payload = {
            'user_id': security_context.user_id,
            'session_id': security_context.session_id,
            'permissions': security_context.permissions,
            'auth_level': security_context.auth_level,
            'iat': datetime.now(),
            'exp': datetime.now() + timedelta(hours=1),
            'iss': 'estatecore-auth',
            'aud': 'estatecore-api'
        }
        
        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Refresh token (medium-lived, encrypted)
        refresh_payload = {
            'user_id': security_context.user_id,
            'session_id': security_context.session_id,
            'token_type': 'refresh',
            'issued_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        refresh_token_data = json.dumps(refresh_payload).encode()
        refresh_token = base64.urlsafe_b64encode(
            self.cipher_suite.encrypt(refresh_token_data)
        ).decode()
        
        return session_token, access_token, refresh_token
    
    async def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """Verify and decode token"""
        try:
            if token_type == 'access':
                # JWT access token
                payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
                return payload
            else:
                # Encrypted session/refresh token
                token_data = base64.urlsafe_b64decode(token.encode())
                decrypted_data = self.cipher_suite.decrypt(token_data)
                payload = json.loads(decrypted_data.decode())
                
                # Check expiration
                expires_at = datetime.fromisoformat(payload['expires_at'])
                if datetime.now() > expires_at:
                    return None
                
                return payload
                
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    # Helper methods for risk assessment
    async def _assess_ip_risk(self, ip_address: str) -> float:
        """Assess risk based on IP address"""
        # Implement IP reputation checking, geolocation, etc.
        # For now, return low risk for all IPs
        return 0.1
    
    async def _assess_location_risk(self, user_identifier: str, location_info: Dict[str, Any]) -> float:
        """Assess risk based on location"""
        # Implement location-based risk assessment
        return 0.1
    
    async def _assess_device_risk(self, device_info: Dict[str, Any], user_identifier: str) -> float:
        """Assess risk based on device characteristics"""
        # Implement device fingerprinting and trust assessment
        return 0.2
    
    async def _assess_time_risk(self, user_identifier: str, timestamp: datetime) -> float:
        """Assess risk based on access time patterns"""
        # Implement time-based risk assessment
        return 0.1
    
    async def _assess_behavioral_risk(self, user_identifier: str, request: AuthenticationRequest) -> float:
        """Assess risk based on behavioral patterns"""
        # Implement behavioral analysis
        return 0.1

# Global instance
_zero_trust_auth = None

def get_zero_trust_authenticator() -> ZeroTrustAuthenticator:
    """Get global zero-trust authenticator instance"""
    global _zero_trust_auth
    if _zero_trust_auth is None:
        _zero_trust_auth = ZeroTrustAuthenticator()
    return _zero_trust_auth

if __name__ == "__main__":
    # Test the zero-trust authenticator
    async def test_authenticator():
        auth = ZeroTrustAuthenticator()
        
        print("Testing Zero-Trust Authenticator")
        print("=" * 50)
        
        # Test authentication request
        request = AuthenticationRequest(
            request_id="test-001",
            user_identifier="admin@estatecore.com",
            auth_method=AuthMethod.PASSWORD,
            credentials={"password": "test_password"},
            device_info={"type": "desktop", "os": "Windows"},
            location_info={"country": "US", "city": "New York"},
            timestamp=datetime.now(),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0...",
            session_id=None
        )
        
        result = await auth.authenticate(request)
        print(f"Authentication result: {result.result.value}")
        print(f"Risk score: {result.risk_score:.3f}")
        print(f"Required methods: {[m.value for m in result.required_methods]}")
        
        print("\nZero-Trust Authenticator Test Complete!")
    
    asyncio.run(test_authenticator())