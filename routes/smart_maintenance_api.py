from flask import Blueprint, request, jsonify, g
from estatecore_backend.models import db, Property
from services.smart_maintenance_service import smart_maintenance_service, MaintenanceCategory, Priority, MaintenanceStatus
from services.rbac_service import require_permission
import logging
import asyncio
from datetime import datetime

smart_maintenance_bp = Blueprint('smart_maintenance', __name__, url_prefix='/api/smart-maintenance')
logger = logging.getLogger(__name__)

@smart_maintenance_bp.route('/schedule', methods=['POST'])
@require_permission('maintenance:create')
def schedule_maintenance():
    """Schedule new maintenance item"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        property_id = data.get('property_id')
        if not property_id:
            return jsonify({'error': 'Property ID is required'}), 400
        
        # Run async scheduling
        async def run_scheduling():
            return await smart_maintenance_service.schedule_maintenance(
                property_id=property_id,
                maintenance_data=data,
                user_id=g.current_user.id
            )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_scheduling())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error scheduling maintenance: {str(e)}")
        return jsonify({'error': 'Failed to schedule maintenance'}), 500

@smart_maintenance_bp.route('/property/<int:property_id>/items', methods=['GET'])
@require_permission('maintenance:read')
def get_property_maintenance(property_id):
    """Get all maintenance items for a property"""
    try:
        status_filter = request.args.get('status')
        category_filter = request.args.get('category')
        
        # Get maintenance items for property
        maintenance_items = [
            item for item in smart_maintenance_service.maintenance_items.values()
            if item.property_id == property_id
        ]
        
        # Apply filters
        if status_filter:
            maintenance_items = [item for item in maintenance_items if item.status.value == status_filter]
        
        if category_filter:
            maintenance_items = [item for item in maintenance_items if item.category.value == category_filter]
        
        # Sort by scheduled date
        maintenance_items.sort(key=lambda x: x.scheduled_date or datetime.min)
        
        return jsonify({
            'success': True,
            'property_id': property_id,
            'maintenance_items': [item.to_dict() for item in maintenance_items],
            'total_count': len(maintenance_items)
        })
        
    except Exception as e:
        logger.error(f"Error getting property maintenance: {str(e)}")
        return jsonify({'error': 'Failed to get maintenance items'}), 500

@smart_maintenance_bp.route('/items/<item_id>', methods=['GET'])
@require_permission('maintenance:read')
def get_maintenance_item(item_id):
    """Get specific maintenance item details"""
    try:
        if item_id not in smart_maintenance_service.maintenance_items:
            return jsonify({'error': 'Maintenance item not found'}), 404
        
        item = smart_maintenance_service.maintenance_items[item_id]
        
        return jsonify({
            'success': True,
            'maintenance_item': item.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting maintenance item: {str(e)}")
        return jsonify({'error': 'Failed to get maintenance item'}), 500

@smart_maintenance_bp.route('/items/<item_id>', methods=['PUT'])
@require_permission('maintenance:update')
def update_maintenance_item(item_id):
    """Update maintenance item"""
    try:
        if item_id not in smart_maintenance_service.maintenance_items:
            return jsonify({'error': 'Maintenance item not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        item = smart_maintenance_service.maintenance_items[item_id]
        
        # Update allowed fields
        if 'status' in data:
            item.status = MaintenanceStatus(data['status'])
        
        if 'actual_cost' in data:
            item.actual_cost = float(data['actual_cost'])
        
        if 'actual_duration_hours' in data:
            item.actual_duration_hours = float(data['actual_duration_hours'])
        
        if 'notes' in data:
            if isinstance(data['notes'], list):
                item.notes.extend(data['notes'])
            else:
                item.notes.append(data['notes'])
        
        if 'assigned_contractor' in data:
            item.assigned_contractor = data['assigned_contractor']
        
        if 'scheduled_date' in data:
            item.scheduled_date = datetime.fromisoformat(data['scheduled_date'])
        
        # Mark as completed if status is completed
        if item.status == MaintenanceStatus.COMPLETED and not item.completed_at:
            item.completed_at = datetime.utcnow()
        
        return jsonify({
            'success': True,
            'maintenance_item': item.to_dict(),
            'message': 'Maintenance item updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating maintenance item: {str(e)}")
        return jsonify({'error': 'Failed to update maintenance item'}), 500

@smart_maintenance_bp.route('/predict/<int:property_id>', methods=['POST'])
@require_permission('maintenance:read')
def generate_predictive_maintenance(property_id):
    """Generate AI-powered predictive maintenance recommendations"""
    try:
        # Run async prediction
        async def run_prediction():
            return await smart_maintenance_service.generate_predictive_maintenance(property_id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_prediction())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error generating predictive maintenance: {str(e)}")
        return jsonify({'error': 'Failed to generate predictions'}), 500

@smart_maintenance_bp.route('/optimize/<int:property_id>', methods=['POST'])
@require_permission('maintenance:update')
def optimize_maintenance_schedule(property_id):
    """Optimize maintenance schedule for efficiency"""
    try:
        data = request.get_json() or {}
        time_window_days = data.get('time_window_days', 30)
        
        # Run async optimization
        async def run_optimization():
            return await smart_maintenance_service.optimize_maintenance_schedule(
                property_id, time_window_days
            )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_optimization())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error optimizing maintenance schedule: {str(e)}")
        return jsonify({'error': 'Failed to optimize schedule'}), 500

@smart_maintenance_bp.route('/analytics', methods=['GET'])
@require_permission('maintenance:read')
def get_maintenance_analytics():
    """Get comprehensive maintenance analytics"""
    try:
        property_id = request.args.get('property_id', type=int)
        date_range_days = request.args.get('date_range_days', 365, type=int)
        
        # Run async analytics
        async def run_analytics():
            return await smart_maintenance_service.get_maintenance_analytics(
                property_id, date_range_days
            )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_analytics())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error getting maintenance analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500

@smart_maintenance_bp.route('/equipment', methods=['GET'])
@require_permission('maintenance:read')
def get_equipment():
    """Get equipment list for a property"""
    try:
        property_id = request.args.get('property_id', type=int)
        
        if property_id:
            equipment_list = [
                eq for eq in smart_maintenance_service.equipment.values()
                if eq.property_id == property_id
            ]
        else:
            equipment_list = list(smart_maintenance_service.equipment.values())
        
        return jsonify({
            'success': True,
            'equipment': [eq.to_dict() for eq in equipment_list],
            'total_count': len(equipment_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting equipment: {str(e)}")
        return jsonify({'error': 'Failed to get equipment'}), 500

@smart_maintenance_bp.route('/equipment', methods=['POST'])
@require_permission('maintenance:create')
def add_equipment():
    """Add new equipment to property"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        required_fields = ['property_id', 'name', 'category', 'manufacturer', 'model', 'installation_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        from services.smart_maintenance_service import Equipment
        import uuid
        
        equipment_id = str(uuid.uuid4())
        equipment = Equipment(
            id=equipment_id,
            property_id=data['property_id'],
            name=data['name'],
            category=MaintenanceCategory(data['category']),
            manufacturer=data['manufacturer'],
            model=data['model'],
            installation_date=datetime.fromisoformat(data['installation_date']),
            warranty_expiry=datetime.fromisoformat(data['warranty_expiry']) if data.get('warranty_expiry') else None,
            expected_lifespan_years=data.get('expected_lifespan_years', 10),
            replacement_cost=data.get('replacement_cost', 0.0),
            energy_efficiency_rating=data.get('energy_efficiency_rating')
        )
        
        smart_maintenance_service.equipment[equipment_id] = equipment
        
        return jsonify({
            'success': True,
            'equipment_id': equipment_id,
            'equipment': equipment.to_dict(),
            'message': 'Equipment added successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding equipment: {str(e)}")
        return jsonify({'error': 'Failed to add equipment'}), 500

@smart_maintenance_bp.route('/dashboard', methods=['GET'])
@require_permission('maintenance:read')
def get_maintenance_dashboard():
    """Get maintenance dashboard data"""
    try:
        property_id = request.args.get('property_id', type=int)
        
        # Get maintenance items
        if property_id:
            maintenance_items = [
                item for item in smart_maintenance_service.maintenance_items.values()
                if item.property_id == property_id
            ]
        else:
            maintenance_items = list(smart_maintenance_service.maintenance_items.values())
        
        # Calculate dashboard metrics
        total_items = len(maintenance_items)
        pending_items = len([item for item in maintenance_items if item.status == MaintenanceStatus.SCHEDULED])
        completed_items = len([item for item in maintenance_items if item.status == MaintenanceStatus.COMPLETED])
        overdue_items = len([item for item in maintenance_items if item.status == MaintenanceStatus.OVERDUE])
        
        # Get recent items
        recent_items = sorted(maintenance_items, key=lambda x: x.created_at, reverse=True)[:10]
        
        # Get equipment data
        if property_id:
            equipment_list = [
                eq for eq in smart_maintenance_service.equipment.values()
                if eq.property_id == property_id
            ]
        else:
            equipment_list = list(smart_maintenance_service.equipment.values())
        
        # Calculate costs
        total_estimated_cost = sum(item.estimated_cost for item in maintenance_items)
        total_actual_cost = sum(item.actual_cost or 0 for item in maintenance_items if item.actual_cost)
        
        dashboard_data = {
            'overview': {
                'total_maintenance_items': total_items,
                'pending_items': pending_items,
                'completed_items': completed_items,
                'overdue_items': overdue_items,
                'completion_rate': completed_items / total_items if total_items > 0 else 0,
                'total_estimated_cost': total_estimated_cost,
                'total_actual_cost': total_actual_cost
            },
            'recent_maintenance': [item.to_dict() for item in recent_items],
            'equipment_summary': {
                'total_equipment': len(equipment_list),
                'equipment_by_category': {},
                'equipment_needing_attention': []
            },
            'upcoming_maintenance': [
                item.to_dict() for item in maintenance_items
                if item.status == MaintenanceStatus.SCHEDULED and item.scheduled_date
            ][:5]
        }
        
        # Equipment by category
        for equipment in equipment_list:
            category = equipment.category.value
            if category not in dashboard_data['equipment_summary']['equipment_by_category']:
                dashboard_data['equipment_summary']['equipment_by_category'][category] = 0
            dashboard_data['equipment_summary']['equipment_by_category'][category] += 1
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data,
            'property_id': property_id
        })
        
    except Exception as e:
        logger.error(f"Error getting maintenance dashboard: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500

@smart_maintenance_bp.route('/contractors', methods=['GET'])
@require_permission('maintenance:read')
def get_contractors():
    """Get available contractors"""
    try:
        # Mock contractor data
        contractors = [
            {
                'id': 'contractor_001',
                'name': 'HVAC Pro Services',
                'categories': ['hvac'],
                'rating': 4.8,
                'hourly_rate': 85,
                'availability': 'available',
                'contact': {
                    'phone': '(555) 123-4567',
                    'email': 'contact@hvacpro.com'
                }
            },
            {
                'id': 'contractor_002',
                'name': 'Elite Plumbing Co',
                'categories': ['plumbing'],
                'rating': 4.9,
                'hourly_rate': 75,
                'availability': 'busy',
                'contact': {
                    'phone': '(555) 234-5678',
                    'email': 'info@eliteplumbing.com'
                }
            },
            {
                'id': 'contractor_003',
                'name': 'Spark Electric',
                'categories': ['electrical'],
                'rating': 4.7,
                'hourly_rate': 80,
                'availability': 'available',
                'contact': {
                    'phone': '(555) 345-6789',
                    'email': 'service@sparkelectric.com'
                }
            }
        ]
        
        category_filter = request.args.get('category')
        if category_filter:
            contractors = [c for c in contractors if category_filter in c['categories']]
        
        return jsonify({
            'success': True,
            'contractors': contractors,
            'total_count': len(contractors)
        })
        
    except Exception as e:
        logger.error(f"Error getting contractors: {str(e)}")
        return jsonify({'error': 'Failed to get contractors'}), 500

@smart_maintenance_bp.route('/templates', methods=['GET'])
@require_permission('maintenance:read')
def get_maintenance_templates():
    """Get maintenance templates"""
    try:
        templates = []
        for template_name, template_data in smart_maintenance_service.maintenance_templates.items():
            templates.append({
                'name': template_name,
                'category': template_data['category'].value,
                'recurring_tasks': template_data['recurring_tasks']
            })
        
        return jsonify({
            'success': True,
            'templates': templates
        })
        
    except Exception as e:
        logger.error(f"Error getting maintenance templates: {str(e)}")
        return jsonify({'error': 'Failed to get templates'}), 500

@smart_maintenance_bp.route('/work-orders', methods=['POST'])
@require_permission('maintenance:create')
def create_work_order():
    """Create work order from maintenance item"""
    try:
        data = request.get_json()
        
        if not data or 'maintenance_item_id' not in data:
            return jsonify({'error': 'Maintenance item ID is required'}), 400
        
        item_id = data['maintenance_item_id']
        
        if item_id not in smart_maintenance_service.maintenance_items:
            return jsonify({'error': 'Maintenance item not found'}), 404
        
        item = smart_maintenance_service.maintenance_items[item_id]
        
        # Create work order (mock implementation)
        work_order = {
            'work_order_id': f"WO-{item_id[:8]}",
            'maintenance_item_id': item_id,
            'property_id': item.property_id,
            'title': item.title,
            'description': item.description,
            'priority': item.priority.value,
            'assigned_contractor': item.assigned_contractor,
            'estimated_cost': item.estimated_cost,
            'scheduled_date': item.scheduled_date.isoformat() if item.scheduled_date else None,
            'status': 'created',
            'created_at': datetime.utcnow().isoformat(),
            'created_by': g.current_user.id
        }
        
        # Update maintenance item status
        item.status = MaintenanceStatus.IN_PROGRESS
        
        return jsonify({
            'success': True,
            'work_order': work_order,
            'message': 'Work order created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating work order: {str(e)}")
        return jsonify({'error': 'Failed to create work order'}), 500

# Health check endpoint
@smart_maintenance_bp.route('/health', methods=['GET'])
def smart_maintenance_health_check():
    """Smart maintenance system health check"""
    try:
        health_status = {
            'status': 'healthy',
            'total_maintenance_items': len(smart_maintenance_service.maintenance_items),
            'total_equipment': len(smart_maintenance_service.equipment),
            'pending_items': len([
                item for item in smart_maintenance_service.maintenance_items.values()
                if item.status == MaintenanceStatus.SCHEDULED
            ]),
            'overdue_items': len([
                item for item in smart_maintenance_service.maintenance_items.values()
                if item.status == MaintenanceStatus.OVERDUE
            ])
        }
        
        return jsonify({
            'success': True,
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"Smart maintenance health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500