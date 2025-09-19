"""
Role-Based Access Control (RBAC) Service for EstateCore
Provides comprehensive permission management and access control
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
from functools import wraps
from flask import request, jsonify, g

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Permission(Enum):
    """System permissions enum"""
    # User Management
    CREATE_USER = "create_user"
    READ_USER = "read_user" 
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    MANAGE_ROLES = "manage_roles"
    
    # Property Management
    CREATE_PROPERTY = "create_property"
    READ_PROPERTY = "read_property"
    UPDATE_PROPERTY = "update_property"
    DELETE_PROPERTY = "delete_property"
    MANAGE_PROPERTY_ACCESS = "manage_property_access"
    
    # Tenant Management
    CREATE_TENANT = "create_tenant"
    READ_TENANT = "read_tenant"
    UPDATE_TENANT = "update_tenant"
    DELETE_TENANT = "delete_tenant"
    VIEW_TENANT_DETAILS = "view_tenant_details"
    
    # Maintenance
    CREATE_MAINTENANCE = "create_maintenance"
    READ_MAINTENANCE = "read_maintenance"
    UPDATE_MAINTENANCE = "update_maintenance"
    DELETE_MAINTENANCE = "delete_maintenance"
    ASSIGN_MAINTENANCE = "assign_maintenance"
    
    # Financial/Payments
    CREATE_PAYMENT = "create_payment"
    READ_PAYMENT = "read_payment"
    UPDATE_PAYMENT = "update_payment"
    DELETE_PAYMENT = "delete_payment"
    PROCESS_REFUNDS = "process_refunds"
    VIEW_FINANCIAL_REPORTS = "view_financial_reports"
    
    # Documents
    UPLOAD_DOCUMENT = "upload_document"
    READ_DOCUMENT = "read_document"
    DELETE_DOCUMENT = "delete_document"
    MANAGE_DOCUMENT_ACCESS = "manage_document_access"
    
    # Analytics & Reports
    VIEW_ANALYTICS = "view_analytics"
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"
    
    # System Administration
    SYSTEM_CONFIG = "system_config"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_INTEGRATIONS = "manage_integrations"
    
    # Communication
    SEND_NOTIFICATIONS = "send_notifications"
    SEND_BULK_MESSAGES = "send_bulk_messages"
    
    # Lease Management
    CREATE_LEASE = "create_lease"
    READ_LEASE = "read_lease"
    UPDATE_LEASE = "update_lease"
    DELETE_LEASE = "delete_lease"
    MANAGE_LEASE = "manage_lease"
    MANAGE_LEASE_RENEWALS = "manage_lease_renewals"
    
    # Access Control
    MANAGE_ACCESS_CONTROL = "manage_access_control"
    VIEW_ACCESS_LOGS = "view_access_logs"

class Role(Enum):
    """System roles enum"""
    SUPER_ADMIN = "super_admin"
    PROPERTY_MANAGER = "property_manager"
    ASSISTANT_MANAGER = "assistant_manager"
    MAINTENANCE_STAFF = "maintenance_staff"
    TENANT = "tenant"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"

@dataclass
class RoleDefinition:
    """Role definition with permissions and constraints"""
    name: str
    display_name: str
    description: str
    permissions: Set[Permission]
    is_system_role: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class UserPermissionContext:
    """User's permission context for access control"""
    user_id: int
    role: Role
    permissions: Set[Permission]
    property_access: List[int] = None  # Property IDs user can access
    tenant_access: List[int] = None   # Tenant IDs user can access
    additional_permissions: Set[Permission] = None
    restrictions: Dict = None
    
    def __post_init__(self):
        if self.property_access is None:
            self.property_access = []
        if self.tenant_access is None:
            self.tenant_access = []
        if self.additional_permissions is None:
            self.additional_permissions = set()
        if self.restrictions is None:
            self.restrictions = {}

class PermissionService:
    def __init__(self):
        """Initialize permission service with default roles"""
        self.roles = self._initialize_default_roles()
        self.user_contexts = {}  # Cache for user permission contexts
        
    def _initialize_default_roles(self) -> Dict[Role, RoleDefinition]:
        """Initialize default system roles with their permissions"""
        roles = {}
        
        # Super Admin - Full access
        roles[Role.SUPER_ADMIN] = RoleDefinition(
            name=Role.SUPER_ADMIN.value,
            display_name="Super Administrator",
            description="Full system access with all permissions",
            permissions=set(Permission)  # All permissions
        )
        
        # Property Manager - Comprehensive property management
        roles[Role.PROPERTY_MANAGER] = RoleDefinition(
            name=Role.PROPERTY_MANAGER.value,
            display_name="Property Manager",
            description="Manages properties, tenants, and operations",
            permissions={
                # User Management (limited)
                Permission.READ_USER, Permission.UPDATE_USER,
                # Property Management
                Permission.CREATE_PROPERTY, Permission.READ_PROPERTY, 
                Permission.UPDATE_PROPERTY, Permission.MANAGE_PROPERTY_ACCESS,
                # Tenant Management
                Permission.CREATE_TENANT, Permission.READ_TENANT, 
                Permission.UPDATE_TENANT, Permission.VIEW_TENANT_DETAILS,
                # Maintenance
                Permission.CREATE_MAINTENANCE, Permission.READ_MAINTENANCE,
                Permission.UPDATE_MAINTENANCE, Permission.ASSIGN_MAINTENANCE,
                # Financial
                Permission.READ_PAYMENT, Permission.UPDATE_PAYMENT,
                Permission.VIEW_FINANCIAL_REPORTS,
                # Documents
                Permission.UPLOAD_DOCUMENT, Permission.READ_DOCUMENT,
                Permission.DELETE_DOCUMENT, Permission.MANAGE_DOCUMENT_ACCESS,
                # Analytics
                Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS, Permission.EXPORT_DATA,
                # Communication
                Permission.SEND_NOTIFICATIONS, Permission.SEND_BULK_MESSAGES,
                # Access Control (limited)
                Permission.VIEW_ACCESS_LOGS
            }
        )
        
        # Assistant Manager - Operational support
        roles[Role.ASSISTANT_MANAGER] = RoleDefinition(
            name=Role.ASSISTANT_MANAGER.value,
            display_name="Assistant Manager",
            description="Assists with daily operations and tenant management",
            permissions={
                # User Management (read only)
                Permission.READ_USER,
                # Property Management (read/update)
                Permission.READ_PROPERTY, Permission.UPDATE_PROPERTY,
                # Tenant Management
                Permission.CREATE_TENANT, Permission.READ_TENANT, 
                Permission.UPDATE_TENANT, Permission.VIEW_TENANT_DETAILS,
                # Maintenance
                Permission.CREATE_MAINTENANCE, Permission.READ_MAINTENANCE,
                Permission.UPDATE_MAINTENANCE,
                # Financial (limited)
                Permission.READ_PAYMENT, Permission.UPDATE_PAYMENT,
                # Documents
                Permission.UPLOAD_DOCUMENT, Permission.READ_DOCUMENT,
                # Analytics (limited)
                Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS,
                # Communication
                Permission.SEND_NOTIFICATIONS
            }
        )
        
        # Maintenance Staff - Maintenance focused
        roles[Role.MAINTENANCE_STAFF] = RoleDefinition(
            name=Role.MAINTENANCE_STAFF.value,
            display_name="Maintenance Staff",
            description="Handles maintenance requests and property upkeep",
            permissions={
                # Property (read only)
                Permission.READ_PROPERTY,
                # Tenant (limited read)
                Permission.READ_TENANT,
                # Maintenance
                Permission.CREATE_MAINTENANCE, Permission.READ_MAINTENANCE,
                Permission.UPDATE_MAINTENANCE,
                # Documents (maintenance related)
                Permission.UPLOAD_DOCUMENT, Permission.READ_DOCUMENT,
                # Communication (notifications)
                Permission.SEND_NOTIFICATIONS
            }
        )
        
        # Tenant - Self-service access
        roles[Role.TENANT] = RoleDefinition(
            name=Role.TENANT.value,
            display_name="Tenant",
            description="Self-service access for tenants",
            permissions={
                # User (own profile only)
                Permission.READ_USER, Permission.UPDATE_USER,
                # Property (read own)
                Permission.READ_PROPERTY,
                # Tenant (read own)
                Permission.READ_TENANT, Permission.UPDATE_TENANT,
                # Maintenance (create/read own)
                Permission.CREATE_MAINTENANCE, Permission.READ_MAINTENANCE,
                # Payments (own payments)
                Permission.CREATE_PAYMENT, Permission.READ_PAYMENT,
                # Documents (own documents)
                Permission.UPLOAD_DOCUMENT, Permission.READ_DOCUMENT
            }
        )
        
        # Accountant - Financial focus
        roles[Role.ACCOUNTANT] = RoleDefinition(
            name=Role.ACCOUNTANT.value,
            display_name="Accountant",
            description="Manages financial records and reports",
            permissions={
                # User (read only)
                Permission.READ_USER,
                # Property (read only)
                Permission.READ_PROPERTY,
                # Tenant (read only)
                Permission.READ_TENANT,
                # Financial (full access)
                Permission.CREATE_PAYMENT, Permission.READ_PAYMENT,
                Permission.UPDATE_PAYMENT, Permission.DELETE_PAYMENT,
                Permission.PROCESS_REFUNDS, Permission.VIEW_FINANCIAL_REPORTS,
                # Documents (financial docs)
                Permission.UPLOAD_DOCUMENT, Permission.READ_DOCUMENT,
                # Analytics (financial)
                Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS, Permission.EXPORT_DATA
            }
        )
        
        # Viewer - Read-only access
        roles[Role.VIEWER] = RoleDefinition(
            name=Role.VIEWER.value,
            display_name="Viewer",
            description="Read-only access to basic information",
            permissions={
                Permission.READ_USER, Permission.READ_PROPERTY,
                Permission.READ_TENANT, Permission.READ_MAINTENANCE,
                Permission.READ_PAYMENT, Permission.READ_DOCUMENT,
                Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS
            }
        )
        
        return roles
    
    def get_role_definition(self, role: Role) -> RoleDefinition:
        """Get role definition by role enum"""
        return self.roles.get(role)
    
    def get_all_roles(self) -> Dict[Role, RoleDefinition]:
        """Get all role definitions"""
        return self.roles
    
    def create_custom_role(self, name: str, display_name: str, description: str, 
                          permissions: Set[Permission]) -> RoleDefinition:
        """Create a custom role (non-system role)"""
        custom_role = RoleDefinition(
            name=name,
            display_name=display_name,
            description=description,
            permissions=permissions,
            is_system_role=False
        )
        # Note: Custom roles would be stored in database in production
        return custom_role
    
    def get_user_permissions(self, user_id: int, role: Role, 
                           property_access: List[int] = None,
                           tenant_access: List[int] = None,
                           additional_permissions: Set[Permission] = None) -> UserPermissionContext:
        """Get user's permission context"""
        role_def = self.get_role_definition(role)
        if not role_def:
            raise ValueError(f"Unknown role: {role}")
        
        # Combine role permissions with additional permissions
        all_permissions = role_def.permissions.copy()
        if additional_permissions:
            all_permissions.update(additional_permissions)
        
        context = UserPermissionContext(
            user_id=user_id,
            role=role,
            permissions=all_permissions,
            property_access=property_access or [],
            tenant_access=tenant_access or [],
            additional_permissions=additional_permissions or set()
        )
        
        # Cache the context
        self.user_contexts[user_id] = context
        return context
    
    def has_permission(self, user_id: int, permission: Permission, 
                      resource_id: int = None, resource_type: str = None) -> bool:
        """Check if user has specific permission"""
        context = self.user_contexts.get(user_id)
        if not context:
            return False
        
        # Check if user has the permission
        if permission not in context.permissions:
            return False
        
        # Apply resource-level access control
        if resource_type and resource_id:
            if resource_type == 'property' and context.property_access:
                return resource_id in context.property_access
            elif resource_type == 'tenant' and context.tenant_access:
                return resource_id in context.tenant_access
            # For tenant role, only allow access to own resources
            elif context.role == Role.TENANT:
                if resource_type == 'tenant':
                    return resource_id == user_id  # Tenant can only access their own record
                elif resource_type == 'property':
                    # Check if tenant has access to this property through their tenancy
                    return self._tenant_has_property_access(user_id, resource_id)
        
        return True
    
    def _tenant_has_property_access(self, user_id: int, property_id: int) -> bool:
        """Check if tenant has access to specific property"""
        # This would check the database for tenant-property relationship
        # For now, return True as a placeholder
        return True
    
    def can_access_user(self, requester_id: int, target_user_id: int) -> bool:
        """Check if requester can access target user's information"""
        requester_context = self.user_contexts.get(requester_id)
        if not requester_context:
            return False
        
        # Super admins can access anyone
        if requester_context.role == Role.SUPER_ADMIN:
            return True
        
        # Users can access their own information
        if requester_id == target_user_id:
            return True
        
        # Property managers and assistants can access users in their properties
        if requester_context.role in [Role.PROPERTY_MANAGER, Role.ASSISTANT_MANAGER]:
            return Permission.READ_USER in requester_context.permissions
        
        return False
    
    def filter_accessible_properties(self, user_id: int, property_ids: List[int]) -> List[int]:
        """Filter property IDs to only those accessible by user"""
        context = self.user_contexts.get(user_id)
        if not context:
            return []
        
        # Super admin and property managers can access all properties
        if context.role in [Role.SUPER_ADMIN, Role.PROPERTY_MANAGER]:
            return property_ids
        
        # Other roles are limited to their assigned properties
        if context.property_access:
            return [pid for pid in property_ids if pid in context.property_access]
        
        return []
    
    def get_accessible_properties(self, user_id: int) -> List[int]:
        """Get list of property IDs user can access"""
        context = self.user_contexts.get(user_id)
        if not context:
            return []
        
        # Super admin can access all properties
        if context.role == Role.SUPER_ADMIN:
            return []  # Empty list means "all properties"
        
        return context.property_access
    
    def audit_permission_check(self, user_id: int, permission: Permission, 
                             resource_type: str = None, resource_id: int = None,
                             granted: bool = None):
        """Log permission check for auditing"""
        context = self.user_contexts.get(user_id)
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'role': context.role.value if context else 'unknown',
            'permission': permission.value,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'granted': granted,
            'ip_address': getattr(request, 'remote_addr', None) if request else None
        }
        
        logger.info(f"Permission audit: {audit_entry}")
        # In production, this would be stored in an audit log database

# Singleton instance
_permission_service = None

def get_permission_service() -> PermissionService:
    """Get singleton permission service instance"""
    global _permission_service
    if _permission_service is None:
        _permission_service = PermissionService()
    return _permission_service

# Decorators for permission checking
def require_permission(permission: Permission, resource_type: str = None):
    """Decorator to require specific permission for API endpoint"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user from request context (this would be set by authentication middleware)
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Get resource ID from URL parameters or request data
            resource_id = None
            if resource_type:
                # Try to extract resource ID from URL parameters
                resource_id = kwargs.get(f'{resource_type}_id')
                if not resource_id and request.json:
                    resource_id = request.json.get(f'{resource_type}_id')
            
            # Check permission
            permission_service = get_permission_service()
            has_perm = permission_service.has_permission(
                user_id, permission, resource_id, resource_type
            )
            
            # Audit the permission check
            permission_service.audit_permission_check(
                user_id, permission, resource_type, resource_id, has_perm
            )
            
            if not has_perm:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(required_roles: List[Role]):
    """Decorator to require specific role(s) for API endpoint"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            permission_service = get_permission_service()
            context = permission_service.user_contexts.get(user_id)
            
            if not context or context.role not in required_roles:
                return jsonify({'error': 'Insufficient role permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Utility functions
def load_user_permissions(user_id: int, role_name: str, 
                         property_access: List[int] = None,
                         tenant_access: List[int] = None,
                         additional_permissions: List[str] = None):
    """Load user permissions into the service (called during login)"""
    try:
        role = Role(role_name)
        additional_perms = set()
        if additional_permissions:
            additional_perms = {Permission(perm) for perm in additional_permissions}
        
        permission_service = get_permission_service()
        return permission_service.get_user_permissions(
            user_id, role, property_access, tenant_access, additional_perms
        )
    except ValueError as e:
        logger.error(f"Invalid role or permission: {e}")
        return None

def clear_user_permissions(user_id: int):
    """Clear user permissions from cache (called during logout)"""
    permission_service = get_permission_service()
    if user_id in permission_service.user_contexts:
        del permission_service.user_contexts[user_id]

def get_user_role_info(user_id: int) -> Dict:
    """Get user's role information for frontend"""
    permission_service = get_permission_service()
    context = permission_service.user_contexts.get(user_id)
    
    if not context:
        return {}
    
    role_def = permission_service.get_role_definition(context.role)
    
    return {
        'role': context.role.value,
        'display_name': role_def.display_name if role_def else context.role.value,
        'permissions': [perm.value for perm in context.permissions],
        'property_access': context.property_access,
        'tenant_access': context.tenant_access
    }

def has_permission(user_id: int, permission: Permission, property_id: Optional[int] = None) -> bool:
    """Module-level function to check if user has permission"""
    permission_service = get_permission_service()
    return permission_service.has_permission(user_id, permission, property_id)

if __name__ == "__main__":
    # Test the permission service
    service = get_permission_service()
    
    print("🔐 Permission Service Test")
    print(f"Available roles: {list(service.roles.keys())}")
    
    # Test permission context
    context = service.get_user_permissions(
        user_id=1, 
        role=Role.PROPERTY_MANAGER,
        property_access=[1, 2, 3]
    )
    
    print(f"Property Manager permissions: {len(context.permissions)}")
    print(f"Has CREATE_PROPERTY: {service.has_permission(1, Permission.CREATE_PROPERTY)}")
    print(f"Has SYSTEM_CONFIG: {service.has_permission(1, Permission.SYSTEM_CONFIG)}")
    
    print("✅ Permission service is ready!")