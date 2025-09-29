import React, { useState, useEffect } from 'react';
import { ROLES, LPR_PERMISSIONS } from '../utils/roles';
import api from '../api';

export default function LPRCompanies() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  const [newCompany, setNewCompany] = useState({
    name: '',
    description: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    max_alerts_per_day: 100,
    max_cameras: 100,
    subscription_type: 'basic'
  });

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await fetch(`${api.BASE}/api/lpr/companies`);
      if (response.ok) {
        const data = await response.json();
        setCompanies(Array.isArray(data) ? data : []);
      } else {
        setMessage('Failed to fetch companies');
        setMessageType('error');
        setCompanies([]);
      }
    } catch (error) {
      setMessage('Network error occurred');
      setMessageType('error');
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${api.BASE}/api/lpr/companies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newCompany),
      });

      const result = await response.json();

      if (response.ok) {
        setMessage('Company created successfully');
        setMessageType('success');
        setShowCreateForm(false);
        setNewCompany({
          name: '',
          description: '',
          contact_email: '',
          contact_phone: '',
          address: '',
          max_alerts_per_day: 100,
          max_cameras: 100,
          subscription_type: 'basic'
        });
        fetchCompanies(); // Refresh list
      } else {
        setMessage(result.error || 'Failed to create company');
        setMessageType('error');
      }
    } catch (error) {
      setMessage('Network error occurred');
      setMessageType('error');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewCompany(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const viewCompanyDetails = async (companyId) => {
    try {
      const response = await fetch(`${api.BASE}/api/lpr/companies/${companyId}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedCompany(data);
      }
    } catch (error) {
      setMessage('Failed to fetch company details');
      setMessageType('error');
    }
  };

  const getSubscriptionBadge = (type) => {
    const colors = {
      basic: 'bg-gray-100 text-gray-800',
      premium: 'bg-blue-100 text-blue-800',
      enterprise: 'bg-purple-100 text-purple-800'
    };
    return colors[type] || colors.basic;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">LPR Companies</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
        >
          Add New Company
        </button>
      </div>

      {message && (
        <div className={`mb-4 p-4 rounded-md ${
          messageType === 'success' 
            ? 'bg-green-50 text-green-700 border border-green-200' 
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message}
        </div>
      )}

      {/* Companies Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {companies.map(company => (
          <div key={company.id} className="bg-white shadow-lg rounded-lg p-6 border hover:shadow-xl transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold text-gray-900 truncate">{company.name}</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSubscriptionBadge(company.subscription_type)}`}>
                {company.subscription_type}
              </span>
            </div>
            
            <p className="text-gray-600 mb-4 line-clamp-2">{company.description || 'No description provided'}</p>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Users:</span>
                <span className="text-sm font-medium">{company.user_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Max Cameras:</span>
                <span className="text-sm font-medium">{company.max_cameras}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Daily Alerts:</span>
                <span className="text-sm font-medium">{company.max_alerts_per_day}</span>
              </div>
            </div>
            
            {company.contact_email && (
              <div className="mb-4">
                <p className="text-sm text-gray-500">Contact:</p>
                <p className="text-sm font-medium">{company.contact_email}</p>
                {company.contact_phone && (
                  <p className="text-sm text-gray-600">{company.contact_phone}</p>
                )}
              </div>
            )}
            
            <div className="flex space-x-2">
              <button
                onClick={() => viewCompanyDetails(company.id)}
                className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-3 rounded text-sm transition-colors"
              >
                View Details
              </button>
              <button className="bg-blue-50 hover:bg-blue-100 text-blue-600 py-2 px-3 rounded text-sm transition-colors">
                Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      {companies.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-4">No LPR companies found</div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md"
          >
            Create First Company
          </button>
        </div>
      )}

      {/* Create Company Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-screen overflow-y-auto">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New LPR Company</h3>
              
              <form onSubmit={handleCreateCompany} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={newCompany.name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    name="description"
                    value={newCompany.description}
                    onChange={handleInputChange}
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contact Email
                  </label>
                  <input
                    type="email"
                    name="contact_email"
                    value={newCompany.contact_email}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contact Phone
                  </label>
                  <input
                    type="tel"
                    name="contact_phone"
                    value={newCompany.contact_phone}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subscription Type
                  </label>
                  <select
                    name="subscription_type"
                    value={newCompany.subscription_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="basic">Basic</option>
                    <option value="premium">Premium</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Cameras
                    </label>
                    <input
                      type="number"
                      name="max_cameras"
                      value={newCompany.max_cameras}
                      onChange={handleInputChange}
                      min="1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Daily Alerts
                    </label>
                    <input
                      type="number"
                      name="max_alerts_per_day"
                      value={newCompany.max_alerts_per_day}
                      onChange={handleInputChange}
                      min="1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
                  >
                    Create Company
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Company Details Modal */}
      {selectedCompany && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <h3 className="text-xl font-semibold text-gray-900">{selectedCompany.name}</h3>
                <button
                  onClick={() => setSelectedCompany(null)}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Company Information</h4>
                  <div className="bg-gray-50 p-4 rounded-md space-y-2">
                    <p><strong>Description:</strong> {selectedCompany.description || 'N/A'}</p>
                    <p><strong>Contact Email:</strong> {selectedCompany.contact_email || 'N/A'}</p>
                    <p><strong>Contact Phone:</strong> {selectedCompany.contact_phone || 'N/A'}</p>
                    <p><strong>Address:</strong> {selectedCompany.address || 'N/A'}</p>
                    <p><strong>Subscription:</strong> {selectedCompany.subscription_type}</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Usage Limits</h4>
                  <div className="bg-gray-50 p-4 rounded-md space-y-2">
                    <p><strong>Max Cameras:</strong> {selectedCompany.max_cameras}</p>
                    <p><strong>Max Daily Alerts:</strong> {selectedCompany.max_alerts_per_day}</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Users ({selectedCompany.user_count})</h4>
                  <div className="bg-gray-50 p-4 rounded-md">
                    {selectedCompany.users && selectedCompany.users.length > 0 ? (
                      <div className="space-y-2">
                        {selectedCompany.users.map(user => (
                          <div key={user.id} className="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0">
                            <div>
                              <p className="font-medium">{user.username}</p>
                              <p className="text-sm text-gray-600">{user.email}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-medium">{user.role}</p>
                              <p className="text-xs text-gray-500">{user.lpr_permissions}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500">No users assigned to this company</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}