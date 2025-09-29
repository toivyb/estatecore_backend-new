import React, { useState, useEffect } from 'react';
import api from '../api';

export default function TenantSelfService() {
  const [tenantData, setTenantData] = useState(null);
  const [payments, setPayments] = useState([]);
  const [maintenanceRequests, setMaintenanceRequests] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  // Forms state
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [showMaintenanceForm, setShowMaintenanceForm] = useState(false);
  const [newMaintenanceRequest, setNewMaintenanceRequest] = useState({
    title: '',
    description: '',
    priority: 'medium',
    category: 'plumbing',
    urgent: false
  });

  useEffect(() => {
    fetchTenantData();
    fetchPayments();
    fetchMaintenanceRequests();
    fetchDocuments();
  }, []);

  const fetchTenantData = async () => {
    try {
      const response = await fetch(`${api.BASE}/api/tenant/profile`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTenantData(data);
      }
    } catch (error) {
      console.error('Error fetching tenant data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPayments = async () => {
    try {
      const response = await fetch(`${api.BASE}/api/tenant/payments`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPayments(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error fetching payments:', error);
      setPayments([]);
    }
  };

  const fetchMaintenanceRequests = async () => {
    try {
      const response = await fetch(`${api.BASE}/api/tenant/maintenance`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMaintenanceRequests(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error fetching maintenance requests:', error);
      setMaintenanceRequests([]);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${api.BASE}/api/tenant/documents`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDocuments(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
      setDocuments([]);
    }
  };

  const submitMaintenanceRequest = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${api.BASE}/api/tenant/maintenance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newMaintenanceRequest)
      });

      if (response.ok) {
        setMessage('Maintenance request submitted successfully');
        setMessageType('success');
        setNewMaintenanceRequest({
          title: '', description: '', priority: 'medium', category: 'plumbing', urgent: false
        });
        setShowMaintenanceForm(false);
        fetchMaintenanceRequests();
      } else {
        setMessage('Failed to submit maintenance request');
        setMessageType('error');
      }
    } catch (error) {
      setMessage('Network error occurred');
      setMessageType('error');
    }
  };

  const makePayment = async (paymentId) => {
    try {
      // Create payment intent
      const response = await fetch(`${api.BASE}/api/payments/create-intent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          payment_id: paymentId,
          amount: payments.find(p => p.id === paymentId)?.amount || 0
        })
      });

      if (response.ok) {
        const result = await response.json();
        // In a real app, you'd integrate with Stripe Elements here
        setMessage('Payment processing initiated');
        setMessageType('success');
        fetchPayments();
      } else {
        setMessage('Failed to process payment');
        setMessageType('error');
      }
    } catch (error) {
      setMessage('Payment processing error');
      setMessageType('error');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      overdue: 'bg-red-100 text-red-800',
      processing: 'bg-blue-100 text-blue-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      emergency: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
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
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">🏠 Tenant Portal</h1>
        {tenantData && (
          <p className="text-gray-600 mt-2">
            Welcome back, {tenantData.name}! Manage your rental account below.
          </p>
        )}
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-md ${
          messageType === 'success' 
            ? 'bg-green-50 text-green-700 border border-green-200' 
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'payments', label: 'Payments', icon: '💳' },
            { id: 'maintenance', label: 'Maintenance', icon: '🔧' },
            { id: 'documents', label: 'Documents', icon: '📄' },
            { id: 'profile', label: 'Profile', icon: '👤' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Next Payment Due</h3>
              <p className="text-2xl font-bold text-blue-600">
                {formatCurrency(payments.find(p => p.status === 'pending')?.amount || 0)}
              </p>
              <p className="text-sm text-gray-500">
                Due: {payments.find(p => p.status === 'pending')?.due_date || 'N/A'}
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Lease Status</h3>
              <p className="text-2xl font-bold text-green-600">Active</p>
              <p className="text-sm text-gray-500">
                Expires: {tenantData?.lease_end_date || 'N/A'}
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-orange-500">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Open Requests</h3>
              <p className="text-2xl font-bold text-orange-600">
                {maintenanceRequests.filter(r => r.status !== 'completed').length}
              </p>
              <p className="text-sm text-gray-500">Maintenance items</p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Property</h3>
              <p className="text-lg font-bold text-purple-600">
                {tenantData?.property_name || 'Property Name'}
              </p>
              <p className="text-sm text-gray-500">
                Unit {tenantData?.unit_number || 'N/A'}
              </p>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {payments.slice(0, 3).map((payment, index) => (
                  <div key={index} className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                        <span className="text-green-600 text-sm">💰</span>
                      </div>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        Rent payment {payment.status === 'completed' ? 'completed' : 'pending'}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatCurrency(payment.amount)} - Due {new Date(payment.due_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(payment.status)}`}>
                        {payment.status}
                      </span>
                    </div>
                  </div>
                ))}
                
                {maintenanceRequests.slice(0, 2).map((request, index) => (
                  <div key={index} className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 bg-orange-100 rounded-full flex items-center justify-center">
                        <span className="text-orange-600 text-sm">🔧</span>
                      </div>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{request.title}</p>
                      <p className="text-sm text-gray-500">
                        Status: {request.status} - Priority: {request.priority}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(request.priority)}`}>
                        {request.priority}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payments Tab */}
      {activeTab === 'payments' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900">Payment History</h2>
            <button
              onClick={() => setShowPaymentForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              💳 Make Payment
            </button>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Payment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Due Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {payments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{payment.id} - {payment.type || 'Rent'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatCurrency(payment.amount)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(payment.due_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(payment.status)}`}>
                        {payment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {payment.status === 'pending' && (
                        <button
                          onClick={() => makePayment(payment.id)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Pay Now
                        </button>
                      )}
                      {payment.status === 'completed' && (
                        <span className="text-green-600">✓ Paid</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Maintenance Tab */}
      {activeTab === 'maintenance' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900">Maintenance Requests</h2>
            <button
              onClick={() => setShowMaintenanceForm(true)}
              className="bg-orange-600 hover:bg-orange-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              🔧 New Request
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {maintenanceRequests.map((request) => (
              <div key={request.id} className="bg-white shadow-lg rounded-lg border">
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">{request.title}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(request.priority)}`}>
                      {request.priority}
                    </span>
                  </div>
                  
                  <p className="text-gray-600 mb-4">{request.description}</p>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Category:</span>
                      <span className="font-medium capitalize">{request.category?.replace('_', ' ')}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Status:</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                        {request.status?.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Submitted:</span>
                      <span className="font-medium">{new Date(request.created_at || Date.now()).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {maintenanceRequests.length === 0 && (
            <div className="text-center py-12">
              <div className="text-gray-500 mb-4">No maintenance requests found</div>
              <button
                onClick={() => setShowMaintenanceForm(true)}
                className="bg-orange-600 hover:bg-orange-700 text-white font-medium py-2 px-4 rounded-md"
              >
                Submit First Request
              </button>
            </div>
          )}
        </div>
      )}

      {/* Documents Tab */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Documents</h2>
          
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Available Documents</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {documents.length > 0 ? documents.map((doc, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <span className="text-2xl">📄</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{doc.name}</p>
                        <p className="text-sm text-gray-500">{doc.type} - {doc.size}</p>
                      </div>
                    </div>
                    <button className="text-blue-600 hover:text-blue-900 text-sm font-medium">
                      Download
                    </button>
                  </div>
                )) : (
                  <div className="text-center py-8 text-gray-500">
                    <span className="text-4xl mb-4 block">📄</span>
                    <p>No documents available</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Profile Tab */}
      {activeTab === 'profile' && tenantData && (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-900">Profile Information</h2>
          
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {tenantData.name || 'Not provided'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {tenantData.email || 'Not provided'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Property</label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {tenantData.property_name || 'Not assigned'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Unit Number</label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {tenantData.unit_number || 'Not assigned'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Lease Start</label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {tenantData.lease_start_date || 'Not provided'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Lease End</label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {tenantData.lease_end_date || 'Not provided'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Maintenance Request Form Modal */}
      {showMaintenanceForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Submit Maintenance Request</h3>
              
              <form onSubmit={submitMaintenanceRequest} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                  <input
                    type="text"
                    value={newMaintenanceRequest.title}
                    onChange={(e) => setNewMaintenanceRequest({...newMaintenanceRequest, title: e.target.value})}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Brief description of the issue"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                  <textarea
                    value={newMaintenanceRequest.description}
                    onChange={(e) => setNewMaintenanceRequest({...newMaintenanceRequest, description: e.target.value})}
                    required
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Detailed description of the problem"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                    <select
                      value={newMaintenanceRequest.priority}
                      onChange={(e) => setNewMaintenanceRequest({...newMaintenanceRequest, priority: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="emergency">Emergency</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                    <select
                      value={newMaintenanceRequest.category}
                      onChange={(e) => setNewMaintenanceRequest({...newMaintenanceRequest, category: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="plumbing">Plumbing</option>
                      <option value="electrical">Electrical</option>
                      <option value="hvac">HVAC</option>
                      <option value="appliances">Appliances</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={newMaintenanceRequest.urgent}
                    onChange={(e) => setNewMaintenanceRequest({...newMaintenanceRequest, urgent: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">
                    This is an urgent request requiring immediate attention
                  </label>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowMaintenanceForm(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 rounded-md transition-colors"
                  >
                    Submit Request
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