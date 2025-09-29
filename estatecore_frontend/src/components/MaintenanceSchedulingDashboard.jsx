import React, { useState, useEffect } from 'react';

const MaintenanceSchedulingDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [maintenanceRequests, setMaintenanceRequests] = useState([]);
  const [maintenanceItems, setMaintenanceItems] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [scheduledMaintenance, setScheduledMaintenance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateRequestForm, setShowCreateRequestForm] = useState(false);
  const [showCreateItemForm, setShowCreateItemForm] = useState(false);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  
  const [newRequest, setNewRequest] = useState({
    property_id: '',
    title: '',
    description: '',
    maintenance_type: 'corrective',
    priority: 'medium',
    estimated_hours: '',
    estimated_cost: '',
    tenant_access_required: false
  });

  const [newItem, setNewItem] = useState({
    property_id: '',
    name: '',
    category: '',
    model: '',
    serial_number: '',
    installation_date: '',
    warranty_expires: '',
    service_interval_days: 90
  });

  const [scheduleForm, setScheduleForm] = useState({
    request_id: '',
    scheduled_date: '',
    vendor_id: ''
  });

  useEffect(() => {
    fetchDashboardData();
    fetchMaintenanceRequests();
    fetchMaintenanceItems();
    fetchVendors();
    fetchScheduledMaintenance();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/maintenance-scheduling/dashboard');
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchMaintenanceRequests = async () => {
    try {
      const response = await fetch('/api/maintenance-scheduling/requests');
      if (response.ok) {
        const data = await response.json();
        setMaintenanceRequests(data.requests || []);
      }
    } catch (error) {
      console.error('Error fetching maintenance requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMaintenanceItems = async () => {
    try {
      const response = await fetch('/api/maintenance-scheduling/items');
      if (response.ok) {
        const data = await response.json();
        setMaintenanceItems(data.items || []);
      }
    } catch (error) {
      console.error('Error fetching maintenance items:', error);
    }
  };

  const fetchVendors = async () => {
    try {
      const response = await fetch('/api/maintenance-scheduling/vendors');
      if (response.ok) {
        const data = await response.json();
        setVendors(data.vendors || []);
      }
    } catch (error) {
      console.error('Error fetching vendors:', error);
    }
  };

  const fetchScheduledMaintenance = async () => {
    try {
      const response = await fetch('/api/maintenance-scheduling/scheduled');
      if (response.ok) {
        const data = await response.json();
        setScheduledMaintenance(data.scheduled_requests || []);
      }
    } catch (error) {
      console.error('Error fetching scheduled maintenance:', error);
    }
  };

  const handleCreateRequest = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/maintenance-scheduling/requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newRequest)
      });

      if (response.ok) {
        setNewRequest({
          property_id: '',
          title: '',
          description: '',
          maintenance_type: 'corrective',
          priority: 'medium',
          estimated_hours: '',
          estimated_cost: '',
          tenant_access_required: false
        });
        setShowCreateRequestForm(false);
        fetchMaintenanceRequests();
        fetchDashboardData();
        alert('Maintenance request created successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to create request: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error creating maintenance request:', error);
      alert('Failed to create maintenance request');
    }
  };

  const handleCreateItem = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/maintenance-scheduling/items', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newItem)
      });

      if (response.ok) {
        setNewItem({
          property_id: '',
          name: '',
          category: '',
          model: '',
          serial_number: '',
          installation_date: '',
          warranty_expires: '',
          service_interval_days: 90
        });
        setShowCreateItemForm(false);
        fetchMaintenanceItems();
        alert('Maintenance item created successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to create item: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error creating maintenance item:', error);
      alert('Failed to create maintenance item');
    }
  };

  const handleScheduleRequest = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/maintenance-scheduling/schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scheduleForm)
      });

      if (response.ok) {
        setScheduleForm({
          request_id: '',
          scheduled_date: '',
          vendor_id: ''
        });
        setShowScheduleForm(false);
        setSelectedRequest(null);
        fetchMaintenanceRequests();
        fetchScheduledMaintenance();
        fetchDashboardData();
        alert('Maintenance request scheduled successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to schedule request: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error scheduling maintenance request:', error);
      alert('Failed to schedule maintenance request');
    }
  };

  const handleUpdateStatus = async (requestId, newStatus) => {
    try {
      const response = await fetch(`/api/maintenance-scheduling/requests/${requestId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        fetchMaintenanceRequests();
        fetchDashboardData();
        alert('Status updated successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to update status: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Failed to update status');
    }
  };

  const generatePreventiveMaintenance = async () => {
    try {
      const response = await fetch('/api/maintenance-scheduling/preventive/generate', {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Generated ${data.generated_count} preventive maintenance requests`);
        fetchMaintenanceRequests();
        fetchDashboardData();
      } else {
        const errorData = await response.json();
        alert(`Failed to generate preventive maintenance: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error generating preventive maintenance:', error);
      alert('Failed to generate preventive maintenance');
    }
  };

  const openScheduleForm = (request) => {
    setSelectedRequest(request);
    setScheduleForm({
      ...scheduleForm,
      request_id: request.id
    });
    setShowScheduleForm(true);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'emergency': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'scheduled': return 'bg-purple-100 text-purple-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
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
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Maintenance Scheduling</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreateRequestForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            🔧 New Request
          </button>
          <button
            onClick={() => setShowCreateItemForm(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
          >
            ⚙️ Add Equipment
          </button>
          <button
            onClick={generatePreventiveMaintenance}
            className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700"
          >
            🔄 Generate Preventive
          </button>
        </div>
      </div>

      {/* Dashboard Overview */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Requests</h3>
            <p className="text-2xl font-bold text-gray-900">{dashboardData.overview?.total_requests || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Pending</h3>
            <p className="text-2xl font-bold text-yellow-600">{dashboardData.overview?.pending_requests || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Scheduled</h3>
            <p className="text-2xl font-bold text-blue-600">{dashboardData.overview?.scheduled_requests || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Emergency</h3>
            <p className="text-2xl font-bold text-red-600">{dashboardData.overview?.emergency_requests || 0}</p>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['overview', 'requests', 'scheduled', 'equipment', 'vendors'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && dashboardData && (
        <div className="space-y-6">
          {/* Emergency Requests */}
          {dashboardData.emergency_requests && dashboardData.emergency_requests.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-red-800 mb-4">🚨 Emergency Requests</h3>
              <div className="space-y-3">
                {dashboardData.emergency_requests.map((request) => (
                  <div key={request.id} className="bg-white p-4 rounded border border-red-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-gray-900">{request.title}</h4>
                        <p className="text-sm text-gray-600">{request.description}</p>
                        <p className="text-xs text-gray-500">Property ID: {request.property_id}</p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => openScheduleForm(request)}
                          className="bg-blue-600 text-white px-3 py-1 text-sm rounded hover:bg-blue-700"
                        >
                          Schedule
                        </button>
                        <button
                          onClick={() => handleUpdateStatus(request.id, 'in_progress')}
                          className="bg-green-600 text-white px-3 py-1 text-sm rounded hover:bg-green-700"
                        >
                          Start Work
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Overdue Maintenance */}
          {dashboardData.overdue_maintenance && dashboardData.overdue_maintenance.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-orange-800 mb-4">⏰ Overdue Maintenance</h3>
              <div className="space-y-3">
                {dashboardData.overdue_maintenance.map((item) => (
                  <div key={item.item.id} className="bg-white p-4 rounded border border-orange-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-gray-900">{item.item.name}</h4>
                        <p className="text-sm text-gray-600">{item.item.category}</p>
                        <p className="text-xs text-red-600">Overdue by {item.overdue_days} days</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
            </div>
            <div className="p-6">
              {dashboardData.recent_activity && dashboardData.recent_activity.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData.recent_activity.slice(0, 5).map((request) => (
                    <div key={request.id} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                      <div>
                        <h4 className="font-medium text-gray-900">{request.title}</h4>
                        <p className="text-sm text-gray-600">{new Date(request.created_at).toLocaleDateString()}</p>
                      </div>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(request.status)}`}>
                        {request.status.replace('_', ' ')}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No recent activity</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Maintenance Requests Tab */}
      {activeTab === 'requests' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Maintenance Requests</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Request</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Property</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {maintenanceRequests.map((request) => (
                  <tr key={request.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{request.title}</div>
                        <div className="text-sm text-gray-500">{request.description}</div>
                      </div>
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {request.property_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(request.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex gap-2">
                        {request.status === 'pending' && (
                          <button
                            onClick={() => openScheduleForm(request)}
                            className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                          >
                            Schedule
                          </button>
                        )}
                        {request.status === 'scheduled' && (
                          <button
                            onClick={() => handleUpdateStatus(request.id, 'in_progress')}
                            className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                          >
                            Start
                          </button>
                        )}
                        {request.status === 'in_progress' && (
                          <button
                            onClick={() => handleUpdateStatus(request.id, 'completed')}
                            className="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700"
                          >
                            Complete
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Scheduled Maintenance Tab */}
      {activeTab === 'scheduled' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Scheduled Maintenance</h3>
          </div>
          <div className="p-6">
            {scheduledMaintenance.length > 0 ? (
              <div className="space-y-4">
                {scheduledMaintenance.map((request) => (
                  <div key={request.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-gray-900">{request.title}</h4>
                        <p className="text-sm text-gray-600">{request.description}</p>
                        <p className="text-sm text-blue-600">
                          Scheduled: {request.scheduled_date ? new Date(request.scheduled_date).toLocaleString() : 'TBD'}
                        </p>
                        {request.assigned_vendor_id && (
                          <p className="text-sm text-gray-500">Vendor: {request.assigned_vendor_id}</p>
                        )}
                      </div>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(request.priority)}`}>
                        {request.priority}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No scheduled maintenance</p>
            )}
          </div>
        </div>
      )}

      {/* Equipment Tab */}
      {activeTab === 'equipment' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Equipment & Assets</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Equipment</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Property</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Service</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Next Service</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {maintenanceItems.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{item.name}</div>
                        <div className="text-sm text-gray-500">{item.model || 'No model'}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.property_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.last_service_date ? new Date(item.last_service_date).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.next_service_due ? new Date(item.next_service_due).toLocaleDateString() : 'Not scheduled'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        item.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {item.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Vendors Tab */}
      {activeTab === 'vendors' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Maintenance Vendors</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vendor</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Specialties</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rating</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hourly Rate</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {vendors.map((vendor) => (
                  <tr key={vendor.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{vendor.name}</div>
                        <div className="text-sm text-gray-500">{vendor.contact_person}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm text-gray-900">{vendor.email}</div>
                        <div className="text-sm text-gray-500">{vendor.phone}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {vendor.specialties.map((specialty, index) => (
                          <span key={index} className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                            {specialty}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ⭐ {vendor.rating}/5
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${vendor.hourly_rate}/hr
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        vendor.status === 'available' ? 'bg-green-100 text-green-800' :
                        vendor.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {vendor.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Request Modal */}
      {showCreateRequestForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Create Maintenance Request</h3>
            </div>
            <form onSubmit={handleCreateRequest} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Property ID</label>
                <input
                  type="number"
                  value={newRequest.property_id}
                  onChange={(e) => setNewRequest({...newRequest, property_id: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={newRequest.title}
                  onChange={(e) => setNewRequest({...newRequest, title: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={newRequest.description}
                  onChange={(e) => setNewRequest({...newRequest, description: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  rows="3"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={newRequest.maintenance_type}
                  onChange={(e) => setNewRequest({...newRequest, maintenance_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="preventive">Preventive</option>
                  <option value="corrective">Corrective</option>
                  <option value="emergency">Emergency</option>
                  <option value="inspection">Inspection</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={newRequest.priority}
                  onChange={(e) => setNewRequest({...newRequest, priority: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                  <option value="emergency">Emergency</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Create Request
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateRequestForm(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Item Modal */}
      {showCreateItemForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Add Equipment/Asset</h3>
            </div>
            <form onSubmit={handleCreateItem} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Property ID</label>
                <input
                  type="number"
                  value={newItem.property_id}
                  onChange={(e) => setNewItem({...newItem, property_id: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Equipment Name</label>
                <input
                  type="text"
                  value={newItem.name}
                  onChange={(e) => setNewItem({...newItem, name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={newItem.category}
                  onChange={(e) => setNewItem({...newItem, category: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                >
                  <option value="">Select Category</option>
                  <option value="HVAC">HVAC</option>
                  <option value="Plumbing">Plumbing</option>
                  <option value="Electrical">Electrical</option>
                  <option value="Appliances">Appliances</option>
                  <option value="Security">Security</option>
                  <option value="Landscaping">Landscaping</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                <input
                  type="text"
                  value={newItem.model}
                  onChange={(e) => setNewItem({...newItem, model: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Service Interval (days)</label>
                <input
                  type="number"
                  value={newItem.service_interval_days}
                  onChange={(e) => setNewItem({...newItem, service_interval_days: parseInt(e.target.value)})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
                >
                  Add Equipment
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateItemForm(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Schedule Request Modal */}
      {showScheduleForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Schedule: {selectedRequest?.title}
              </h3>
            </div>
            <form onSubmit={handleScheduleRequest} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Scheduled Date & Time</label>
                <input
                  type="datetime-local"
                  value={scheduleForm.scheduled_date}
                  onChange={(e) => setScheduleForm({...scheduleForm, scheduled_date: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assign Vendor (Optional)</label>
                <select
                  value={scheduleForm.vendor_id}
                  onChange={(e) => setScheduleForm({...scheduleForm, vendor_id: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="">Auto-assign best vendor</option>
                  {vendors.map((vendor) => (
                    <option key={vendor.id} value={vendor.id}>
                      {vendor.name} - ${vendor.hourly_rate}/hr
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Schedule Request
                </button>
                <button
                  type="button"
                  onClick={() => setShowScheduleForm(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaintenanceSchedulingDashboard;