from flask import request, g, current_app
from functools import wraps
from datetime import datetime, time
import json
import ipaddress
from estatecore_backend.models import db, User
from models.rbac import Role, Permission, UserRole, AccessLog, SecurityPolicy
from typing import List, Optional, Dict, Any

class RBACService:
    """Role-Based Access Control Service"""
    
    @staticmethod
    def create_default_roles():
        """Create default system roles"""
        default_roles = [
            {
                'name': 'super_admin',
                'description': 'Super Administrator with full system access',
                'is_system_role': True,
                'permissions': ['*:*']  # All permissions
            },
            {
                'name': 'property_manager',
                'description': 'Property Manager with property and tenant management',
                'is_system_role': True,
                'permissions': [
                    'properties:*', 'tenants:*', 'maintenance:*', 
                    'payments:read', 'reports:read'
                ]
            },
            {
                'name': 'tenant',
                'description': 'Tenant with limited access to own data',
                'is_system_role': True,
                'permissions': [
                    'profile:read', 'profile:update', 'payments:create',
                    'maintenance:create', 'documents:read'
                ]
            },
            {
                'name': 'maintenance_staff',
                'description': 'Maintenance staff with work order access',
                'is_system_role': True,
                'permissions': [
                    'maintenance:read', 'maintenance:update', 'maintenance:create',
                    'properties:read'
                ]
            },
            {
                'name': 'accountant',
                'description': 'Financial staff with payment and reporting access',
                'is_system_role': True,
                'permissions': [
                    'payments:*', 'reports:*', 'financials:*',
                    'tenants:read', 'properties:read'
                ]
            },
            {
                'name': 'security_staff',
                'description': 'Security personnel with access control management',
                'is_system_role': True,
                'permissions': [
                    'access:*', 'security:*', 'lpr:*',
                    'visitors:*', 'incidents:*'
                ]
            }
        ]
        
        for role_data in default_roles:
            role = Role.query.filter_by(name=role_data['name']).first()
            if not role:
                role = Role(
                    name=role_data['name'],
                    description=role_data['description'],
                    is_system_role=role_data['is_system_role']
                )
                db.session.add(role)
                db.session.flush()
                
                # Add permissions
                for perm_name in role_data['permissions']:
                    if perm_name == '*:*':
                        # Grant all permissions
                        all_permissions = Permission.query.all()
                        for permission in all_permissions:
                            role.add_permission(permission)
                    else:
                        permission = Permission.query.filter_by(name=perm_name).first()
                        if permission:
                            role.add_permission(permission)
        
        db.session.commit()
    
    @staticmethod
    def create_default_permissions():
        """Create default system permissions"""
        default_permissions = [
            # Property Management
            {'name': 'properties:create', 'resource': 'properties', 'action': 'create', 'description': 'Create new properties'},
            {'name': 'properties:read', 'resource': 'properties', 'action': 'read', 'description': 'View properties'},
            {'name': 'properties:update', 'resource': 'properties', 'action': 'update', 'description': 'Update properties'},
            {'name': 'properties:delete', 'resource': 'properties', 'action': 'delete', 'description': 'Delete properties'},
            {'name': 'properties:manage', 'resource': 'properties', 'action': 'manage', 'description': 'Full property management'},
            
            # Tenant Management
            {'name': 'tenants:create', 'resource': 'tenants', 'action': 'create', 'description': 'Add new tenants'},
            {'name': 'tenants:read', 'resource': 'tenants', 'action': 'read', 'description': 'View tenant information'},
            {'name': 'tenants:update', 'resource': 'tenants', 'action': 'update', 'description': 'Update tenant information'},
            {'name': 'tenants:delete', 'resource': 'tenants', 'action': 'delete', 'description': 'Remove tenants'},
            {'name': 'tenants:manage', 'resource': 'tenants', 'action': 'manage', 'description': 'Full tenant management'},
            
            # Payment Management
            {'name': 'payments:create', 'resource': 'payments', 'action': 'create', 'description': 'Process payments'},
            {'name': 'payments:read', 'resource': 'payments', 'action': 'read', 'description': 'View payment information'},
            {'name': 'payments:update', 'resource': 'payments', 'action': 'update', 'description': 'Update payment records'},
            {'name': 'payments:delete', 'resource': 'payments', 'action': 'delete', 'description': 'Delete payment records'},
            {'name': 'payments:refund', 'resource': 'payments', 'action': 'refund', 'description': 'Process refunds'},
            
            # Maintenance Management
            {'name': 'maintenance:create', 'resource': 'maintenance', 'action': 'create', 'description': 'Create maintenance requests'},
            {'name': 'maintenance:read', 'resource': 'maintenance', 'action': 'read', 'description': 'View maintenance requests'},
            {'name': 'maintenance:update', 'resource': 'maintenance', 'action': 'update', 'description': 'Update maintenance requests'},
            {'name': 'maintenance:assign', 'resource': 'maintenance', 'action': 'assign', 'description': 'Assign maintenance tasks'},
            {'name': 'maintenance:complete', 'resource': 'maintenance', 'action': 'complete', 'description': 'Mark maintenance as complete'},
            
            # User Management
            {'name': 'users:create', 'resource': 'users', 'action': 'create', 'description': 'Create user accounts'},
            {'name': 'users:read', 'resource': 'users', 'action': 'read', 'description': 'View user information'},
            {'name': 'users:update', 'resource': 'users', 'action': 'update', 'description': 'Update user information'},
            {'name': 'users:delete', 'resource': 'users', 'action': 'delete', 'description': 'Delete user accounts'},
            {'name': 'users:manage_roles', 'resource': 'users', 'action': 'manage_roles', 'description': 'Manage user roles'},
            
            # Access Control
            {'name': 'access:grant', 'resource': 'access', 'action': 'grant', 'description': 'Grant access permissions'},
            {'name': 'access:revoke', 'resource': 'access', 'action': 'revoke', 'description': 'Revoke access permissions'},
            {'name': 'access:monitor', 'resource': 'access', 'action': 'monitor', 'description': 'Monitor access logs'},
            
            # Security
            {'name': 'security:configure', 'resource': 'security', 'action': 'configure', 'description': 'Configure security settings'},
            {'name': 'security:monitor', 'resource': 'security', 'action': 'monitor', 'description': 'Monitor security events'},
            {'name': 'security:audit', 'resource': 'security', 'action': 'audit', 'description': 'Access security audit logs'},
            
            # Reports
            {'name': 'reports:view', 'resource': 'reports', 'action': 'view', 'description': 'View reports'},
            {'name': 'reports:create', 'resource': 'reports', 'action': 'create', 'description': 'Create custom reports'},
            {'name': 'reports:export', 'resource': 'reports', 'action': 'export', 'description': 'Export report data'},
            
            # Profile Management
            {'name': 'profile:read', 'resource': 'profile', 'action': 'read', 'description': 'View own profile'},
            {'name': 'profile:update', 'resource': 'profile', 'action': 'update', 'description': 'Update own profile'},
            
            # Document Management
            {'name': 'documents:read', 'resource': 'documents', 'action': 'read', 'description': 'View documents'},
            {'name': 'documents:upload', 'resource': 'documents', 'action': 'upload', 'description': 'Upload documents'},
            {'name': 'documents:delete', 'resource': 'documents', 'action': 'delete', 'description': 'Delete documents'},
            
            # LPR System
            {'name': 'lpr:view', 'resource': 'lpr', 'action': 'view', 'description': 'View LPR events'},
            {'name': 'lpr:manage', 'resource': 'lpr', 'action': 'manage', 'description': 'Manage LPR system'},
            {'name': 'lpr:configure', 'resource': 'lpr', 'action': 'configure', 'description': 'Configure LPR settings'},
        ]
        
        for perm_data in default_permissions:
            permission = Permission.query.filter_by(name=perm_data['name']).first()
            if not permission:
                permission = Permission(
                    name=perm_data['name'],
                    resource=perm_data['resource'],
                    action=perm_data['action'],
                    description=perm_data['description'],
                    is_system_permission=True
                )
                db.session.add(permission)
        
        db.session.commit()
    
    @staticmethod
    def check_permission(user_id: int, permission: str, resource_id: Optional[str] = None, 
                        context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if user has permission for a specific action"""
        try:
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return False
            
            # Get user roles
            user_roles = UserRole.query.filter_by(
                user_id=user_id, 
                is_active=True
            ).all()
            
            # Check if any role has the permission
            has_permission = False
            for user_role in user_roles:
                if user_role.role.has_permission(permission):
                    # Check context-specific access
                    if RBACService._check_context_access(user_role, context):
                        has_permission = True
                        break
            
            # Apply security policies
            if has_permission:
                has_permission = RBACService._check_security_policies(user, permission, context)
            
            # Log access attempt
            RBACService._log_access_attempt(
                user_id=user_id,
                action=permission.split(':')[1] if ':' in permission else permission,
                resource=permission.split(':')[0] if ':' in permission else 'unknown',
                resource_id=resource_id,
                permission_required=permission,
                access_granted=has_permission,
                additional_data=context
            )
            
            return has_permission
            
        except Exception as e:
            current_app.logger.error(f"Permission check error: {str(e)}")
            return False
    
    @staticmethod
    def _check_context_access(user_role: UserRole, context: Optional[Dict[str, Any]]) -> bool:
        """Check if user role applies to the current context"""
        if not context:
            return True
        
        # Property-specific role
        if user_role.property_id and context.get('property_id'):
            return user_role.property_id == context['property_id']
        
        # Organization-specific role
        if user_role.organization_id and context.get('organization_id'):
            return user_role.organization_id == context['organization_id']
        
        # Global role (no specific context)
        if not user_role.property_id and not user_role.organization_id:
            return True
        
        return False
    
    @staticmethod
    def _check_security_policies(user: User, permission: str, context: Optional[Dict[str, Any]]) -> bool:
        """Check security policies for additional access control"""
        policies = SecurityPolicy.query.filter(
            db.or_(
                SecurityPolicy.applies_to_user_id == user.id,
                SecurityPolicy.applies_to_role_id.in_([ur.role_id for ur in user.user_roles])
            ),
            SecurityPolicy.is_active == True
        ).all()
        
        for policy in policies:
            if not RBACService._evaluate_policy(policy, user, context):
                return False
        
        return True
    
    @staticmethod
    def _evaluate_policy(policy: SecurityPolicy, user: User, context: Optional[Dict[str, Any]]) -> bool:
        """Evaluate a specific security policy"""
        config = policy.policy_config
        
        if policy.policy_type == 'time_based':
            return RBACService._check_time_policy(config, context)
        elif policy.policy_type == 'location_based':
            return RBACService._check_location_policy(config, context)
        elif policy.policy_type == 'device_based':
            return RBACService._check_device_policy(config, context)
        
        return True
    
    @staticmethod
    def _check_time_policy(config: Dict[str, Any], context: Optional[Dict[str, Any]]) -> bool:
        """Check time-based access policy"""
        if not config.get('allowed_hours'):
            return True
        
        current_time = datetime.now().time()
        start_time = time.fromisoformat(config['allowed_hours']['start'])
        end_time = time.fromisoformat(config['allowed_hours']['end'])
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:  # Crosses midnight
            return current_time >= start_time or current_time <= end_time
    
    @staticmethod
    def _check_location_policy(config: Dict[str, Any], context: Optional[Dict[str, Any]]) -> bool:
        """Check location-based access policy"""
        if not config.get('allowed_ips') or not context or not context.get('ip_address'):
            return True
        
        user_ip = context['ip_address']
        allowed_ips = config['allowed_ips']
        
        try:
            user_ip_obj = ipaddress.ip_address(user_ip)
            for allowed_ip in allowed_ips:
                if '/' in allowed_ip:  # CIDR notation
                    if user_ip_obj in ipaddress.ip_network(allowed_ip):
                        return True
                else:  # Single IP
                    if user_ip_obj == ipaddress.ip_address(allowed_ip):
                        return True
            return False
        except ValueError:
            return False
    
    @staticmethod
    def _check_device_policy(config: Dict[str, Any], context: Optional[Dict[str, Any]]) -> bool:
        """Check device-based access policy"""
        if not config.get('allowed_devices') or not context or not context.get('user_agent'):
            return True
        
        user_agent = context['user_agent'].lower()
        allowed_devices = [device.lower() for device in config['allowed_devices']]
        
        return any(device in user_agent for device in allowed_devices)
    
    @staticmethod
    def _log_access_attempt(user_id: int, action: str, resource: str, resource_id: Optional[str],
                           permission_required: str, access_granted: bool, 
                           additional_data: Optional[Dict[str, Any]] = None):
        """Log access attempt for security monitoring"""
        try:
            access_log = AccessLog(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                permission_required=permission_required,
                access_granted=access_granted,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get('User-Agent') if request else None,
                session_id=request.session.get('session_id') if request and hasattr(request, 'session') else None,
                additional_data_dict=additional_data or {}
            )
            db.session.add(access_log)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to log access attempt: {str(e)}")
    
    @staticmethod
    def assign_role(user_id: int, role_id: int, property_id: Optional[int] = None,
                   organization_id: Optional[int] = None, assigned_by_id: Optional[int] = None,
                   expires_at: Optional[datetime] = None) -> bool:
        """Assign role to user"""
        try:
            # Check if assignment already exists
            existing = UserRole.query.filter_by(
                user_id=user_id,
                role_id=role_id,
                property_id=property_id,
                organization_id=organization_id,
                is_active=True
            ).first()
            
            if existing:
                return True
            
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                property_id=property_id,
                organization_id=organization_id,
                assigned_by_id=assigned_by_id,
                expires_at=expires_at
            )
            
            db.session.add(user_role)
            db.session.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to assign role: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def revoke_role(user_id: int, role_id: int, property_id: Optional[int] = None,
                   organization_id: Optional[int] = None) -> bool:
        """Revoke role from user"""
        try:
            user_role = UserRole.query.filter_by(
                user_id=user_id,
                role_id=role_id,
                property_id=property_id,
                organization_id=organization_id,
                is_active=True
            ).first()
            
            if user_role:
                user_role.is_active = False
                db.session.commit()
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to revoke role: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_user_permissions(user_id: int) -> List[str]:
        """Get all permissions for a user"""
        user_roles = UserRole.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        permissions = set()
        for user_role in user_roles:
            for permission in user_role.role.permissions:
                permissions.add(permission.name)
        
        return list(permissions)
    
    @staticmethod
    def get_user_roles(user_id: int) -> List[Dict[str, Any]]:
        """Get all roles for a user"""
        user_roles = UserRole.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        return [ur.to_dict() for ur in user_roles]

def require_permission(permission: str, resource_id_param: Optional[str] = None):
    """Decorator to require specific permission for route access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user') or not g.current_user:
                return {'error': 'Authentication required'}, 401
            
            resource_id = None
            if resource_id_param:
                resource_id = kwargs.get(resource_id_param) or request.json.get(resource_id_param)
            
            context = {
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'property_id': kwargs.get('property_id') or request.json.get('property_id'),
                'organization_id': getattr(g.current_user, 'organization_id', None)
            }
            
            if not RBACService.check_permission(
                user_id=g.current_user.id,
                permission=permission,
                resource_id=str(resource_id) if resource_id else None,
                context=context
            ):
                return {'error': 'Insufficient permissions'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(role_name: str):
    """Decorator to require specific role for route access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user') or not g.current_user:
                return {'error': 'Authentication required'}, 401
            
            user_roles = RBACService.get_user_roles(g.current_user.id)
            has_role = any(role['role_name'] == role_name for role in user_roles)
            
            if not has_role:
                return {'error': f'Role {role_name} required'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator