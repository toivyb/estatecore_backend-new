import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import ipaddress
from collections import defaultdict
import re

from flask import current_app, request
from estatecore_backend.models import db, User
from models.rbac import AccessLog
from services.rbac_service import RBACService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    BRUTE_FORCE = "brute_force"
    SUSPICIOUS_LOGIN = "suspicious_login"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    MALICIOUS_FILE = "malicious_file"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTACK = "csrf_attack"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

@dataclass
class SecurityAlert:
    id: str
    alert_type: AlertType
    threat_level: ThreatLevel
    title: str
    description: str
    source_ip: str
    user_id: Optional[int]
    timestamp: datetime
    metadata: Dict[str, Any]
    is_resolved: bool = False
    resolution_notes: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type.value,
            'threat_level': self.threat_level.value,
            'title': self.title,
            'description': self.description,
            'source_ip': self.source_ip,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'is_resolved': self.is_resolved,
            'resolution_notes': self.resolution_notes
        }

class SecurityMonitoringService:
    """Advanced security monitoring and threat detection service"""
    
    def __init__(self):
        self.active_alerts = []
        self.ip_tracking = defaultdict(list)
        self.user_sessions = defaultdict(dict)
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.rate_limits = defaultdict(lambda: defaultdict(list))
        
    def _load_suspicious_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for detecting malicious activity"""
        return {
            'sql_injection': [
                r"(\bunion\b.*\bselect\b)",
                r"(\bselect\b.*\bfrom\b.*\bwhere\b)",
                r"(\bdrop\b.*\btable\b)",
                r"(\binsert\b.*\binto\b)",
                r"(\bdelete\b.*\bfrom\b)",
                r"(\bupdate\b.*\bset\b)",
                r"(\b(or|and)\b.*\b(1=1|1='1')\b)",
                r"(\b(exec|execute)\b.*\b(sp_|xp_)\b)"
            ],
            'xss': [
                r"<script.*?>.*?</script>",
                r"javascript:",
                r"vbscript:",
                r"onload\s*=",
                r"onerror\s*=",
                r"onclick\s*=",
                r"<iframe.*?>",
                r"document\.cookie",
                r"window\.location"
            ],
            'path_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"/etc/passwd",
                r"/etc/shadow",
                r"\\windows\\system32",
                r"cmd\.exe",
                r"powershell\.exe"
            ]
        }
    
    def monitor_login_attempt(self, email: str, ip_address: str, user_agent: str, 
                            success: bool, user_id: Optional[int] = None) -> List[SecurityAlert]:
        """Monitor login attempts for suspicious activity"""
        alerts = []
        
        # Track login attempts per IP
        self.ip_tracking[ip_address].append({
            'timestamp': datetime.utcnow(),
            'email': email,
            'success': success,
            'user_agent': user_agent
        })
        
        # Check for brute force attacks
        recent_attempts = [
            attempt for attempt in self.ip_tracking[ip_address]
            if attempt['timestamp'] > datetime.utcnow() - timedelta(minutes=15)
        ]
        
        failed_attempts = [attempt for attempt in recent_attempts if not attempt['success']]
        
        if len(failed_attempts) >= 5:
            alert = SecurityAlert(
                id=self._generate_alert_id(),
                alert_type=AlertType.BRUTE_FORCE,
                threat_level=ThreatLevel.HIGH,
                title="Brute Force Attack Detected",
                description=f"Multiple failed login attempts from IP {ip_address}",
                source_ip=ip_address,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                metadata={
                    'failed_attempts': len(failed_attempts),
                    'target_emails': list(set([attempt['email'] for attempt in failed_attempts])),
                    'user_agents': list(set([attempt['user_agent'] for attempt in failed_attempts]))
                }
            )
            alerts.append(alert)
        
        # Check for suspicious login patterns
        if success and user_id:
            user_previous_ips = self._get_user_ip_history(user_id)
            if user_previous_ips and ip_address not in user_previous_ips:
                # Check geographic anomaly (simplified - would need GeoIP in production)
                alert = SecurityAlert(
                    id=self._generate_alert_id(),
                    alert_type=AlertType.SUSPICIOUS_LOGIN,
                    threat_level=ThreatLevel.MEDIUM,
                    title="Login from New Location",
                    description=f"User logged in from previously unseen IP address",
                    source_ip=ip_address,
                    user_id=user_id,
                    timestamp=datetime.utcnow(),
                    metadata={
                        'email': email,
                        'user_agent': user_agent,
                        'previous_ips': user_previous_ips[-5:]  # Last 5 IPs
                    }
                )
                alerts.append(alert)
        
        # Store alerts
        for alert in alerts:
            self.active_alerts.append(alert)
            self._notify_security_team(alert)
        
        return alerts
    
    def monitor_access_attempt(self, user_id: int, action: str, resource: str, 
                             permission_required: str, access_granted: bool,
                             ip_address: str, additional_data: Dict[str, Any] = None) -> List[SecurityAlert]:
        """Monitor access attempts for privilege escalation and unauthorized access"""
        alerts = []
        
        if not access_granted:
            # Track failed access attempts
            user_failed_attempts = [
                log for log in AccessLog.query.filter_by(
                    user_id=user_id,
                    access_granted=False
                ).filter(
                    AccessLog.timestamp > datetime.utcnow() - timedelta(minutes=30)
                ).all()
            ]
            
            if len(user_failed_attempts) >= 10:
                alert = SecurityAlert(
                    id=self._generate_alert_id(),
                    alert_type=AlertType.PRIVILEGE_ESCALATION,
                    threat_level=ThreatLevel.HIGH,
                    title="Potential Privilege Escalation Attempt",
                    description=f"User attempting to access resources without permission",
                    source_ip=ip_address,
                    user_id=user_id,
                    timestamp=datetime.utcnow(),
                    metadata={
                        'failed_attempts': len(user_failed_attempts),
                        'resources_attempted': list(set([log.resource for log in user_failed_attempts])),
                        'permissions_attempted': list(set([log.permission_required for log in user_failed_attempts]))
                    }
                )
                alerts.append(alert)
        
        # Check for sensitive resource access
        sensitive_resources = ['users', 'security', 'financial', 'admin']
        if any(resource.startswith(sr) for sr in sensitive_resources):
            if access_granted:
                user = User.query.get(user_id)
                if user and user.role not in ['admin', 'super_admin']:
                    alert = SecurityAlert(
                        id=self._generate_alert_id(),
                        alert_type=AlertType.UNAUTHORIZED_ACCESS,
                        threat_level=ThreatLevel.MEDIUM,
                        title="Sensitive Resource Access",
                        description=f"Non-admin user accessed sensitive resource: {resource}",
                        source_ip=ip_address,
                        user_id=user_id,
                        timestamp=datetime.utcnow(),
                        metadata={
                            'resource': resource,
                            'action': action,
                            'user_role': user.role,
                            'permission_used': permission_required
                        }
                    )
                    alerts.append(alert)
        
        # Store alerts
        for alert in alerts:
            self.active_alerts.append(alert)
            self._notify_security_team(alert)
        
        return alerts
    
    def scan_request_for_threats(self, request_data: str, ip_address: str, 
                                user_id: Optional[int] = None) -> List[SecurityAlert]:
        """Scan incoming requests for malicious patterns"""
        alerts = []
        
        # Check for SQL injection
        for pattern in self.suspicious_patterns['sql_injection']:
            if re.search(pattern, request_data, re.IGNORECASE):
                alert = SecurityAlert(
                    id=self._generate_alert_id(),
                    alert_type=AlertType.SQL_INJECTION,
                    threat_level=ThreatLevel.CRITICAL,
                    title="SQL Injection Attempt Detected",
                    description="Malicious SQL patterns found in request",
                    source_ip=ip_address,
                    user_id=user_id,
                    timestamp=datetime.utcnow(),
                    metadata={
                        'pattern_matched': pattern,
                        'request_snippet': request_data[:200]
                    }
                )
                alerts.append(alert)
                break
        
        # Check for XSS
        for pattern in self.suspicious_patterns['xss']:
            if re.search(pattern, request_data, re.IGNORECASE):
                alert = SecurityAlert(
                    id=self._generate_alert_id(),
                    alert_type=AlertType.XSS_ATTEMPT,
                    threat_level=ThreatLevel.HIGH,
                    title="Cross-Site Scripting Attempt",
                    description="Malicious JavaScript patterns found in request",
                    source_ip=ip_address,
                    user_id=user_id,
                    timestamp=datetime.utcnow(),
                    metadata={
                        'pattern_matched': pattern,
                        'request_snippet': request_data[:200]
                    }
                )
                alerts.append(alert)
                break
        
        # Check for path traversal
        for pattern in self.suspicious_patterns['path_traversal']:
            if re.search(pattern, request_data, re.IGNORECASE):
                alert = SecurityAlert(
                    id=self._generate_alert_id(),
                    alert_type=AlertType.UNAUTHORIZED_ACCESS,
                    threat_level=ThreatLevel.HIGH,
                    title="Path Traversal Attempt",
                    description="Directory traversal patterns found in request",
                    source_ip=ip_address,
                    user_id=user_id,
                    timestamp=datetime.utcnow(),
                    metadata={
                        'pattern_matched': pattern,
                        'request_snippet': request_data[:200]
                    }
                )
                alerts.append(alert)
                break
        
        # Store alerts
        for alert in alerts:
            self.active_alerts.append(alert)
            self._notify_security_team(alert)
        
        return alerts
    
    def check_rate_limits(self, ip_address: str, endpoint: str, user_id: Optional[int] = None) -> List[SecurityAlert]:
        """Check and enforce rate limits"""
        alerts = []
        current_time = datetime.utcnow()
        
        # Clean old entries
        self.rate_limits[ip_address][endpoint] = [
            timestamp for timestamp in self.rate_limits[ip_address][endpoint]
            if timestamp > current_time - timedelta(minutes=1)
        ]
        
        # Add current request
        self.rate_limits[ip_address][endpoint].append(current_time)
        
        # Check if rate limit exceeded
        request_count = len(self.rate_limits[ip_address][endpoint])
        rate_limit = self._get_rate_limit_for_endpoint(endpoint)
        
        if request_count > rate_limit:
            alert = SecurityAlert(
                id=self._generate_alert_id(),
                alert_type=AlertType.RATE_LIMIT_EXCEEDED,
                threat_level=ThreatLevel.MEDIUM,
                title="Rate Limit Exceeded",
                description=f"IP {ip_address} exceeded rate limit for {endpoint}",
                source_ip=ip_address,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                metadata={
                    'endpoint': endpoint,
                    'request_count': request_count,
                    'rate_limit': rate_limit,
                    'time_window': '1 minute'
                }
            )
            alerts.append(alert)
            self.active_alerts.append(alert)
        
        return alerts
    
    def detect_anomalous_behavior(self, user_id: int, action: str, metadata: Dict[str, Any]) -> List[SecurityAlert]:
        """Detect anomalous user behavior patterns"""
        alerts = []
        
        # Get user's historical behavior
        user_logs = AccessLog.query.filter_by(user_id=user_id).filter(
            AccessLog.timestamp > datetime.utcnow() - timedelta(days=30)
        ).all()
        
        if len(user_logs) < 10:  # Not enough data for analysis
            return alerts
        
        # Analyze time patterns
        access_hours = [log.timestamp.hour for log in user_logs]
        current_hour = datetime.utcnow().hour
        
        # Check if accessing at unusual time
        if access_hours.count(current_hour) < len(access_hours) * 0.1:  # Less than 10% of historical access
            alert = SecurityAlert(
                id=self._generate_alert_id(),
                alert_type=AlertType.ANOMALOUS_BEHAVIOR,
                threat_level=ThreatLevel.LOW,
                title="Unusual Access Time",
                description=f"User accessing system at unusual time: {current_hour}:00",
                source_ip=request.remote_addr if request else 'unknown',
                user_id=user_id,
                timestamp=datetime.utcnow(),
                metadata={
                    'current_hour': current_hour,
                    'typical_hours': list(set(access_hours)),
                    'action': action
                }
            )
            alerts.append(alert)
        
        # Analyze resource access patterns
        accessed_resources = [log.resource for log in user_logs]
        current_resource = metadata.get('resource', action)
        
        if current_resource not in accessed_resources:
            alert = SecurityAlert(
                id=self._generate_alert_id(),
                alert_type=AlertType.ANOMALOUS_BEHAVIOR,
                threat_level=ThreatLevel.LOW,
                title="New Resource Access",
                description=f"User accessing new type of resource: {current_resource}",
                source_ip=request.remote_addr if request else 'unknown',
                user_id=user_id,
                timestamp=datetime.utcnow(),
                metadata={
                    'new_resource': current_resource,
                    'typical_resources': list(set(accessed_resources)),
                    'action': action
                }
            )
            alerts.append(alert)
        
        # Store alerts
        for alert in alerts:
            self.active_alerts.append(alert)
        
        return alerts
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Recent alerts
        recent_alerts = [
            alert for alert in self.active_alerts
            if alert.timestamp > last_24h
        ]
        
        # Alert statistics
        alert_stats = {
            'total_alerts': len(self.active_alerts),
            'alerts_24h': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a.threat_level == ThreatLevel.CRITICAL]),
            'high_alerts': len([a for a in recent_alerts if a.threat_level == ThreatLevel.HIGH]),
            'unresolved_alerts': len([a for a in self.active_alerts if not a.is_resolved])
        }
        
        # Top threat IPs
        ip_threat_count = defaultdict(int)
        for alert in recent_alerts:
            ip_threat_count[alert.source_ip] += 1
        
        top_threat_ips = sorted(ip_threat_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Alert types breakdown
        alert_types = defaultdict(int)
        for alert in recent_alerts:
            alert_types[alert.alert_type.value] += 1
        
        # Recent access logs
        recent_access_logs = AccessLog.query.filter(
            AccessLog.timestamp > last_24h
        ).order_by(AccessLog.timestamp.desc()).limit(100).all()
        
        return {
            'alert_stats': alert_stats,
            'recent_alerts': [alert.to_dict() for alert in recent_alerts[:20]],
            'top_threat_ips': top_threat_ips,
            'alert_types': dict(alert_types),
            'recent_access_logs': [
                {
                    'id': log.id,
                    'user_id': log.user_id,
                    'action': log.action,
                    'resource': log.resource,
                    'access_granted': log.access_granted,
                    'ip_address': log.ip_address,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in recent_access_logs
            ]
        }
    
    def resolve_alert(self, alert_id: str, resolution_notes: str) -> bool:
        """Resolve a security alert"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.is_resolved = True
                alert.resolution_notes = resolution_notes
                return True
        return False
    
    def block_ip(self, ip_address: str, reason: str, duration_hours: int = 24) -> bool:
        """Block an IP address"""
        # In a real implementation, this would integrate with firewall/WAF
        logger.warning(f"Blocking IP {ip_address} for {duration_hours} hours. Reason: {reason}")
        
        # Create alert for IP blocking
        alert = SecurityAlert(
            id=self._generate_alert_id(),
            alert_type=AlertType.UNAUTHORIZED_ACCESS,
            threat_level=ThreatLevel.HIGH,
            title="IP Address Blocked",
            description=f"IP {ip_address} has been blocked due to security concerns",
            source_ip=ip_address,
            user_id=None,
            timestamp=datetime.utcnow(),
            metadata={
                'reason': reason,
                'duration_hours': duration_hours,
                'blocked_by': 'automated_system'
            }
        )
        self.active_alerts.append(alert)
        
        return True
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"SEC_{timestamp}_{len(self.active_alerts):04d}"
    
    def _get_user_ip_history(self, user_id: int) -> List[str]:
        """Get user's IP address history"""
        logs = AccessLog.query.filter_by(user_id=user_id).filter(
            AccessLog.timestamp > datetime.utcnow() - timedelta(days=30)
        ).all()
        
        return list(set([log.ip_address for log in logs if log.ip_address]))
    
    def _get_rate_limit_for_endpoint(self, endpoint: str) -> int:
        """Get rate limit for specific endpoint"""
        rate_limits = {
            '/api/auth/login': 5,
            '/api/users': 10,
            '/api/properties': 20,
            '/api/payments': 15,
            'default': 30
        }
        
        for pattern, limit in rate_limits.items():
            if pattern in endpoint:
                return limit
        
        return rate_limits['default']
    
    def _notify_security_team(self, alert: SecurityAlert):
        """Notify security team of new alert"""
        if alert.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            logger.critical(f"SECURITY ALERT: {alert.title} - {alert.description}")
            # In production: send email, SMS, Slack notification, etc.
        else:
            logger.warning(f"Security Alert: {alert.title}")

# Global instance
security_monitor = SecurityMonitoringService()