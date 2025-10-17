import React, { useState, useEffect } from 'react';
import api from '../api';

const TenantDashboard = () => {
  const [tenantData, setTenantData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [payments, setPayments] = useState([]);
  const [maintenanceRequests, setMaintenanceRequests] = useState([]);

  useEffect(() => {
    fetchTenantData();
    fetchPayments();
    fetchMaintenanceRequests();
  }, []);

  const fetchTenantData = async () => {
    try {
      const response = await api.get('/api/portal/tenant/dashboard');
      if (response.success) {
        setTenantData(response.data);
      } else {
        console.error('Error fetching tenant data:', response.error);
        // Fallback to mock data if API fails
        setTenantData({
          tenant: {
            name: 'John Smith',
            email: 'john.smith@email.com',
            phone: '(555) 123-4567',
            unit: '2A',
            property: 'Sunset Apartments',
            lease_start: '2024-01-01',
            lease_end: '2025-01-01',
            rent_amount: 1500,
            security_deposit: 1500
          },
          current_balance: 0,
          next_payment_due: '2025-02-01',
          next_payment_amount: 1500
        });
      }
    } catch (error) {
      console.error('Error fetching tenant data:', error);
      // Fallback to mock data
      setTenantData({
        tenant: {
          name: 'Mock Tenant',
          email: 'mock@tenant.com',
          phone: '(555) 000-0000',
          unit: 'N/A',
          property: 'Demo Property',
          lease_start: '2024-01-01',
          lease_end: '2025-01-01',
          rent_amount: 1500,
          security_deposit: 1500
        },
        current_balance: 0,
        next_payment_due: '2025-02-01',
        next_payment_amount: 1500
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchPayments = async () => {
    try {
      // Mock payment data
      setPayments([
        {
          id: 1,
          date: '2025-01-01',
          amount: 1500,
          description: 'Monthly Rent - January 2025',
          status: 'paid',
          method: 'Online Payment'
        },
        {
          id: 2,
          date: '2024-12-01',
          amount: 1500,
          description: 'Monthly Rent - December 2024',
          status: 'paid',
          method: 'Bank Transfer'
        },
        {
          id: 3,
          date: '2024-11-01',
          amount: 1500,
          description: 'Monthly Rent - November 2024',
          status: 'paid',
          method: 'Online Payment'
        }
      ]);
    } catch (error) {
      console.error('Error fetching payments:', error);
    }
  };

  const fetchMaintenanceRequests = async () => {
    try {
      // Mock maintenance data
      setMaintenanceRequests([
        {
          id: 1,
          title: 'Kitchen Faucet Leak',
          description: 'The kitchen faucet is dripping constantly',
          status: 'completed',
          priority: 'medium',
          submitted_date: '2024-12-15',
          completed_date: '2024-12-18'
        },
        {
          id: 2,
          title: 'Air Conditioning Not Working',
          description: 'AC unit not cooling properly',
          status: 'in_progress',
          priority: 'high',
          submitted_date: '2024-12-20'
        }
      ]);
    } catch (error) {
      console.error('Error fetching maintenance requests:', error);
    }
  };

  const submitMaintenanceRequest = async (requestData) => {
    try {
      const response = await api.post('/api/maintenance/requests', requestData);
      if (response.success) {
        fetchMaintenanceRequests();
        return { success: true };
      }
    } catch (error) {
      console.error('Error submitting maintenance request:', error);
      return { success: false, error: 'Failed to submit request' };
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'paid': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'overdue': return 'bg-red-100 text-red-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'open': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading tenant dashboard...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">Tenant Dashboard</h1>
            {tenantData && (
              <p className="text-gray-600">Welcome back, {tenantData.tenant.name}</p>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {tenantData && (
          <>
            {/* Quick Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500">Current Balance</h3>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(tenantData.current_balance)}</p>
                <p className="text-sm text-gray-600">All payments up to date</p>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500">Next Payment</h3>
                <p className="text-2xl font-bold text-blue-600">{formatCurrency(tenantData.next_payment_amount)}</p>
                <p className="text-sm text-gray-600">Due {formatDate(tenantData.next_payment_due)}</p>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500">Your Unit</h3>
                <p className="text-2xl font-bold text-gray-900">{tenantData.tenant.unit}</p>
                <p className="text-sm text-gray-600">{tenantData.tenant.property}</p>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500">Lease Expires</h3>
                <p className="text-2xl font-bold text-orange-600">{formatDate(tenantData.tenant.lease_end)}</p>
                <p className="text-sm text-gray-600">Contact us to renew</p>
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Payment History */}
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Payments</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {payments.map((payment) => (
                      <div key={payment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">{payment.description}</p>
                          <p className="text-sm text-gray-600">{formatDate(payment.date)} • {payment.method}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-gray-900">{formatCurrency(payment.amount)}</p>
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(payment.status)}`}>
                            {payment.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-6">
                    <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                      💳 Make Payment
                    </button>
                  </div>
                </div>
              </div>

              {/* Maintenance Requests */}
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Maintenance Requests</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {maintenanceRequests.map((request) => (
                      <div key={request.id} className="p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-medium text-gray-900">{request.title}</h4>
                            <p className="text-sm text-gray-600 mt-1">{request.description}</p>
                            <p className="text-xs text-gray-500 mt-2">
                              Submitted: {formatDate(request.submitted_date)}
                              {request.completed_date && ` • Completed: ${formatDate(request.completed_date)}`}
                            </p>
                          </div>
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(request.status)}`}>
                            {request.status.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-6">
                    <button className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors">
                      🔧 Submit New Request
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="mt-8 bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Emergency Contacts</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-4 border border-gray-200 rounded-lg">
                  <div className="text-2xl mb-2">🚨</div>
                  <h4 className="font-medium text-gray-900">Emergency Maintenance</h4>
                  <p className="text-gray-600">(555) 911-HELP</p>
                  <p className="text-sm text-gray-500">24/7 Emergency Line</p>
                </div>
                
                <div className="text-center p-4 border border-gray-200 rounded-lg">
                  <div className="text-2xl mb-2">🏢</div>
                  <h4 className="font-medium text-gray-900">Property Manager</h4>
                  <p className="text-gray-600">(555) 123-4567</p>
                  <p className="text-sm text-gray-500">Mon-Fri 9AM-6PM</p>
                </div>
                
                <div className="text-center p-4 border border-gray-200 rounded-lg">
                  <div className="text-2xl mb-2">💼</div>
                  <h4 className="font-medium text-gray-900">Leasing Office</h4>
                  <p className="text-gray-600">(555) 987-6543</p>
                  <p className="text-sm text-gray-500">Mon-Sat 10AM-7PM</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default TenantDashboard;