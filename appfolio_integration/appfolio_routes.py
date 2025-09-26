"""
AppFolio Integration Routes

Flask routes for AppFolio integration API endpoints.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import asyncio
from typing import Dict, Any

from .appfolio_integration_service import get_appfolio_integration_service
from .appfolio_auth_service import AppFolioProductType
from .appfolio_sync_service import SyncDirection, SyncMode
from .appfolio_enterprise_service import AccessLevel, ReportType, BulkOperationType

logger = logging.getLogger(__name__)

# Create Blueprint
appfolio_bp = Blueprint('appfolio', __name__, url_prefix='/api/v1/integrations/appfolio')

def require_organization(f):
    """Decorator to require organization_id parameter"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        organization_id = request.json.get('organization_id') if request.json else request.args.get('organization_id')
        if not organization_id:
            return jsonify({'error': 'organization_id is required'}), 400
        return f(organization_id, *args, **kwargs)
    return decorated_function

def handle_async(f):
    """Decorator to handle async functions in Flask routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(f(*args, **kwargs))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Async route error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    return decorated_function

# =====================================================
# CONNECTION MANAGEMENT ROUTES
# =====================================================

@appfolio_bp.route('/integrate', methods=['POST'])
@require_organization
def create_integration(organization_id: str):
    """Create new AppFolio integration"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        # Parse configuration
        from .appfolio_integration_service import IntegrationConfiguration, IntegrationMode
        
        config = IntegrationConfiguration(
            organization_id=organization_id,
            integration_name=data.get('integration_name', 'AppFolio Integration'),
            appfolio_products=[AppFolioProductType(p) for p in data.get('appfolio_products', ['property_manager'])],
            sync_enabled=data.get('sync_enabled', True),
            real_time_sync=data.get('real_time_sync', True),
            enterprise_features=data.get('enterprise_features', False),
            webhook_enabled=data.get('webhook_enabled', True),
            mode=IntegrationMode(data.get('mode', 'sandbox')),
            sync_entities=data.get('sync_entities', []),
            excluded_entities=data.get('excluded_entities', [])
        )
        
        result = service.create_integration(organization_id, config)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating integration: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/connect', methods=['POST'])
@require_organization
def connect_to_appfolio(organization_id: str):
    """Start OAuth connection to AppFolio"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        product_types = [AppFolioProductType(p) for p in data.get('product_types', ['property_manager'])]
        custom_scopes = data.get('custom_scopes', [])
        
        result = service.connect_to_appfolio(organization_id, product_types, custom_scopes)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting connection: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/oauth/callback', methods=['POST'])
def oauth_callback():
    """Handle OAuth callback from AppFolio"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        code = data.get('code')
        state = data.get('state')
        
        if not code or not state:
            return jsonify({'error': 'Missing code or state parameter'}), 400
        
        result = service.complete_oauth_flow(code, state)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/status/<organization_id>', methods=['GET'])
def get_connection_status(organization_id: str):
    """Get AppFolio connection status"""
    try:
        service = get_appfolio_integration_service()
        result = service.get_connection_status(organization_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting connection status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/disconnect', methods=['POST'])
@require_organization
def disconnect_appfolio(organization_id: str):
    """Disconnect from AppFolio"""
    try:
        service = get_appfolio_integration_service()
        result = service.disconnect_appfolio(organization_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error disconnecting: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =====================================================
# SYNCHRONIZATION ROUTES
# =====================================================

@appfolio_bp.route('/sync/full', methods=['POST'])
@require_organization
@handle_async
async def start_full_sync(organization_id: str):
    """Start full data synchronization"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        sync_direction = data.get('sync_direction', 'both')
        entity_types = data.get('entity_types')
        
        result = await service.start_full_sync(organization_id, sync_direction, entity_types)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting full sync: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/sync/incremental', methods=['POST'])
@require_organization
@handle_async
async def start_incremental_sync(organization_id: str):
    """Start incremental data synchronization"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        entity_types = data.get('entity_types')
        since_timestamp = data.get('since_timestamp')
        
        result = await service.start_incremental_sync(organization_id, entity_types, since_timestamp)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting incremental sync: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/sync/status/<organization_id>', methods=['GET'])
@appfolio_bp.route('/sync/status/<organization_id>/<job_id>', methods=['GET'])
def get_sync_status(organization_id: str, job_id: str = None):
    """Get synchronization status"""
    try:
        service = get_appfolio_integration_service()
        result = service.get_sync_status(organization_id, job_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/sync/cancel/<job_id>', methods=['POST'])
def cancel_sync(job_id: str):
    """Cancel a running sync job"""
    try:
        service = get_appfolio_integration_service()
        result = service.cancel_sync(job_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error cancelling sync: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =====================================================
# CONFIGURATION ROUTES
# =====================================================

@appfolio_bp.route('/config/<organization_id>', methods=['GET'])
def get_integration_config(organization_id: str):
    """Get integration configuration"""
    try:
        service = get_appfolio_integration_service()
        result = service.get_integration_config(organization_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/config/<organization_id>', methods=['PUT'])
def update_integration_config(organization_id: str):
    """Update integration configuration"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        result = service.update_integration_config(organization_id, data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =====================================================
# HEALTH AND MONITORING ROUTES
# =====================================================

@appfolio_bp.route('/health/<organization_id>', methods=['GET'])
def get_integration_health(organization_id: str):
    """Get integration health status"""
    try:
        service = get_appfolio_integration_service()
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        health = service.get_integration_health(organization_id, force_refresh)
        return jsonify({
            'status': health.status.value,
            'connection_health': health.connection_health,
            'sync_health': health.sync_health,
            'webhook_health': health.webhook_health,
            'data_quality_score': health.data_quality_score,
            'uptime_percentage': health.uptime_percentage,
            'error_rate': health.error_rate,
            'issues': health.issues,
            'warnings': health.warnings,
            'recommendations': health.recommendations,
            'last_check': health.last_check.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting health status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/summary/<organization_id>', methods=['GET'])
def get_integration_summary(organization_id: str):
    """Get comprehensive integration summary"""
    try:
        service = get_appfolio_integration_service()
        result = service.get_integration_summary(organization_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =====================================================
# ENTERPRISE FEATURES ROUTES
# =====================================================

@appfolio_bp.route('/enterprise/portfolios', methods=['POST'])
@require_organization
def create_portfolio(organization_id: str):
    """Create property portfolio"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        portfolio_name = data.get('name')
        property_ids = data.get('property_ids', [])
        
        if not portfolio_name:
            return jsonify({'error': 'Portfolio name is required'}), 400
        
        portfolio = service.enterprise_service.create_property_portfolio(
            organization_id, portfolio_name, property_ids, **data
        )
        
        return jsonify({
            'success': True,
            'portfolio': {
                'portfolio_id': portfolio.portfolio_id,
                'name': portfolio.name,
                'property_count': len(portfolio.property_ids),
                'total_units': portfolio.total_units
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating portfolio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/enterprise/portfolios/<organization_id>', methods=['GET'])
def list_portfolios(organization_id: str):
    """List portfolios for organization"""
    try:
        service = get_appfolio_integration_service()
        portfolios = service.enterprise_service.list_portfolios(organization_id)
        
        return jsonify({
            'success': True,
            'portfolios': [
                {
                    'portfolio_id': p.portfolio_id,
                    'name': p.name,
                    'property_count': len(p.property_ids),
                    'total_units': p.total_units,
                    'monthly_income': p.monthly_income,
                    'occupancy_rate': p.occupancy_rate
                }
                for p in portfolios
            ]
        })
        
    except Exception as e:
        logger.error(f"Error listing portfolios: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/enterprise/reports', methods=['POST'])
@require_organization
def create_custom_report(organization_id: str):
    """Create custom report"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        report_name = data.get('name')
        report_type = ReportType(data.get('type', 'financial_summary'))
        
        if not report_name:
            return jsonify({'error': 'Report name is required'}), 400
        
        report = service.enterprise_service.create_custom_report(
            organization_id, report_name, report_type, **data
        )
        
        return jsonify({
            'success': True,
            'report': {
                'report_id': report.report_id,
                'name': report.name,
                'type': report.report_type.value,
                'created_at': report.created_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/enterprise/reports/<report_id>/generate', methods=['POST'])
def generate_report(report_id: str):
    """Generate custom report"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        date_range = data.get('date_range')
        
        result = service.enterprise_service.generate_custom_report(report_id, date_range)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/enterprise/bulk', methods=['POST'])
@require_organization
@handle_async
async def create_bulk_operation(organization_id: str):
    """Create bulk operation"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        operation_type = BulkOperationType(data.get('operation_type'))
        entity_type = data.get('entity_type')
        
        if not entity_type:
            return jsonify({'error': 'entity_type is required'}), 400
        
        operation = service.enterprise_service.create_bulk_operation(
            organization_id, operation_type, entity_type, **data
        )
        
        # Execute the operation
        result = await service.enterprise_service.execute_bulk_operation(operation.operation_id)
        
        return jsonify({
            'success': True,
            'operation_id': operation.operation_id,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error creating bulk operation: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =====================================================
# WEBHOOK ROUTES
# =====================================================

@appfolio_bp.route('/webhooks/setup', methods=['POST'])
@require_organization
def setup_webhooks(organization_id: str):
    """Setup webhook subscriptions"""
    try:
        service = get_appfolio_integration_service()
        data = request.get_json()
        
        event_types = data.get('event_types')
        
        result = service.webhook_service.setup_organization_webhooks(organization_id, event_types)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error setting up webhooks: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/webhooks/status/<organization_id>', methods=['GET'])
def get_webhook_status(organization_id: str):
    """Get webhook status"""
    try:
        service = get_appfolio_integration_service()
        result = service.webhook_service.get_webhook_status(organization_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting webhook status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@appfolio_bp.route('/webhooks/events/<organization_id>', methods=['GET'])
def get_webhook_events(organization_id: str):
    """Get webhook events"""
    try:
        service = get_appfolio_integration_service()
        limit = int(request.args.get('limit', 50))
        
        events = service.webhook_service.get_webhook_events(organization_id, limit)
        
        return jsonify({
            'success': True,
            'events': [
                {
                    'event_id': e.event_id,
                    'event_type': e.event_type.value,
                    'entity_type': e.entity_type,
                    'entity_id': e.entity_id,
                    'status': e.status.value,
                    'timestamp': e.timestamp.isoformat()
                }
                for e in events
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting webhook events: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =====================================================
# UTILITY ROUTES
# =====================================================

@appfolio_bp.route('/test', methods=['GET'])
def test_integration():
    """Test integration service"""
    return jsonify({
        'service': 'AppFolio Integration',
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': str(datetime.utcnow())
    })

@appfolio_bp.route('/products', methods=['GET'])
def list_appfolio_products():
    """List available AppFolio products"""
    return jsonify({
        'products': [
            {
                'id': product.value,
                'name': product.value.replace('_', ' ').title(),
                'description': f"AppFolio {product.value.replace('_', ' ').title()}"
            }
            for product in AppFolioProductType
        ]
    })

@appfolio_bp.route('/entities', methods=['GET'])
def list_sync_entities():
    """List available sync entities"""
    return jsonify({
        'entities': [
            'properties',
            'units', 
            'tenants',
            'leases',
            'payments',
            'work_orders',
            'vendors',
            'accounts',
            'transactions',
            'documents',
            'portfolios',
            'applications',
            'messages'
        ]
    })

# Error handlers
@appfolio_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@appfolio_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401

@appfolio_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@appfolio_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500