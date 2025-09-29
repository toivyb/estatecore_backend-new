import React, { useState, useEffect } from 'react';
import api from '../api';

export default function EnhancedCompanies() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showMetricsModal, setShowMetricsModal] = useState(false);
  const [showBillingModal, setShowBillingModal] = useState(false);
  const [showTrialModal, setShowTrialModal] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [companyMetrics, setCompanyMetrics] = useState(null);
  
  const [newCompany, setNewCompany] = useState({
    name: '',
    billing_email: '',
    subscription_plan: 'basic',
    phone: '',
    address: ''
  });

  const [billingSettings, setBillingSettings] = useState({
    payment_method: 'card',
    auto_billing: true,
    mrr_override: '',
    subscription_plan: 'basic'
  });

  const [trialSettings, setTrialSettings] = useState({
    trial_days: 30
  });

  useEffect(() => {
    fetchCompanies();
    fetchAnalytics();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/companies');
      if (response.success) {
        setCompanies(response.companies);
      }
    } catch (error) {
      console.error('Error fetching companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await api.get('/api/companies/analytics');
      if (response.success) {
        setAnalytics(response);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const fetchCompanyMetrics = async (companyId) => {
    try {
      const response = await api.get(`/api/companies/${companyId}/metrics`);
      if (response.success) {
        setCompanyMetrics(response);
      }
    } catch (error) {
      console.error('Error fetching company metrics:', error);
    }
  };

  const createCompany = async () => {
    try {
      const response = await api.post('/api/companies', newCompany);
      if (response.success) {
        setCompanies([...companies, response.company]);
        setNewCompany({ name: '', billing_email: '', subscription_plan: 'basic', phone: '', address: '' });
        setShowCreateModal(false);
        fetchAnalytics(); // Refresh analytics
        alert('Company created successfully!');
      }
    } catch (error) {
      console.error('Error creating company:', error);
      alert('Error creating company. Check console for details.');
    }
  };

  const updateCompanyBilling = async () => {
    try {
      const response = await api.put(`/api/companies/${selectedCompany.id}/billing`, billingSettings);
      if (response.success) {
        setShowBillingModal(false);
        fetchCompanies(); // Refresh company data
        alert(response.message || 'Billing updated successfully!');
      }
    } catch (error) {
      console.error('Error updating billing:', error);
      alert('Error updating billing settings.');
    }
  };

  const extendTrial = async () => {
    try {
      const response = await api.post(`/api/companies/${selectedCompany.id}/trial`, trialSettings);
      if (response.success) {
        setShowTrialModal(false);
        fetchCompanies(); // Refresh company data
        alert(response.message || 'Trial extended successfully!');
      }
    } catch (error) {
      console.error('Error extending trial:', error);
      alert('Error extending trial.');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'trial': return 'bg-blue-100 text-blue-800';
      case 'suspended': return 'bg-yellow-100 text-yellow-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      case 'past_due': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPlanColor = (plan) => {
    switch (plan) {
      case 'trial': return 'bg-blue-100 text-blue-800';
      case 'basic': return 'bg-green-100 text-green-800';
      case 'premium': return 'bg-purple-100 text-purple-800';
      case 'enterprise': return 'bg-indigo-100 text-indigo-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const openMetricsModal = (company) => {
    setSelectedCompany(company);
    fetchCompanyMetrics(company.id);
    setShowMetricsModal(true);
  };

  const openBillingModal = (company) => {
    setSelectedCompany(company);
    setBillingSettings({
      payment_method: company.payment_method || 'card',
      auto_billing: company.auto_billing !== undefined ? company.auto_billing : true,
      mrr_override: company.mrr_override || '',
      subscription_plan: company.subscription_plan
    });
    setShowBillingModal(true);
  };

  const openTrialModal = (company) => {
    setSelectedCompany(company);
    setShowTrialModal(true);
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
      {/* Header with Tabs */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">🏢 Advanced Company Management</h1>
            <p className="text-gray-600">Comprehensive SaaS platform management</p>
          </div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            ➕ Add Company
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', name: 'Overview', icon: '📊' },
              { id: 'analytics', name: 'Analytics', icon: '📈' },
              { id: 'billing', name: 'Billing', icon: '💳' }
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
                {tab.icon} {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Analytics Dashboard */}
      {activeTab === 'analytics' && analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Platform Metrics */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Platform Overview</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Companies:</span>
                <span className="font-medium">{analytics.platform_metrics.total_companies}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Active:</span>
                <span className="font-medium text-green-600">{analytics.platform_metrics.active_companies}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Trial:</span>
                <span className="font-medium text-blue-600">{analytics.platform_metrics.trial_companies}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Churn Rate:</span>
                <span className="font-medium text-red-600">{analytics.platform_metrics.churn_rate}%</span>
              </div>
            </div>
          </div>

          {/* Revenue Metrics */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Metrics</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total MRR:</span>
                <span className="font-medium text-green-600">{formatCurrency(analytics.revenue_metrics.total_mrr)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total ARR:</span>
                <span className="font-medium text-green-600">{formatCurrency(analytics.revenue_metrics.total_arr)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg MRR/Company:</span>
                <span className="font-medium">{formatCurrency(analytics.revenue_metrics.average_mrr_per_company)}</span>
              </div>
            </div>
          </div>

          {/* Plan Distribution */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Plan Distribution</h3>
            <div className="space-y-3">
              {Object.entries(analytics.plan_distribution).map(([plan, count]) => (
                <div key={plan} className="flex justify-between">
                  <span className={`text-sm px-2 py-1 rounded ${getPlanColor(plan)}`}>{plan}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Top Companies */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Companies</h3>
            <div className="space-y-2">
              {analytics.top_companies.slice(0, 5).map((company, index) => (
                <div key={index} className="flex justify-between items-center">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{company.name}</div>
                    <div className="text-xs text-gray-500">{company.plan}</div>
                  </div>
                  <span className="text-sm font-medium text-green-600">{formatCurrency(company.mrr)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Companies Grid/Table */}
      {(activeTab === 'overview' || activeTab === 'billing') && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {companies.map(company => (
            <div key={company.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{company.name}</h3>
                  <p className="text-sm text-gray-600">{company.billing_email}</p>
                </div>
                <div className="flex flex-col space-y-2">
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(company.status)}`}>
                    {company.status}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${getPlanColor(company.subscription_plan)}`}>
                    {company.subscription_plan}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Monthly Fee:</span>
                  <span className="font-semibold text-green-600">{formatCurrency(company.monthly_fee)}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Annual Revenue:</span>
                  <span className="font-medium">{formatCurrency(company.monthly_fee * 12)}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Properties:</span>
                  <span className="font-medium">{company.property_count || 0}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Total Units:</span>
                  <span className="font-medium">{company.total_units || 0}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Users:</span>
                  <span className="font-medium">{company.user_count || 0}</span>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t flex flex-wrap gap-2">
                <button 
                  onClick={() => openMetricsModal(company)}
                  className="flex-1 bg-blue-600 text-white px-3 py-2 text-sm rounded hover:bg-blue-700"
                >
                  📊 Metrics
                </button>
                <button 
                  onClick={() => openBillingModal(company)}
                  className="flex-1 bg-green-600 text-white px-3 py-2 text-sm rounded hover:bg-green-700"
                >
                  💳 Billing
                </button>
                <button 
                  onClick={() => openTrialModal(company)}
                  className="flex-1 bg-purple-600 text-white px-3 py-2 text-sm rounded hover:bg-purple-700"
                >
                  🚀 Trial
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {companies.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-4">No companies found</div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            ➕ Create Your First Company
          </button>
        </div>
      )}

      {/* Create Company Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowCreateModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Create New Company</h3>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Company Name *</label>
                  <input
                    type="text"
                    value={newCompany.name}
                    onChange={(e) => setNewCompany({...newCompany, name: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter company name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Billing Email *</label>
                  <input
                    type="email"
                    value={newCompany.billing_email}
                    onChange={(e) => setNewCompany({...newCompany, billing_email: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="billing@company.com"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subscription Plan</label>
                  <select
                    value={newCompany.subscription_plan}
                    onChange={(e) => setNewCompany({...newCompany, subscription_plan: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="trial">Trial - Free for 30 days</option>
                    <option value="basic">Basic - $2.00/unit/month</option>
                    <option value="premium">Premium - $2.50/unit/month</option>
                    <option value="enterprise">Enterprise - $3.00/unit/month</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    type="tel"
                    value={newCompany.phone}
                    onChange={(e) => setNewCompany({...newCompany, phone: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="(555) 123-4567"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                  <textarea
                    value={newCompany.address}
                    onChange={(e) => setNewCompany({...newCompany, address: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows="2"
                    placeholder="Company address"
                  />
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={createCompany}
                  disabled={!newCompany.name || !newCompany.billing_email}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Company
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Company Metrics Modal */}
      {showMetricsModal && selectedCompany && companyMetrics && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowMetricsModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">
                  Company Metrics - {selectedCompany.name}
                </h3>
              </div>
              
              <div className="px-6 py-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {/* Usage Metrics */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-3">📊 Usage Metrics</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Properties:</span>
                        <span className="font-medium">{companyMetrics.usage_metrics.properties}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Total Units:</span>
                        <span className="font-medium">{companyMetrics.usage_metrics.total_units}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Occupied Units:</span>
                        <span className="font-medium">{companyMetrics.usage_metrics.occupied_units}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Vacancy Rate:</span>
                        <span className="font-medium">{companyMetrics.usage_metrics.vacancy_rate}%</span>
                      </div>
                    </div>
                  </div>

                  {/* Financial Metrics */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-3">💰 Financial Metrics</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Monthly Fee:</span>
                        <span className="font-medium text-green-600">{formatCurrency(companyMetrics.billing_metrics.monthly_fee)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Annual Revenue:</span>
                        <span className="font-medium">{formatCurrency(companyMetrics.billing_metrics.annual_revenue)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Monthly Rent:</span>
                        <span className="font-medium">{formatCurrency(companyMetrics.usage_metrics.monthly_rent_collected)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Avg Rent/Unit:</span>
                        <span className="font-medium">{formatCurrency(companyMetrics.usage_metrics.average_rent_per_unit)}</span>
                      </div>
                    </div>
                  </div>

                  {/* User Metrics */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-3">👥 User Metrics</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Total Users:</span>
                        <span className="font-medium">{companyMetrics.user_metrics.total_users}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Active Users:</span>
                        <span className="font-medium text-green-600">{companyMetrics.user_metrics.active_users}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Inactive Users:</span>
                        <span className="font-medium text-red-600">{companyMetrics.user_metrics.inactive_users}</span>
                      </div>
                    </div>
                  </div>

                  {/* Growth Metrics */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-3">📈 Growth Metrics</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Properties Growth:</span>
                        <span className="font-medium text-green-600">{companyMetrics.growth_metrics.properties_growth}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Units Growth:</span>
                        <span className="font-medium text-green-600">{companyMetrics.growth_metrics.units_growth}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Revenue Growth:</span>
                        <span className="font-medium text-green-600">{companyMetrics.growth_metrics.revenue_growth}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">User Growth:</span>
                        <span className="font-medium text-green-600">{companyMetrics.growth_metrics.user_growth}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
                <button
                  onClick={() => setShowMetricsModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Billing Settings Modal */}
      {showBillingModal && selectedCompany && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowBillingModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">
                  Billing Settings - {selectedCompany.name}
                </h3>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subscription Plan</label>
                  <select
                    value={billingSettings.subscription_plan}
                    onChange={(e) => setBillingSettings({...billingSettings, subscription_plan: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="trial">Trial - Free</option>
                    <option value="basic">Basic - $2.00/unit/month</option>
                    <option value="premium">Premium - $2.50/unit/month</option>
                    <option value="enterprise">Enterprise - $3.00/unit/month</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
                  <select
                    value={billingSettings.payment_method}
                    onChange={(e) => setBillingSettings({...billingSettings, payment_method: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="card">Credit Card</option>
                    <option value="bank_transfer">Bank Transfer</option>
                    <option value="invoice">Invoice</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">MRR Override</label>
                  <input
                    type="number"
                    step="0.01"
                    value={billingSettings.mrr_override}
                    onChange={(e) => setBillingSettings({...billingSettings, mrr_override: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Custom monthly fee (optional)"
                  />
                  <p className="text-xs text-gray-500 mt-1">Leave empty to use plan-based pricing</p>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="auto_billing"
                    checked={billingSettings.auto_billing}
                    onChange={(e) => setBillingSettings({...billingSettings, auto_billing: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="auto_billing" className="ml-2 block text-sm text-gray-900">
                    Enable Auto Billing
                  </label>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => setShowBillingModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={updateCompanyBilling}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Update Billing
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Trial Extension Modal */}
      {showTrialModal && selectedCompany && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowTrialModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">
                  Extend Trial - {selectedCompany.name}
                </h3>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Trial Duration (Days)</label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={trialSettings.trial_days}
                    onChange={(e) => setTrialSettings({...trialSettings, trial_days: parseInt(e.target.value)})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Number of days to extend the trial period</p>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">Trial Extension Effects:</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Company status will be set to "trial"</li>
                    <li>• Subscription plan will be set to "trial"</li>
                    <li>• Monthly fee will be $0.00</li>
                    <li>• Trial will expire in {trialSettings.trial_days} days</li>
                  </ul>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => setShowTrialModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={extendTrial}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  Extend Trial
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}