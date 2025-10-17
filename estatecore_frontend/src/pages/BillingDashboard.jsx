import React, { useState, useEffect } from 'react';
import api from '../api';

export default function BillingDashboard() {
  const [billingData, setBillingData] = useState({});
  const [subscriptions, setSubscriptions] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      setLoading(true);

      // Fetch subscription analytics
      const subscriptionResult = await api.get('/api/billing/analytics/subscriptions');
      if (subscriptionResult.success) {
        setAnalytics(prev => ({ ...prev, subscriptions: subscriptionResult.data }));
      }

      // Fetch payment analytics
      const paymentResult = await api.get('/api/billing/analytics/payments');
      if (paymentResult.success) {
        setAnalytics(prev => ({ ...prev, payments: paymentResult.data }));
      }

      // Fetch revenue analytics
      const revenueResult = await api.get('/api/billing/analytics/revenue');
      if (revenueResult.success) {
        setAnalytics(prev => ({ ...prev, revenue: revenueResult.data }));
      }

      // Fetch pricing tiers
      const pricingResult = await api.get('/api/billing/admin/pricing-tiers');
      if (pricingResult.success) {
        setBillingData(prev => ({ ...prev, pricingTiers: pricingResult.data }));
      }

      setLoading(false);
      setError('');
    } catch (err) {
      console.error('Error fetching billing data:', err);
      setError('Failed to load billing data');
      setLoading(false);
    }
  };

  const createSubscription = async (subscriptionData) => {
    try {
      const result = await api.post('/api/billing/subscriptions', subscriptionData);
      if (result.success) {
        alert('Subscription created successfully!');
        fetchBillingData(); // Refresh data
      } else {
        alert('Failed to create subscription');
      }
    } catch (err) {
      console.error('Error creating subscription:', err);
      alert('Error creating subscription');
    }
  };

  const processScheduledPayments = async () => {
    try {
      const result = await api.post('/api/billing/admin/process-scheduled-payments', {});
      if (result.success) {
        alert(`Processed ${result.data.processed_payments} scheduled payments`);
        fetchBillingData(); // Refresh data
      } else {
        alert('Failed to process scheduled payments');
      }
    } catch (err) {
      console.error('Error processing payments:', err);
      alert('Error processing scheduled payments');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  const getTierColor = (tier) => {
    const colors = {
      starter: 'bg-blue-100 text-blue-800',
      professional: 'bg-green-100 text-green-800',
      enterprise: 'bg-purple-100 text-purple-800',
      custom: 'bg-orange-100 text-orange-800'
    };
    return colors[tier] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Loading Billing Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">SaaS Billing Dashboard</h1>
          <p className="text-gray-600">Comprehensive billing and subscription management</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={processScheduledPayments}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition"
          >
            Process Scheduled Payments
          </button>
          
          <button
            onClick={fetchBillingData}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
          >
            Refresh Data
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: '📊' },
            { id: 'subscriptions', name: 'Subscriptions', icon: '📝' },
            { id: 'revenue', name: 'Revenue', icon: '💰' },
            { id: 'customers', name: 'Customers', icon: '👥' },
            { id: 'pricing', name: 'Pricing Tiers', icon: '💎' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-semibold">💰</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Monthly Recurring Revenue</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(analytics.subscriptions?.monthly_recurring_revenue || 0)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-semibold">📈</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Annual Run Rate</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(analytics.revenue?.annual_run_rate || 0)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <span className="text-purple-600 font-semibold">👥</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Active Subscriptions</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {analytics.subscriptions?.active_subscriptions || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                    <span className="text-orange-600 font-semibold">💳</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Payment Success Rate</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatPercentage(analytics.payments?.success_rate || 0)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Charts and Analytics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Subscription Tier Distribution */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold mb-4">Subscription Tier Distribution</h3>
              {analytics.subscriptions?.tier_distribution && (
                <div className="space-y-3">
                  {Object.entries(analytics.subscriptions.tier_distribution).map(([tier, count]) => (
                    <div key={tier} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className={`px-2 py-1 rounded text-xs font-semibold mr-2 ${getTierColor(tier)}`}>
                          {tier.charAt(0).toUpperCase() + tier.slice(1)}
                        </span>
                      </div>
                      <span className="font-semibold">{count} customers</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Payment Method Breakdown */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold mb-4">Payment Method Usage</h3>
              {analytics.payments?.method_breakdown && (
                <div className="space-y-3">
                  {Object.entries(analytics.payments.method_breakdown).map(([method, data]) => (
                    <div key={method} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="text-sm font-medium capitalize mr-2">
                          {method.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">{data.count} transactions</div>
                        <div className="text-sm text-gray-500">{formatCurrency(data.volume)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Billing Activity</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b">
                <div>
                  <p className="font-medium">New subscription created</p>
                  <p className="text-sm text-gray-500">Professional Plan - Acme Corp</p>
                </div>
                <span className="text-sm text-gray-500">2 hours ago</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b">
                <div>
                  <p className="font-medium">Payment processed successfully</p>
                  <p className="text-sm text-gray-500">{formatCurrency(299)} - Invoice #INV-202501-0123</p>
                </div>
                <span className="text-sm text-gray-500">4 hours ago</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b">
                <div>
                  <p className="font-medium">Subscription upgraded</p>
                  <p className="text-sm text-gray-500">Starter → Professional - TechStart Inc</p>
                </div>
                <span className="text-sm text-gray-500">1 day ago</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Subscriptions Tab */}
      {activeTab === 'subscriptions' && (
        <div className="space-y-6">
          {/* Unit-Based Billing Management */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Unit-Based Billing Management</h3>
              <div className="text-sm text-gray-600 bg-blue-50 px-3 py-2 rounded border border-blue-200">
                💡 Pricing: $2.50 per unit managed
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {analytics.subscriptions?.active_subscriptions || 0}
                </div>
                <div className="text-sm text-gray-500">Active Subscriptions</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {analytics.subscriptions?.trial_subscriptions || 0}
                </div>
                <div className="text-sm text-gray-500">Trial Subscriptions</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {formatCurrency(analytics.subscriptions?.average_revenue_per_user || 0)}
                </div>
                <div className="text-sm text-gray-500">Average Revenue Per User</div>
              </div>
            </div>
          </div>

          {/* Subscription List */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Subscriptions</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Customer</th>
                    <th className="text-left py-2">Plan</th>
                    <th className="text-left py-2">Status</th>
                    <th className="text-left py-2">Monthly Value</th>
                    <th className="text-left py-2">Next Billing</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="py-2">Acme Corporation</td>
                    <td className="py-2">
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                        Professional
                      </span>
                    </td>
                    <td className="py-2">
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                        Active
                      </span>
                    </td>
                    <td className="py-2">{formatCurrency(299)}</td>
                    <td className="py-2">Jan 25, 2025</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-2">TechStart Inc</td>
                    <td className="py-2">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        Starter
                      </span>
                    </td>
                    <td className="py-2">
                      <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">
                        Trial
                      </span>
                    </td>
                    <td className="py-2">{formatCurrency(99)}</td>
                    <td className="py-2">Feb 5, 2025</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Revenue Tab */}
      {activeTab === 'revenue' && (
        <div className="space-y-6">
          {/* Revenue Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h4 className="text-sm font-medium text-gray-500">Total Revenue</h4>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(analytics.revenue?.total_revenue || 0)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h4 className="text-sm font-medium text-gray-500">Transaction Count</h4>
              <p className="text-2xl font-bold text-blue-600">
                {analytics.revenue?.transaction_count || 0}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h4 className="text-sm font-medium text-gray-500">Average Transaction</h4>
              <p className="text-2xl font-bold text-purple-600">
                {formatCurrency(analytics.revenue?.average_transaction_size || 0)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h4 className="text-sm font-medium text-gray-500">Churn Rate</h4>
              <p className="text-2xl font-bold text-red-600">
                {formatPercentage(analytics.subscriptions?.churn_rate || 0)}
              </p>
            </div>
          </div>

          {/* Revenue Growth */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Revenue Growth</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Monthly Recurring Revenue</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Current MRR</span>
                    <span className="font-semibold">
                      {formatCurrency(analytics.subscriptions?.monthly_recurring_revenue || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Annual Run Rate</span>
                    <span className="font-semibold">
                      {formatCurrency(analytics.subscriptions?.annual_recurring_revenue || 0)}
                    </span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Growth Metrics</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Month-over-Month Growth</span>
                    <span className="font-semibold text-green-600">+12.5%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Customer Lifetime Value</span>
                    <span className="font-semibold">{formatCurrency(2400)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Customers Tab */}
      {activeTab === 'customers' && (
        <div className="space-y-6">
          {/* Customer Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h4 className="text-sm font-medium text-gray-500">Total Customers</h4>
              <p className="text-2xl font-bold text-blue-600">
                {analytics.subscriptions?.total_subscriptions || 0}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h4 className="text-sm font-medium text-gray-500">New This Month</h4>
              <p className="text-2xl font-bold text-green-600">12</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h4 className="text-sm font-medium text-gray-500">Churned This Month</h4>
              <p className="text-2xl font-bold text-red-600">2</p>
            </div>
          </div>

          {/* Customer Segments */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Customer Segments</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">By Plan</h4>
                {analytics.subscriptions?.tier_distribution && (
                  <div className="space-y-2">
                    {Object.entries(analytics.subscriptions.tier_distribution).map(([tier, count]) => (
                      <div key={tier} className="flex justify-between">
                        <span className="capitalize">{tier}</span>
                        <span className="font-semibold">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div>
                <h4 className="font-medium mb-3">By Payment Method</h4>
                {analytics.payments?.method_breakdown && (
                  <div className="space-y-2">
                    {Object.entries(analytics.payments.method_breakdown).map(([method, data]) => (
                      <div key={method} className="flex justify-between">
                        <span className="capitalize">{method.replace('_', ' ')}</span>
                        <span className="font-semibold">{data.count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pricing Tiers Tab */}
      {activeTab === 'pricing' && billingData.pricingTiers && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(billingData.pricingTiers).map(([tierKey, tier]) => (
              <div key={tierKey} className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold">{tier.name}</h3>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getTierColor(tierKey)}`}>
                    {tierKey.charAt(0).toUpperCase() + tierKey.slice(1)}
                  </span>
                </div>
                
                <p className="text-gray-600 mb-4">{tier.description}</p>
                
                <div className="mb-6">
                  <div className="text-3xl font-bold text-green-600">
                    $2.50
                    <span className="text-lg font-normal text-gray-500">/unit</span>
                  </div>
                  <div className="text-sm text-gray-600 bg-green-50 px-2 py-1 rounded">
                    Pay only for units you manage
                  </div>
                </div>
                
                <div className="space-y-3 mb-6">
                  <div className="flex justify-between text-sm">
                    <span>Properties</span>
                    <span className="font-semibold">
                      {tier.max_properties === 999999 ? 'Unlimited' : tier.max_properties}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Units</span>
                    <span className="font-semibold">
                      {tier.max_units === 999999 ? 'Unlimited' : tier.max_units}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Users</span>
                    <span className="font-semibold">
                      {tier.max_users === 999999 ? 'Unlimited' : tier.max_users}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Storage</span>
                    <span className="font-semibold">{tier.max_documents_gb} GB</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>API Calls</span>
                    <span className="font-semibold">{tier.max_api_calls_per_month.toLocaleString()}/month</span>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-medium text-sm">Features</h4>
                  {Object.entries(tier.features).map(([feature, enabled]) => (
                    <div key={feature} className="flex items-center text-sm">
                      <span className={`mr-2 ${enabled ? 'text-green-500' : 'text-gray-400'}`}>
                        {enabled ? '✓' : '✗'}
                      </span>
                      <span className={enabled ? 'text-gray-900' : 'text-gray-400'}>
                        {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}