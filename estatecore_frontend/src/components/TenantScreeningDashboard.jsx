import React, { useState, useEffect } from 'react';

const TenantScreeningDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [applications, setApplications] = useState([]);
  const [screeningChecks, setScreeningChecks] = useState([]);
  const [screeningCriteria, setScreeningCriteria] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showApplicationForm, setShowApplicationForm] = useState(false);
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterProperty, setFilterProperty] = useState('');
  
  const [newApplication, setNewApplication] = useState({
    property_id: '',
    unit_id: '',
    personal_info: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      ssn: '',
      date_of_birth: '',
      current_address: ''
    },
    employment_info: {
      employer: '',
      position: '',
      annual_income: '',
      employment_start_date: '',
      supervisor_name: '',
      supervisor_phone: ''
    },
    rental_history: [
      {
        address: '',
        landlord_name: '',
        landlord_phone: '',
        monthly_rent: '',
        lease_start: '',
        lease_end: '',
        reason_for_leaving: ''
      }
    ],
    references: [
      {
        name: '',
        relationship: '',
        phone: '',
        email: ''
      },
      {
        name: '',
        relationship: '',
        phone: '',
        email: ''
      }
    ],
    emergency_contacts: [
      {
        name: '',
        relationship: '',
        phone: '',
        email: ''
      }
    ],
    application_fee_paid: false
  });

  const [decision, setDecision] = useState({
    decision: '',
    notes: '',
    conditions: []
  });

  useEffect(() => {
    fetchDashboardData();
    fetchApplications();
    fetchScreeningCriteria();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/tenant-screening/dashboard');
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchApplications = async () => {
    try {
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (filterProperty) params.append('property_id', filterProperty);

      const response = await fetch(`/api/tenant-screening/applications?${params}`);
      if (response.ok) {
        const data = await response.json();
        setApplications(data.applications || []);
      }
    } catch (error) {
      console.error('Error fetching applications:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchScreeningChecks = async (applicationId = '') => {
    try {
      const params = new URLSearchParams();
      if (applicationId) params.append('application_id', applicationId);

      const response = await fetch(`/api/tenant-screening/checks?${params}`);
      if (response.ok) {
        const data = await response.json();
        setScreeningChecks(data.checks || []);
      }
    } catch (error) {
      console.error('Error fetching screening checks:', error);
    }
  };

  const fetchScreeningCriteria = async () => {
    try {
      const response = await fetch('/api/tenant-screening/criteria');
      if (response.ok) {
        const data = await response.json();
        setScreeningCriteria(data);
      }
    } catch (error) {
      console.error('Error fetching screening criteria:', error);
    }
  };

  const handleSubmitApplication = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/tenant-screening/applications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newApplication)
      });

      if (response.ok) {
        setNewApplication({
          property_id: '',
          unit_id: '',
          personal_info: {
            first_name: '',
            last_name: '',
            email: '',
            phone: '',
            ssn: '',
            date_of_birth: '',
            current_address: ''
          },
          employment_info: {
            employer: '',
            position: '',
            annual_income: '',
            employment_start_date: '',
            supervisor_name: '',
            supervisor_phone: ''
          },
          rental_history: [
            {
              address: '',
              landlord_name: '',
              landlord_phone: '',
              monthly_rent: '',
              lease_start: '',
              lease_end: '',
              reason_for_leaving: ''
            }
          ],
          references: [
            {
              name: '',
              relationship: '',
              phone: '',
              email: ''
            },
            {
              name: '',
              relationship: '',
              phone: '',
              email: ''
            }
          ],
          emergency_contacts: [
            {
              name: '',
              relationship: '',
              phone: '',
              email: ''
            }
          ],
          application_fee_paid: false
        });
        setShowApplicationForm(false);
        fetchApplications();
        fetchDashboardData();
        alert('Application submitted successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to submit application: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error submitting application:', error);
      alert('Failed to submit application');
    }
  };

  const handleApplicationDecision = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`/api/tenant-screening/applications/${selectedApplication.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(decision)
      });

      if (response.ok) {
        setDecision({
          decision: '',
          notes: '',
          conditions: []
        });
        setShowDecisionModal(false);
        setSelectedApplication(null);
        fetchApplications();
        fetchDashboardData();
        alert('Application decision updated successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to update decision: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error updating application decision:', error);
      alert('Failed to update application decision');
    }
  };

  const calculateApplicationScore = async (applicationId) => {
    try {
      const response = await fetch(`/api/tenant-screening/applications/${applicationId}/score`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert(`Application Score: ${data.score_breakdown.overall_score}/${data.score_breakdown.max_possible_score}\nRisk Level: ${data.score_breakdown.risk_level.toUpperCase()}`);
        }
      }
    } catch (error) {
      console.error('Error calculating score:', error);
      alert('Failed to calculate application score');
    }
  };

  const openDecisionModal = (application) => {
    setSelectedApplication(application);
    setDecision({
      decision: '',
      notes: '',
      conditions: []
    });
    setShowDecisionModal(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'conditionally_approved': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'under_review': return 'bg-blue-100 text-blue-800';
      case 'background_check': return 'bg-purple-100 text-purple-800';
      case 'credit_check': return 'bg-indigo-100 text-indigo-800';
      case 'submitted': return 'bg-gray-100 text-gray-800';
      case 'withdrawn': return 'bg-gray-100 text-gray-600';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCheckStatusColor = (status) => {
    switch (status) {
      case 'pass': return 'bg-green-100 text-green-800';
      case 'conditional': return 'bg-yellow-100 text-yellow-800';
      case 'fail': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
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
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Tenant Screening</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowApplicationForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            📋 New Application
          </button>
          <button
            onClick={() => fetchApplications()}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Dashboard Overview */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Applications</h3>
            <p className="text-2xl font-bold text-gray-900">{dashboardData.overview?.total_applications || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Pending Reviews</h3>
            <p className="text-2xl font-bold text-yellow-600">{dashboardData.overview?.pending_reviews || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Completed Screenings</h3>
            <p className="text-2xl font-bold text-blue-600">{dashboardData.overview?.completed_screenings || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Avg Processing Time</h3>
            <p className="text-2xl font-bold text-purple-600">{dashboardData.overview?.avg_processing_days || 0} days</p>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['overview', 'applications', 'screening', 'reports', 'criteria'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && dashboardData && (
        <div className="space-y-6">
          {/* Status Breakdown */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Application Status Breakdown</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(dashboardData.status_breakdown || {}).map(([status, count]) => (
                  <div key={status} className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{count}</div>
                    <div className="text-sm text-gray-500">{status.replace('_', ' ').toUpperCase()}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Applications */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Applications</h3>
            </div>
            <div className="p-6">
              {dashboardData.recent_applications && dashboardData.recent_applications.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData.recent_applications.map((app) => (
                    <div key={app.id} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                      <div>
                        <h4 className="font-medium text-gray-900">{app.applicant_name}</h4>
                        <p className="text-sm text-gray-600">Property {app.property_id} • {new Date(app.submitted_at).toLocaleDateString()}</p>
                      </div>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(app.status)}`}>
                        {app.status.replace('_', ' ')}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No recent applications</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Applications Tab */}
      {activeTab === 'applications' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={filterStatus}
                  onChange={(e) => {
                    setFilterStatus(e.target.value);
                    setTimeout(() => fetchApplications(), 100);
                  }}
                  className="border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="">All Statuses</option>
                  <option value="submitted">Submitted</option>
                  <option value="under_review">Under Review</option>
                  <option value="background_check">Background Check</option>
                  <option value="credit_check">Credit Check</option>
                  <option value="approved">Approved</option>
                  <option value="conditionally_approved">Conditionally Approved</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Property</label>
                <input
                  type="number"
                  value={filterProperty}
                  onChange={(e) => {
                    setFilterProperty(e.target.value);
                    setTimeout(() => fetchApplications(), 100);
                  }}
                  placeholder="Property ID"
                  className="border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
            </div>
          </div>

          {/* Applications Table */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Tenant Applications</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Applicant</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Property</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Income</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Submitted</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {applications.map((application) => (
                    <tr key={application.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{application.applicant_name}</div>
                          <div className="text-sm text-gray-500">{application.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">Property {application.property_id}</div>
                        <div className="text-sm text-gray-500">{application.unit_id || 'No unit specified'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${application.annual_income?.toLocaleString() || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(application.status)}`}>
                          {application.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(application.submitted_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex gap-2">
                          <button
                            onClick={() => calculateApplicationScore(application.id)}
                            className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                          >
                            📊 Score
                          </button>
                          {application.status !== 'approved' && application.status !== 'rejected' && (
                            <button
                              onClick={() => openDecisionModal(application)}
                              className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                            >
                              ✅ Decide
                            </button>
                          )}
                          <button
                            onClick={() => fetchScreeningChecks(application.id)}
                            className="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700"
                          >
                            🔍 Checks
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Screening Tab */}
      {activeTab === 'screening' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Screening Checks</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Application</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Check Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Completed</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {screeningChecks.map((check) => (
                  <tr key={check.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {check.application_id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {check.check_type.replace('_', ' ').toUpperCase()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCheckStatusColor(check.status)}`}>
                        {check.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {check.score !== null ? Math.round(check.score) : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {check.completed_at ? new Date(check.completed_at).toLocaleDateString() : 'Pending'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${check.cost.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Reports Tab */}
      {activeTab === 'reports' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Screening Reports</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">📊 Summary Report</h4>
                <p className="text-sm text-gray-600 mb-4">Overview of all screening activities and metrics</p>
                <button
                  onClick={() => window.open('/api/tenant-screening/reports/summary', '_blank')}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  View Summary
                </button>
              </div>
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">📈 Approval Metrics</h4>
                <p className="text-sm text-gray-600 mb-4">Analysis of approval rates and trends</p>
                <button className="bg-gray-400 text-white px-4 py-2 rounded-md cursor-not-allowed">
                  Coming Soon
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Criteria Tab */}
      {activeTab === 'criteria' && screeningCriteria && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Screening Criteria</h3>
          </div>
          <div className="p-6 space-y-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-4">Application Requirements</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Min Credit Score</label>
                  <div className="mt-1 text-sm text-gray-900">{screeningCriteria.criteria?.min_credit_score}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Max Debt-to-Income Ratio</label>
                  <div className="mt-1 text-sm text-gray-900">{(screeningCriteria.criteria?.max_debt_to_income_ratio * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Min Income Multiplier</label>
                  <div className="mt-1 text-sm text-gray-900">{screeningCriteria.criteria?.min_income_multiplier}x rent</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Required References</label>
                  <div className="mt-1 text-sm text-gray-900">{screeningCriteria.criteria?.require_references}</div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-4">Scoring Model Weights</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Credit Score Weight</label>
                  <div className="mt-1 text-sm text-gray-900">{(screeningCriteria.scoring_model?.credit_score_weight * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Income Weight</label>
                  <div className="mt-1 text-sm text-gray-900">{(screeningCriteria.scoring_model?.income_weight * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Employment Weight</label>
                  <div className="mt-1 text-sm text-gray-900">{(screeningCriteria.scoring_model?.employment_weight * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">References Weight</label>
                  <div className="mt-1 text-sm text-gray-900">{(screeningCriteria.scoring_model?.references_weight * 100).toFixed(1)}%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Application Modal */}
      {showApplicationForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-4xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">New Tenant Application</h3>
            </div>
            <form onSubmit={handleSubmitApplication} className="p-6 space-y-6">
              {/* Property Information */}
              <div>
                <h4 className="font-medium text-gray-900 mb-4">Property Information</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Property ID *</label>
                    <input
                      type="number"
                      value={newApplication.property_id}
                      onChange={(e) => setNewApplication({...newApplication, property_id: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Unit ID</label>
                    <input
                      type="text"
                      value={newApplication.unit_id}
                      onChange={(e) => setNewApplication({...newApplication, unit_id: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              </div>

              {/* Personal Information */}
              <div>
                <h4 className="font-medium text-gray-900 mb-4">Personal Information</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                    <input
                      type="text"
                      value={newApplication.personal_info.first_name}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        personal_info: {...newApplication.personal_info, first_name: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                    <input
                      type="text"
                      value={newApplication.personal_info.last_name}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        personal_info: {...newApplication.personal_info, last_name: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                    <input
                      type="email"
                      value={newApplication.personal_info.email}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        personal_info: {...newApplication.personal_info, email: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
                    <input
                      type="tel"
                      value={newApplication.personal_info.phone}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        personal_info: {...newApplication.personal_info, phone: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">SSN *</label>
                    <input
                      type="text"
                      value={newApplication.personal_info.ssn}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        personal_info: {...newApplication.personal_info, ssn: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="XXX-XX-XXXX"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth *</label>
                    <input
                      type="date"
                      value={newApplication.personal_info.date_of_birth}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        personal_info: {...newApplication.personal_info, date_of_birth: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Employment Information */}
              <div>
                <h4 className="font-medium text-gray-900 mb-4">Employment Information</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Employer *</label>
                    <input
                      type="text"
                      value={newApplication.employment_info.employer}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        employment_info: {...newApplication.employment_info, employer: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Position</label>
                    <input
                      type="text"
                      value={newApplication.employment_info.position}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        employment_info: {...newApplication.employment_info, position: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Annual Income *</label>
                    <input
                      type="number"
                      value={newApplication.employment_info.annual_income}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        employment_info: {...newApplication.employment_info, annual_income: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Employment Start Date *</label>
                    <input
                      type="date"
                      value={newApplication.employment_info.employment_start_date}
                      onChange={(e) => setNewApplication({
                        ...newApplication,
                        employment_info: {...newApplication.employment_info, employment_start_date: e.target.value}
                      })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Submit Application
                </button>
                <button
                  type="button"
                  onClick={() => setShowApplicationForm(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Decision Modal */}
      {showDecisionModal && selectedApplication && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Application Decision: {selectedApplication.applicant_name}
              </h3>
            </div>
            <form onSubmit={handleApplicationDecision} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Decision *</label>
                <select
                  value={decision.decision}
                  onChange={(e) => setDecision({...decision, decision: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                >
                  <option value="">Select Decision</option>
                  <option value="approved">Approved</option>
                  <option value="conditionally_approved">Conditionally Approved</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={decision.notes}
                  onChange={(e) => setDecision({...decision, notes: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  rows="3"
                  placeholder="Decision reasoning and notes..."
                />
              </div>
              {decision.decision === 'conditionally_approved' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Conditions</label>
                  <textarea
                    value={decision.conditions.join('\n')}
                    onChange={(e) => setDecision({...decision, conditions: e.target.value.split('\n').filter(c => c.trim())})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    rows="3"
                    placeholder="Enter each condition on a new line..."
                  />
                </div>
              )}
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Submit Decision
                </button>
                <button
                  type="button"
                  onClick={() => setShowDecisionModal(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TenantScreeningDashboard;