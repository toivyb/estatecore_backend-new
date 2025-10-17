import React, { useState, useEffect } from 'react';
import api from '../api';

const PropertyManagerDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [maintenanceRequests, setMaintenanceRequests] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
    fetchMaintenanceRequests();
    fetchTenants();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await api.get('/api/portal/property-manager/dashboard');
      if (response.success) {
        setDashboardData(response.data);
      } else {
        console.error('Error fetching property manager dashboard:', response.error);
        // Fallback to regular dashboard if role-specific fails
        const fallbackData = await api.get('/api/dashboard');
        setDashboardData(fallbackData.data);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Mock fallback data
      setDashboardData({
        stats: {
          total_properties: 0,
          total_units: 0,
          occupied_units: 0,
          total_tenants: 0,
          occupancy_rate: 0,
          monthly_revenue: 0
        },
        properties: [],
        recent_maintenance: [],
        tenant_issues: []
      });
    }
  };

  const fetchMaintenanceRequests = async () => {
    try {
      const data = await api.get('/api/maintenance/requests');
      setMaintenanceRequests(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching maintenance requests:', error);
      // Mock data for demonstration
      setMaintenanceRequests([
        {
          id: 1,
          title: 'Kitchen Faucet Leak',
          tenant: 'John Smith',
          unit: '2A',
          priority: 'medium',
          status: 'open',
          submitted_date: '2025-01-01',
          description: 'Kitchen faucet is dripping continuously'
        },
        {
          id: 2,
          title: 'HVAC Not Working',
          tenant: 'Jane Doe',
          unit: '5B',
          priority: 'high',
          status: 'in_progress',
          submitted_date: '2024-12-30',
          description: 'Air conditioning unit not cooling properly'
        },
        {
          id: 3,
          title: 'Broken Window',
          tenant: 'Mike Johnson',
          unit: '3C',
          priority: 'high',
          status: 'open',
          submitted_date: '2024-12-28',
          description: 'Living room window cracked'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTenants = async () => {
    try {
      const data = await api.get('/api/tenants');
      setTenants(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching tenants:', error);
    }
  };

  const handleMaintenanceAction = async (requestId, action) => {
    try {
      const response = await api.put(`/api/maintenance/requests/${requestId}`, {
        status: action
      });
      if (response.success) {
        fetchMaintenanceRequests();
      }
    } catch (error) {
      console.error('Error updating maintenance request:', error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-orange-100 text-orange-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount || 0);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading property manager dashboard...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">Property Manager Dashboard</h1>
            <p className="text-gray-600">Daily operations and tenant management</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Stats */}
        {dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
              <h3 className="text-sm font-medium text-gray-500">Active Tenants</h3>
              <p className="text-3xl font-bold text-blue-600">{dashboardData.total_tenants}</p>
              <p className="text-sm text-gray-600">Across all units</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
              <h3 className="text-sm font-medium text-gray-500">Open Maintenance</h3>
              <p className="text-3xl font-bold text-red-600">{maintenanceRequests.filter(r => r.status === 'open').length}</p>
              <p className="text-sm text-gray-600">Requests pending</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
              <h3 className="text-sm font-medium text-gray-500">Occupancy Rate</h3>
              <p className="text-3xl font-bold text-green-600">{dashboardData.occupancy_rate}%</p>
              <p className="text-sm text-gray-600">Current occupancy</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
              <h3 className="text-sm font-medium text-gray-500">Monthly Revenue</h3>
              <p className="text-3xl font-bold text-purple-600">{formatCurrency(dashboardData.total_revenue)}</p>
              <p className="text-sm text-gray-600">Current month</p>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: '📊' },
                { id: 'maintenance', label: 'Maintenance', icon: '🔧' },
                { id: 'tenants', label: 'Tenants', icon: '👥' },
                { id: 'leases', label: 'Leases', icon: '📄' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">New maintenance request</p>
                      <p className="text-xs text-gray-500">Unit 2A - Kitchen faucet leak - 2 hours ago</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Rent payment received</p>
                      <p className="text-xs text-gray-500">Unit 3B - $1,500 - 4 hours ago</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Maintenance completed</p>
                      <p className="text-xs text-gray-500">Unit 7A - HVAC repair - 1 day ago</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Lease expiring soon</p>
                      <p className="text-xs text-gray-500">Unit 5C - 30 days remaining - 2 days ago</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 gap-4">
                  <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
                    <div className="text-2xl mb-2">🔧</div>
                    <div className="text-sm font-medium">Create Work Order</div>
                  </button>
                  <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
                    <div className="text-2xl mb-2">👤</div>
                    <div className="text-sm font-medium">Add New Tenant</div>
                  </button>
                  <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
                    <div className="text-2xl mb-2">📄</div>
                    <div className="text-sm font-medium">Generate Report</div>
                  </button>
                  <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
                    <div className="text-2xl mb-2">📞</div>
                    <div className="text-sm font-medium">Contact Tenant</div>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'maintenance' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Maintenance Requests</h3>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                  + New Request
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Request
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tenant/Unit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Submitted
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {maintenanceRequests.map((request) => (
                    <tr key={request.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{request.title}</div>
                          <div className="text-sm text-gray-500">{request.description}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{request.tenant}</div>
                        <div className="text-sm text-gray-500">Unit {request.unit}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(request.priority)}`}>
                          {request.priority}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(request.status)}`}>
                          {request.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(request.submitted_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        {request.status === 'open' && (
                          <button
                            onClick={() => handleMaintenanceAction(request.id, 'in_progress')}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Start
                          </button>
                        )}
                        {request.status === 'in_progress' && (
                          <button
                            onClick={() => handleMaintenanceAction(request.id, 'completed')}
                            className="text-green-600 hover:text-green-900"
                          >
                            Complete
                          </button>
                        )}
                        <button className="text-gray-600 hover:text-gray-900">
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'tenants' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Tenant Management</h3>
                <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
                  + Add Tenant
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {tenants.slice(0, 6).map((tenant) => (
                  <div key={tenant.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-900">{tenant.name}</h4>
                        <p className="text-sm text-gray-600">{tenant.email}</p>
                        <p className="text-sm text-gray-600">{tenant.phone}</p>
                      </div>
                      <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        Active
                      </span>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Unit:</span>
                        <span className="font-medium">2A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Rent:</span>
                        <span className="font-medium">{formatCurrency(1500)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Lease:</span>
                        <span className="font-medium">Dec 2025</span>
                      </div>
                    </div>
                    
                    <div className="mt-4 flex space-x-2">
                      <button className="flex-1 bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700">
                        Contact
                      </button>
                      <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-3 rounded text-sm hover:bg-gray-200">
                        Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'leases' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Lease Management</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="text-center p-4 border border-gray-200 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">3</div>
                  <div className="text-sm text-gray-600">Expiring This Month</div>
                </div>
                <div className="text-center p-4 border border-gray-200 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">7</div>
                  <div className="text-sm text-gray-600">Expiring in 60 Days</div>
                </div>
                <div className="text-center p-4 border border-gray-200 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">12</div>
                  <div className="text-sm text-gray-600">Renewed This Quarter</div>
                </div>
              </div>
              
              <div className="text-center py-8 text-gray-500">
                <div className="text-2xl mb-2">📄</div>
                <p>Lease management tools coming soon...</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PropertyManagerDashboard;