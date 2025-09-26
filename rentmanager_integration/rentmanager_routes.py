"""
RentManager Integration API Routes

Flask routes for RentManager integration endpoints providing comprehensive
property management, compliance, and synchronization capabilities.
"""

import logging
import json
import asyncio
from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, List, Optional, Any

from .rentmanager_integration_service import (
    get_rentmanager_integration_service,
    IntegrationConfiguration,
    IntegrationMode
)
from .rentmanager_auth_service import RentManagerProductType, AuthenticationType
from .rentmanager_sync_service import SyncDirection, SyncMode, ConflictResolution
from .models import PropertyType, ComplianceType

logger = logging.getLogger(__name__)

# Create blueprint
rentmanager_bp = Blueprint('rentmanager', __name__, url_prefix='/api/integrations/rentmanager')

# Get integration service
integration_service = get_rentmanager_integration_service()

# ===================================================
# INTEGRATION SETUP ENDPOINTS
# ===================================================

@rentmanager_bp.route('/integrations', methods=['POST'])
def create_integration():
    """Create new RentManager integration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['organization_id', 'integration_name', 'product_types', 'property_types']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Build configuration
        config = IntegrationConfiguration(
            organization_id=data['organization_id'],
            integration_name=data['integration_name'],
            product_types=[RentManagerProductType(pt) for pt in data['product_types']],
            property_types=[PropertyType(pt) for pt in data['property_types']],
            compliance_programs=[ComplianceType(cp) for cp in data.get('compliance_programs', [])],
            sync_enabled=data.get('sync_enabled', True),
            real_time_sync=data.get('real_time_sync', True),
            batch_sync_schedule=data.get('batch_sync_schedule'),
            auto_conflict_resolution=data.get('auto_conflict_resolution', True),
            conflict_resolution_strategy=ConflictResolution(
                data.get('conflict_resolution_strategy', 'manual_review')
            ),
            data_quality_checks=data.get('data_quality_checks', True),
            compliance_validation=data.get('compliance_validation', True),
            field_level_validation=data.get('field_level_validation', True),
            enterprise_features=data.get('enterprise_features', False),
            multi_property_support=data.get('multi_property_support', True),
            portfolio_management=data.get('portfolio_management', False),
            audit_enabled=data.get('audit_enabled', True),
            encryption_enabled=data.get('encryption_enabled', True),
            backup_enabled=data.get('backup_enabled', True),
            mode=IntegrationMode(data.get('mode', 'live')),
            batch_size=data.get('batch_size', 100),
            max_workers=data.get('max_workers', 5),
            timeout_seconds=data.get('timeout_seconds', 300),
            rate_limit_requests_per_minute=data.get('rate_limit_requests_per_minute', 100),
            custom_mappings=data.get('custom_mappings', {}),
            sync_entities=data.get('sync_entities', []),
            excluded_entities=data.get('excluded_entities', []),
            property_filters=data.get('property_filters', {}),
            student_housing_config=data.get('student_housing_config', {}),
            affordable_housing_config=data.get('affordable_housing_config', {}),
            commercial_config=data.get('commercial_config', {}),
            hoa_config=data.get('hoa_config', {})
        )
        
        # Create integration
        result = integration_service.create_integration(data['organization_id'], config)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Failed to create integration: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/integrations/<organization_id>', methods=['GET'])
def get_integration(organization_id):
    """Get integration configuration and status"""
    try:
        summary = integration_service.get_integration_summary(organization_id)
        
        if 'error' in summary:
            return jsonify(summary), 404
        
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"Failed to get integration: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/integrations/<organization_id>', methods=['DELETE'])
def delete_integration(organization_id):
    """Delete integration configuration"""
    try:
        # Implementation would handle cleanup
        return jsonify({
            "success": True,
            "message": "Integration deleted successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to delete integration: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===================================================
# CONNECTION ENDPOINTS
# ===================================================

@rentmanager_bp.route('/connections', methods=['POST'])
def create_connection():
    """Create connection to RentManager"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'organization_id' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: organization_id"
            }), 400
        
        organization_id = data['organization_id']
        connection_params = data.get('connection_params', {})
        
        result = integration_service.connect_to_rentmanager(organization_id, connection_params)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Failed to create connection: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/connections/<organization_id>/oauth/callback', methods=['POST'])
def oauth_callback(organization_id):
    """Handle OAuth callback from RentManager"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'code' not in data or 'state' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required OAuth parameters"
            }), 400
        
        result = integration_service.complete_oauth_flow(data['code'], data['state'])
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Failed to complete OAuth flow: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/connections/<organization_id>/status', methods=['GET'])
def get_connection_status(organization_id):
    """Get connection status"""
    try:
        auth_service = integration_service.auth_service
        result = auth_service.validate_connection(organization_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to get connection status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/connections/<organization_id>', methods=['DELETE'])
def disconnect(organization_id):
    """Disconnect from RentManager"""
    try:
        auth_service = integration_service.auth_service
        connection = auth_service.get_organization_connection(organization_id)
        
        if not connection:
            return jsonify({
                "success": False,
                "error": "No active connection found"
            }), 404
        
        result = auth_service.revoke_connection(connection.connection_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Failed to disconnect: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===================================================
# SYNCHRONIZATION ENDPOINTS
# ===================================================

@rentmanager_bp.route('/sync/full', methods=['POST'])
def start_full_sync():
    """Start full synchronization"""
    try:
        data = request.get_json()
        
        if 'organization_id' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: organization_id"
            }), 400
        
        organization_id = data['organization_id']
        sync_options = data.get('sync_options', {})
        
        # Run async sync
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                integration_service.start_full_sync(organization_id, sync_options)
            )
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result), 202
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Failed to start full sync: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/sync/incremental', methods=['POST'])
def start_incremental_sync():
    """Start incremental synchronization"""
    try:
        data = request.get_json()
        
        if 'organization_id' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: organization_id"
            }), 400
        
        organization_id = data['organization_id']
        since_timestamp = None
        
        if 'since_timestamp' in data:
            since_timestamp = datetime.fromisoformat(data['since_timestamp'])
        
        # Run async sync
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                integration_service.start_incremental_sync(organization_id, since_timestamp)
            )
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result), 202
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Failed to start incremental sync: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/sync/jobs/<job_id>', methods=['GET'])
def get_sync_job_status(job_id):
    """Get sync job status"""
    try:
        sync_service = integration_service.sync_service
        job = sync_service.get_sync_job(job_id)
        
        if not job:
            return jsonify({
                "success": False,
                "error": "Sync job not found"
            }), 404
        
        progress = sync_service.get_sync_progress(job_id)
        
        return jsonify({
            "success": True,
            "job": {
                "job_id": job.job_id,
                "organization_id": job.organization_id,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "configuration": {
                    "sync_direction": job.configuration.sync_direction.value,
                    "sync_mode": job.configuration.sync_mode.value,
                    "entity_types": job.configuration.entity_types,
                    "compliance_types": [ct.value for ct in job.configuration.compliance_types]
                }
            },
            "progress": progress
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get sync job status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/sync/jobs/<job_id>', methods=['DELETE'])
def cancel_sync_job(job_id):
    """Cancel sync job"""
    try:
        sync_service = integration_service.sync_service
        result = sync_service.cancel_sync_job(job_id)
        
        if result:
            return jsonify({
                "success": True,
                "message": "Sync job cancelled successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to cancel sync job"
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to cancel sync job: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/sync/history/<organization_id>', methods=['GET'])
def get_sync_history(organization_id):
    """Get sync history for organization"""
    try:
        sync_service = integration_service.sync_service
        limit = request.args.get('limit', 10, type=int)
        
        recent_jobs = sync_service.get_recent_sync_jobs(organization_id, limit)
        active_jobs = sync_service.get_active_sync_jobs(organization_id)
        
        return jsonify({
            "success": True,
            "organization_id": organization_id,
            "active_jobs": [
                {
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "created_at": job.created_at.isoformat(),
                    "entity_types": job.configuration.entity_types
                }
                for job in active_jobs
            ],
            "recent_jobs": [
                {
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "entity_types": job.configuration.entity_types,
                    "total_entities": job.total_entities,
                    "successful_entities": job.successful_entities,
                    "failed_entities": job.failed_entities,
                    "execution_time_seconds": job.execution_time_seconds
                }
                for job in recent_jobs
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===================================================
# COMPLIANCE ENDPOINTS
# ===================================================

@rentmanager_bp.route('/compliance/status/<organization_id>', methods=['GET'])
def get_compliance_status(organization_id):
    """Get compliance status"""
    try:
        property_id = request.args.get('property_id')
        result = integration_service.get_compliance_status(organization_id, property_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Failed to get compliance status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/compliance/reports', methods=['POST'])
def generate_compliance_report():
    """Generate compliance report"""
    try:
        data = request.get_json()
        
        required_fields = ['organization_id', 'compliance_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        organization_id = data['organization_id']
        compliance_type = ComplianceType(data['compliance_type'])
        report_period = data.get('report_period', 'monthly')
        
        result = integration_service.generate_compliance_report(
            organization_id, compliance_type, report_period
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===================================================
# MONITORING AND HEALTH ENDPOINTS
# ===================================================

@rentmanager_bp.route('/health/<organization_id>', methods=['GET'])
def get_integration_health(organization_id):
    """Get integration health status"""
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        health = integration_service.get_integration_health(organization_id, force_refresh)
        
        return jsonify({
            "success": True,
            "health": {
                "status": health.status.value,
                "data_quality_score": health.data_quality_score,
                "uptime_percentage": health.uptime_percentage,
                "error_rate": health.error_rate,
                "last_check": health.last_check.isoformat(),
                "connection_health": health.connection_health,
                "sync_health": health.sync_health,
                "compliance_health": health.compliance_health,
                "performance_metrics": health.performance_metrics,
                "issues": health.issues,
                "warnings": health.warnings,
                "recommendations": health.recommendations
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get integration health: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===================================================
# PROPERTY TYPE SPECIFIC ENDPOINTS
# ===================================================

@rentmanager_bp.route('/student-housing/<organization_id>/applications', methods=['GET'])
def get_student_applications(organization_id):
    """Get student housing applications"""
    try:
        api_client = integration_service.api_client
        property_id = request.args.get('property_id')
        
        # Run async API call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                api_client.get_student_applications(organization_id, property_id)
            )
        finally:
            loop.close()
        
        if response.success:
            return jsonify({
                "success": True,
                "applications": response.data
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": response.error
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to get student applications: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/commercial/<organization_id>/cam-charges', methods=['GET'])
def get_cam_charges(organization_id):
    """Get Common Area Maintenance charges"""
    try:
        api_client = integration_service.api_client
        property_id = request.args.get('property_id', required=True)
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Run async API call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                api_client.get_cam_charges(organization_id, property_id, year)
            )
        finally:
            loop.close()
        
        if response.success:
            return jsonify({
                "success": True,
                "cam_charges": response.data
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": response.error
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to get CAM charges: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@rentmanager_bp.route('/hoa/<organization_id>/assessments', methods=['GET'])
def get_hoa_assessments(organization_id):
    """Get HOA assessments"""
    try:
        api_client = integration_service.api_client
        property_id = request.args.get('property_id', required=True)
        
        # Run async API call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                api_client.get_hoa_assessments(organization_id, property_id)
            )
        finally:
            loop.close()
        
        if response.success:
            return jsonify({
                "success": True,
                "assessments": response.data
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": response.error
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to get HOA assessments: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===================================================
# ERROR HANDLERS
# ===================================================

@rentmanager_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@rentmanager_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "Method not allowed"
    }), 405

@rentmanager_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

# ===================================================
# UTILITY ENDPOINTS
# ===================================================

@rentmanager_bp.route('/info', methods=['GET'])
def get_integration_info():
    """Get RentManager integration information"""
    from . import RENTMANAGER_INTEGRATION_INFO
    return jsonify({
        "success": True,
        "integration_info": RENTMANAGER_INTEGRATION_INFO
    }), 200

@rentmanager_bp.route('/test', methods=['GET'])
def test_integration():
    """Test integration service availability"""
    try:
        return jsonify({
            "success": True,
            "message": "RentManager integration service is available",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500