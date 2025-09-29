import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TenantPaymentForm, { QuickPayButton } from './TenantPayRent';
import { PaymentHistoryWidget } from './PaymentHistory';
import PaymentConfirmation, { PaymentSuccessMessage } from './PaymentConfirmation';

export default function TenantPaymentDashboard({ tenantId, propertyId, tenantName, tenantEmail }) {
  const [balance, setBalance] = useState(null);
  const [paymentTypes, setPaymentTypes] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [completedPayment, setCompletedPayment] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, [tenantId]);

  const fetchDashboardData = async () => {
    try {
      const [balanceResponse, typesResponse] = await Promise.all([
        axios.get(`/api/payments/tenant/${tenantId}/balance`),
        axios.get('/api/payments/types')
      ]);
      
      setBalance(balanceResponse.data);
      setPaymentTypes(typesResponse.data.payment_types);
    } catch (err) {
      setError('Failed to load payment dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickPayment = (paymentType, amount, description = '') => {
    setSelectedPayment({
      tenantId,
      propertyId,
      amount,
      paymentType,
      description,
      tenantName,
      tenantEmail
    });
    setShowPaymentForm(true);
  };

  const handlePaymentSuccess = (result) => {
    setShowPaymentForm(false);
    setSelectedPayment(null);
    setCompletedPayment(result);
    setShowConfirmation(true);
    
    // Refresh balance after successful payment
    fetchDashboardData();
    
    // Show success message
    setSuccessMessage({
      amount: result.amount,
      receipt_number: result.receipt_number
    });
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  const handlePaymentError = (error) => {
    setShowPaymentForm(false);
    setSelectedPayment(null);
    alert(`Payment failed: ${error}`);
  };

  const handleCancel = () => {
    setShowPaymentForm(false);
    setSelectedPayment(null);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading payment dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-sm text-red-800">{error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Success Message */}
      {successMessage && (
        <PaymentSuccessMessage
          payment={successMessage}
          onClose={() => setSuccessMessage(null)}
        />
      )}

      {/* Account Balance Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Account Balance</h2>
          <button
            onClick={fetchDashboardData}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Refresh
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              ${Math.abs(balance?.current_balance || 0).toFixed(2)}
            </div>
            <div className={`text-sm ${balance?.current_balance > 0 ? 'text-red-600' : balance?.current_balance < 0 ? 'text-green-600' : 'text-gray-600'}`}>
              {balance?.current_balance > 0 ? 'Amount Due' : balance?.current_balance < 0 ? 'Credit Balance' : 'Balance Current'}
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              ${balance?.total_paid?.toFixed(2) || '0.00'}
            </div>
            <div className="text-sm text-gray-600">Total Paid</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              ${balance?.security_deposit?.toFixed(2) || '0.00'}
            </div>
            <div className="text-sm text-gray-600">Security Deposit</div>
          </div>
        </div>

        {balance?.last_payment_date && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600">
              Last Payment: ${balance.last_payment_amount?.toFixed(2)} on{' '}
              {new Date(balance.last_payment_date).toLocaleDateString()}
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Payments</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Rent Payment */}
          <div className="border rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Monthly Rent</h4>
            <p className="text-sm text-gray-600 mb-3">Pay your monthly rent</p>
            <div className="flex items-center justify-between">
              <span className="text-lg font-semibold">$1,200.00</span>
              <QuickPayButton
                tenantId={tenantId}
                propertyId={propertyId}
                amount={1200.00}
                paymentType="rent"
                description="Monthly rent payment"
                onSuccess={handlePaymentSuccess}
                onError={handlePaymentError}
                className="text-sm px-3 py-1"
              />
            </div>
          </div>

          {/* Late Fee */}
          {balance?.current_balance > 0 && (
            <div className="border rounded-lg p-4 border-red-200 bg-red-50">
              <h4 className="font-medium text-red-900 mb-2">Late Fee</h4>
              <p className="text-sm text-red-600 mb-3">Outstanding late fee</p>
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold text-red-900">$50.00</span>
                <QuickPayButton
                  tenantId={tenantId}
                  propertyId={propertyId}
                  amount={50.00}
                  paymentType="late_fee"
                  description="Late payment fee"
                  onSuccess={handlePaymentSuccess}
                  onError={handlePaymentError}
                  className="text-sm px-3 py-1 bg-red-600 hover:bg-red-700"
                />
              </div>
            </div>
          )}

          {/* Utilities */}
          <div className="border rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Utilities</h4>
            <p className="text-sm text-gray-600 mb-3">Water, electricity, gas</p>
            <div className="flex items-center justify-between">
              <span className="text-lg font-semibold">$150.00</span>
              <QuickPayButton
                tenantId={tenantId}
                propertyId={propertyId}
                amount={150.00}
                paymentType="utilities"
                description="Utility bill payment"
                onSuccess={handlePaymentSuccess}
                onError={handlePaymentError}
                className="text-sm px-3 py-1"
              />
            </div>
          </div>

          {/* Custom Amount */}
          <div className="border rounded-lg p-4 border-blue-200 bg-blue-50">
            <h4 className="font-medium text-blue-900 mb-2">Other Payment</h4>
            <p className="text-sm text-blue-600 mb-3">Custom amount payment</p>
            <button
              onClick={() => handleQuickPayment('other', 0, 'Custom payment')}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              Enter Amount
            </button>
          </div>
        </div>
      </div>

      {/* Payment History Widget */}
      <PaymentHistoryWidget tenantId={tenantId} limit={5} />

      {/* Payment Form Modal */}
      {showPaymentForm && selectedPayment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="p-4 border-b">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">Make Payment</h2>
                <button
                  onClick={handleCancel}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            {selectedPayment.paymentType === 'other' ? (
              <CustomPaymentForm
                tenantId={tenantId}
                propertyId={propertyId}
                tenantName={tenantName}
                tenantEmail={tenantEmail}
                onSuccess={handlePaymentSuccess}
                onError={handlePaymentError}
                onCancel={handleCancel}
              />
            ) : (
              <div className="p-4">
                <TenantPaymentForm
                  {...selectedPayment}
                  onSuccess={handlePaymentSuccess}
                  onError={handlePaymentError}
                  onCancel={handleCancel}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Payment Confirmation Modal */}
      {showConfirmation && completedPayment && (
        <PaymentConfirmation
          paymentId={completedPayment.payment_id}
          onClose={() => setShowConfirmation(false)}
        />
      )}
    </div>
  );
}

// Custom payment form for variable amounts
function CustomPaymentForm({ tenantId, propertyId, tenantName, tenantEmail, onSuccess, onError, onCancel }) {
  const [amount, setAmount] = useState('');
  const [paymentType, setPaymentType] = useState('other');
  const [description, setDescription] = useState('');
  const [showStripeForm, setShowStripeForm] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    const numAmount = parseFloat(amount);
    
    if (!numAmount || numAmount <= 0) {
      alert('Please enter a valid amount');
      return;
    }
    
    if (!description.trim()) {
      alert('Please enter a description');
      return;
    }
    
    setShowStripeForm(true);
  };

  if (showStripeForm) {
    return (
      <div className="p-4">
        <TenantPaymentForm
          tenantId={tenantId}
          propertyId={propertyId}
          amount={parseFloat(amount)}
          paymentType={paymentType}
          description={description}
          tenantName={tenantName}
          tenantEmail={tenantEmail}
          onSuccess={onSuccess}
          onError={onError}
          onCancel={() => setShowStripeForm(false)}
        />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="p-6 space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Payment Type
        </label>
        <select
          value={paymentType}
          onChange={(e) => setPaymentType(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="other">Other Fee</option>
          <option value="utilities">Utilities</option>
          <option value="maintenance">Maintenance Fee</option>
          <option value="late_fee">Late Fee</option>
          <option value="deposit">Security Deposit</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Amount ($)
        </label>
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="0.00"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows="3"
          placeholder="What is this payment for?"
          required
        />
      </div>

      <div className="flex space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Continue to Payment
        </button>
      </div>
    </form>
  );
}