import React, { useState, useEffect } from 'react';
import StripePaymentForm from './StripePaymentForm';
import api from '../api';
import { formatCurrency } from '../config/stripe';

const RentPaymentDashboard = ({ tenantId, isAdmin = false }) => {
  const [rentInfo, setRentInfo] = useState(null);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedPaymentAmount, setSelectedPaymentAmount] = useState(0);

  useEffect(() => {
    fetchRentInfo();
    fetchPaymentHistory();
  }, [tenantId]);

  const fetchRentInfo = async () => {
    try {
      // Use dedicated Stripe server on port 5011 with tenant ID 1 (demo)
      const response = await fetch(`http://localhost:5011/api/tenants/1/rent-info`);
      const data = await response.json();
      if (data.success) {
        setRentInfo(data.data);
        setSelectedPaymentAmount(data.data.amount_due || data.data.monthly_rent || 0);
      }
    } catch (error) {
      console.error('Error fetching rent info:', error);
    }
  };

  const fetchPaymentHistory = async () => {
    try {
      // Use dedicated Stripe server on port 5011 with tenant ID 1 (demo)
      const response = await fetch(`http://localhost:5011/api/tenants/1/payment-history`);
      const data = await response.json();
      if (data.success) {
        setPaymentHistory(data.data.payments || []);
      }
    } catch (error) {
      console.error('Error fetching payment history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSuccess = (paymentIntent) => {
    console.log('Payment successful:', paymentIntent);
    setShowPaymentForm(false);
    
    // Refresh data
    fetchRentInfo();
    fetchPaymentHistory();
    
    // Show success message
    alert('Payment completed successfully!');
  };

  const handlePaymentError = (error) => {
    console.error('Payment failed:', error);
    alert('Payment failed. Please try again.');
  };

  const getPaymentStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPaymentStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'pending': return '⏳';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading payment information...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Rent Information Card */}
      {rentInfo && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Rent Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-blue-700">Monthly Rent</h4>
              <p className="text-2xl font-bold text-blue-900">
                ${rentInfo.monthly_rent?.toLocaleString() || '0'}
              </p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-orange-700">Amount Due</h4>
              <p className="text-2xl font-bold text-orange-900">
                ${rentInfo.amount_due?.toLocaleString() || '0'}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-green-700">Next Due Date</h4>
              <p className="text-lg font-bold text-green-900">
                {rentInfo.next_due_date ? new Date(rentInfo.next_due_date).toLocaleDateString() : 'Not set'}
              </p>
            </div>
          </div>
          
          {rentInfo.amount_due > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Quick Payment Options</h4>
                  <p className="text-sm text-gray-500">Select an amount to pay</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <button
                  onClick={() => setSelectedPaymentAmount(rentInfo.monthly_rent)}
                  className="p-3 border border-gray-300 rounded-lg hover:bg-gray-50 text-center"
                >
                  <div className="text-sm text-gray-600">Full Rent</div>
                  <div className="font-bold">${rentInfo.monthly_rent}</div>
                </button>
                <button
                  onClick={() => setSelectedPaymentAmount(rentInfo.amount_due)}
                  className="p-3 border border-gray-300 rounded-lg hover:bg-gray-50 text-center"
                >
                  <div className="text-sm text-gray-600">Amount Due</div>
                  <div className="font-bold">${rentInfo.amount_due}</div>
                </button>
                <button
                  onClick={() => setSelectedPaymentAmount(rentInfo.monthly_rent / 2)}
                  className="p-3 border border-gray-300 rounded-lg hover:bg-gray-50 text-center"
                >
                  <div className="text-sm text-gray-600">Half Rent</div>
                  <div className="font-bold">${(rentInfo.monthly_rent / 2).toFixed(0)}</div>
                </button>
                <div className="p-3 border border-gray-300 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Custom</div>
                  <input
                    type="number"
                    value={selectedPaymentAmount}
                    onChange={(e) => setSelectedPaymentAmount(parseFloat(e.target.value) || 0)}
                    className="w-full text-sm border-0 bg-transparent font-bold focus:outline-none"
                    placeholder="Amount"
                    min="1"
                    step="0.01"
                  />
                </div>
              </div>
              
              <button
                onClick={() => setShowPaymentForm(true)}
                disabled={selectedPaymentAmount <= 0}
                className={`w-full py-3 px-4 rounded-lg font-medium ${
                  selectedPaymentAmount > 0
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Pay ${selectedPaymentAmount.toLocaleString()} Now
              </button>
            </div>
          )}
        </div>
      )}

      {/* Payment History */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Payment History</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment ID
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paymentHistory.length > 0 ? (
                paymentHistory.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(payment.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      ${payment.amount?.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {payment.description || 'Rent Payment'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPaymentStatusColor(payment.status)}`}>
                        <span className="mr-1">{getPaymentStatusIcon(payment.status)}</span>
                        {payment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {payment.payment_intent_id?.substring(0, 20)}...
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-gray-500">
                    No payment history found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Payment Form Modal */}
      {showPaymentForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-screen overflow-y-auto">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Complete Payment</h3>
            </div>
            <div className="p-6">
              <StripePaymentForm
                amount={selectedPaymentAmount}
                description={`Rent Payment - ${new Date().toLocaleDateString()}`}
                tenantId={tenantId}
                propertyId={rentInfo?.property_id}
                onSuccess={handlePaymentSuccess}
                onError={handlePaymentError}
                onCancel={() => setShowPaymentForm(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RentPaymentDashboard;