from flask import Blueprint, request, jsonify, g
from estatecore_backend.models import db, User
from services.security_monitoring_service import security_monitor, ThreatLevel, AlertType
from services.rbac_service import require_permission
import logging

security_bp = Blueprint('security', __name__, url_prefix='/api/security')
logger = logging.getLogger(__name__)

@security_bp.route('/dashboard', methods=['GET'])
@require_permission('security:monitor')
def get_security_dashboard():
    """Get security dashboard data"""
    try:
        dashboard_data = security_monitor.get_security_dashboard_data()
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching security dashboard data: {str(e)}")
        return jsonify({'error': 'Failed to fetch security dashboard data'}), 500

@security_bp.route('/alerts', methods=['GET'])
@require_permission('security:monitor')
def get_security_alerts():
    """Get security alerts with optional filtering"""
    try:
        threat_level = request.args.get('threat_level')
        alert_type = request.args.get('alert_type')
        resolved = request.args.get('resolved')
        limit = request.args.get('limit', 50, type=int)
        
        alerts = security_monitor.active_alerts.copy()
        
        # Apply filters
        if threat_level:
            alerts = [alert for alert in alerts if alert.threat_level.value == threat_level]
        
        if alert_type:
            alerts = [alert for alert in alerts if alert.alert_type.value == alert_type]
        
        if resolved is not None:
            is_resolved = resolved.lower() == 'true'
            alerts = [alert for alert in alerts if alert.is_resolved == is_resolved]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        alerts = alerts[:limit]
        
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts],
            'total': len(security_monitor.active_alerts),
            'filtered': len(alerts)
        })
        
    except Exception as e:
        logger.error(f"Error fetching security alerts: {str(e)}")
        return jsonify({'error': 'Failed to fetch security alerts'}), 500

@security_bp.route('/alerts/<alert_id>/resolve', methods=['POST'])
@require_permission('security:manage')
def resolve_alert(alert_id):
    """Resolve a security alert"""
    try:
        data = request.get_json() or {}
        resolution_notes = data.get('resolution_notes', '')
        
        success = security_monitor.resolve_alert(alert_id, resolution_notes)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Alert resolved successfully'
            })
        else:
            return jsonify({'error': 'Alert not found'}), 404
            
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {str(e)}")
        return jsonify({'error': 'Failed to resolve alert'}), 500

@security_bp.route('/block-ip', methods=['POST'])
@require_permission('security:manage')
def block_ip():
    """Block an IP address"""
    try:
        data = request.get_json()
        
        if not data or not data.get('ip_address'):
            return jsonify({'error': 'IP address is required'}), 400
        
        ip_address = data['ip_address']
        reason = data.get('reason', 'Manual block by security team')
        duration_hours = data.get('duration_hours', 24)
        
        success = security_monitor.block_ip(ip_address, reason, duration_hours)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'IP {ip_address} has been blocked for {duration_hours} hours'
            })
        else:
            return jsonify({'error': 'Failed to block IP address'}), 500
            
    except Exception as e:
        logger.error(f"Error blocking IP: {str(e)}")
        return jsonify({'error': 'Failed to block IP address'}), 500

@security_bp.route('/scan-request', methods=['POST'])
@require_permission('security:configure')
def scan_request():
    """Manually scan a request for threats"""
    try:
        data = request.get_json()
        
        if not data or not data.get('request_data'):
            return jsonify({'error': 'Request data is required'}), 400
        
        request_data = data['request_data']
        ip_address = data.get('ip_address', request.remote_addr)
        user_id = data.get('user_id')
        
        alerts = security_monitor.scan_request_for_threats(
            request_data=request_data,
            ip_address=ip_address,
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'threats_detected': len(alerts),
            'alerts': [alert.to_dict() for alert in alerts]
        })
        
    except Exception as e:
        logger.error(f"Error scanning request: {str(e)}")
        return jsonify({'error': 'Failed to scan request'}), 500

@security_bp.route('/user-behavior/<int:user_id>', methods=['GET'])
@require_permission('security:monitor')
def analyze_user_behavior(user_id):
    """Analyze user behavior for anomalies"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get recent user activity for analysis
        from models.rbac import AccessLog
        from datetime import datetime, timedelta
        
        recent_logs = AccessLog.query.filter_by(user_id=user_id).filter(
            AccessLog.timestamp > datetime.utcnow() - timedelta(days=30)
        ).order_by(AccessLog.timestamp.desc()).limit(100).all()
        
        # Analyze patterns
        access_hours = [log.timestamp.hour for log in recent_logs]
        resources_accessed = [log.resource for log in recent_logs]
        ip_addresses = list(set([log.ip_address for log in recent_logs if log.ip_address]))
        
        # Calculate activity patterns
        activity_by_hour = {}
        for hour in range(24):
            activity_by_hour[hour] = access_hours.count(hour)
        
        resource_frequency = {}
        for resource in set(resources_accessed):
            resource_frequency[resource] = resources_accessed.count(resource)
        
        # Check for anomalies
        alerts = security_monitor.detect_anomalous_behavior(
            user_id=user_id,
            action='behavior_analysis',
            metadata={'analysis_type': 'manual_review'}
        )
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            },
            'analysis': {
                'total_activities': len(recent_logs),
                'unique_ips': len(ip_addresses),
                'activity_by_hour': activity_by_hour,
                'resource_frequency': resource_frequency,
                'ip_addresses': ip_addresses
            },
            'anomalies_detected': len(alerts),
            'alerts': [alert.to_dict() for alert in alerts]
        })
        
    except Exception as e:
        logger.error(f"Error analyzing user behavior: {str(e)}")
        return jsonify({'error': 'Failed to analyze user behavior'}), 500

@security_bp.route('/threat-intelligence', methods=['GET'])
@require_permission('security:monitor')
def get_threat_intelligence():
    """Get threat intelligence data"""
    try:
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        # Analyze threat patterns from recent alerts
        recent_alerts = [
            alert for alert in security_monitor.active_alerts
            if alert.timestamp > datetime.utcnow() - timedelta(days=7)
        ]
        
        # Group by IP address
        ip_threat_map = defaultdict(list)
        for alert in recent_alerts:
            ip_threat_map[alert.source_ip].append(alert)
        
        # Calculate threat scores
        threat_ips = []
        for ip, alerts in ip_threat_map.items():
            threat_score = sum([
                4 if alert.threat_level == ThreatLevel.CRITICAL else
                3 if alert.threat_level == ThreatLevel.HIGH else
                2 if alert.threat_level == ThreatLevel.MEDIUM else 1
                for alert in alerts
            ])
            
            threat_ips.append({
                'ip_address': ip,
                'alert_count': len(alerts),
                'threat_score': threat_score,
                'alert_types': list(set([alert.alert_type.value for alert in alerts])),
                'last_seen': max([alert.timestamp for alert in alerts]).isoformat()
            })
        
        # Sort by threat score
        threat_ips.sort(key=lambda x: x['threat_score'], reverse=True)
        
        # Analyze attack patterns
        attack_patterns = defaultdict(int)
        for alert in recent_alerts:
            attack_patterns[alert.alert_type.value] += 1
        
        # Geographic analysis (simplified - would use GeoIP in production)
        geographic_data = {
            'high_risk_regions': ['Unknown'],  # Would be populated with actual GeoIP data
            'attack_origins': {'Unknown': len(set([alert.source_ip for alert in recent_alerts]))}
        }
        
        return jsonify({
            'success': True,
            'threat_intelligence': {
                'top_threat_ips': threat_ips[:20],
                'attack_patterns': dict(attack_patterns),
                'geographic_data': geographic_data,
                'trending_threats': [
                    'Brute force attacks on login endpoints',
                    'SQL injection attempts in user input',
                    'Suspicious login patterns from new locations'
                ],
                'recommendations': [
                    'Implement stronger rate limiting on authentication endpoints',
                    'Enable MFA for all administrative accounts',
                    'Review and update input validation rules',
                    'Consider implementing geographic access restrictions'
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching threat intelligence: {str(e)}")
        return jsonify({'error': 'Failed to fetch threat intelligence'}), 500

@security_bp.route('/configure', methods=['GET', 'POST'])
@require_permission('security:configure')
def security_configuration():
    """Get or update security configuration"""
    if request.method == 'GET':
        try:
            # Return current security configuration
            config = {
                'rate_limiting': {
                    'enabled': True,
                    'default_limit': 30,
                    'login_limit': 5,
                    'api_limit': 100
                },
                'threat_detection': {
                    'sql_injection': True,
                    'xss_detection': True,
                    'brute_force': True,
                    'anomaly_detection': True
                },
                'alerting': {
                    'email_notifications': True,
                    'webhook_url': None,
                    'alert_thresholds': {
                        'critical': 'immediate',
                        'high': '5_minutes',
                        'medium': '1_hour',
                        'low': '24_hours'
                    }
                },
                'blocking': {
                    'auto_block_critical': True,
                    'auto_block_duration': 24,
                    'whitelist_ips': ['127.0.0.1', '::1']
                }
            }
            
            return jsonify({
                'success': True,
                'configuration': config
            })
            
        except Exception as e:
            logger.error(f"Error fetching security configuration: {str(e)}")
            return jsonify({'error': 'Failed to fetch security configuration'}), 500
    
    else:  # POST
        try:
            data = request.get_json()
            
            # In a real implementation, this would update the security configuration
            # For now, we'll just validate and return success
            
            required_sections = ['rate_limiting', 'threat_detection', 'alerting', 'blocking']
            for section in required_sections:
                if section not in data:
                    return jsonify({'error': f'Missing required section: {section}'}), 400
            
            # Log configuration change
            logger.info(f"Security configuration updated by user {g.current_user.id}")
            
            return jsonify({
                'success': True,
                'message': 'Security configuration updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating security configuration: {str(e)}")
            return jsonify({'error': 'Failed to update security configuration'}), 500

@security_bp.route('/health', methods=['GET'])
def security_health_check():
    """Security monitoring system health check"""
    try:
        health_status = {
            'status': 'healthy',
            'monitoring_active': True,
            'active_alerts': len(security_monitor.active_alerts),
            'unresolved_alerts': len([a for a in security_monitor.active_alerts if not a.is_resolved]),
            'last_alert': None
        }
        
        if security_monitor.active_alerts:
            latest_alert = max(security_monitor.active_alerts, key=lambda x: x.timestamp)
            health_status['last_alert'] = latest_alert.timestamp.isoformat()
        
        return jsonify({
            'success': True,
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"Security health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Middleware to monitor all requests
@security_bp.before_app_request
def monitor_request():
    """Monitor incoming requests for security threats"""
    try:
        # Skip monitoring for security endpoints to avoid recursion
        if request.endpoint and request.endpoint.startswith('security.'):
            return
        
        # Get request data for analysis
        request_data = ''
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.is_json:
                    request_data = str(request.get_json())
                else:
                    request_data = str(request.form)
            except:
                pass  # Ignore if we can't read request data
        
        # Add query parameters
        if request.args:
            request_data += str(request.args)
        
        # Monitor login attempts
        if request.endpoint == 'auth.login' and request.method == 'POST':
            try:
                data = request.get_json() or {}
                email = data.get('email', '')
                
                # We'll check the response in the after_request handler
                # to determine if login was successful
                g.login_attempt = {
                    'email': email,
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            except:
                pass
        
        # Check rate limits
        if request.remote_addr and request.endpoint:
            security_monitor.check_rate_limits(
                ip_address=request.remote_addr,
                endpoint=request.endpoint,
                user_id=getattr(g, 'current_user', {}).get('id') if hasattr(g, 'current_user') else None
            )
        
        # Scan request for threats
        if request_data and request.remote_addr:
            security_monitor.scan_request_for_threats(
                request_data=request_data,
                ip_address=request.remote_addr,
                user_id=getattr(g, 'current_user', {}).get('id') if hasattr(g, 'current_user') else None
            )
            
    except Exception as e:
        logger.error(f"Error in security monitoring middleware: {str(e)}")

@security_bp.after_app_request
def monitor_response(response):
    """Monitor responses for security analysis"""
    try:
        # Monitor login attempt results
        if hasattr(g, 'login_attempt') and request.endpoint == 'auth.login':
            login_data = g.login_attempt
            success = response.status_code == 200
            
            # Extract user_id if login was successful
            user_id = None
            if success:
                try:
                    # In a real implementation, extract user_id from response or session
                    user = User.query.filter_by(email=login_data['email']).first()
                    if user:
                        user_id = user.id
                except:
                    pass
            
            security_monitor.monitor_login_attempt(
                email=login_data['email'],
                ip_address=login_data['ip_address'],
                user_agent=login_data['user_agent'],
                success=success,
                user_id=user_id
            )
        
    except Exception as e:
        logger.error(f"Error in security response monitoring: {str(e)}")
    
    return response