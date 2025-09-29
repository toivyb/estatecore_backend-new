import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Toast from './ui/Toast';

const RentCollectionDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [filter, setFilter] = useState({
    status: 'all',
    month: new Date().toISOString().slice(0, 7) // YYYY-MM
  });

  // Status color mapping
  const statusColors = {
    current: 'bg-green-100 text-green-800 border-green-200',
    late: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    overdue: 'bg-red-100 text-red-800 border-red-200',
    paid: 'bg-blue-100 text-blue-800 border-blue-200',
    partial_paid: 'bg-purple-100 text-purple-800 border-purple-200'
  };

  const paymentStatusColors = {
    pending: 'bg-gray-100 text-gray-800',
    processing: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800'
  };

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/rent/dashboard', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      showToast('Failed to fetch dashboard data', 'error');
    }
  };

  // Fetch invoices
  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.status !== 'all') params.append('status', filter.status);
      if (filter.month) params.append('month', filter.month);

      const response = await fetch(`/api/rent/invoices?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setInvoices(data);
      }
    } catch (error) {
      console.error('Error fetching invoices:', error);
      showToast('Failed to fetch invoices', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch payments
  const fetchPayments = async () => {
    try {
      const response = await fetch('/api/rent/payments?limit=20', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPayments(data);
      }
    } catch (error) {
      console.error('Error fetching payments:', error);
    }
  };

  // Generate monthly invoices
  const generateMonthlyInvoices = async (targetMonth) => {
    setLoading(true);
    try {
      const response = await fetch('/api/rent/invoices/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          target_month: targetMonth
        })
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast(result.message, 'success');
        fetchDashboardData();
        fetchInvoices();
        setShowGenerateModal(false);
      } else {
        showToast(result.error || 'Failed to generate invoices', 'error');
      }
    } catch (error) {
      console.error('Error generating invoices:', error);
      showToast('Failed to generate invoices', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Send rent reminders
  const sendRentReminders = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/rent/reminders/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({ type: 'all' })
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast(result.message, 'success');
      } else {
        showToast(result.error || 'Failed to send reminders', 'error');
      }
    } catch (error) {
      console.error('Error sending reminders:', error);
      showToast('Failed to send reminders', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Process payment
  const processPayment = async (paymentData) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/rent/invoices/${selectedInvoice.id}/pay`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(paymentData)
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast('Payment processed successfully', 'success');
        fetchDashboardData();
        fetchInvoices();
        fetchPayments();
        setShowPaymentModal(false);
        setSelectedInvoice(null);
      } else {
        showToast(result.error || 'Payment processing failed', 'error');
      }
    } catch (error) {
      console.error('Error processing payment:', error);
      showToast('Payment processing failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Show toast notification
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  useEffect(() => {
    fetchDashboardData();
    fetchInvoices();
    fetchPayments();
  }, []);

  useEffect(() => {
    fetchInvoices();
  }, [filter]);

  return (
    <div className="space-y-6">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Rent Collection</h2>
          <p className="text-gray-600">
            {dashboardData?.current_month || 'Loading...'} • Dashboard
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={() => setShowGenerateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Generate Invoices
          </Button>
          
          <Button
            onClick={sendRentReminders}
            disabled={loading}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            Send Reminders
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Rent Due</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(dashboardData.total_rent_due)}
                </p>
              </div>
              <div className="text-3xl">💰</div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Collected</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(dashboardData.total_collected)}
                </p>
              </div>
              <div className="text-3xl">✅</div>
            </div>
            <div className="mt-2">
              <div className="flex items-center text-sm">
                <span className="text-green-600 font-medium">
                  {dashboardData.collection_rate?.toFixed(1)}%
                </span>
                <span className="text-gray-500 ml-1">collection rate</span>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Overdue Amount</p>
                <p className="text-2xl font-bold text-red-600">
                  {formatCurrency(dashboardData.overdue_amount)}
                </p>
              </div>
              <div className="text-3xl">⚠️</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">
                {dashboardData.outstanding_invoices} outstanding invoices
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Late Fees</p>
                <p className="text-2xl font-bold text-orange-600">
                  {formatCurrency(dashboardData.late_fees_collected)}
                </p>
              </div>
              <div className="text-3xl">📈</div>
            </div>
          </Card>
        </div>
      )}

      {/* Payment Methods Breakdown */}
      {dashboardData?.payment_methods_breakdown && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Payment Methods This Month</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(dashboardData.payment_methods_breakdown).map(([method, amount]) => (
              <div key={method} className="text-center">
                <p className="text-sm text-gray-600 capitalize">
                  {method.replace('_', ' ')}
                </p>
                <p className="text-lg font-semibold">
                  {formatCurrency(amount)}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Status
            </label>
            <select
              value={filter.status}
              onChange={(e) => setFilter({ ...filter, status: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="current">Current</option>
              <option value="late">Late</option>
              <option value="overdue">Overdue</option>
              <option value="paid">Paid</option>
              <option value="partial_paid">Partially Paid</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Month
            </label>
            <input
              type="month"
              value={filter.month}
              onChange={(e) => setFilter({ ...filter, month: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </Card>

      {/* Invoices List */}
      <Card className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">
            Rent Invoices ({invoices.length})
          </h3>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading invoices...</p>
          </div>
        ) : invoices.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-6xl mb-4">📄</div>
            <p className="text-gray-600">No invoices found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tenant
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Property/Unit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount Due
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
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {invoice.tenant_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {invoice.tenant_email}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {invoice.property_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        Unit {invoice.unit_number}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {formatCurrency(invoice.total_amount)}
                      </div>
                      {invoice.late_fee > 0 && (
                        <div className="text-sm text-red-600">
                          +{formatCurrency(invoice.late_fee)} late fee
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(invoice.due_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColors[invoice.status] || 'bg-gray-100 text-gray-800'}`}>
                        {invoice.status.replace('_', ' ')}
                      </span>
                      <div className="mt-1">
                        <span className={`inline-flex px-2 py-1 text-xs rounded-full ${paymentStatusColors[invoice.payment_status] || 'bg-gray-100 text-gray-800'}`}>
                          {invoice.payment_status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {invoice.payment_status === 'pending' && (
                        <Button
                          onClick={() => {
                            setSelectedInvoice(invoice);
                            setShowPaymentModal(true);
                          }}
                          size="sm"
                          className="bg-green-600 hover:bg-green-700 text-white"
                        >
                          Process Payment
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Recent Payments */}
      {payments.length > 0 && (
        <Card className="p-4">
          <h3 className="text-lg font-semibold mb-4">Recent Payments</h3>
          <div className="space-y-3">
            {payments.slice(0, 5).map((payment) => (
              <div key={payment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-medium">$</span>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {payment.tenant_name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {payment.property_name} - Unit {payment.unit_number}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {formatCurrency(payment.amount)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(payment.created_at)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Generate Invoices Modal */}
      <Modal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        title="Generate Monthly Invoices"
      >
        <InvoiceGenerationForm
          onSubmit={generateMonthlyInvoices}
          onCancel={() => setShowGenerateModal(false)}
          loading={loading}
        />
      </Modal>

      {/* Payment Processing Modal */}
      <Modal
        isOpen={showPaymentModal}
        onClose={() => {
          setShowPaymentModal(false);
          setSelectedInvoice(null);
        }}
        title="Process Payment"
      >
        {selectedInvoice && (
          <PaymentForm
            invoice={selectedInvoice}
            onSubmit={processPayment}
            onCancel={() => {
              setShowPaymentModal(false);
              setSelectedInvoice(null);
            }}
            loading={loading}
          />
        )}
      </Modal>
    </div>
  );
};

// Invoice Generation Form Component
const InvoiceGenerationForm = ({ onSubmit, onCancel, loading }) => {
  const [targetMonth, setTargetMonth] = useState(() => {
    const nextMonth = new Date();
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    return nextMonth.toISOString().slice(0, 7);
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(targetMonth + '-01');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Month
        </label>
        <input
          type="month"
          value={targetMonth}
          onChange={(e) => setTargetMonth(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <p className="text-sm text-gray-500 mt-1">
          Generate invoices for all active tenants for this month
        </p>
      </div>

      <div className="flex justify-end space-x-3">
        <Button
          type="button"
          onClick={onCancel}
          variant="outline"
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate Invoices'}
        </Button>
      </div>
    </form>
  );
};

// Payment Form Component
const PaymentForm = ({ invoice, onSubmit, onCancel, loading }) => {
  const [paymentData, setPaymentData] = useState({
    amount: invoice.total_amount,
    payment_method: 'credit_card',
    description: `Payment for ${invoice.description}`
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(paymentData);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900">Invoice Details</h4>
        <div className="mt-2 space-y-1 text-sm text-gray-600">
          <div>Tenant: {invoice.tenant_name}</div>
          <div>Property: {invoice.property_name} - Unit {invoice.unit_number}</div>
          <div>Amount Due: {formatCurrency(invoice.total_amount)}</div>
          <div>Due Date: {new Date(invoice.due_date).toLocaleDateString()}</div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Payment Amount
        </label>
        <input
          type="number"
          step="0.01"
          value={paymentData.amount}
          onChange={(e) => setPaymentData({ ...paymentData, amount: parseFloat(e.target.value) })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Payment Method
        </label>
        <select
          value={paymentData.payment_method}
          onChange={(e) => setPaymentData({ ...paymentData, payment_method: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="credit_card">Credit Card</option>
          <option value="debit_card">Debit Card</option>
          <option value="bank_transfer">Bank Transfer</option>
          <option value="ach">ACH Transfer</option>
          <option value="check">Check</option>
          <option value="cash">Cash</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description (Optional)
        </label>
        <textarea
          value={paymentData.description}
          onChange={(e) => setPaymentData({ ...paymentData, description: e.target.value })}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex justify-end space-x-3">
        <Button
          type="button"
          onClick={onCancel}
          variant="outline"
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Process Payment'}
        </Button>
      </div>
    </form>
  );
};

export default RentCollectionDashboard;