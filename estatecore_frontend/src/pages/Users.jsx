import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function Users() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [properties, setProperties] = useState([]);
  const [availableUnits, setAvailableUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [filters, setFilters] = useState({
    role: '',
    company: '',
    status: '',
    search: ''
  });

  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    role: 'property_manager',
    company_id: '',
    property_access: [],
    phone: '',
    status: 'active',
    property_id: '',
    unit_number: ''
  });

  const roles = [
    { value: 'super_admin', label: 'Super Admin', description: 'Full system access' },
    { value: 'company_admin', label: 'Company Admin', description: 'Manage company and all properties' },
    { value: 'property_admin', label: 'Property Admin', description: 'Manage specific properties' },
    { value: 'property_manager', label: 'Property Manager', description: 'Day-to-day property operations' },
    { value: 'tenant', label: 'Tenant', description: 'Tenant portal access' },
    { value: 'vendor', label: 'Vendor', description: 'Vendor/contractor access' }
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [usersResponse, companiesResponse, propertiesResponse] = await Promise.all([
        api.get('/api/users'),
        api.get('/api/companies'),
        api.get('/api/properties')
      ]);

      if (usersResponse.success) {
        setUsers(usersResponse.users || []);
      }

      if (companiesResponse.success) {
        setCompanies(companiesResponse.companies || []);
      }

      if (propertiesResponse.success) {
        setProperties(propertiesResponse.properties || []);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      setError('Failed to load users data');
    } finally {
      setLoading(false);
    }
  };

  // Load properties when company changes for property roles
  const loadPropertiesForCompany = async (companyId) => {
    if (!companyId) {
      setProperties([]);
      return;
    }
    try {
      const response = await api.get(`/api/properties?company_id=${companyId}`);
      if (response.success) {
        setProperties(response.properties || []);
      }
    } catch (error) {
      console.error('Error loading properties:', error);
    }
  };

  // Load available units when property changes for tenant role
  const loadAvailableUnits = async (propertyId) => {
    if (!propertyId) {
      setAvailableUnits([]);
      return;
    }
    try {
      const response = await api.get(`/api/properties/${propertyId}/units`);
      if (response.success) {
        setAvailableUnits(response.available_units || []);
      }
    } catch (error) {
      console.error('Error loading units:', error);
    }
  };

  // Handle user role change
  const handleRoleChange = (role) => {
    setNewUser({
      ...newUser,
      role,
      company_id: '',
      property_id: '',
      unit_number: '',
      property_access: []
    });
    setProperties([]);
    setAvailableUnits([]);
  };

  // Handle company change for property roles
  const handleCompanyChange = (companyId) => {
    setNewUser({
      ...newUser,
      company_id: companyId,
      property_id: '',
      property_access: []
    });
    if (['property_admin', 'property_manager'].includes(newUser.role)) {
      loadPropertiesForCompany(companyId);
    }
  };

  // Handle property change for tenant role
  const handlePropertyChange = (propertyId) => {
    setNewUser({
      ...newUser,
      property_id: propertyId,
      unit_number: ''
    });
    if (newUser.role === 'tenant') {
      loadAvailableUnits(propertyId);
    } else if (['property_admin', 'property_manager'].includes(newUser.role)) {
      // For property roles, add to property_access array
      const selectedProperty = properties.find(p => p.id === parseInt(propertyId));
      if (selectedProperty && !newUser.property_access.includes(propertyId)) {
        setNewUser({
          ...newUser,
          property_access: [...newUser.property_access, propertyId]
        });
      }
    }
  };

  const createUser = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/api/users', newUser);
      if (response.success) {
        await loadData();
        setShowCreateModal(false);
        setNewUser({
          name: '',
          email: '',
          role: 'property_manager',
          company_id: '',
          property_access: [],
          phone: '',
          status: 'active',
          property_id: '',
          unit_number: ''
        });
        setProperties([]);
        setAvailableUnits([]);
        setError('');
      } else {
        setError(response.error || 'Failed to create user');
      }
    } catch (error) {
      console.error('Error creating user:', error);
      setError('Failed to create user');
    }
  };

  const updateUser = async (e) => {
    e.preventDefault();
    try {
      const response = await api.put(`/api/users/${selectedUser.id}`, selectedUser);
      if (response.success) {
        await loadData();
        setShowEditModal(false);
        setSelectedUser(null);
        setError('');
      } else {
        setError(response.error || 'Failed to update user');
      }
    } catch (error) {
      console.error('Error updating user:', error);
      setError('Failed to update user');
    }
  };

  const deleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
      const response = await api.delete(`/api/users/${userId}`);
      if (response.success) {
        await loadData();
        setError('');
      } else {
        setError(response.error || 'Failed to delete user');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      setError('Failed to delete user');
    }
  };

  const resetPassword = async (userId) => {
    if (!confirm('Send password reset email to this user?')) return;
    
    try {
      const response = await api.post(`/api/users/${userId}/reset-password`);
      if (response.success) {
        alert('Password reset email sent successfully');
      } else {
        setError(response.error || 'Failed to send password reset');
      }
    } catch (error) {
      console.error('Error sending password reset:', error);
      setError('Failed to send password reset');
    }
  };

  const toggleUserStatus = async (userId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    try {
      const response = await api.patch(`/api/users/${userId}/status`, { status: newStatus });
      if (response.success) {
        await loadData();
        setError('');
      } else {
        setError(response.error || 'Failed to update user status');
      }
    } catch (error) {
      console.error('Error updating user status:', error);
      setError('Failed to update user status');
    }
  };

  const getRoleColor = (role) => {
    const colors = {
      super_admin: 'bg-red-100 text-red-800',
      company_admin: 'bg-purple-100 text-purple-800',
      property_admin: 'bg-blue-100 text-blue-800',
      property_manager: 'bg-green-100 text-green-800',
      tenant: 'bg-yellow-100 text-yellow-800',
      vendor: 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status) => {
    return status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
  };

  const filteredUsers = users.filter(user => {
    if (filters.role && user.role !== filters.role) return false;
    if (filters.company && user.company_id !== parseInt(filters.company)) return false;
    if (filters.status && user.status !== filters.status) return false;
    if (filters.search && !user.name.toLowerCase().includes(filters.search.toLowerCase()) && 
        !user.email.toLowerCase().includes(filters.search.toLowerCase())) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">👥 User Management</h1>
            <p className="text-gray-600">Manage system users, roles, and permissions</p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => navigate('/invite-user')}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              ✉️ Invite User
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              ➕ Add User
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-4">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <select
              value={filters.role}
              onChange={(e) => setFilters({...filters, role: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Roles</option>
              {roles.map(role => (
                <option key={role.value} value={role.value}>{role.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
            <select
              value={filters.company}
              onChange={(e) => setFilters({...filters, company: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Companies</option>
              {companies.map(company => (
                <option key={company.id} value={company.id}>{company.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <input
              type="text"
              placeholder="Search by name or email..."
              value={filters.search}
              onChange={(e) => setFilters({...filters, search: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium">Users ({filteredUsers.length})</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.map((user) => {
                const company = companies.find(c => c.id === user.company_id);
                return (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                        {user.phone && <div className="text-xs text-gray-400">{user.phone}</div>}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(user.role)}`}>
                        {roles.find(r => r.value === user.role)?.label || user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {company?.name || 'No Company'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(user.status)}`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      <button
                        onClick={() => {setSelectedUser(user); setShowEditModal(true);}}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        ✏️ Edit
                      </button>
                      <button
                        onClick={() => toggleUserStatus(user.id, user.status)}
                        className={user.status === 'active' ? 'text-orange-600 hover:text-orange-900' : 'text-green-600 hover:text-green-900'}
                      >
                        {user.status === 'active' ? '⏸️ Deactivate' : '▶️ Activate'}
                      </button>
                      <button
                        onClick={() => resetPassword(user.id)}
                        className="text-purple-600 hover:text-purple-900"
                      >
                        🔑 Reset Password
                      </button>
                      <button
                        onClick={() => deleteUser(user.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        🗑️ Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowCreateModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              <form onSubmit={createUser}>
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Create New User</h3>
                </div>
                
                <div className="px-6 py-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                    <input
                      type="text"
                      required
                      value={newUser.name}
                      onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                    <input
                      type="email"
                      required
                      value={newUser.email}
                      onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                    <input
                      type="tel"
                      value={newUser.phone}
                      onChange={(e) => setNewUser({...newUser, phone: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Role *</label>
                    <select
                      required
                      value={newUser.role}
                      onChange={(e) => handleRoleChange(e.target.value)}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      {roles.map(role => (
                        <option key={role.value} value={role.value}>{role.label}</option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Company Selection - Required for property admins/managers and tenants */}
                  {(['property_admin', 'property_manager', 'tenant'].includes(newUser.role)) && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Company *</label>
                      <select
                        required
                        value={newUser.company_id}
                        onChange={(e) => handleCompanyChange(e.target.value)}
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select Company</option>
                        {companies.map(company => (
                          <option key={company.id} value={company.id}>{company.name}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Property Selection - For property admins/managers */}
                  {(['property_admin', 'property_manager'].includes(newUser.role) && newUser.company_id) && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {newUser.role === 'property_admin' ? 'Managed Properties' : 'Assigned Properties'}
                      </label>
                      <select
                        value={newUser.property_id}
                        onChange={(e) => handlePropertyChange(e.target.value)}
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select Property to Add</option>
                        {properties.filter(p => p.company_id === parseInt(newUser.company_id)).map(property => (
                          <option key={property.id} value={property.id}>{property.name} - {property.address}</option>
                        ))}
                      </select>
                      {newUser.property_access.length > 0 && (
                        <div className="mt-2">
                          <p className="text-sm text-gray-600 mb-2">Selected Properties:</p>
                          <div className="flex flex-wrap gap-2">
                            {newUser.property_access.map(propId => {
                              const property = properties.find(p => p.id === parseInt(propId));
                              return property ? (
                                <span key={propId} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                  {property.name}
                                  <button
                                    type="button"
                                    onClick={() => setNewUser({
                                      ...newUser,
                                      property_access: newUser.property_access.filter(id => id !== propId)
                                    })}
                                    className="ml-1 text-blue-600 hover:text-blue-800"
                                  >
                                    ×
                                  </button>
                                </span>
                              ) : null;
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Property and Unit Selection - For tenants */}
                  {(newUser.role === 'tenant' && newUser.company_id) && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Property *</label>
                        <select
                          required
                          value={newUser.property_id}
                          onChange={(e) => handlePropertyChange(e.target.value)}
                          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Select Property</option>
                          {properties.filter(p => p.company_id === parseInt(newUser.company_id)).map(property => (
                            <option key={property.id} value={property.id}>{property.name} - {property.address}</option>
                          ))}
                        </select>
                      </div>

                      {(newUser.property_id && availableUnits.length > 0) && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Available Unit *</label>
                          <select
                            required
                            value={newUser.unit_number}
                            onChange={(e) => setNewUser({...newUser, unit_number: e.target.value})}
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">Select Unit</option>
                            {availableUnits.map(unit => (
                              <option key={unit.unit_number} value={unit.unit_number}>
                                Unit {unit.unit_number}
                              </option>
                            ))}
                          </select>
                          <p className="mt-1 text-xs text-gray-500">
                            {availableUnits.length} available units in {properties.find(p => p.id === parseInt(newUser.property_id))?.name}
                          </p>
                        </div>
                      )}

                      {(newUser.property_id && availableUnits.length === 0) && (
                        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <p className="text-sm text-yellow-800">
                            No available units in the selected property. All units are currently occupied.
                          </p>
                        </div>
                      )}
                    </>
                  )}

                  {/* General Company Selection - For other roles */}
                  {(!['property_admin', 'property_manager', 'tenant'].includes(newUser.role)) && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
                      <select
                        value={newUser.company_id}
                        onChange={(e) => setNewUser({...newUser, company_id: e.target.value})}
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select Company</option>
                        {companies.map(company => (
                          <option key={company.id} value={company.id}>{company.name}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
                
                <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Create User
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowEditModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              <form onSubmit={updateUser}>
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Edit User</h3>
                </div>
                
                <div className="px-6 py-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                    <input
                      type="text"
                      required
                      value={selectedUser.name}
                      onChange={(e) => setSelectedUser({...selectedUser, name: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                    <input
                      type="email"
                      required
                      value={selectedUser.email}
                      onChange={(e) => setSelectedUser({...selectedUser, email: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                    <input
                      type="tel"
                      value={selectedUser.phone || ''}
                      onChange={(e) => setSelectedUser({...selectedUser, phone: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Role *</label>
                    <select
                      required
                      value={selectedUser.role}
                      onChange={(e) => setSelectedUser({...selectedUser, role: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      {roles.map(role => (
                        <option key={role.value} value={role.value}>{role.label}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
                    <select
                      value={selectedUser.company_id || ''}
                      onChange={(e) => setSelectedUser({...selectedUser, company_id: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Company</option>
                      {companies.map(company => (
                        <option key={company.id} value={company.id}>{company.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Update User
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}