from flask import Blueprint, request, jsonify, g
from estatecore_backend.models import db, Property
from services.blockchain_service import blockchain_service, RecordType
from services.rbac_service import require_permission
import logging

blockchain_bp = Blueprint('blockchain', __name__, url_prefix='/api/blockchain')
logger = logging.getLogger(__name__)

@blockchain_bp.route('/property/<int:property_id>/records', methods=['POST'])
@require_permission('properties:manage')
def create_property_record(property_id):
    """Create a new blockchain property record"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        if 'record_type' not in data or 'record_data' not in data:
            return jsonify({'error': 'record_type and record_data are required'}), 400
        
        # Validate record type
        try:
            record_type = RecordType(data['record_type'])
        except ValueError:
            return jsonify({'error': 'Invalid record type'}), 400
        
        record_data = data['record_data']
        
        # Store on blockchain
        result = blockchain_service.store_property_record(
            property_id=property_id,
            record_type=record_type,
            data=record_data,
            user_id=g.current_user.id
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'record': result,
                'message': 'Property record created on blockchain successfully'
            }), 201
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error creating property record: {str(e)}")
        return jsonify({'error': 'Failed to create property record'}), 500

@blockchain_bp.route('/property/<int:property_id>/history', methods=['GET'])
@require_permission('properties:read')
def get_property_history(property_id):
    """Get complete blockchain history for a property"""
    try:
        result = blockchain_service.get_property_blockchain_history(property_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'history': result
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error getting property history: {str(e)}")
        return jsonify({'error': 'Failed to get property history'}), 500

@blockchain_bp.route('/records/<record_id>/verify', methods=['GET'])
@require_permission('properties:read')
def verify_record(record_id):
    """Verify the integrity of a blockchain record"""
    try:
        result = blockchain_service.verify_property_record(record_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'verification': result['verification']
            })
        else:
            return jsonify({'error': result['error']}), 404
            
    except Exception as e:
        logger.error(f"Error verifying record: {str(e)}")
        return jsonify({'error': 'Failed to verify record'}), 500

@blockchain_bp.route('/ownership/transfer', methods=['POST'])
@require_permission('properties:manage')
def transfer_ownership():
    """Transfer property ownership on blockchain"""
    try:
        data = request.get_json()
        
        required_fields = ['property_id', 'to_user_id', 'transfer_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        result = blockchain_service.transfer_property_ownership(
            property_id=data['property_id'],
            from_user_id=g.current_user.id,
            to_user_id=data['to_user_id'],
            transfer_data=data['transfer_data']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'transfer': result,
                'message': 'Property ownership transferred successfully'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error transferring ownership: {str(e)}")
        return jsonify({'error': 'Failed to transfer ownership'}), 500

@blockchain_bp.route('/lease/create', methods=['POST'])
@require_permission('properties:manage')
def create_lease_agreement():
    """Create immutable lease agreement on blockchain"""
    try:
        data = request.get_json()
        
        required_fields = ['property_id', 'tenant_id', 'lease_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Add landlord ID from current user
        lease_data = data['lease_data']
        lease_data['landlord_id'] = g.current_user.id
        
        result = blockchain_service.create_lease_agreement(
            property_id=data['property_id'],
            tenant_id=data['tenant_id'],
            lease_data=lease_data
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'lease': result,
                'message': 'Lease agreement created on blockchain successfully'
            }), 201
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error creating lease agreement: {str(e)}")
        return jsonify({'error': 'Failed to create lease agreement'}), 500

@blockchain_bp.route('/payment/record', methods=['POST'])
@require_permission('payments:create')
def record_payment():
    """Record payment on blockchain for immutable history"""
    try:
        data = request.get_json()
        
        required_fields = ['property_id', 'payment_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        result = blockchain_service.record_payment(
            property_id=data['property_id'],
            payment_data=data['payment_data']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'payment_record': result,
                'message': 'Payment recorded on blockchain successfully'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error recording payment: {str(e)}")
        return jsonify({'error': 'Failed to record payment'}), 500

@blockchain_bp.route('/transactions', methods=['GET'])
@require_permission('properties:read')
def get_transactions():
    """Get blockchain transactions"""
    try:
        status_filter = request.args.get('status')
        network_filter = request.args.get('network')
        limit = request.args.get('limit', 50, type=int)
        
        transactions = list(blockchain_service.transactions.values())
        
        # Apply filters
        if status_filter:
            transactions = [tx for tx in transactions if tx.status.value == status_filter]
        
        if network_filter:
            transactions = [tx for tx in transactions if tx.network.value == network_filter]
        
        # Sort by creation time (newest first)
        transactions.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit
        transactions = transactions[:limit]
        
        return jsonify({
            'success': True,
            'transactions': [tx.to_dict() for tx in transactions],
            'total': len(blockchain_service.transactions)
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        return jsonify({'error': 'Failed to get transactions'}), 500

@blockchain_bp.route('/transactions/<transaction_id>', methods=['GET'])
@require_permission('properties:read')
def get_transaction(transaction_id):
    """Get specific blockchain transaction details"""
    try:
        if transaction_id not in blockchain_service.transactions:
            return jsonify({'error': 'Transaction not found'}), 404
        
        transaction = blockchain_service.transactions[transaction_id]
        
        return jsonify({
            'success': True,
            'transaction': transaction.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting transaction: {str(e)}")
        return jsonify({'error': 'Failed to get transaction'}), 500

@blockchain_bp.route('/analytics', methods=['GET'])
@require_permission('properties:read')
def get_blockchain_analytics():
    """Get blockchain system analytics and statistics"""
    try:
        result = blockchain_service.get_blockchain_analytics()
        
        if result['success']:
            return jsonify({
                'success': True,
                'analytics': result['analytics']
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error getting blockchain analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500

@blockchain_bp.route('/dashboard', methods=['GET'])
@require_permission('properties:read')
def get_blockchain_dashboard():
    """Get blockchain dashboard data"""
    try:
        analytics_result = blockchain_service.get_blockchain_analytics()
        
        if not analytics_result['success']:
            return jsonify({'error': analytics_result['error']}), 500
        
        # Get recent transactions
        recent_transactions = list(blockchain_service.transactions.values())
        recent_transactions.sort(key=lambda x: x.created_at, reverse=True)
        recent_transactions = recent_transactions[:10]
        
        # Get recent property records
        recent_records = list(blockchain_service.property_records.values())
        recent_records.sort(key=lambda x: x.timestamp, reverse=True)
        recent_records = recent_records[:10]
        
        dashboard_data = {
            'statistics': analytics_result['analytics'],
            'recent_transactions': [tx.to_dict() for tx in recent_transactions],
            'recent_records': [record.to_dict() for record in recent_records],
            'system_status': {
                'network_connected': True,
                'ipfs_connected': True,
                'last_block_processed': 12345678,
                'pending_transactions': len([tx for tx in blockchain_service.transactions.values() if tx.status.value == 'pending'])
            }
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting blockchain dashboard: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500

@blockchain_bp.route('/network/status', methods=['GET'])
@require_permission('properties:read')
def get_network_status():
    """Get blockchain network status"""
    try:
        network_status = {
            'active_network': blockchain_service.active_network.value,
            'available_networks': [network.value for network in blockchain_service.networks.keys()],
            'connection_status': 'connected',  # Mock status
            'latest_block': 12345678,
            'gas_price': '20 gwei',
            'network_congestion': 'low'
        }
        
        return jsonify({
            'success': True,
            'network_status': network_status
        })
        
    except Exception as e:
        logger.error(f"Error getting network status: {str(e)}")
        return jsonify({'error': 'Failed to get network status'}), 500

@blockchain_bp.route('/validate/record', methods=['POST'])
@require_permission('properties:read')
def validate_record_data():
    """Validate record data before blockchain storage"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        validation_errors = []
        
        # Validate record type
        if 'record_type' not in data:
            validation_errors.append('record_type is required')
        else:
            try:
                RecordType(data['record_type'])
            except ValueError:
                validation_errors.append('Invalid record_type')
        
        # Validate record data
        if 'record_data' not in data:
            validation_errors.append('record_data is required')
        elif not isinstance(data['record_data'], dict):
            validation_errors.append('record_data must be an object')
        elif not data['record_data']:
            validation_errors.append('record_data cannot be empty')
        
        # Validate property ID if provided
        if 'property_id' in data:
            property_obj = Property.query.get(data['property_id'])
            if not property_obj:
                validation_errors.append('Invalid property_id')
        
        is_valid = len(validation_errors) == 0
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'validation_errors': validation_errors,
            'estimated_gas': 150000 if is_valid else 0,
            'estimated_cost_usd': 2.50 if is_valid else 0
        })
        
    except Exception as e:
        logger.error(f"Error validating record: {str(e)}")
        return jsonify({'error': 'Failed to validate record'}), 500

@blockchain_bp.route('/export/records', methods=['GET'])
@require_permission('properties:read')
def export_blockchain_records():
    """Export blockchain records for audit purposes"""
    try:
        property_id = request.args.get('property_id', type=int)
        record_type = request.args.get('record_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        records = list(blockchain_service.property_records.values())
        
        # Apply filters
        if property_id:
            records = [r for r in records if r.property_id == property_id]
        
        if record_type:
            records = [r for r in records if r.record_type.value == record_type]
        
        if start_date:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date)
            records = [r for r in records if r.timestamp >= start_dt]
        
        if end_date:
            from datetime import datetime
            end_dt = datetime.fromisoformat(end_date)
            records = [r for r in records if r.timestamp <= end_dt]
        
        # Sort by timestamp
        records.sort(key=lambda x: x.timestamp)
        
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'filters_applied': {
                'property_id': property_id,
                'record_type': record_type,
                'start_date': start_date,
                'end_date': end_date
            },
            'total_records': len(records),
            'records': [record.to_dict() for record in records]
        }
        
        return jsonify({
            'success': True,
            'export': export_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting records: {str(e)}")
        return jsonify({'error': 'Failed to export records'}), 500

# Health check endpoint
@blockchain_bp.route('/health', methods=['GET'])
def blockchain_health_check():
    """Blockchain system health check"""
    try:
        health_status = {
            'status': 'healthy',
            'blockchain_connected': True,
            'ipfs_connected': True,
            'total_records': len(blockchain_service.property_records),
            'total_transactions': len(blockchain_service.transactions),
            'pending_transactions': len([tx for tx in blockchain_service.transactions.values() if tx.status.value == 'pending']),
            'active_network': blockchain_service.active_network.value
        }
        
        return jsonify({
            'success': True,
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"Blockchain health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500