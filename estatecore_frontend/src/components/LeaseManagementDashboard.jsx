import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Toast from './ui/Toast';

const LeaseManagementDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [expiringLeases, setExpiringLeases] = useState([]);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [showRenewalModal, setShowRenewalModal] = useState(false);
  const [showViolationModal, setShowViolationModal] = useState(false);
  const [selectedLease, setSelectedLease] = useState(null);
  const [filter, setFilter] = useState({
    status: 'all',
    timeframe: 60 // days for expiring leases
  });

  // Status color mapping
  const statusColors = {
    active: 'bg-green-100 text-green-800 border-green-200',
    expiring: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    expired: 'bg-red-100 text-red-800 border-red-200',
    renewed: 'bg-blue-100 text-blue-800 border-blue-200',
    terminated: 'bg-gray-100 text-gray-800 border-gray-200'
  };

  const renewalStatusColors = {
    not_started: 'bg-gray-100 text-gray-800',
    notice_sent: 'bg-blue-100 text-blue-800',
    in_negotiation: 'bg-yellow-100 text-yellow-800',
    accepted: 'bg-green-100 text-green-800',
    declined: 'bg-red-100 text-red-800'
  };

  const violationSeverityColors = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800'
  };

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/lease/dashboard', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setDashboardData(result.data);
        }
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      showToast('Failed to fetch dashboard data', 'error');
    }
  };

  // Fetch expiring leases
  const fetchExpiringLeases = async () => {
    try {
      const response = await fetch(`/api/lease/expiring?days=${filter.timeframe}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setExpiringLeases(result.expiring_leases || []);
        }
      }
    } catch (error) {
      console.error('Error fetching expiring leases:', error);
      showToast('Failed to fetch expiring leases', 'error');
    }
  };

  // Process lease renewals
  const processLeaseRenewals = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/lease/renewals/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast(result.message, 'success');
        fetchDashboardData();
        fetchExpiringLeases();
      } else {
        showToast(result.error || 'Failed to process renewals', 'error');
      }
    } catch (error) {
      console.error('Error processing renewals:', error);
      showToast('Failed to process renewals', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Send renewal notices
  const sendRenewalNotices = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/lease/renewal-notices/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({ notice_type: 'initial' })
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast(result.message, 'success');
        fetchDashboardData();
      } else {
        showToast(result.error || 'Failed to send notices', 'error');
      }
    } catch (error) {
      console.error('Error sending notices:', error);
      showToast('Failed to send notices', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Create lease renewal
  const createLeaseRenewal = async (renewalData) => {
    setLoading(true);
    try {
      const response = await fetch('/api/lease/renewals/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(renewalData)
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast('Lease renewal created successfully', 'success');
        fetchDashboardData();
        fetchExpiringLeases();
        setShowRenewalModal(false);
        setSelectedLease(null);
      } else {
        showToast(result.error || 'Failed to create renewal', 'error');
      }
    } catch (error) {
      console.error('Error creating renewal:', error);
      showToast('Failed to create renewal', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Track lease violation
  const trackViolation = async (violationData) => {
    setLoading(true);
    try {
      const response = await fetch('/api/lease/violations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(violationData)
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast('Lease violation recorded', 'success');
        fetchDashboardData();
        setShowViolationModal(false);
      } else {
        showToast(result.error || 'Failed to record violation', 'error');
      }
    } catch (error) {
      console.error('Error recording violation:', error);
      showToast('Failed to record violation', 'error');
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

  // Calculate days until date
  const daysUntil = (dateString) => {
    const today = new Date();
    const targetDate = new Date(dateString);
    const diffTime = targetDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  useEffect(() => {
    fetchDashboardData();
    fetchExpiringLeases();
  }, []);

  useEffect(() => {
    fetchExpiringLeases();
  }, [filter.timeframe]);

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
          <h2 className="text-2xl font-bold text-gray-900">Lease Management</h2>
          <p className="text-gray-600">
            Automated lease lifecycle management • Dashboard
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={processLeaseRenewals}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Process Renewals
          </Button>
          
          <Button
            onClick={sendRenewalNotices}
            disabled={loading}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            Send Notices
          </Button>

          <Button
            onClick={() => setShowViolationModal(true)}
            className="bg-orange-600 hover:bg-orange-700 text-white"
          >
            Report Violation
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Leases</p>
                <p className="text-2xl font-bold text-gray-900">
                  {dashboardData.total_active_leases || 0}
                </p>
              </div>
              <div className="text-3xl">📋</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-green-600 font-medium">
                {dashboardData.occupancy_rate?.toFixed(1) || 0}% occupancy
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Expiring Soon</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {dashboardData.expiring_soon || 0}
                </p>
              </div>
              <div className="text-3xl">⚠️</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">
                Next 60 days
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Renewal Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {dashboardData.renewal_rate?.toFixed(1) || 0}%
                </p>
              </div>
              <div className="text-3xl">🔄</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">
                Last 12 months
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Open Violations</p>
                <p className="text-2xl font-bold text-red-600">
                  {dashboardData.lease_violations?.open || 0}
                </p>
              </div>
              <div className="text-3xl">🚨</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">
                {dashboardData.lease_violations?.resolved || 0} resolved
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Renewal Pipeline */}
      {dashboardData?.renewal_pipeline && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Renewal Pipeline</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(dashboardData.renewal_pipeline).map(([status, count]) => (
              <div key={status} className="text-center">
                <div className={`inline-flex px-3 py-2 rounded-full text-sm font-medium ${renewalStatusColors[status] || 'bg-gray-100 text-gray-800'}`}>
                  {status.replace('_', ' ')}
                </div>
                <p className="text-2xl font-bold mt-2">{count}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Lease Status Breakdown */}
      {dashboardData?.lease_status_breakdown && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Lease Status Overview</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(dashboardData.lease_status_breakdown).map(([status, count]) => (
              <div key={status} className="text-center">
                <span className={`inline-flex px-3 py-2 rounded-full text-sm font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
                  {status}
                </span>
                <p className="text-xl font-bold mt-2">{count}</p>
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
              Expiring Lease Timeframe
            </label>
            <select
              value={filter.timeframe}
              onChange={(e) => setFilter({ ...filter, timeframe: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={30}>Next 30 days</option>
              <option value={60}>Next 60 days</option>
              <option value={90}>Next 90 days</option>
              <option value={180}>Next 6 months</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Lease Status Filter
            </label>
            <select
              value={filter.status}
              onChange={(e) => setFilter({ ...filter, status: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="expiring">Expiring</option>
              <option value="expired">Expired</option>
              <option value="renewed">Renewed</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Expiring Leases Table */}
      <Card className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">
            Expiring Leases ({expiringLeases.length})
          </h3>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading leases...</p>
          </div>
        ) : expiringLeases.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-6xl mb-4">📅</div>
            <p className="text-gray-600">No expiring leases found</p>
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
                    End Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Days Left
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Renewal Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {expiringLeases.map((lease) => (
                  <tr key={lease.lease_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {lease.tenant_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        Unit {lease.unit_number}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(lease.end_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${
                        daysUntil(lease.end_date) <= 30 ? 'text-red-600' :
                        daysUntil(lease.end_date) <= 60 ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {daysUntil(lease.end_date)} days
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        renewalStatusColors[lease.renewal_status] || 'bg-gray-100 text-gray-800'
                      }`}>
                        {lease.renewal_status?.replace('_', ' ') || 'not started'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Button
                        onClick={() => {
                          setSelectedLease(lease);
                          setShowRenewalModal(true);
                        }}
                        size="sm"
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        Manage Renewal
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Recent Activity */}
      {dashboardData?.recent_renewals && dashboardData.recent_renewals.length > 0 && (
        <Card className="p-4">
          <h3 className="text-lg font-semibold mb-4">Recent Renewals</h3>
          <div className="space-y-3">
            {dashboardData.recent_renewals.map((renewal, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-medium">✓</span>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {renewal.tenant_name}
                    </div>
                    <div className="text-sm text-gray-500">
                      Unit {renewal.unit_number} - Renewed
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {formatCurrency(renewal.new_rent)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(renewal.renewal_date)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Lease Renewal Modal */}
      <Modal
        isOpen={showRenewalModal}
        onClose={() => {
          setShowRenewalModal(false);
          setSelectedLease(null);
        }}
        title="Manage Lease Renewal"
      >
        {selectedLease && (
          <LeaseRenewalForm
            lease={selectedLease}
            onSubmit={createLeaseRenewal}
            onCancel={() => {
              setShowRenewalModal(false);
              setSelectedLease(null);
            }}
            loading={loading}
          />
        )}
      </Modal>

      {/* Violation Tracking Modal */}
      <Modal
        isOpen={showViolationModal}
        onClose={() => setShowViolationModal(false)}
        title="Report Lease Violation"
      >
        <ViolationForm
          onSubmit={trackViolation}
          onCancel={() => setShowViolationModal(false)}
          loading={loading}
        />
      </Modal>
    </div>
  );
};

// Lease Renewal Form Component
const LeaseRenewalForm = ({ lease, onSubmit, onCancel, loading }) => {
  const [renewalData, setRenewalData] = useState({
    lease_id: lease.lease_id,
    renewal_terms: {
      start_date: '',
      end_date: '',
      rent_amount: lease.rent_amount || 1500,
      lease_type: 'fixed_term',
      auto_renewal: false,
      terms: {}
    }
  });

  // Set default dates (1 year lease starting when current lease ends)
  useEffect(() => {
    if (lease.end_date) {
      const startDate = new Date(lease.end_date);
      startDate.setDate(startDate.getDate() + 1); // Start day after current lease ends
      
      const endDate = new Date(startDate);
      endDate.setFullYear(endDate.getFullYear() + 1); // 1 year lease
      
      setRenewalData(prev => ({
        ...prev,
        renewal_terms: {
          ...prev.renewal_terms,
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0]
        }
      }));
    }
  }, [lease]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(renewalData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900">Current Lease Details</h4>
        <div className="mt-2 space-y-1 text-sm text-gray-600">
          <div>Tenant: {lease.tenant_name}</div>
          <div>Unit: {lease.unit_number}</div>
          <div>Current End Date: {new Date(lease.end_date).toLocaleDateString()}</div>
          <div>Current Rent: ${lease.rent_amount}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            New Start Date
          </label>
          <input
            type="date"
            value={renewalData.renewal_terms.start_date}
            onChange={(e) => setRenewalData({
              ...renewalData,
              renewal_terms: {
                ...renewalData.renewal_terms,
                start_date: e.target.value
              }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            New End Date
          </label>
          <input
            type="date"
            value={renewalData.renewal_terms.end_date}
            onChange={(e) => setRenewalData({
              ...renewalData,
              renewal_terms: {
                ...renewalData.renewal_terms,
                end_date: e.target.value
              }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          New Rent Amount
        </label>
        <input
          type="number"
          step="0.01"
          value={renewalData.renewal_terms.rent_amount}
          onChange={(e) => setRenewalData({
            ...renewalData,
            renewal_terms: {
              ...renewalData.renewal_terms,
              rent_amount: parseFloat(e.target.value)
            }
          })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Lease Type
        </label>
        <select
          value={renewalData.renewal_terms.lease_type}
          onChange={(e) => setRenewalData({
            ...renewalData,
            renewal_terms: {
              ...renewalData.renewal_terms,
              lease_type: e.target.value
            }
          })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="fixed_term">Fixed Term</option>
          <option value="month_to_month">Month to Month</option>
          <option value="corporate">Corporate</option>
        </select>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="auto_renewal"
          checked={renewalData.renewal_terms.auto_renewal}
          onChange={(e) => setRenewalData({
            ...renewalData,
            renewal_terms: {
              ...renewalData.renewal_terms,
              auto_renewal: e.target.checked
            }
          })}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="auto_renewal" className="ml-2 block text-sm text-gray-900">
          Enable automatic renewal
        </label>
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
          {loading ? 'Creating...' : 'Create Renewal'}
        </Button>
      </div>
    </form>
  );
};

// Violation Form Component
const ViolationForm = ({ onSubmit, onCancel, loading }) => {
  const [violationData, setViolationData] = useState({
    lease_id: '',
    type: '',
    description: '',
    severity: 'medium'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(violationData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Lease ID
        </label>
        <input
          type="text"
          value={violationData.lease_id}
          onChange={(e) => setViolationData({ ...violationData, lease_id: e.target.value })}
          placeholder="Enter lease ID"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Violation Type
        </label>
        <select
          value={violationData.type}
          onChange={(e) => setViolationData({ ...violationData, type: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="">Select violation type</option>
          <option value="late_payment">Late Payment</option>
          <option value="noise_complaint">Noise Complaint</option>
          <option value="property_damage">Property Damage</option>
          <option value="unauthorized_occupant">Unauthorized Occupant</option>
          <option value="pet_violation">Pet Violation</option>
          <option value="lease_breach">Lease Breach</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Severity
        </label>
        <select
          value={violationData.severity}
          onChange={(e) => setViolationData({ ...violationData, severity: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <textarea
          value={violationData.description}
          onChange={(e) => setViolationData({ ...violationData, description: e.target.value })}
          rows={4}
          placeholder="Describe the violation in detail..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
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
          {loading ? 'Recording...' : 'Record Violation'}
        </Button>
      </div>
    </form>
  );
};

export default LeaseManagementDashboard;