import React, { useState, useEffect, createContext, useContext } from 'react';

// Permission Context
const PermissionContext = createContext();

// Permission Provider Component
export const PermissionProvider = ({ children }) => {
  const [userPermissions, setUserPermissions] = useState({});
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  // Fetch user permissions
  const fetchUserPermissions = async () => {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setUserPermissions({
          permissions: userData.permissions || [],
          role: userData.role,
          property_access: userData.property_access || [],
          tenant_access: userData.tenant_access || []
        });
      } else {
        // Token might be invalid
        localStorage.removeItem('authToken');
      }
    } catch (error) {
      console.error('Error fetching user permissions:', error);
    } finally {
      setLoading(false);
    }
  };

  // Check if user has specific permission
  const hasPermission = (permission, resourceType = null, resourceId = null) => {
    if (!userPermissions.permissions) return false;
    
    // Check if user has the permission
    if (!userPermissions.permissions.includes(permission)) {
      return false;
    }

    // Apply resource-level access control
    if (resourceType && resourceId) {
      if (resourceType === 'property' && userPermissions.property_access.length > 0) {
        return userPermissions.property_access.includes(resourceId);
      } else if (resourceType === 'tenant' && userPermissions.tenant_access.length > 0) {
        return userPermissions.tenant_access.includes(resourceId);
      }
    }

    return true;
  };

  // Check if user has any of the specified permissions
  const hasAnyPermission = (permissions) => {
    return permissions.some(permission => hasPermission(permission));
  };

  // Check if user has all of the specified permissions
  const hasAllPermissions = (permissions) => {
    return permissions.every(permission => hasPermission(permission));
  };

  // Check if user has specific role
  const hasRole = (roles) => {
    if (!userPermissions.role) return false;
    const roleArray = Array.isArray(roles) ? roles : [roles];
    return roleArray.includes(userPermissions.role);
  };

  // Check multiple permissions at once (for API optimization)
  const checkPermissions = async (permissionsToCheck, resourceType = null, resourceId = null) => {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) return {};

      const response = await fetch('/api/permissions/check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          permissions: permissionsToCheck,
          resource_type: resourceType,
          resource_id: resourceId
        })
      });

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Error checking permissions:', error);
    }
    
    return {};
  };

  // Update user permissions (after role change, etc.)
  const refreshPermissions = () => {
    fetchUserPermissions();
  };

  const contextValue = {
    user,
    userPermissions,
    loading,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    checkPermissions,
    refreshPermissions
  };

  useEffect(() => {
    fetchUserPermissions();
  }, []);

  return (
    <PermissionContext.Provider value={contextValue}>
      {children}
    </PermissionContext.Provider>
  );
};

// Hook to use permission context
export const usePermissions = () => {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
};

// Permission Guard Component
const PermissionGuard = ({ 
  permission = null,
  permissions = null,
  role = null,
  requireAll = false,
  resourceType = null,
  resourceId = null,
  fallback = null,
  children 
}) => {
  const { hasPermission, hasAnyPermission, hasAllPermissions, hasRole, loading } = usePermissions();

  // Show loading state
  if (loading) {
    return fallback || null;
  }

  // Check role-based access
  if (role) {
    if (!hasRole(role)) {
      return fallback || null;
    }
  }

  // Check permission-based access
  if (permission) {
    if (!hasPermission(permission, resourceType, resourceId)) {
      return fallback || null;
    }
  }

  // Check multiple permissions
  if (permissions && Array.isArray(permissions)) {
    if (requireAll) {
      if (!hasAllPermissions(permissions)) {
        return fallback || null;
      }
    } else {
      if (!hasAnyPermission(permissions)) {
        return fallback || null;
      }
    }
  }

  return children;
};

// Higher-Order Component for permission checking
export const withPermissions = (requiredPermissions = {}) => {
  return (WrappedComponent) => {
    return (props) => {
      return (
        <PermissionGuard {...requiredPermissions}>
          <WrappedComponent {...props} />
        </PermissionGuard>
      );
    };
  };
};

// Permission-based Button Component
export const PermissionButton = ({ 
  permission,
  permissions,
  role,
  requireAll = false,
  resourceType = null,
  resourceId = null,
  children,
  disabledTitle = "You don't have permission to perform this action",
  ...buttonProps 
}) => {
  const { hasPermission, hasAnyPermission, hasAllPermissions, hasRole } = usePermissions();

  let hasAccess = true;

  // Check role-based access
  if (role && !hasRole(role)) {
    hasAccess = false;
  }

  // Check permission-based access
  if (permission && !hasPermission(permission, resourceType, resourceId)) {
    hasAccess = false;
  }

  // Check multiple permissions
  if (permissions && Array.isArray(permissions)) {
    if (requireAll && !hasAllPermissions(permissions)) {
      hasAccess = false;
    } else if (!requireAll && !hasAnyPermission(permissions)) {
      hasAccess = false;
    }
  }

  return (
    <button
      {...buttonProps}
      disabled={!hasAccess || buttonProps.disabled}
      title={!hasAccess ? disabledTitle : buttonProps.title}
      className={`${buttonProps.className || ''} ${!hasAccess ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {children}
    </button>
  );
};

// Permission-based Link Component
export const PermissionLink = ({ 
  permission,
  permissions,
  role,
  requireAll = false,
  resourceType = null,
  resourceId = null,
  fallback = null,
  children,
  ...linkProps 
}) => {
  return (
    <PermissionGuard
      permission={permission}
      permissions={permissions}
      role={role}
      requireAll={requireAll}
      resourceType={resourceType}
      resourceId={resourceId}
      fallback={fallback}
    >
      <a {...linkProps}>
        {children}
      </a>
    </PermissionGuard>
  );
};

// Permission Status Indicator
export const PermissionStatus = ({ className = '' }) => {
  const { user, userPermissions, loading } = usePermissions();

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
        <span className="text-sm text-gray-500">Loading...</span>
      </div>
    );
  }

  if (!user) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
        <span className="text-sm text-red-600">Not authenticated</span>
      </div>
    );
  }

  const roleColors = {
    super_admin: 'bg-red-500',
    property_manager: 'bg-blue-500',
    assistant_manager: 'bg-green-500',
    maintenance_staff: 'bg-yellow-500',
    tenant: 'bg-purple-500',
    accountant: 'bg-orange-500',
    viewer: 'bg-gray-500'
  };

  const roleColor = roleColors[userPermissions.role] || 'bg-gray-500';

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`w-2 h-2 ${roleColor} rounded-full`}></div>
      <span className="text-sm text-gray-700">
        {user.first_name} {user.last_name} ({userPermissions.role?.replace('_', ' ')})
      </span>
    </div>
  );
};

// Debug component to show user permissions (dev only)
export const PermissionDebug = () => {
  const { user, userPermissions, loading } = usePermissions();

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  if (loading) return <div>Loading permissions...</div>;

  return (
    <div className="fixed bottom-4 right-4 bg-white border shadow-lg rounded-lg p-4 max-w-xs text-xs">
      <h4 className="font-bold mb-2">Debug: User Permissions</h4>
      <div className="space-y-1">
        <div><strong>User:</strong> {user?.email || 'Not logged in'}</div>
        <div><strong>Role:</strong> {userPermissions.role || 'None'}</div>
        <div><strong>Permissions:</strong> {userPermissions.permissions?.length || 0}</div>
        <div><strong>Properties:</strong> {userPermissions.property_access?.length || 'All'}</div>
      </div>
    </div>
  );
};

export default PermissionGuard;