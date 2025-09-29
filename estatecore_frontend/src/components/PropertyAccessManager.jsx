import React, { useState, useEffect } from 'react';
import api from '../api';

export default function PropertyAccessManager({ companyId, onClose }) {
  const [users, setUsers] = useState([]);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [availablePermissions, setAvailablePermissions] = useState({});
  const [showPermissionsManager, setShowPermissionsManager] = useState(false);

  useEffect(() => {
    fetchCompanyData();
    fetchAvailablePermissions();
  }, [companyId]);

  const fetchCompanyData = async () => {
    try {
      const response = await api.get(`/api/companies/${companyId}/users`);
      if (response.success) {
        setUsers(response.users);
        setProperties(response.company_properties);
      }
    } catch (error) {
      console.error('Error fetching company data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailablePermissions = async () => {
    try {
      const response = await api.get('/api/permissions/available');
      if (response.success) {
        setAvailablePermissions(response.permissions);
      }
    } catch (error) {
      console.error('Error fetching permissions:', error);
    }
  };

  const updateUserPropertyAccess = async (userId, propertyIds) => {
    try {
      const response = await api.put(`/api/companies/${companyId}/users/${userId}/property-access`, {
        property_ids: propertyIds
      });
      
      if (response.success) {
        // Update local state
        setUsers(prevUsers => 
          prevUsers.map(user => 
            user.id === userId 
              ? { ...user, property_access: propertyIds }
              : user
          )
        );
        
        // Refresh data to get updated accessible_properties
        fetchCompanyData();
      }
    } catch (error) {
      console.error('Error updating property access:', error);
    }
  };

  const updateUserPermissions = async (userId, permissions) => {
    try {
      const response = await api.put(`/api/companies/${companyId}/users/${userId}/permissions`, {
        permissions: permissions
      });
      
      if (response.success) {
        // Update local state
        setUsers(prevUsers => 
          prevUsers.map(user => 
            user.id === userId 
              ? { ...user, permissions: permissions }
              : user
          )
        );
        
        // Refresh data to get updated information
        fetchCompanyData();
      }
    } catch (error) {
      console.error('Error updating permissions:', error);
    }
  };

  const createUser = async (userData) => {
    try {
      const response = await api.post(`/api/companies/${companyId}/users`, userData);
      if (response.success) {
        fetchCompanyData(); // Refresh data
        setShowCreateUser(false);
      }
    } catch (error) {
      console.error('Error creating user:', error);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg">
          <div>Loading property access management...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-blue-600 text-white p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">Property Access Management</h2>
              <p className="text-blue-100">Manage team members and their property access levels</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[70vh]">
          {/* Action Buttons */}
          <div className="mb-6 flex justify-between items-center">
            <h3 className="text-lg font-semibold">Team Members ({users.length})</h3>
            <div className="space-x-2">
              <button
                onClick={() => setShowPermissionsManager(true)}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
              >
                🔐 Manage Permissions
              </button>
              <button
                onClick={() => setShowCreateUser(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                + Add Team Member
              </button>
            </div>
          </div>

          {/* Users Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {users.map(user => (
              <UserAccessCard
                key={user.id}
                user={user}
                properties={properties}
                onUpdateAccess={updateUserPropertyAccess}
                isSelected={selectedUser?.id === user.id}
                onSelect={() => setSelectedUser(user)}
                onUpdatePermissions={updateUserPermissions}
                availablePermissions={availablePermissions}
              />
            ))}
          </div>

          {/* Create User Modal */}
          {showCreateUser && (
            <CreateUserModal
              companyId={companyId}
              properties={properties}
              onCreateUser={createUser}
              onClose={() => setShowCreateUser(false)}
            />
          )}

          {/* Permissions Manager Modal */}
          {showPermissionsManager && (
            <PermissionsManagerModal
              users={users}
              availablePermissions={availablePermissions}
              onUpdatePermissions={updateUserPermissions}
              onClose={() => setShowPermissionsManager(false)}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function UserAccessCard({ user, properties, onUpdateAccess, isSelected, onSelect, onUpdatePermissions, availablePermissions }) {
  const [editMode, setEditMode] = useState(false);
  const [selectedProperties, setSelectedProperties] = useState(user.property_access);

  const handleToggleProperty = (propertyId) => {
    if (user.role === 'company_admin') return; // Company admins have access to all

    setSelectedProperties(prev => 
      prev.includes(propertyId)
        ? prev.filter(id => id !== propertyId)
        : [...prev, propertyId]
    );
  };

  const handleSaveAccess = () => {
    onUpdateAccess(user.id, selectedProperties);
    setEditMode(false);
  };

  const handleCancelEdit = () => {
    setSelectedProperties(user.property_access);
    setEditMode(false);
  };

  const roleColor = {
    'company_admin': 'bg-purple-100 text-purple-800',
    'property_admin': 'bg-blue-100 text-blue-800',
    'property_manager': 'bg-green-100 text-green-800',
    'viewer': 'bg-gray-100 text-gray-800'
  };

  return (
    <div className={`border rounded-lg p-4 ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
      {/* User Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="font-semibold text-lg">{user.name}</h4>
          <p className="text-gray-600 text-sm">{user.email}</p>
          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium mt-1 ${roleColor[user.role] || 'bg-gray-100 text-gray-800'}`}>
            {user.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </span>
        </div>
        
        {user.role !== 'company_admin' && (
          <div className="flex space-x-2">
            {editMode ? (
              <>
                <button
                  onClick={handleSaveAccess}
                  className="text-green-600 hover:text-green-800 text-sm"
                >
                  Save
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="text-gray-600 hover:text-gray-800 text-sm"
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                onClick={() => setEditMode(true)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                Edit Access
              </button>
            )}
          </div>
        )}
      </div>

      {/* Property Access */}
      <div>
        <h5 className="font-medium mb-2">Property Access:</h5>
        
        {user.role === 'company_admin' ? (
          <div className="text-sm text-purple-600 font-medium">
            ✓ Full access to all company properties
          </div>
        ) : (
          <div className="space-y-2">
            {properties.map(property => {
              const hasAccess = editMode 
                ? selectedProperties.includes(property.id)
                : user.property_access.includes(property.id);
              
              return (
                <div key={property.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium text-sm">{property.name}</div>
                    <div className="text-xs text-gray-600">{property.address} • {property.units} units</div>
                  </div>
                  
                  {editMode ? (
                    <button
                      onClick={() => handleToggleProperty(property.id)}
                      className={`px-3 py-1 rounded text-xs font-medium ${
                        hasAccess 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {hasAccess ? '✓ Access' : 'No Access'}
                    </button>
                  ) : (
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      hasAccess 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {hasAccess ? '✓ Access' : 'No Access'}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Permissions Summary */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="text-sm text-gray-600 space-y-1">
          <div>
            <strong>Property Access:</strong> {user.accessible_properties?.length || 0} of {properties.length} properties
          </div>
          <div>
            <strong>Permissions:</strong> {user.permissions?.length || 0} granted
          </div>
          {user.permissions && user.permissions.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {user.permissions.slice(0, 3).map(permission => {
                const permInfo = availablePermissions[permission];
                return (
                  <span key={permission} className="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                    {permInfo?.name || permission}
                  </span>
                );
              })}
              {user.permissions.length > 3 && (
                <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                  +{user.permissions.length - 3} more
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CreateUserModal({ companyId, properties, onCreateUser, onClose }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: 'property_manager',
    property_access: []
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreateUser(formData);
  };

  const toggleProperty = (propertyId) => {
    setFormData(prev => ({
      ...prev,
      property_access: prev.property_access.includes(propertyId)
        ? prev.property_access.filter(id => id !== propertyId)
        : [...prev.property_access, propertyId]
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        <div className="bg-green-600 text-white p-4">
          <h3 className="text-xl font-bold">Add Team Member</h3>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Role</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="property_manager">Property Manager</option>
                <option value="property_admin">Property Admin</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>
            
            {formData.role !== 'company_admin' && (
              <div>
                <label className="block text-sm font-medium mb-2">Property Access</label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {properties.map(property => (
                    <div key={property.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div>
                        <div className="font-medium text-sm">{property.name}</div>
                        <div className="text-xs text-gray-600">{property.address}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleProperty(property.id)}
                        className={`px-3 py-1 rounded text-xs font-medium ${
                          formData.property_access.includes(property.id)
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {formData.property_access.includes(property.id) ? '✓ Access' : 'No Access'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              Create User
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function PermissionsManagerModal({ users, availablePermissions, onUpdatePermissions, onClose }) {
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedPermissions, setSelectedPermissions] = useState([]);

  const selectUser = (user) => {
    setSelectedUser(user);
    setSelectedPermissions(user.permissions || []);
  };

  const togglePermission = (permission) => {
    setSelectedPermissions(prev => 
      prev.includes(permission)
        ? prev.filter(p => p !== permission)
        : [...prev, permission]
    );
  };

  const savePermissions = () => {
    if (selectedUser) {
      onUpdatePermissions(selectedUser.id, selectedPermissions);
      setSelectedUser(null);
      setSelectedPermissions([]);
    }
  };

  const groupedPermissions = Object.entries(availablePermissions).reduce((acc, [key, value]) => {
    const category = value.category;
    if (!acc[category]) acc[category] = [];
    acc[category].push({ key, ...value });
    return acc;
  }, {});

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <div className="bg-purple-600 text-white p-4">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-bold">🔐 Granular Permissions Management</h3>
            <button onClick={onClose} className="text-white hover:text-gray-200 text-2xl">×</button>
          </div>
        </div>
        
        <div className="flex h-[80vh]">
          {/* User List */}
          <div className="w-1/3 border-r border-gray-200 p-4 overflow-y-auto">
            <h4 className="font-semibold mb-4">Select User</h4>
            <div className="space-y-2">
              {users.filter(u => u.role !== 'company_admin').map(user => (
                <button
                  key={user.id}
                  onClick={() => selectUser(user)}
                  className={`w-full text-left p-3 rounded border ${
                    selectedUser?.id === user.id 
                      ? 'border-purple-500 bg-purple-50' 
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium">{user.name}</div>
                  <div className="text-sm text-gray-600">{user.email}</div>
                  <div className="text-xs text-gray-500">
                    {user.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} • 
                    {user.permissions?.length || 0} permissions
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Permissions Editor */}
          <div className="flex-1 p-4 overflow-y-auto">
            {selectedUser ? (
              <div>
                <div className="mb-4">
                  <h4 className="text-lg font-semibold">
                    Editing Permissions for {selectedUser.name}
                  </h4>
                  <p className="text-gray-600">
                    Role: {selectedUser.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                </div>

                {Object.entries(groupedPermissions).map(([category, permissions]) => (
                  <div key={category} className="mb-6">
                    <h5 className="font-medium text-gray-900 mb-3 capitalize">
                      {category.replace('_', ' ')} Permissions
                    </h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {permissions.map(permission => (
                        <div
                          key={permission.key}
                          className={`p-3 rounded border cursor-pointer transition-colors ${
                            selectedPermissions.includes(permission.key)
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-gray-200 hover:bg-gray-50'
                          }`}
                          onClick={() => togglePermission(permission.key)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="font-medium text-sm">{permission.name}</div>
                              <div className="text-xs text-gray-600 mt-1">
                                {permission.description}
                              </div>
                            </div>
                            <div className="ml-2">
                              {selectedPermissions.includes(permission.key) ? (
                                <div className="w-5 h-5 bg-purple-500 rounded flex items-center justify-center">
                                  <span className="text-white text-xs">✓</span>
                                </div>
                              ) : (
                                <div className="w-5 h-5 border border-gray-300 rounded"></div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}

                <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
                  <button
                    onClick={() => {
                      setSelectedUser(null);
                      setSelectedPermissions([]);
                    }}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={savePermissions}
                    className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                  >
                    Save Permissions
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">🔐</div>
                <h4 className="text-lg font-medium mb-2">Select a User</h4>
                <p>Choose a team member from the left to manage their permissions</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}