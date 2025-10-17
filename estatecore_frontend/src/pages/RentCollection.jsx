import React, { useState, useEffect } from 'react';
import api from '../api';

export default function RentCollection() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [calculatingFees, setCalculatingFees] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const data = await api.get('/api/rent/dashboard');
      setDashboardData(data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      setMessage('Network error occurred');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const generateMonthlyRent = async () => {
    setGenerating(true);
    setMessage('');
    
    try {
      const currentMonth = new Date().toISOString().slice(0, 7); // YYYY-MM format
      
      const result = await api.post('/api/rent/generate', { month: currentMonth });
      
      if (result.success || result.generated_count !== undefined) {
        setMessage(`Successfully generated ${result.generated_count || 0} rent invoices for ${result.month}`);
        setMessageType('success');
        fetchDashboardData(); // Refresh data
      } else {
        setMessage(result.error || 'Failed to generate rent invoices');
        setMessageType('error');
      }
    } catch (error) {
      setMessage('Network error occurred');
      setMessageType('error');
    } finally {
      setGenerating(false);
    }
  };

  const calculateLateFees = async () => {
    setCalculatingFees(true);
    setMessage('');
    
    try {
      const result = await api.post('/api/rent/late-fees', {
        late_fee_amount: 50.0,
        grace_period_days: 5
      });
      
      if (result.success || result.updated_count !== undefined) {
        setMessage(`Applied late fees to ${result.updated_count || 0} overdue payments`);
        setMessageType('success');
        fetchDashboardData(); // Refresh data
      } else {
        setMessage(result.error || 'Failed to calculate late fees');
        setMessageType('error');
      }
    } catch (error) {
      setMessage('Network error occurred');
      setMessageType('error');
    } finally {
      setCalculatingFees(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'overdue':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
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
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">💰 Rent Collection Dashboard</h1>
        <div className="flex space-x-3">
          <button
            onClick={generateMonthlyRent}
            disabled={generating}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50"
          >
            {generating ? 'Generating...' : '📧 Generate Monthly Rent'}
          </button>
          <button
            onClick={calculateLateFees}
            disabled={calculatingFees}
            className="bg-orange-600 hover:bg-orange-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50"
          >
            {calculatingFees ? 'Calculating...' : '⚠️ Calculate Late Fees'}
          </button>
        </div>
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

      {dashboardData && (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Total Rent Due</h3>
              <p className="text-2xl font-bold text-blue-600">
                {formatCurrency(dashboardData.metrics?.total_rent_due || 0)}
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Total Collected</h3>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(dashboardData.metrics?.total_collected || 0)}
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Collection Rate</h3>
              <p className="text-2xl font-bold text-purple-600">
                {dashboardData.metrics?.collection_rate || 0}%
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-red-500">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Overdue Payments</h3>
              <p className="text-2xl font-bold text-red-600">
                {dashboardData.metrics?.overdue_count || 0}
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-orange-500">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Overdue Amount</h3>
              <p className="text-2xl font-bold text-orange-600">
                {formatCurrency(dashboardData.metrics?.overdue_amount || 0)}
              </p>
            </div>
          </div>

          {/* Overdue Payments */}
          {dashboardData.overdue_payments && dashboardData.overdue_payments.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden mb-8">
              <div className="px-6 py-4 border-b border-gray-200 bg-red-50">
                <h3 className="text-lg font-medium text-red-900">
                  🚨 Overdue Payments ({dashboardData.overdue_payments.length})
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tenant
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Due Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Days Overdue
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
                    {dashboardData.overdue_payments.map((payment) => (
                      <tr key={payment.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {payment.tenant_name || `Tenant #${payment.tenant_id}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {formatCurrency(payment.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(payment.due_date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-medium">
                          {payment.days_overdue} days
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(payment.status)}`}>
                            {payment.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <button className="text-blue-600 hover:text-blue-900 mr-3">
                            Send Reminder
                          </button>
                          <button className="text-green-600 hover:text-green-900">
                            Process Payment
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Current Month Payments */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                📅 Current Month Payments ({dashboardData.current_month_payments?.length || 0})
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Payment ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tenant
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
                  {dashboardData.current_month_payments && dashboardData.current_month_payments.length > 0 ? (
                    dashboardData.current_month_payments.map((payment) => (
                      <tr key={payment.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          #{payment.id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {payment.tenant_name || `Tenant #${payment.tenant_id}`}
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
                            <button className="text-green-600 hover:text-green-900">
                              Process Payment
                            </button>
                          )}
                          {payment.status === 'completed' && (
                            <span className="text-green-600">✓ Paid</span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                        No payments found for current month
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}