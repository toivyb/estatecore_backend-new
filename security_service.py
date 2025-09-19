"""
Enhanced Security Service for EstateCore
Advanced authentication, authorization, audit logging, and security monitoring
"""

import os
import logging
import hashlib
import secrets
import jwt
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import ipaddress
from functools import wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Security event types for audit logging"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SECURITY_ALERT = "security_alert"

class ThreatLevel(Enum):
    """Threat level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SessionStatus(Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    id: str
    event_type: SecurityEventType
    user_id: Optional[int]
    ip_address: str
    user_agent: str
    timestamp: datetime
    threat_level: ThreatLevel
    details: Dict
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    success: bool = True
    metadata: Dict = field(default_factory=dict)

@dataclass
class UserSession:
    """User session data structure"""
    id: str
    user_id: int
    ip_address: str
    user_agent: str
    created_at: datetime
    last_accessed: datetime
    expires_at: datetime
    status: SessionStatus
    token_hash: str
    permissions: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

@dataclass
class APIKey:
    """API key data structure"""
    id: str
    key_hash: str
    user_id: int
    name: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    is_active: bool = True
    rate_limit: int = 1000  # requests per hour
    usage_count: int = 0

@dataclass
class RateLimitRule:
    """Rate limiting rule"""
    endpoint: str
    max_requests: int
    time_window: int  # seconds
    per_user: bool = True
    per_ip: bool = False

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    id: str
    alert_type: str
    severity: ThreatLevel
    user_id: Optional[int]
    ip_address: str
    description: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

class SecurityService:
    def __init__(self):
        """Initialize security service"""
        self.secret_key = os.getenv('JWT_SECRET_KEY', self._generate_secret_key())
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT_HOURS', '24'))
        self.max_login_attempts = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
        self.lockout_duration = int(os.getenv('LOCKOUT_DURATION_MINUTES', '30'))
        self.password_salt_rounds = int(os.getenv('PASSWORD_SALT_ROUNDS', '12'))
        
        # In-memory storage for demonstration (would use database in production)
        self.sessions = {}
        self.api_keys = {}
        self.security_events = []
        self.failed_attempts = {}
        self.rate_limits = {}
        self.security_alerts = []
        
        # Initialize rate limiting rules
        self.rate_limit_rules = self._get_default_rate_limits()
        
        # Initialize security monitoring
        self._initialize_security_monitoring()
        
    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key"""
        return secrets.token_urlsafe(32)
    
    def _get_default_rate_limits(self) -> List[RateLimitRule]:
        """Get default rate limiting rules"""
        return [
            RateLimitRule('/api/auth/login', 10, 300, per_user=False, per_ip=True),  # 10 per 5min per IP
            RateLimitRule('/api/auth/reset-password', 5, 3600, per_user=False, per_ip=True),  # 5 per hour per IP
            RateLimitRule('/api/financial/*', 100, 3600, per_user=True),  # 100 per hour per user
            RateLimitRule('/api/lease/*', 200, 3600, per_user=True),  # 200 per hour per user
            RateLimitRule('/api/*', 1000, 3600, per_user=True),  # 1000 per hour per user (general)
        ]
    
    def _initialize_security_monitoring(self):
        """Initialize security monitoring and alerting"""
        logger.info("Security monitoring initialized")
        # Would integrate with external security monitoring services
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt or fallback to sha256"""
        try:
            if BCRYPT_AVAILABLE:
                salt = bcrypt.gensalt(rounds=self.password_salt_rounds)
                hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
                return hashed.decode('utf-8')
            else:
                # Fallback to sha256 with salt
                salt = secrets.token_hex(16)
                hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
                return f"sha256${salt}${hashed}"
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            if BCRYPT_AVAILABLE and not hashed.startswith('sha256$'):
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            elif hashed.startswith('sha256$'):
                # Handle sha256 fallback
                parts = hashed.split('$')
                if len(parts) == 3:
                    salt = parts[1]
                    stored_hash = parts[2]
                    computed_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
                    return computed_hash == stored_hash
                return False
            else:
                return False
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def create_session(self, user_id: int, ip_address: str, user_agent: str, 
                      permissions: List[str] = None) -> Dict:
        """Create a new user session"""
        try:
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            expires_at = now + timedelta(hours=self.session_timeout)
            
            # Generate JWT token
            token_payload = {
                'session_id': session_id,
                'user_id': user_id,
                'exp': expires_at,
                'iat': now,
                'permissions': permissions or []
            }
            
            token = jwt.encode(token_payload, self.secret_key, algorithm='HS256')
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Create session object
            session = UserSession(
                id=session_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=now,
                last_accessed=now,
                expires_at=expires_at,
                status=SessionStatus.ACTIVE,
                token_hash=token_hash,
                permissions=permissions or []
            )
            
            # Store session
            self.sessions[session_id] = session
            
            # Log security event
            self.log_security_event(
                event_type=SecurityEventType.SESSION_CREATED,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                threat_level=ThreatLevel.LOW,
                details={'session_id': session_id},
                success=True
            )
            
            return {
                'success': True,
                'token': token,
                'session_id': session_id,
                'expires_at': expires_at.isoformat(),
                'permissions': permissions or []
            }
            
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_session(self, token: str, ip_address: str = None) -> Dict:
        """Validate session token"""
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            session_id = payload.get('session_id')
            user_id = payload.get('user_id')
            
            # Get session from storage
            session = self.sessions.get(session_id)
            if not session:
                return {'valid': False, 'error': 'Session not found'}
            
            # Check session status
            if session.status != SessionStatus.ACTIVE:
                return {'valid': False, 'error': 'Session not active'}
            
            # Check expiration
            if datetime.utcnow() > session.expires_at:
                session.status = SessionStatus.EXPIRED
                self.log_security_event(
                    event_type=SecurityEventType.SESSION_EXPIRED,
                    user_id=user_id,
                    ip_address=ip_address or 'unknown',
                    user_agent='',
                    threat_level=ThreatLevel.LOW,
                    details={'session_id': session_id}
                )
                return {'valid': False, 'error': 'Session expired'}
            
            # Check IP address (optional security measure)
            if ip_address and self._is_suspicious_ip_change(session, ip_address):
                self._flag_suspicious_activity(session, ip_address, 'IP address change')
            
            # Update last accessed time
            session.last_accessed = datetime.utcnow()
            
            return {
                'valid': True,
                'user_id': user_id,
                'session_id': session_id,
                'permissions': session.permissions,
                'session': session
            }
            
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError as e:
            return {'valid': False, 'error': f'Invalid token: {e}'}
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return {'valid': False, 'error': str(e)}
    
    def revoke_session(self, session_id: str, user_id: int = None) -> bool:
        """Revoke a user session"""
        try:
            session = self.sessions.get(session_id)
            if session:
                session.status = SessionStatus.REVOKED
                
                self.log_security_event(
                    event_type=SecurityEventType.SESSION_EXPIRED,
                    user_id=user_id or session.user_id,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    threat_level=ThreatLevel.LOW,
                    details={'session_id': session_id, 'revoked': True}
                )
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Session revocation failed: {e}")
            return False
    
    def create_api_key(self, user_id: int, name: str, permissions: List[str], 
                      expires_at: datetime = None, rate_limit: int = 1000) -> Dict:
        """Create a new API key"""
        try:
            key_id = str(uuid.uuid4())
            raw_key = f"ec_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            
            api_key = APIKey(
                id=key_id,
                key_hash=key_hash,
                user_id=user_id,
                name=name,
                permissions=permissions,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                rate_limit=rate_limit
            )
            
            # Store API key
            self.api_keys[key_id] = api_key
            
            # Log security event
            self.log_security_event(
                event_type=SecurityEventType.API_KEY_CREATED,
                user_id=user_id,
                ip_address='system',
                user_agent='system',
                threat_level=ThreatLevel.LOW,
                details={'api_key_id': key_id, 'name': name}
            )
            
            return {
                'success': True,
                'api_key': raw_key,  # Only returned once
                'key_id': key_id,
                'permissions': permissions,
                'rate_limit': rate_limit
            }
            
        except Exception as e:
            logger.error(f"API key creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_api_key(self, api_key: str) -> Dict:
        """Validate API key"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Find matching API key
            for key_obj in self.api_keys.values():
                if key_obj.key_hash == key_hash and key_obj.is_active:
                    # Check expiration
                    if key_obj.expires_at and datetime.utcnow() > key_obj.expires_at:
                        return {'valid': False, 'error': 'API key expired'}
                    
                    # Update usage
                    key_obj.last_used = datetime.utcnow()
                    key_obj.usage_count += 1
                    
                    return {
                        'valid': True,
                        'user_id': key_obj.user_id,
                        'permissions': key_obj.permissions,
                        'rate_limit': key_obj.rate_limit,
                        'api_key_id': key_obj.id
                    }
            
            return {'valid': False, 'error': 'Invalid API key'}
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return {'valid': False, 'error': str(e)}
    
    def check_rate_limit(self, identifier: str, endpoint: str, user_id: int = None) -> Dict:
        """Check rate limiting for requests"""
        try:
            current_time = time.time()
            
            # Find applicable rate limit rule
            rule = self._find_rate_limit_rule(endpoint)
            if not rule:
                return {'allowed': True}
            
            # Create rate limit key
            if rule.per_user and user_id:
                limit_key = f"user:{user_id}:{endpoint}"
            elif rule.per_ip:
                limit_key = f"ip:{identifier}:{endpoint}"
            else:
                limit_key = f"global:{endpoint}"
            
            # Initialize or get existing rate limit data
            if limit_key not in self.rate_limits:
                self.rate_limits[limit_key] = {
                    'requests': [],
                    'blocked_until': None
                }
            
            rate_data = self.rate_limits[limit_key]
            
            # Clean old requests outside time window
            cutoff_time = current_time - rule.time_window
            rate_data['requests'] = [
                req_time for req_time in rate_data['requests'] 
                if req_time > cutoff_time
            ]
            
            # Check if currently blocked
            if rate_data['blocked_until'] and current_time < rate_data['blocked_until']:
                return {
                    'allowed': False,
                    'error': 'Rate limit exceeded',
                    'retry_after': int(rate_data['blocked_until'] - current_time)
                }
            
            # Check request count
            if len(rate_data['requests']) >= rule.max_requests:
                # Block for the remainder of the time window
                rate_data['blocked_until'] = current_time + rule.time_window
                
                # Log rate limit event
                self.log_security_event(
                    event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                    user_id=user_id,
                    ip_address=identifier if rule.per_ip else 'unknown',
                    user_agent='',
                    threat_level=ThreatLevel.MEDIUM,
                    details={
                        'endpoint': endpoint,
                        'limit_key': limit_key,
                        'requests_count': len(rate_data['requests'])
                    }
                )
                
                return {
                    'allowed': False,
                    'error': 'Rate limit exceeded',
                    'retry_after': rule.time_window
                }
            
            # Allow request and record it
            rate_data['requests'].append(current_time)
            
            return {
                'allowed': True,
                'remaining': rule.max_requests - len(rate_data['requests']),
                'reset_time': int(cutoff_time + rule.time_window)
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return {'allowed': True}  # Fail open for security
    
    def _find_rate_limit_rule(self, endpoint: str) -> Optional[RateLimitRule]:
        """Find applicable rate limit rule for endpoint"""
        for rule in self.rate_limit_rules:
            if rule.endpoint.endswith('*'):
                # Wildcard matching
                prefix = rule.endpoint[:-1]
                if endpoint.startswith(prefix):
                    return rule
            elif rule.endpoint == endpoint:
                return rule
        return None
    
    def log_security_event(self, event_type: SecurityEventType, user_id: Optional[int], 
                          ip_address: str, user_agent: str, threat_level: ThreatLevel,
                          details: Dict, endpoint: str = None, success: bool = True,
                          session_id: str = None) -> str:
        """Log security event for audit trail"""
        try:
            event_id = str(uuid.uuid4())
            
            event = SecurityEvent(
                id=event_id,
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                threat_level=threat_level,
                details=details,
                endpoint=endpoint,
                success=success,
                session_id=session_id
            )
            
            # Store event
            self.security_events.append(event)
            
            # Check for suspicious patterns
            self._analyze_security_event(event)
            
            logger.info(f"Security event logged: {event_type.value} - {threat_level.value}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Security event logging failed: {e}")
            return ""
    
    def _analyze_security_event(self, event: SecurityEvent):
        """Analyze security event for suspicious patterns"""
        try:
            # Check for suspicious activity patterns
            if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                self._create_security_alert(event)
            
            # Check for multiple failed login attempts
            if event.event_type == SecurityEventType.LOGIN_FAILURE:
                self._check_brute_force_attempt(event)
            
            # Check for unusual access patterns
            if event.event_type == SecurityEventType.DATA_ACCESS:
                self._check_unusual_access_pattern(event)
                
        except Exception as e:
            logger.error(f"Security event analysis failed: {e}")
    
    def _create_security_alert(self, event: SecurityEvent):
        """Create security alert for high-priority events"""
        try:
            alert_id = str(uuid.uuid4())
            
            alert = SecurityAlert(
                id=alert_id,
                alert_type=event.event_type.value,
                severity=event.threat_level,
                user_id=event.user_id,
                ip_address=event.ip_address,
                description=f"Security event detected: {event.event_type.value}",
                timestamp=event.timestamp,
                metadata=event.details
            )
            
            self.security_alerts.append(alert)
            
            # Send notifications for critical alerts
            if event.threat_level == ThreatLevel.CRITICAL:
                self._send_security_notification(alert)
                
        except Exception as e:
            logger.error(f"Security alert creation failed: {e}")
    
    def _send_security_notification(self, alert: SecurityAlert):
        """Send security notification to administrators"""
        # Would integrate with notification services (email, Slack, etc.)
        logger.warning(f"CRITICAL SECURITY ALERT: {alert.description}")
    
    def _check_brute_force_attempt(self, event: SecurityEvent):
        """Check for brute force login attempts"""
        try:
            ip_key = f"failed_login:{event.ip_address}"
            current_time = datetime.utcnow()
            
            if ip_key not in self.failed_attempts:
                self.failed_attempts[ip_key] = []
            
            # Add current attempt
            self.failed_attempts[ip_key].append(current_time)
            
            # Clean old attempts (outside 1 hour window)
            cutoff_time = current_time - timedelta(hours=1)
            self.failed_attempts[ip_key] = [
                attempt_time for attempt_time in self.failed_attempts[ip_key]
                if attempt_time > cutoff_time
            ]
            
            # Check if threshold exceeded
            if len(self.failed_attempts[ip_key]) >= self.max_login_attempts:
                self._create_security_alert(SecurityEvent(
                    id=str(uuid.uuid4()),
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    user_id=event.user_id,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    timestamp=current_time,
                    threat_level=ThreatLevel.HIGH,
                    details={
                        'type': 'brute_force_attempt',
                        'failed_attempts': len(self.failed_attempts[ip_key])
                    }
                ))
                
        except Exception as e:
            logger.error(f"Brute force check failed: {e}")
    
    def _check_unusual_access_pattern(self, event: SecurityEvent):
        """Check for unusual data access patterns"""
        # Would implement ML-based anomaly detection
        pass
    
    def _is_suspicious_ip_change(self, session: UserSession, new_ip: str) -> bool:
        """Check if IP address change is suspicious"""
        try:
            old_ip = ipaddress.ip_address(session.ip_address)
            new_ip_addr = ipaddress.ip_address(new_ip)
            
            # Check if IPs are in different geographical regions (simplified)
            # In production, would use IP geolocation services
            if old_ip.is_private != new_ip_addr.is_private:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"IP change check failed: {e}")
            return False
    
    def _flag_suspicious_activity(self, session: UserSession, ip_address: str, reason: str):
        """Flag suspicious activity for a session"""
        try:
            session.status = SessionStatus.SUSPICIOUS
            
            self.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_id=session.user_id,
                ip_address=ip_address,
                user_agent=session.user_agent,
                threat_level=ThreatLevel.MEDIUM,
                details={
                    'reason': reason,
                    'session_id': session.id,
                    'original_ip': session.ip_address,
                    'new_ip': ip_address
                },
                session_id=session.id
            )
            
        except Exception as e:
            logger.error(f"Suspicious activity flagging failed: {e}")
    
    def get_security_dashboard_data(self) -> Dict:
        """Get security dashboard data"""
        try:
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # Calculate metrics
            recent_events = [e for e in self.security_events if e.timestamp > last_24h]
            weekly_events = [e for e in self.security_events if e.timestamp > last_7d]
            
            active_sessions = len([s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE])
            security_alerts = len([a for a in self.security_alerts if not a.resolved])
            
            # Event type breakdown
            event_types = {}
            for event in recent_events:
                event_type = event.event_type.value
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Threat level breakdown
            threat_levels = {}
            for event in recent_events:
                level = event.threat_level.value
                threat_levels[level] = threat_levels.get(level, 0) + 1
            
            return {
                'overview': {
                    'active_sessions': active_sessions,
                    'security_alerts': security_alerts,
                    'events_24h': len(recent_events),
                    'events_7d': len(weekly_events),
                    'api_keys_active': len([k for k in self.api_keys.values() if k.is_active])
                },
                'recent_events': [
                    {
                        'id': e.id,
                        'type': e.event_type.value,
                        'user_id': e.user_id,
                        'ip_address': e.ip_address,
                        'timestamp': e.timestamp.isoformat(),
                        'threat_level': e.threat_level.value,
                        'success': e.success
                    }
                    for e in sorted(recent_events, key=lambda x: x.timestamp, reverse=True)[:20]
                ],
                'event_breakdown': {
                    'by_type': event_types,
                    'by_threat_level': threat_levels
                },
                'security_alerts': [
                    {
                        'id': a.id,
                        'type': a.alert_type,
                        'severity': a.severity.value,
                        'description': a.description,
                        'timestamp': a.timestamp.isoformat(),
                        'resolved': a.resolved
                    }
                    for a in sorted(self.security_alerts, key=lambda x: x.timestamp, reverse=True)[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Security dashboard data generation failed: {e}")
            return {}

# Singleton instance
_security_service = None

def get_security_service() -> SecurityService:
    """Get singleton security service instance"""
    global _security_service
    if _security_service is None:
        _security_service = SecurityService()
    return _security_service

def create_security_service() -> SecurityService:
    """Create security service instance"""
    return SecurityService()

# Security decorators
def require_valid_session(f):
    """Decorator to require valid session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        token = auth_header.split(' ')[1]
        ip_address = request.remote_addr
        
        # Validate session
        security_service = get_security_service()
        validation_result = security_service.validate_session(token, ip_address)
        
        if not validation_result.get('valid'):
            return jsonify({'error': validation_result.get('error', 'Invalid session')}), 401
        
        # Add user info to request context
        request.user_id = validation_result['user_id']
        request.session_id = validation_result['session_id']
        request.user_permissions = validation_result['permissions']
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_api_key(f):
    """Decorator to require valid API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key
        security_service = get_security_service()
        validation_result = security_service.validate_api_key(api_key)
        
        if not validation_result.get('valid'):
            return jsonify({'error': validation_result.get('error', 'Invalid API key')}), 401
        
        # Add API key info to request context
        request.api_user_id = validation_result['user_id']
        request.api_permissions = validation_result['permissions']
        request.api_key_id = validation_result['api_key_id']
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limited(f):
    """Decorator to apply rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        # Get identifier (IP or user ID)
        identifier = request.remote_addr
        user_id = getattr(request, 'user_id', None)
        endpoint = request.endpoint
        
        # Check rate limit
        security_service = get_security_service()
        rate_check = security_service.check_rate_limit(identifier, endpoint, user_id)
        
        if not rate_check.get('allowed'):
            response = jsonify({
                'error': rate_check.get('error', 'Rate limit exceeded'),
                'retry_after': rate_check.get('retry_after')
            })
            response.status_code = 429
            if 'retry_after' in rate_check:
                response.headers['Retry-After'] = str(rate_check['retry_after'])
            return response
        
        return f(*args, **kwargs)
    
    return decorated_function

if __name__ == "__main__":
    # Test the security service
    service = get_security_service()
    
    print("🔐 Security Service Test")
    
    # Test password hashing
    password = "test_password_123!"
    hashed = service.hash_password(password)
    verified = service.verify_password(password, hashed)
    print(f"Password hashing: {verified}")
    
    # Test session creation
    session_result = service.create_session(
        user_id=1,
        ip_address="192.168.1.100",
        user_agent="Test Browser",
        permissions=["read_property", "write_property"]
    )
    print(f"Session creation: {session_result.get('success', False)}")
    
    # Test session validation
    if session_result.get('success'):
        token = session_result['token']
        validation_result = service.validate_session(token, "192.168.1.100")
        print(f"Session validation: {validation_result.get('valid', False)}")
    
    # Test dashboard data
    dashboard = service.get_security_dashboard_data()
    print(f"Dashboard Data: {len(dashboard)} sections")
    
    print("✅ Security service is ready!")