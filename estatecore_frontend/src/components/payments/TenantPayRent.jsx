import React, { useState, useEffect } from "react";
import { loadStripe } from "@stripe/stripe-js";
import {
  Elements,
  CardElement,
  useStripe,
  useElements
} from "@stripe/react-stripe-js";
import axios from "axios";

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || "pk_test_...");

// Payment form component
function PaymentForm({ 
  paymentData, 
  onSuccess, 
  onError, 
  onCancel 
}) {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [paymentIntent, setPaymentIntent] = useState(null);

  useEffect(() => {
    createPaymentIntent();
  }, []);

  const createPaymentIntent = async () => {
    try {
      const response = await axios.post('/api/payments/create-payment-intent', paymentData);
      if (response.data.success) {
        setPaymentIntent(response.data);
      } else {
        setError('Failed to create payment intent');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create payment intent');
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!stripe || !elements || !paymentIntent) {
      return;
    }

    setIsProcessing(true);
    setError('');

    const cardElement = elements.getElement(CardElement);

    try {
      // Confirm payment with Stripe
      const { error: confirmError, paymentIntent: confirmedPayment } = await stripe.confirmCardPayment(
        paymentIntent.client_secret,
        {
          payment_method: {
            card: cardElement,
            billing_details: {
              name: paymentData.tenant_name,
              email: paymentData.tenant_email,
            },
          },
        }
      );

      if (confirmError) {
        setError(confirmError.message);
      } else if (confirmedPayment.status === 'succeeded') {
        // Confirm payment on our backend
        await axios.post(`/api/payments/${paymentIntent.payment_id}/confirm`);
        onSuccess({
          payment_id: paymentIntent.payment_id,
          receipt_number: paymentIntent.receipt_number,
          amount: paymentIntent.amount
        });
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Payment failed. Please try again.');
      onError(err.response?.data?.error || 'Payment failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: '#424770',
        '::placeholder': {
          color: '#aab7c4',
        },
      },
      invalid: {
        color: '#9e2146',
      },
    },
  };

  if (!paymentIntent) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Setting up payment...</span>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Payment Summary */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-semibold text-lg mb-2">Payment Summary</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Payment Type:</span>
            <span className="font-medium">{paymentData.payment_type_display}</span>
          </div>
          <div className="flex justify-between">
            <span>Amount:</span>
            <span className="font-medium">${paymentIntent.amount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            <span>Processing Fee:</span>
            <span>${paymentIntent.processing_fee.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            <span>Net Amount:</span>
            <span>${paymentIntent.net_amount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between font-semibold text-lg border-t pt-2">
            <span>Total to Pay:</span>
            <span>${paymentIntent.amount.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Card Information */}
      <div className="space-y-4">
        <h3 className="font-semibold text-lg">Payment Method</h3>
        <div className="p-4 border rounded-lg">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Card Information
          </label>
          <CardElement options={cardElementOptions} />
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isProcessing}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!stripe || isProcessing}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Processing...
            </div>
          ) : (
            `Pay $${paymentIntent.amount.toFixed(2)}`
          )}
        </button>
      </div>

      {/* Security Notice */}
      <div className="text-xs text-gray-500 text-center">
        <div className="flex items-center justify-center space-x-1">
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
          </svg>
          <span>Your payment information is secure and encrypted</span>
        </div>
      </div>
    </form>
  );
}

// Main payment component
export default function TenantPaymentForm({ 
  tenantId, 
  propertyId, 
  amount, 
  paymentType = 'rent',
  description = '',
  dueDate = null,
  tenantName = '',
  tenantEmail = '',
  onSuccess,
  onError,
  onCancel 
}) {
  const paymentData = {
    tenant_id: tenantId,
    property_id: propertyId,
    amount: amount,
    payment_type: paymentType,
    payment_method: 'credit_card',
    description: description,
    due_date: dueDate,
    tenant_name: tenantName,
    tenant_email: tenantEmail,
    payment_type_display: getPaymentTypeDisplay(paymentType)
  };

  return (
    <Elements stripe={stripePromise}>
      <div className="max-w-md mx-auto bg-white p-6 rounded-lg shadow-lg">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 text-center">Make Payment</h2>
          <p className="text-gray-600 text-center mt-2">
            Secure payment powered by Stripe
          </p>
        </div>
        
        <PaymentForm
          paymentData={paymentData}
          onSuccess={onSuccess}
          onError={onError}
          onCancel={onCancel}
        />
      </div>
    </Elements>
  );
}

// Helper function to get payment type display name
function getPaymentTypeDisplay(paymentType) {
  const types = {
    rent: 'Rent Payment',
    late_fee: 'Late Fee',
    deposit: 'Security Deposit',
    utilities: 'Utilities',
    maintenance: 'Maintenance Fee',
    other: 'Other Fee'
  };
  return types[paymentType] || 'Payment';
}

// Quick pay button component for simple payments
export function QuickPayButton({ 
  tenantId, 
  propertyId, 
  amount, 
  paymentType = 'rent',
  description = '',
  onSuccess,
  onError,
  className = '',
  disabled = false 
}) {
  const [showPaymentForm, setShowPaymentForm] = useState(false);

  const handlePaymentSuccess = (result) => {
    setShowPaymentForm(false);
    if (onSuccess) onSuccess(result);
  };

  const handlePaymentError = (error) => {
    setShowPaymentForm(false);
    if (onError) onError(error);
  };

  const handleCancel = () => {
    setShowPaymentForm(false);
  };

  if (showPaymentForm) {
    return (
      <TenantPaymentForm
        tenantId={tenantId}
        propertyId={propertyId}
        amount={amount}
        paymentType={paymentType}
        description={description}
        onSuccess={handlePaymentSuccess}
        onError={handlePaymentError}
        onCancel={handleCancel}
      />
    );
  }

  return (
    <button
      onClick={() => setShowPaymentForm(true)}
      disabled={disabled}
      className={`px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      Pay ${amount.toFixed(2)}
    </button>
  );
}
