import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Toast from './ui/Toast';

const RoleManager = () => {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [currentUserPermissions, setCurrentUserPermissions] = useState({});
  const [toast, setToast] = useState(null);
  const [filter, setFilter] = useState({
    role: 'all',
    search: ''
  });

  // Role color mapping
  const roleColors = {
    super_admin: 'bg-red-100 text-red-800 border-red-200',
    property_manager: 'bg-blue-100 text-blue-800 border-blue-200',
    assistant_manager: 'bg-green-100 text-green-800 border-green-200',
    maintenance_staff: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    tenant: 'bg-purple-100 text-purple-800 border-purple-200',
    accountant: 'bg-orange-100 text-orange-800 border-orange-200',
    viewer: 'bg-gray-100 text-gray-800 border-gray-200'
  };

  // Fetch data functions
  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      showToast('Failed to fetch users', 'error');
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await fetch('/api/permissions/roles', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setRoles(data);
      }
    } catch (error) {
      console.error('Error fetching roles:', error);
      showToast('Failed to fetch roles', 'error');
    }
  };

  const fetchPermissions = async () => {
    try {
      const response = await fetch('/api/permissions/permissions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setPermissions(data);
      }
    } catch (error) {
      console.error('Error fetching permissions:', error);
      showToast('Failed to fetch permissions', 'error');
    }
  };

  const fetchUserPermissions = async (userId) => {
    try {
      const response = await fetch(`/api/users/${userId}/permissions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setCurrentUserPermissions(data);
      }
    } catch (error) {
      console.error('Error fetching user permissions:', error);
      showToast('Failed to fetch user permissions', 'error');
    }
  };

  // Update user role
  const updateUserRole = async (userId, roleData) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/users/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(roleData)
      });

      if (response.ok) {
        showToast('User role updated successfully', 'success');
        fetchUsers(); // Refresh user list
        setShowRoleModal(false);
        setSelectedUser(null);
      } else {
        const error = await response.json();
        showToast(error.error || 'Failed to update user role', 'error');
      }
    } catch (error) {
      console.error('Error updating user role:', error);
      showToast('Failed to update user role', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Show toast notification
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  // Filter users
  const filteredUsers = users.filter(user => {
    const matchesRole = filter.role === 'all' || user.role === filter.role;
    const matchesSearch = !filter.search || 
      user.email.toLowerCase().includes(filter.search.toLowerCase()) ||
      `${user.first_name} ${user.last_name}`.toLowerCase().includes(filter.search.toLowerCase());
    
    return matchesRole && matchesSearch;
  });

  // Get role display info
  const getRoleInfo = (roleName) => {
    const role = roles.find(r => r.id === roleName);
    return role || { display_name: roleName, description: '' };
  };

  // Get permission category icon
  const getCategoryIcon = (category) => {
    const icons = {
      'create': '➕',
      'read': '👁️',
      'update': '✏️',
      'delete': '🗑️',
      'manage': '⚙️',
      'view': '📊',
      'send': '📤',
      'process': '💳',
      'upload': '📤',
      'system': '🔧'
    };
    return icons[category] || '📋';
  };

  useEffect(() => {
    fetchUsers();
    fetchRoles();
    fetchPermissions();
  }, []);

  return (
    <div className="space-y-6">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Role Management</h2>
          <p className="text-gray-600">Manage user roles and permissions</p>
        </div>
      </div>

      {/* Role Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {roles.map(role => {
          const userCount = users.filter(u => u.role === role.id).length;
          return (
            <Card key={role.id} className="p-4 text-center">
              <div className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${roleColors[role.id] || 'bg-gray-100 text-gray-800'}`}>
                {role.display_name}
              </div>
              <div className="text-2xl font-bold text-gray-900 mt-2">{userCount}</div>
              <div className="text-sm text-gray-600">users</div>
            </Card>
          );
        })}
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Role
            </label>
            <select
              value={filter.role}
              onChange={(e) => setFilter({ ...filter, role: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Roles</option>
              {roles.map(role => (
                <option key={role.id} value={role.id}>
                  {role.display_name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Users
            </label>
            <input
              type="text"
              placeholder="Search by name or email..."
              value={filter.search}
              onChange={(e) => setFilter({ ...filter, search: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </Card>

      {/* Users List */}
      <Card className="p-4">
        <h3 className="text-lg font-semibold mb-4">
          Users ({filteredUsers.length})
        </h3>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading users...</p>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-6xl mb-4">👥</div>
            <p className="text-gray-600">No users found</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredUsers.map((user) => {
              const roleInfo = getRoleInfo(user.role);
              return (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-medium">
                        {`${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() || user.email[0].toUpperCase()}
                      </span>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {user.first_name && user.last_name 
                          ? `${user.first_name} ${user.last_name}`
                          : user.email
                        }
                      </p>
                      <p className="text-sm text-gray-500">{user.email}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${roleColors[user.role] || 'bg-gray-100 text-gray-800'}`}>
                          {roleInfo.display_name}
                        </span>
                        {!user.is_active && (
                          <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Inactive
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button
                      onClick={() => {
                        setSelectedUser(user);
                        fetchUserPermissions(user.id);
                        setShowPermissionModal(true);
                      }}
                      variant="outline"
                      size="sm"
                    >
                      View Permissions
                    </Button>
                    
                    <Button
                      onClick={() => {
                        setSelectedUser(user);
                        setShowRoleModal(true);
                      }}
                      size="sm"
                    >
                      Change Role
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Role Change Modal */}
      <Modal
        isOpen={showRoleModal}
        onClose={() => {
          setShowRoleModal(false);
          setSelectedUser(null);
        }}
        title="Change User Role"
      >
        {selectedUser && (
          <RoleChangeForm
            user={selectedUser}
            roles={roles}
            onSubmit={updateUserRole}
            onCancel={() => {
              setShowRoleModal(false);
              setSelectedUser(null);
            }}
            loading={loading}
          />
        )}
      </Modal>

      {/* Permissions View Modal */}
      <Modal
        isOpen={showPermissionModal}
        onClose={() => {
          setShowPermissionModal(false);
          setSelectedUser(null);
          setCurrentUserPermissions({});
        }}
        title="User Permissions"
        size="large"
      >
        {selectedUser && (
          <PermissionsView
            user={selectedUser}
            permissions={currentUserPermissions}
            allPermissions={permissions}
          />
        )}
      </Modal>
    </div>
  );
};

// Role Change Form Component
const RoleChangeForm = ({ user, roles, onSubmit, onCancel, loading }) => {
  const [selectedRole, setSelectedRole] = useState(user.role);
  const [propertyAccess, setPropertyAccess] = useState([]);
  const [tenantAccess, setTenantAccess] = useState([]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const roleData = {
      role: selectedRole,
      property_access: propertyAccess,
      tenant_access: tenantAccess
    };
    
    onSubmit(user.id, roleData);
  };

  const selectedRoleInfo = roles.find(r => r.id === selectedRole);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <p className="text-sm text-gray-600 mb-4">
          Changing role for: <strong>{user.first_name} {user.last_name}</strong> ({user.email})
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Role
        </label>
        <select
          value={selectedRole}
          onChange={(e) => setSelectedRole(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          {roles.map(role => (
            <option key={role.id} value={role.id}>
              {role.display_name}
            </option>
          ))}
        </select>
        
        {selectedRoleInfo && (
          <div className="mt-2 p-3 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-800">
              <strong>Description:</strong> {selectedRoleInfo.description}
            </p>
            <p className="text-sm text-blue-600 mt-1">
              <strong>Permissions:</strong> {selectedRoleInfo.permissions.length} permissions included
            </p>
          </div>
        )}
      </div>

      {/* Property Access (for non-tenant roles) */}
      {selectedRole !== 'tenant' && selectedRole !== 'super_admin' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Property Access (Optional)
          </label>
          <input
            type="text"
            placeholder="Property IDs (comma separated, e.g., 1,2,3)"
            value={propertyAccess.join(',')}
            onChange={(e) => {
              const ids = e.target.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
              setPropertyAccess(ids);
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Leave empty to allow access to all properties
          </p>
        </div>
      )}

      <div className="flex justify-end space-x-3">
        <Button
          type="button"
          onClick={onCancel}
          variant="outline"
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={loading}
        >
          {loading ? 'Updating...' : 'Update Role'}
        </Button>
      </div>
    </form>
  );
};

// Permissions View Component
const PermissionsView = ({ user, permissions, allPermissions }) => {
  const getCategoryIcon = (category) => {
    const icons = {
      'create': '➕',
      'read': '👁️',
      'update': '✏️',
      'delete': '🗑️',
      'manage': '⚙️',
      'view': '📊',
      'send': '📤',
      'process': '💳',
      'upload': '📤',
      'system': '🔧'
    };
    return icons[category] || '📋';
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">
          {user.first_name} {user.last_name} ({permissions.role})
        </h3>
        <p className="text-sm text-gray-600">{user.email}</p>
      </div>

      {/* Access Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h4 className="font-medium text-blue-900">Role</h4>
          <p className="text-blue-700">{permissions.display_name || permissions.role}</p>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <h4 className="font-medium text-green-900">Property Access</h4>
          <p className="text-green-700">
            {permissions.property_access?.length 
              ? `${permissions.property_access.length} properties`
              : 'All properties'
            }
          </p>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg">
          <h4 className="font-medium text-purple-900">Total Permissions</h4>
          <p className="text-purple-700">{permissions.permissions?.length || 0}</p>
        </div>
      </div>

      {/* Permissions by Category */}
      <div>
        <h4 className="text-md font-medium mb-3">Permissions by Category</h4>
        {Object.entries(allPermissions).map(([category, perms]) => {
          const userCategoryPerms = perms.filter(perm => 
            permissions.permissions?.includes(perm.id)
          );
          
          if (userCategoryPerms.length === 0) return null;
          
          return (
            <div key={category} className="mb-4 border rounded-lg p-4">
              <h5 className="font-medium text-gray-900 mb-2 flex items-center">
                <span className="mr-2">{getCategoryIcon(category)}</span>
                {category.charAt(0).toUpperCase() + category.slice(1)} 
                <span className="ml-2 text-sm text-gray-500">
                  ({userCategoryPerms.length}/{perms.length})
                </span>
              </h5>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {userCategoryPerms.map(perm => (
                  <div key={perm.id} className="flex items-center text-sm">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    {perm.display_name}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Property Access Details */}
      {permissions.property_access?.length > 0 && (
        <div>
          <h4 className="text-md font-medium mb-3">Accessible Properties</h4>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">
              Property IDs: {permissions.property_access.join(', ')}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoleManager;