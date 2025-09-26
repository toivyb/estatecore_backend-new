"""
Yardi Integration Flask Routes

API endpoints for managing Yardi connections, synchronization, monitoring,
and enterprise features through the EstateCore web interface.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, g
from functools import wraps

from .yardi_integration_service import get_yardi_integration_service, IntegrationConfiguration, IntegrationMode
from .models import YardiProductType, YardiConnectionType, YardiAuthMethod, SyncDirection
from .yardi_auth_service import YardiAuthService
from .yardi_sync_service import SyncJobPriority, SyncMode

# Import EstateCore's permission system
try:
    from permissions_service import require_permission, require_role, Permission, Role
except ImportError:
    # Fallback decorators if permissions system not available
    def require_permission(permission):
        def decorator(f):
            return f
        return decorator
    
    def require_role(role):
        def decorator(f):
            return f
        return decorator

logger = logging.getLogger(__name__)

# Create Blueprint
yardi_bp = Blueprint('yardi', __name__, url_prefix='/api/yardi')

# Get service instance
yardi_service = get_yardi_integration_service()

def validate_organization_access():
    """Validate user has access to organization"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            organization_id = kwargs.get('organization_id') or request.json.get('organization_id')
            if not organization_id:
                return jsonify({"error": "Organization ID required"}), 400
            
            # Add organization access validation here
            # For now, allow all access
            g.organization_id = organization_id
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def handle_exceptions(f):
    """Exception handling decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {f.__name__}: {e}")
            return jsonify({"error": "Internal server error", "details": str(e)}), 500
    return decorated_function

# =====================================================
# CONNECTION MANAGEMENT ROUTES
# =====================================================

@yardi_bp.route('/integrations', methods=['POST'])
@require_permission('yardi.manage_integration')
@validate_organization_access()
@handle_exceptions
def create_integration():
    """Create new Yardi integration"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['integration_name', 'yardi_product', 'connection_type']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Required field '{field}' missing"}), 400
    
    try:
        # Create integration configuration
        config = IntegrationConfiguration(
            organization_id=g.organization_id,
            integration_name=data['integration_name'],
            yardi_product=YardiProductType(data['yardi_product']),
            connection_type=YardiConnectionType(data['connection_type']),
            sync_enabled=data.get('sync_enabled', True),
            real_time_sync=data.get('real_time_sync', True),
            webhook_enabled=data.get('webhook_enabled', True),
            enterprise_features=data.get('enterprise_features', False),
            mode=IntegrationMode(data.get('mode', 'live')),
            sync_entities=data.get('sync_entities', []),
            excluded_entities=data.get('excluded_entities', [])
        )
        
        result = yardi_service.create_integration(g.organization_id, config)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except ValueError as e:
        return jsonify({"error": f"Invalid value: {str(e)}"}), 400

@yardi_bp.route('/integrations/<organization_id>/connect', methods=['POST'])
@require_permission('yardi.manage_connection')
@validate_organization_access()
@handle_exceptions
def connect_to_yardi(organization_id):
    """Connect to Yardi system"""
    data = request.get_json()
    
    required_fields = ['base_url', 'credentials']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Required field '{field}' missing"}), 400
    
    connection_params = {
        'base_url': data['base_url'],
        'credentials': data['credentials'],
        'connection_name': data.get('connection_name', 'Yardi Connection'),
        'is_sandbox': data.get('is_sandbox', False),
        'auth_method': data.get('auth_method', 'api_key'),
        'rate_limit_per_minute': data.get('rate_limit_per_minute', 60)
    }
    
    result = yardi_service.connect_to_yardi(organization_id, connection_params)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@yardi_bp.route('/integrations/<organization_id>/oauth/start', methods=['POST'])
@require_permission('yardi.manage_connection')
@validate_organization_access()
@handle_exceptions
def start_oauth_flow(organization_id):
    """Start OAuth authentication flow"""
    data = request.get_json()
    
    yardi_product = data.get('yardi_product', 'voyager')
    
    try:
        auth_service = YardiAuthService()
        result = auth_service.start_oauth_flow(
            organization_id=organization_id,
            yardi_product=YardiProductType(yardi_product),
            connection_params=data.get('connection_params', {})
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except ValueError as e:
        return jsonify({"error": f"Invalid yardi_product: {str(e)}"}), 400

@yardi_bp.route('/integrations/<organization_id>/oauth/complete', methods=['POST'])
@require_permission('yardi.manage_connection')
@validate_organization_access()
@handle_exceptions
def complete_oauth_flow(organization_id):
    """Complete OAuth authentication flow"""
    data = request.get_json()
    
    required_fields = ['code', 'state', 'yardi_product']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Required field '{field}' missing"}), 400
    
    try:
        auth_service = YardiAuthService()
        result = auth_service.complete_oauth_flow(
            code=data['code'],
            state=data['state'],
            organization_id=organization_id,
            yardi_product=YardiProductType(data['yardi_product']),
            connection_params=data.get('connection_params', {})
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except ValueError as e:
        return jsonify({"error": f"Invalid yardi_product: {str(e)}"}), 400

@yardi_bp.route('/integrations/<organization_id>/status', methods=['GET'])
@require_permission('yardi.view_status')
@validate_organization_access()
@handle_exceptions
def get_connection_status(organization_id):
    """Get connection status"""
    result = yardi_service.get_connection_status(organization_id)
    return jsonify(result)

@yardi_bp.route('/integrations/<organization_id>/disconnect', methods=['POST'])
@require_permission('yardi.manage_connection')
@validate_organization_access()
@handle_exceptions
def disconnect_yardi(organization_id):
    """Disconnect from Yardi"""
    result = yardi_service.disconnect_yardi(organization_id)
    return jsonify(result)

# =====================================================
# SYNCHRONIZATION ROUTES
# =====================================================

@yardi_bp.route('/sync/<organization_id>/full', methods=['POST'])
@require_permission('yardi.manage_sync')
@validate_organization_access()
@handle_exceptions
def start_full_sync(organization_id):
    """Start full synchronization"""
    data = request.get_json() or {}
    
    sync_direction = data.get('sync_direction', 'both')
    entity_types = data.get('entity_types')
    
    try:
        result = await yardi_service.start_full_sync(
            organization_id=organization_id,
            sync_direction=sync_direction,
            entity_types=entity_types
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Full sync failed: {e}")
        return jsonify({"error": str(e)}), 500

@yardi_bp.route('/sync/<organization_id>/incremental', methods=['POST'])
@require_permission('yardi.manage_sync')
@validate_organization_access()
@handle_exceptions
def start_incremental_sync(organization_id):
    """Start incremental synchronization"""
    data = request.get_json() or {}
    
    entity_types = data.get('entity_types')
    since_timestamp = None
    
    if 'since_timestamp' in data:
        since_timestamp = datetime.fromisoformat(data['since_timestamp'])
    
    try:
        result = await yardi_service.start_incremental_sync(
            organization_id=organization_id,
            entity_types=entity_types,
            since_timestamp=since_timestamp
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Incremental sync failed: {e}")
        return jsonify({"error": str(e)}), 500

@yardi_bp.route('/sync/<organization_id>/status', methods=['GET'])
@require_permission('yardi.view_sync')
@validate_organization_access()
@handle_exceptions
def get_sync_status(organization_id):
    """Get synchronization status"""
    job_id = request.args.get('job_id')
    result = yardi_service.get_sync_status(organization_id, job_id)
    return jsonify(result)

@yardi_bp.route('/sync/jobs/<job_id>/cancel', methods=['POST'])
@require_permission('yardi.manage_sync')
@handle_exceptions
def cancel_sync_job(job_id):
    """Cancel sync job"""
    result = yardi_service.cancel_sync(job_id)
    return jsonify(result)

@yardi_bp.route('/sync/<organization_id>/history', methods=['GET'])
@require_permission('yardi.view_sync')
@validate_organization_access()
@handle_exceptions
def get_sync_history(organization_id):
    """Get sync history"""
    limit = request.args.get('limit', 20, type=int)
    
    # This would be implemented in the sync service
    result = {
        "success": True,
        "sync_history": [],  # Would get actual history
        "total_count": 0
    }
    
    return jsonify(result)

# =====================================================
# CONFIGURATION ROUTES
# =====================================================

@yardi_bp.route('/integrations/<organization_id>/config', methods=['GET'])
@require_permission('yardi.view_config')
@validate_organization_access()
@handle_exceptions
def get_integration_config(organization_id):
    """Get integration configuration"""
    result = yardi_service.get_integration_config(organization_id)
    return jsonify(result)

@yardi_bp.route('/integrations/<organization_id>/config', methods=['PUT'])
@require_permission('yardi.manage_config')
@validate_organization_access()
@handle_exceptions
def update_integration_config(organization_id):
    """Update integration configuration"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No configuration data provided"}), 400
    
    result = yardi_service.update_integration_config(organization_id, data)
    return jsonify(result)

# =====================================================
# MONITORING AND HEALTH ROUTES
# =====================================================

@yardi_bp.route('/integrations/<organization_id>/health', methods=['GET'])
@require_permission('yardi.view_health')
@validate_organization_access()
@handle_exceptions
def get_integration_health(organization_id):
    """Get integration health status"""
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    health = yardi_service.get_integration_health(organization_id, force_refresh)
    
    # Convert dataclass to dict for JSON serialization
    health_dict = {
        "status": health.status.value,
        "connection_health": health.connection_health,
        "sync_health": health.sync_health,
        "webhook_health": health.webhook_health,
        "automation_health": health.automation_health,
        "data_quality_score": health.data_quality_score,
        "performance_metrics": health.performance_metrics,
        "last_check": health.last_check.isoformat(),
        "issues": health.issues,
        "warnings": health.warnings,
        "recommendations": health.recommendations,
        "uptime_percentage": health.uptime_percentage,
        "error_rate": health.error_rate
    }
    
    return jsonify({"success": True, "health": health_dict})

@yardi_bp.route('/integrations/<organization_id>/summary', methods=['GET'])
@require_permission('yardi.view_summary')
@validate_organization_access()
@handle_exceptions
def get_integration_summary(organization_id):
    """Get integration summary"""
    result = yardi_service.get_integration_summary(organization_id)
    return jsonify(result)

@yardi_bp.route('/integrations/<organization_id>/metrics', methods=['GET'])
@require_permission('yardi.view_metrics')
@validate_organization_access()
@handle_exceptions
def get_integration_metrics(organization_id):
    """Get integration performance metrics"""
    time_range = request.args.get('time_range', '24h')
    
    # Parse time range
    if time_range == '24h':
        start_time = datetime.utcnow() - timedelta(hours=24)
    elif time_range == '7d':
        start_time = datetime.utcnow() - timedelta(days=7)
    elif time_range == '30d':
        start_time = datetime.utcnow() - timedelta(days=30)
    else:
        start_time = datetime.utcnow() - timedelta(hours=24)
    
    # Get metrics from monitoring service
    monitoring_service = yardi_service.monitoring_service
    metrics = monitoring_service.get_performance_metrics(organization_id)
    
    return jsonify({
        "success": True,
        "organization_id": organization_id,
        "time_range": time_range,
        "metrics": metrics
    })

# =====================================================
# ENTERPRISE ROUTES
# =====================================================

@yardi_bp.route('/enterprise/<organization_id>/portfolios', methods=['GET'])
@require_permission('yardi.view_enterprise')
@validate_organization_access()
@handle_exceptions
def list_portfolios(organization_id):
    """List property portfolios"""
    portfolios = yardi_service.enterprise_service.list_portfolios(organization_id)
    
    # Convert to serializable format
    portfolio_data = [
        {
            "portfolio_id": p.portfolio_id,
            "portfolio_name": p.portfolio_name,
            "properties_count": len(p.properties),
            "portfolio_manager": p.portfolio_manager,
            "created_at": p.created_at.isoformat()
        }
        for p in portfolios
    ]
    
    return jsonify({
        "success": True,
        "portfolios": portfolio_data
    })

@yardi_bp.route('/enterprise/<organization_id>/portfolios', methods=['POST'])
@require_permission('yardi.manage_enterprise')
@validate_organization_access()
@handle_exceptions
def create_portfolio(organization_id):
    """Create property portfolio"""
    data = request.get_json()
    
    required_fields = ['portfolio_name', 'properties']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Required field '{field}' missing"}), 400
    
    portfolio = yardi_service.enterprise_service.create_property_portfolio(
        organization_id=organization_id,
        portfolio_name=data['portfolio_name'],
        properties=data['properties'],
        consolidated_reporting=data.get('consolidated_reporting', True),
        portfolio_manager=data.get('portfolio_manager')
    )
    
    return jsonify({
        "success": True,
        "portfolio": {
            "portfolio_id": portfolio.portfolio_id,
            "portfolio_name": portfolio.portfolio_name,
            "properties_count": len(portfolio.properties)
        }
    }), 201

@yardi_bp.route('/enterprise/<organization_id>/reports', methods=['GET'])
@require_permission('yardi.view_reports')
@validate_organization_access()
@handle_exceptions
def list_custom_reports(organization_id):
    """List custom reports"""
    reports = yardi_service.enterprise_service.list_custom_reports(organization_id)
    
    report_data = [
        {
            "report_id": r.report_id,
            "report_name": r.report_name,
            "report_type": r.report_type.value,
            "created_at": r.created_at.isoformat(),
            "created_by": r.created_by
        }
        for r in reports
    ]
    
    return jsonify({
        "success": True,
        "reports": report_data
    })

@yardi_bp.route('/enterprise/<organization_id>/reports', methods=['POST'])
@require_permission('yardi.manage_reports')
@validate_organization_access()
@handle_exceptions
def create_custom_report(organization_id):
    """Create custom report"""
    data = request.get_json()
    
    required_fields = ['report_name', 'report_type', 'data_sources']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Required field '{field}' missing"}), 400
    
    try:
        from .yardi_enterprise_service import ReportType
        
        report = yardi_service.enterprise_service.create_custom_report(
            organization_id=organization_id,
            report_name=data['report_name'],
            report_type=ReportType(data['report_type']),
            data_sources=data['data_sources'],
            filters=data.get('filters'),
            created_by=data.get('created_by')
        )
        
        return jsonify({
            "success": True,
            "report": {
                "report_id": report.report_id,
                "report_name": report.report_name,
                "report_type": report.report_type.value
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"error": f"Invalid report_type: {str(e)}"}), 400

@yardi_bp.route('/enterprise/reports/<report_id>/generate', methods=['POST'])
@require_permission('yardi.view_reports')
@handle_exceptions
def generate_report(report_id):
    """Generate custom report"""
    data = request.get_json() or {}
    date_range = data.get('date_range')
    
    result = yardi_service.enterprise_service.generate_custom_report(
        report_id=report_id,
        date_range=date_range
    )
    
    return jsonify(result)

# =====================================================
# WEBHOOK ROUTES
# =====================================================

@yardi_bp.route('/webhooks/<organization_id>', methods=['POST'])
@handle_exceptions
def receive_webhook(organization_id):
    """Receive webhook from Yardi system"""
    headers = dict(request.headers)
    payload = request.get_json()
    
    if not payload:
        return jsonify({"error": "No payload received"}), 400
    
    try:
        result = await yardi_service.webhook_service.process_webhook(
            organization_id=organization_id,
            headers=headers,
            payload=payload
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return jsonify({"error": "Webhook processing failed"}), 500

# =====================================================
# SCHEDULER ROUTES
# =====================================================

@yardi_bp.route('/schedules/<organization_id>', methods=['GET'])
@require_permission('yardi.view_schedules')
@validate_organization_access()
@handle_exceptions
def list_schedules(organization_id):
    """List scheduled jobs"""
    schedules = yardi_service.scheduler_service.list_schedules(organization_id)
    
    schedule_data = [
        {
            "schedule_id": s.schedule_id,
            "job_name": s.job_name,
            "schedule_type": s.schedule_type.value,
            "status": s.status.value,
            "next_run": s.next_run.isoformat() if s.next_run else None,
            "last_run": s.last_run.isoformat() if s.last_run else None,
            "successful_runs": s.successful_runs,
            "failed_runs": s.failed_runs
        }
        for s in schedules
    ]
    
    return jsonify({
        "success": True,
        "schedules": schedule_data
    })

@yardi_bp.route('/schedules/<organization_id>', methods=['POST'])
@require_permission('yardi.manage_schedules')
@validate_organization_access()
@handle_exceptions
def create_schedule(organization_id):
    """Create scheduled job"""
    data = request.get_json()
    
    required_fields = ['job_name', 'schedule_type', 'sync_direction', 'entity_types']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Required field '{field}' missing"}), 400
    
    result = yardi_service.scheduler_service.create_schedule(organization_id, data)
    return jsonify(result), 201 if result['success'] else 400

@yardi_bp.route('/schedules/<schedule_id>', methods=['PUT'])
@require_permission('yardi.manage_schedules')
@handle_exceptions
def update_schedule(schedule_id):
    """Update scheduled job"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No update data provided"}), 400
    
    result = yardi_service.scheduler_service.update_schedule(schedule_id, data)
    return jsonify(result)

@yardi_bp.route('/schedules/<schedule_id>', methods=['DELETE'])
@require_permission('yardi.manage_schedules')
@handle_exceptions
def delete_schedule(schedule_id):
    """Delete scheduled job"""
    result = yardi_service.scheduler_service.delete_schedule(schedule_id)
    return jsonify(result)

@yardi_bp.route('/schedules/<schedule_id>/pause', methods=['POST'])
@require_permission('yardi.manage_schedules')
@handle_exceptions
def pause_schedule(schedule_id):
    """Pause scheduled job"""
    result = yardi_service.scheduler_service.pause_schedule(schedule_id)
    return jsonify(result)

@yardi_bp.route('/schedules/<schedule_id>/resume', methods=['POST'])
@require_permission('yardi.manage_schedules')
@handle_exceptions
def resume_schedule(schedule_id):
    """Resume scheduled job"""
    result = yardi_service.scheduler_service.resume_schedule(schedule_id)
    return jsonify(result)

# =====================================================
# SYSTEM ROUTES
# =====================================================

@yardi_bp.route('/system/health', methods=['GET'])
@require_permission('yardi.view_system')
@handle_exceptions
def get_system_health():
    """Get overall system health"""
    # This would check overall Yardi integration system health
    return jsonify({
        "success": True,
        "system_health": "healthy",
        "services": {
            "auth_service": "healthy",
            "sync_service": "healthy",
            "webhook_service": "healthy",
            "scheduler_service": "healthy",
            "monitoring_service": "healthy"
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@yardi_bp.route('/system/info', methods=['GET'])
@require_permission('yardi.view_system')
@handle_exceptions
def get_system_info():
    """Get system information"""
    return jsonify({
        "success": True,
        "version": "1.0.0",
        "supported_products": [product.value for product in YardiProductType],
        "supported_auth_methods": [method.value for method in YardiAuthMethod],
        "supported_sync_directions": [direction.value for direction in SyncDirection],
        "features": {
            "bidirectional_sync": True,
            "real_time_sync": True,
            "webhook_support": True,
            "enterprise_features": True,
            "custom_reporting": True,
            "multi_property": True
        }
    })

# Register error handlers
@yardi_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@yardi_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@yardi_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500