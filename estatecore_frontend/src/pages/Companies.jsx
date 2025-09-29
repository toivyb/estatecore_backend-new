import React, { useState, useEffect } from 'react';
import api from '../api';
import EnhancedCompanies from './EnhancedCompanies';

export default function Companies() {
  const [useEnhancedView, setUseEnhancedView] = useState(true);

  // If enhanced view is enabled, use the enhanced component
  if (useEnhancedView) {
    return (
      <div>
        <div className="mb-4 flex justify-end">
          <button
            onClick={() => setUseEnhancedView(false)}
            className="text-sm text-blue-600 hover:text-blue-800 underline"
          >
            Switch to Basic View
          </button>
        </div>
        <EnhancedCompanies />
      </div>
    );
  }

  // Original basic component below
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [newCompany, setNewCompany] = useState({
    name: '',
    billing_email: '',
    subscription_plan: 'basic'
  });

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/companies');
      if (response.success) {
        setCompanies(response.companies);
      }
    } catch (error) {
      console.error('Error fetching companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const createCompany = async () => {
    try {
      const response = await api.post('/api/companies', newCompany);
      if (response.success) {
        setCompanies([...companies, response.company]);
        setNewCompany({ name: '', billing_email: '', subscription_plan: 'basic' });
        setShowCreateModal(false);
      }
    } catch (error) {
      console.error('Error creating company:', error);
      alert('Error creating company. Check console for details.');
    }
  };

  const viewCompanyDetails = (company) => {
    setSelectedCompany(company);
    setShowViewModal(true);
  };

  const editCompany = (company) => {
    setSelectedCompany({...company});
    setShowEditModal(true);
  };

  const updateCompany = async () => {
    try {
      const response = await api.put(`/api/companies/${selectedCompany.id}`, selectedCompany);
      if (response.success) {
        setCompanies(companies.map(c => c.id === selectedCompany.id ? response.company : c));
        setShowEditModal(false);
        setSelectedCompany(null);
        
        // Show message about user status changes if any occurred
        if (response.user_status_changes && response.user_status_changes.action) {
          const { action, count, affected_users } = response.user_status_changes;
          const userList = affected_users.length > 0 ? `\n\nAffected users: ${affected_users.join(', ')}` : '';
          alert(`Company updated successfully!\n\n${count} users have been ${action}.${userList}`);
        }
      }
    } catch (error) {
      console.error('Error updating company:', error);
      alert('Error updating company. Check console for details.');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'suspended': return 'bg-yellow-100 text-yellow-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPlanColor = (plan) => {
    switch (plan) {
      case 'basic': return 'bg-blue-100 text-blue-800';
      case 'premium': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

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
            <h1 className="text-2xl font-bold text-gray-900 mb-2">🏢 Company Management (Basic View)</h1>
            <p className="text-gray-600">Manage organizations and their subscriptions</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setUseEnhancedView(true)}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              Switch to Enhanced View
            </button>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              ➕ Add Company
            </button>
          </div>
        </div>
      </div>

      {/* Companies Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {companies.map(company => (
          <div key={company.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{company.name}</h3>
                <p className="text-sm text-gray-600">{company.billing_email}</p>
              </div>
              <div className="flex flex-col space-y-2">
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(company.status)}`}>
                  {company.status}
                </span>
                <span className={`px-2 py-1 text-xs rounded-full ${getPlanColor(company.subscription_plan)}`}>
                  {company.subscription_plan}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Monthly Fee:</span>
                <span className="font-semibold text-green-600">${company.monthly_fee} ({company.total_units || 0} units)</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Properties:</span>
                <span className="font-medium">{company.property_count || 0}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Users:</span>
                <span className="font-medium">{company.user_count || 0}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Units:</span>
                <span className="font-medium">{company.total_units || 0}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Created:</span>
                <span className="text-sm">{formatDate(company.created_at)}</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t flex space-x-2">
              <button 
                onClick={() => viewCompanyDetails(company)}
                className="flex-1 bg-blue-600 text-white px-3 py-2 text-sm rounded hover:bg-blue-700"
              >
                👁️ View Details
              </button>
              <button 
                onClick={() => editCompany(company)}
                className="bg-gray-600 text-white px-3 py-2 text-sm rounded hover:bg-gray-700"
              >
                ✏️ Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      {companies.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-4">No companies found</div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            ➕ Create Your First Company
          </button>
        </div>
      )}

      {/* Create Company Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowCreateModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Create New Company</h3>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    value={newCompany.name}
                    onChange={(e) => setNewCompany({...newCompany, name: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter company name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Billing Email *
                  </label>
                  <input
                    type="email"
                    value={newCompany.billing_email}
                    onChange={(e) => setNewCompany({...newCompany, billing_email: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="billing@company.com"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subscription Plan
                  </label>
                  <select
                    value={newCompany.subscription_plan}
                    onChange={(e) => setNewCompany({...newCompany, subscription_plan: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="basic">Basic - $2.00/unit/month</option>
                    <option value="premium">Premium - $2.50/unit/month</option>
                  </select>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={createCompany}
                  disabled={!newCompany.name || !newCompany.billing_email}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Company
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View Company Details Modal */}
      {showViewModal && selectedCompany && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowViewModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Company Details</h3>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Company Name</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedCompany.name}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Status</label>
                    <span className={`mt-1 inline-flex px-2 py-1 text-xs rounded-full ${getStatusColor(selectedCompany.status)}`}>
                      {selectedCompany.status}
                    </span>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Billing Email</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedCompany.billing_email}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Subscription Plan</label>
                    <span className={`mt-1 inline-flex px-2 py-1 text-xs rounded-full ${getPlanColor(selectedCompany.subscription_plan)}`}>
                      {selectedCompany.subscription_plan}
                    </span>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Monthly Fee</label>
                    <p className="mt-1 text-sm font-semibold text-green-600">${selectedCompany.monthly_fee}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Total Units</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedCompany.total_units || 0}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Properties</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedCompany.property_count || 0}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Users</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedCompany.user_count || 0}</p>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Created Date</label>
                  <p className="mt-1 text-sm text-gray-900">{formatDate(selectedCompany.created_at)}</p>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
                <button
                  onClick={() => setShowViewModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Company Modal */}
      {showEditModal && selectedCompany && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowEditModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Edit Company</h3>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    value={selectedCompany.name}
                    onChange={(e) => setSelectedCompany({...selectedCompany, name: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Billing Email *
                  </label>
                  <input
                    type="email"
                    value={selectedCompany.billing_email}
                    onChange={(e) => setSelectedCompany({...selectedCompany, billing_email: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subscription Plan
                  </label>
                  <select
                    value={selectedCompany.subscription_plan}
                    onChange={(e) => setSelectedCompany({...selectedCompany, subscription_plan: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="basic">Basic - $2.00/unit/month</option>
                    <option value="premium">Premium - $2.50/unit/month</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Status
                  </label>
                  <select
                    value={selectedCompany.status}
                    onChange={(e) => setSelectedCompany({...selectedCompany, status: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="active">Active</option>
                    <option value="suspended">Suspended</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={updateCompany}
                  disabled={!selectedCompany.name || !selectedCompany.billing_email}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Company
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}