"""
Flask Routes for QuickBooks Integration

Provides REST API endpoints for all QuickBooks integration functionality
integrated with the EstateCore API Gateway and authentication system.
"""

from flask import Blueprint, request, jsonify, redirect, session, current_app
from functools import wraps
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from .quickbooks_integration_service import get_quickbooks_integration_service
from .enterprise_features import AccessLevel, ReportType, IntegrationType
from .automation_engine import WorkflowType

logger = logging.getLogger(__name__)

# Create Blueprint
quickbooks_bp = Blueprint('quickbooks', __name__, url_prefix='/api/quickbooks')

# Get the integration service
integration_service = get_quickbooks_integration_service()

def auth_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This would integrate with EstateCore's authentication system
        # For now, we'll check for a basic session or API key
        
        auth_header = request.headers.get('Authorization')
        session_user = session.get('user_id')
        
        if not (auth_header or session_user):
            return jsonify({'error': 'Authentication required'}), 401
        
        # Extract organization_id from request or session
        # This would be handled by EstateCore's auth system
        organization_id = request.json.get('organization_id') if request.json else None
        organization_id = organization_id or request.args.get('organization_id')
        organization_id = organization_id or session.get('organization_id')
        
        if not organization_id:
            return jsonify({'error': 'Organization ID required'}), 400
        
        # Add to request context
        request.organization_id = organization_id
        request.user_id = session_user or 'api_user'
        
        return f(*args, **kwargs)
    return decorated_function

def enterprise_required(access_level: AccessLevel = AccessLevel.BASIC):
    """Decorator to require enterprise access level"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check user access level
            user_permissions = integration_service.enterprise_service.get_user_permissions(user_id)
            if not user_permissions:
                return jsonify({'error': 'Access denied'}), 403
            
            user_access_level = AccessLevel(user_permissions['access_level'])
            
            # Check if user has required access level
            access_levels = [AccessLevel.READ_ONLY, AccessLevel.BASIC, AccessLevel.ADVANCED, AccessLevel.FULL_ACCESS, AccessLevel.ADMIN]
            if access_levels.index(user_access_level) < access_levels.index(access_level):
                return jsonify({'error': 'Insufficient access level'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Connection Management Routes

@quickbooks_bp.route('/connect', methods=['POST'])
@auth_required
def start_connection():
    """Start QuickBooks OAuth connection flow"""
    try:
        result = integration_service.start_oauth_flow(request.organization_id)
        
        if result['success']:
            # Store state in session for security
            session['qb_oauth_state'] = result['state']
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting connection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@quickbooks_bp.route('/oauth/callback', methods=['GET'])
def oauth_callback():
    """Handle OAuth callback from QuickBooks"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        realm_id = request.args.get('realmId')
        
        if not all([code, state, realm_id]):
            return jsonify({'error': 'Missing required OAuth parameters'}), 400
        
        # Verify state matches session
        session_state = session.get('qb_oauth_state')
        if not session_state or session_state != state:
            return jsonify({'error': 'Invalid OAuth state'}), 400
        
        # Complete OAuth flow
        result = integration_service.complete_oauth_flow(code, state, realm_id)
        
        # Clear session state
        session.pop('qb_oauth_state', None)
        
        if result['success']:
            # Redirect to success page or return success response
            return redirect('/dashboard/quickbooks/connected')
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/status', methods=['GET'])
@auth_required
def get_connection_status():
    """Get QuickBooks connection status"""
    try:
        status = integration_service.get_connection_status(request.organization_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/disconnect', methods=['POST'])
@auth_required
def disconnect():
    """Disconnect QuickBooks integration"""
    try:
        result = integration_service.disconnect_quickbooks(request.organization_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")
        return jsonify({'error': str(e)}), 500

# Data Synchronization Routes

@quickbooks_bp.route('/sync', methods=['POST'])
@auth_required
def sync_all_data():
    """Synchronize all data between EstateCore and QuickBooks"""
    try:
        data = request.get_json() or {}
        direction = data.get('direction', 'both')  # 'to_qb', 'from_qb', or 'both'
        
        # Run async sync
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            integration_service.sync_all_data(request.organization_id, direction)
        )
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@quickbooks_bp.route('/sync/entity', methods=['POST'])
@auth_required
def sync_entity():
    """Manually sync specific entities"""
    try:
        data = request.get_json()
        entity_type = data.get('entity_type')
        entity_data = data.get('entity_data', [])
        
        if not entity_type:
            return jsonify({'error': 'entity_type is required'}), 400
        
        result = integration_service.sync_entity_manual(
            request.organization_id, entity_type, entity_data
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Entity sync error: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/sync/history', methods=['GET'])
@auth_required
def get_sync_history():
    """Get synchronization history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        history = integration_service.sync_service.get_sync_history(
            request.organization_id, limit
        )
        
        return jsonify({
            'success': True,
            'sync_history': history
        })
        
    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        return jsonify({'error': str(e)}), 500

# Automation Routes

@quickbooks_bp.route('/automation/enable', methods=['POST'])
@auth_required
def enable_automation():
    """Enable automated workflows"""
    try:
        data = request.get_json() or {}
        workflow_types = data.get('workflow_types')
        
        result = integration_service.enable_automation(
            request.organization_id, workflow_types
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error enabling automation: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/automation/execute', methods=['POST'])
@auth_required
def execute_workflow():
    """Manually execute a workflow"""
    try:
        data = request.get_json()
        workflow_type = data.get('workflow_type')
        parameters = data.get('parameters')
        
        if not workflow_type:
            return jsonify({'error': 'workflow_type is required'}), 400
        
        result = integration_service.execute_workflow_manual(
            request.organization_id, workflow_type, parameters
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/automation/status', methods=['GET'])
@auth_required
def get_automation_status():
    """Get automation status"""
    try:
        status = integration_service.get_automation_status(request.organization_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/automation/workflows', methods=['GET'])
@auth_required
def list_workflows():
    """List available workflow types"""
    try:
        workflows = [
            {
                'type': wf.value,
                'name': wf.value.replace('_', ' ').title(),
                'description': f'Automated {wf.value.replace("_", " ")}'
            }
            for wf in WorkflowType
        ]
        
        return jsonify({
            'success': True,
            'workflows': workflows
        })
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        return jsonify({'error': str(e)}), 500

# Data Quality and Reconciliation Routes

@quickbooks_bp.route('/reconcile', methods=['POST'])
@auth_required
def perform_reconciliation():
    """Perform data reconciliation"""
    try:
        data = request.get_json() or {}
        entity_types = data.get('entity_types')
        period_days = data.get('period_days', 30)
        
        result = integration_service.perform_reconciliation(
            request.organization_id, entity_types, period_days
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Reconciliation error: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/data-quality', methods=['GET'])
@auth_required
def get_data_quality():
    """Get data quality score"""
    try:
        result = integration_service.get_data_quality_score(request.organization_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting data quality: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/audit-trail', methods=['GET'])
@auth_required
def get_audit_trail():
    """Get audit trail"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        result = integration_service.get_audit_trail(request.organization_id, limit)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        return jsonify({'error': str(e)}), 500

# Enterprise Features Routes

@quickbooks_bp.route('/enterprise/portfolios', methods=['POST'])
@auth_required
@enterprise_required(AccessLevel.ADVANCED)
def create_portfolio():
    """Create multi-property portfolio"""
    try:
        data = request.get_json()
        portfolio_name = data.get('portfolio_name')
        properties = data.get('properties', [])
        
        if not portfolio_name or not properties:
            return jsonify({'error': 'portfolio_name and properties are required'}), 400
        
        result = integration_service.setup_multi_property(
            request.organization_id, portfolio_name, properties
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/enterprise/portfolios', methods=['GET'])
@auth_required
@enterprise_required(AccessLevel.BASIC)
def list_portfolios():
    """List property portfolios"""
    try:
        portfolios = integration_service.enterprise_service.list_portfolios(
            request.organization_id
        )
        
        return jsonify({
            'success': True,
            'portfolios': portfolios
        })
        
    except Exception as e:
        logger.error(f"Error listing portfolios: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/enterprise/reports', methods=['POST'])
@auth_required
@enterprise_required(AccessLevel.ADVANCED)
def create_custom_report():
    """Create custom report"""
    try:
        data = request.get_json()
        report_name = data.get('report_name')
        report_type = data.get('report_type')
        
        if not report_name or not report_type:
            return jsonify({'error': 'report_name and report_type are required'}), 400
        
        # Extract additional parameters
        report_params = {k: v for k, v in data.items() 
                        if k not in ['report_name', 'report_type']}
        
        result = integration_service.create_custom_report(
            request.organization_id, report_name, report_type, **report_params
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/enterprise/reports', methods=['GET'])
@auth_required
@enterprise_required(AccessLevel.BASIC)
def list_custom_reports():
    """List custom reports"""
    try:
        reports = integration_service.enterprise_service.list_custom_reports(
            request.organization_id
        )
        
        return jsonify({
            'success': True,
            'reports': reports
        })
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/enterprise/reports/<report_id>/generate', methods=['POST'])
@auth_required
@enterprise_required(AccessLevel.BASIC)
def generate_report(report_id):
    """Generate custom report"""
    try:
        data = request.get_json() or {}
        date_range = data.get('date_range')
        
        result = integration_service.generate_report(report_id, date_range)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/enterprise/report-types', methods=['GET'])
@auth_required
def list_report_types():
    """List available report types"""
    try:
        report_types = [
            {
                'type': rt.value,
                'name': rt.value.replace('_', ' ').title(),
                'description': f'{rt.value.replace("_", " ").title()} report'
            }
            for rt in ReportType
        ]
        
        return jsonify({
            'success': True,
            'report_types': report_types
        })
        
    except Exception as e:
        logger.error(f"Error listing report types: {e}")
        return jsonify({'error': str(e)}), 500

# Health and Monitoring Routes

@quickbooks_bp.route('/health', methods=['GET'])
@auth_required
def get_integration_health():
    """Get integration health status"""
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        health = integration_service.get_integration_health(
            request.organization_id, force_refresh
        )
        
        # Convert to dict for JSON response
        health_dict = {
            'status': health.status.value,
            'connection_health': health.connection_health,
            'sync_health': health.sync_health,
            'automation_health': health.automation_health,
            'data_quality': health.data_quality,
            'last_check': health.last_check.isoformat(),
            'issues': health.issues,
            'recommendations': health.recommendations
        }
        
        return jsonify({
            'success': True,
            'health': health_dict
        })
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/summary', methods=['GET'])
@auth_required
def get_integration_summary():
    """Get comprehensive integration summary"""
    try:
        summary = integration_service.get_integration_summary(request.organization_id)
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({'error': str(e)}), 500

# Configuration Routes

@quickbooks_bp.route('/config/sync', methods=['GET'])
@auth_required
def get_sync_config():
    """Get synchronization configuration"""
    try:
        config = integration_service.sync_service.get_sync_configuration(
            request.organization_id
        )
        
        if config:
            return jsonify({
                'success': True,
                'config': {
                    'auto_sync_enabled': config.auto_sync_enabled,
                    'sync_interval_minutes': config.sync_interval_minutes,
                    'conflict_resolution': config.conflict_resolution.value,
                    'sync_entities': config.sync_entities,
                    'max_retry_attempts': config.max_retry_attempts,
                    'batch_size': config.batch_size
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No sync configuration found'
            })
            
    except Exception as e:
        logger.error(f"Error getting sync config: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/config/sync', methods=['PUT'])
@auth_required
@enterprise_required(AccessLevel.ADVANCED)
def update_sync_config():
    """Update synchronization configuration"""
    try:
        data = request.get_json()
        
        success = integration_service.sync_service.update_sync_configuration(
            request.organization_id, data
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Configuration updated'})
        else:
            return jsonify({'success': False, 'error': 'Configuration not found'})
            
    except Exception as e:
        logger.error(f"Error updating sync config: {e}")
        return jsonify({'error': str(e)}), 500

# Account Mapping Routes

@quickbooks_bp.route('/accounts', methods=['GET'])
@auth_required
def get_quickbooks_accounts():
    """Get QuickBooks chart of accounts"""
    try:
        connection = integration_service.oauth_service.get_organization_connection(
            request.organization_id
        )
        
        if not connection:
            return jsonify({'error': 'No QuickBooks connection found'}), 400
        
        accounts = integration_service.api_client.get_accounts(
            connection.connection_id, force_refresh=True
        )
        
        return jsonify({
            'success': True,
            'accounts': accounts
        })
        
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/mapping/properties', methods=['POST'])
@auth_required
@enterprise_required(AccessLevel.ADVANCED)
def create_property_mapping():
    """Create property account mapping"""
    try:
        data = request.get_json()
        
        required_fields = ['property_id', 'property_name', 'revenue_account_id', 
                          'expense_account_id', 'deposit_account_id', 'ar_account_id']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        mapping = integration_service.mapping_service.create_property_mapping(**data)
        
        return jsonify({
            'success': True,
            'mapping_id': mapping.property_id,
            'message': 'Property mapping created'
        })
        
    except Exception as e:
        logger.error(f"Error creating property mapping: {e}")
        return jsonify({'error': str(e)}), 500

@quickbooks_bp.route('/mapping/properties', methods=['GET'])
@auth_required
def list_property_mappings():
    """List property account mappings"""
    try:
        mappings = integration_service.mapping_service.list_property_mappings()
        
        return jsonify({
            'success': True,
            'mappings': [
                {
                    'property_id': m.property_id,
                    'property_name': m.property_name,
                    'revenue_account_id': m.revenue_account_id,
                    'expense_account_id': m.expense_account_id,
                    'deposit_account_id': m.deposit_account_id,
                    'ar_account_id': m.ar_account_id,
                    'custom_class_id': m.custom_class_id,
                    'location_id': m.location_id
                }
                for m in mappings
            ]
        })
        
    except Exception as e:
        logger.error(f"Error listing property mappings: {e}")
        return jsonify({'error': str(e)}), 500

# Error handler
@quickbooks_bp.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error in QuickBooks routes: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Register the blueprint with the main app
def register_quickbooks_routes(app):
    """Register QuickBooks routes with Flask app"""
    app.register_blueprint(quickbooks_bp)
    logger.info("QuickBooks integration routes registered")