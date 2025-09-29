from flask import Blueprint, request, jsonify, g
from estatecore_backend.models import db, User
from models.rbac import Role, Permission, UserRole, AccessLog, SecurityPolicy
from services.rbac_service import RBACService, require_permission, require_role
from datetime import datetime, timedelta
import logging

rbac_bp = Blueprint('rbac', __name__, url_prefix='/api/rbac')
logger = logging.getLogger(__name__)

# Role Management Routes
@rbac_bp.route('/roles', methods=['GET'])
@require_permission('users:read')
def get_roles():
    """Get all roles"""
    try:
        roles = Role.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'roles': [role.to_dict() for role in roles]
        })
    except Exception as e:
        logger.error(f"Error fetching roles: {str(e)}")
        return jsonify({'error': 'Failed to fetch roles'}), 500

@rbac_bp.route('/roles', methods=['POST'])
@require_permission('users:manage_roles')
def create_role():
    """Create a new role"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Role name is required'}), 400
        
        # Check if role already exists
        existing_role = Role.query.filter_by(name=data['name']).first()
        if existing_role:
            return jsonify({'error': 'Role with this name already exists'}), 400
        
        role = Role(
            name=data['name'],
            description=data.get('description', ''),
            is_system_role=False
        )
        
        db.session.add(role)
        db.session.flush()
        
        # Add permissions if provided
        permission_ids = data.get('permission_ids', [])
        for permission_id in permission_ids:
            permission = Permission.query.get(permission_id)
            if permission:
                role.add_permission(permission)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'role': role.to_dict(),
            'message': 'Role created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating role: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create role'}), 500

@rbac_bp.route('/roles/<int:role_id>', methods=['PUT'])
@require_permission('users:manage_roles')
def update_role(role_id):
    """Update a role"""
    try:
        role = Role.query.get_or_404(role_id)
        
        if role.is_system_role:
            return jsonify({'error': 'Cannot modify system roles'}), 400
        
        data = request.get_json()
        
        if 'name' in data:
            # Check if new name conflicts with existing role
            existing_role = Role.query.filter(
                Role.name == data['name'],
                Role.id != role_id
            ).first()
            if existing_role:
                return jsonify({'error': 'Role with this name already exists'}), 400
            role.name = data['name']
        
        if 'description' in data:
            role.description = data['description']
        
        if 'is_active' in data:
            role.is_active = data['is_active']
        
        # Update permissions if provided
        if 'permission_ids' in data:
            # Clear existing permissions
            role.permissions.clear()
            
            # Add new permissions
            for permission_id in data['permission_ids']:
                permission = Permission.query.get(permission_id)
                if permission:
                    role.add_permission(permission)
        
        role.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'role': role.to_dict(),
            'message': 'Role updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating role: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update role'}), 500

@rbac_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@require_permission('users:manage_roles')
def delete_role(role_id):
    """Delete a role"""
    try:
        role = Role.query.get_or_404(role_id)
        
        if role.is_system_role:
            return jsonify({'error': 'Cannot delete system roles'}), 400
        
        # Check if role is assigned to any users
        user_roles = UserRole.query.filter_by(role_id=role_id, is_active=True).first()
        if user_roles:
            return jsonify({'error': 'Cannot delete role that is assigned to users'}), 400
        
        role.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Role deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting role: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete role'}), 500

# Permission Management Routes
@rbac_bp.route('/permissions', methods=['GET'])
@require_permission('users:read')
def get_permissions():
    """Get all permissions"""
    try:
        permissions = Permission.query.all()
        
        # Group permissions by resource
        grouped_permissions = {}
        for permission in permissions:
            resource = permission.resource
            if resource not in grouped_permissions:
                grouped_permissions[resource] = []
            grouped_permissions[resource].append(permission.to_dict())
        
        return jsonify({
            'success': True,
            'permissions': [p.to_dict() for p in permissions],
            'grouped_permissions': grouped_permissions
        })
        
    except Exception as e:
        logger.error(f"Error fetching permissions: {str(e)}")
        return jsonify({'error': 'Failed to fetch permissions'}), 500

@rbac_bp.route('/permissions', methods=['POST'])
@require_permission('users:manage_roles')
def create_permission():
    """Create a new permission"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'resource', 'action']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if permission already exists
        existing_permission = Permission.query.filter_by(name=data['name']).first()
        if existing_permission:
            return jsonify({'error': 'Permission with this name already exists'}), 400
        
        permission = Permission(
            name=data['name'],
            description=data.get('description', ''),
            resource=data['resource'],
            action=data['action'],
            is_system_permission=False
        )
        
        db.session.add(permission)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'permission': permission.to_dict(),
            'message': 'Permission created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating permission: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create permission'}), 500

# User Role Assignment Routes
@rbac_bp.route('/users/<int:user_id>/roles', methods=['GET'])
@require_permission('users:read')
def get_user_roles(user_id):
    """Get roles assigned to a user"""
    try:
        user = User.query.get_or_404(user_id)
        user_roles = RBACService.get_user_roles(user_id)
        permissions = RBACService.get_user_permissions(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'username': user.username,
            'roles': user_roles,
            'permissions': permissions
        })
        
    except Exception as e:
        logger.error(f"Error fetching user roles: {str(e)}")
        return jsonify({'error': 'Failed to fetch user roles'}), 500

@rbac_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@require_permission('users:manage_roles')
def assign_user_role(user_id):
    """Assign role to user"""
    try:
        data = request.get_json()
        
        if not data.get('role_id'):
            return jsonify({'error': 'role_id is required'}), 400
        
        role = Role.query.get(data['role_id'])
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        
        expires_at = None
        if data.get('expires_in_days'):
            expires_at = datetime.utcnow() + timedelta(days=data['expires_in_days'])
        
        success = RBACService.assign_role(
            user_id=user_id,
            role_id=data['role_id'],
            property_id=data.get('property_id'),
            organization_id=data.get('organization_id'),
            assigned_by_id=g.current_user.id,
            expires_at=expires_at
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Role assigned successfully'
            })
        else:
            return jsonify({'error': 'Failed to assign role'}), 500
            
    except Exception as e:
        logger.error(f"Error assigning user role: {str(e)}")
        return jsonify({'error': 'Failed to assign role'}), 500

@rbac_bp.route('/users/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
@require_permission('users:manage_roles')
def revoke_user_role(user_id, role_id):
    """Revoke role from user"""
    try:
        data = request.get_json() or {}
        
        success = RBACService.revoke_role(
            user_id=user_id,
            role_id=role_id,
            property_id=data.get('property_id'),
            organization_id=data.get('organization_id')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Role revoked successfully'
            })
        else:
            return jsonify({'error': 'Failed to revoke role'}), 500
            
    except Exception as e:
        logger.error(f"Error revoking user role: {str(e)}")
        return jsonify({'error': 'Failed to revoke role'}), 500

# Access Control Routes
@rbac_bp.route('/check-permission', methods=['POST'])
def check_permission():
    """Check if current user has specific permission"""
    try:
        if not hasattr(g, 'current_user') or not g.current_user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        permission = data.get('permission')
        
        if not permission:
            return jsonify({'error': 'permission is required'}), 400
        
        context = {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'property_id': data.get('property_id'),
            'organization_id': data.get('organization_id')
        }
        
        has_permission = RBACService.check_permission(
            user_id=g.current_user.id,
            permission=permission,
            resource_id=data.get('resource_id'),
            context=context
        )
        
        return jsonify({
            'success': True,
            'has_permission': has_permission,
            'permission': permission
        })
        
    except Exception as e:
        logger.error(f"Error checking permission: {str(e)}")
        return jsonify({'error': 'Failed to check permission'}), 500

# Access Logs Routes
@rbac_bp.route('/access-logs', methods=['GET'])
@require_permission('security:audit')
def get_access_logs():
    """Get access logs for security monitoring"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        user_id = request.args.get('user_id', type=int)
        resource = request.args.get('resource')
        access_granted = request.args.get('access_granted')
        
        query = AccessLog.query
        
        # Apply filters
        if user_id:
            query = query.filter(AccessLog.user_id == user_id)
        if resource:
            query = query.filter(AccessLog.resource == resource)
        if access_granted is not None:
            query = query.filter(AccessLog.access_granted == (access_granted.lower() == 'true'))
        
        # Order by timestamp desc
        query = query.order_by(AccessLog.timestamp.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'access_logs': [log.to_dict() for log in pagination.items],
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching access logs: {str(e)}")
        return jsonify({'error': 'Failed to fetch access logs'}), 500

# Security Policy Routes
@rbac_bp.route('/security-policies', methods=['GET'])
@require_permission('security:configure')
def get_security_policies():
    """Get security policies"""
    try:
        policies = SecurityPolicy.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'policies': [policy.to_dict() for policy in policies]
        })
        
    except Exception as e:
        logger.error(f"Error fetching security policies: {str(e)}")
        return jsonify({'error': 'Failed to fetch security policies'}), 500

@rbac_bp.route('/security-policies', methods=['POST'])
@require_permission('security:configure')
def create_security_policy():
    """Create a new security policy"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'policy_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        policy = SecurityPolicy(
            name=data['name'],
            description=data.get('description', ''),
            policy_type=data['policy_type'],
            policy_config=data.get('policy_config', {}),
            applies_to_role_id=data.get('applies_to_role_id'),
            applies_to_user_id=data.get('applies_to_user_id')
        )
        
        db.session.add(policy)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'policy': policy.to_dict(),
            'message': 'Security policy created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating security policy: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create security policy'}), 500

# Initialize RBAC System
@rbac_bp.route('/initialize', methods=['POST'])
@require_role('super_admin')
def initialize_rbac():
    """Initialize RBAC system with default roles and permissions"""
    try:
        RBACService.create_default_permissions()
        RBACService.create_default_roles()
        
        return jsonify({
            'success': True,
            'message': 'RBAC system initialized successfully'
        })
        
    except Exception as e:
        logger.error(f"Error initializing RBAC: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to initialize RBAC system'}), 500

# Health Check
@rbac_bp.route('/health', methods=['GET'])
def health_check():
    """RBAC system health check"""
    try:
        # Count roles and permissions
        role_count = Role.query.filter_by(is_active=True).count()
        permission_count = Permission.query.count()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'statistics': {
                'active_roles': role_count,
                'total_permissions': permission_count,
                'system_ready': role_count > 0 and permission_count > 0
            }
        })
        
    except Exception as e:
        logger.error(f"RBAC health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500