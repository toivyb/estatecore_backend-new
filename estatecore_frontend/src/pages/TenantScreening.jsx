import React, { useState, useEffect } from 'react';

const TenantScreening = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [screeningResults, setScreeningResults] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [currentTab, setCurrentTab] = useState('applications');
  const [filters, setFilters] = useState({
    status: 'all',
    property_id: ''
  });

  // Dialogs
  const [showNewApplicationDialog, setShowNewApplicationDialog] = useState(false);
  const [showScreeningDialog, setShowScreeningDialog] = useState(false);
  const [showDecisionDialog, setShowDecisionDialog] = useState(false);

  // Forms
  const [newApplication, setNewApplication] = useState({
    property_id: '',
    applicant_name: '',
    email: '',
    phone_number: '',
    annual_income: '',
    employment_type: 'full_time',
    credit_score: '',
    monthly_rent_budget: ''
  });

  const [screeningRequest, setScreeningRequest] = useState({
    screening_type: 'comprehensive',
    priority: 'normal'
  });

  const [decision, setDecision] = useState({
    decision: '',
    notes: '',
    security_deposit_multiplier: 1.0
  });

  useEffect(() => {
    loadApplications();
    loadAnalytics();
  }, [filters]);

  const loadApplications = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();
      
      if (filters.status !== 'all') {
        queryParams.append('status', filters.status);
      }
      if (filters.property_id) {
        queryParams.append('property_id', filters.property_id);
      }

      const response = await fetch(`/api/tenant-screening/applications?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setApplications(data.applications || []);
      } else {
        console.error('Failed to load applications');
        setApplications([]);
      }
    } catch (error) {
      console.error('Error loading applications:', error);
      setApplications([]);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await fetch('/api/tenant-screening/analytics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const handleCreateApplication = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/tenant-screening/applications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newApplication)
      });

      if (response.ok) {
        setShowNewApplicationDialog(false);
        setNewApplication({
          property_id: '',
          applicant_name: '',
          email: '',
          phone_number: '',
          annual_income: '',
          employment_type: 'full_time',
          credit_score: '',
          monthly_rent_budget: ''
        });
        loadApplications();
        alert('Application created successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to create application: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating application:', error);
      alert('Failed to create application. Please try again.');
    }
  };

  const handleRunScreening = async () => {
    if (!selectedApplication) return;

    try {
      setLoading(true);
      const response = await fetch('/api/tenant-screening/screen', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          application_id: selectedApplication.application_id,
          ...screeningRequest
        })
      });

      if (response.ok) {
        const data = await response.json();
        setScreeningResults(data);
        setShowScreeningDialog(false);
        loadApplications();
        alert('Screening completed successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to run screening: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error running screening:', error);
      alert('Failed to run screening. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMakeDecision = async () => {
    if (!screeningResults) return;

    try {
      const response = await fetch(`/api/tenant-screening/screenings/${screeningResults.screening_id}/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(decision)
      });

      if (response.ok) {
        setShowDecisionDialog(false);
        setDecision({
          decision: '',
          notes: '',
          security_deposit_multiplier: 1.0
        });
        loadApplications();
        alert('Decision recorded successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to record decision: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error making decision:', error);
      alert('Failed to record decision. Please try again.');
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'low': return 'text-green-800 bg-green-100';
      case 'medium': return 'text-yellow-800 bg-yellow-100';
      case 'high': return 'text-red-800 bg-red-100';
      case 'critical': return 'text-red-800 bg-red-200';
      default: return 'text-gray-800 bg-gray-100';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'text-green-800 bg-green-100';
      case 'conditionally_approved': return 'text-blue-800 bg-blue-100';
      case 'declined': return 'text-red-800 bg-red-100';
      case 'under_review': return 'text-yellow-800 bg-yellow-100';
      case 'submitted': return 'text-gray-800 bg-gray-100';
      default: return 'text-gray-800 bg-gray-100';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount || 0);
  };

  const ApplicationsTab = () => (
    <div>
      {/* Filters and Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 space-y-4 sm:space-y-0">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex flex-col">
            <label className="text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All</option>
              <option value="submitted">Submitted</option>
              <option value="under_review">Under Review</option>
              <option value="approved">Approved</option>
              <option value="conditionally_approved">Conditionally Approved</option>
              <option value="declined">Declined</option>
            </select>
          </div>
          
          <div className="flex flex-col">
            <label className="text-sm font-medium text-gray-700 mb-1">Property ID</label>
            <input
              type="text"
              value={filters.property_id}
              onChange={(e) => setFilters(prev => ({ ...prev, property_id: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter Property ID"
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={loadApplications}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              🔍 Apply Filters
            </button>
          </div>
        </div>

        <button
          onClick={() => setShowNewApplicationDialog(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          ➕ New Application
        </button>
      </div>

      {/* Applications Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Applicant
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Property
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Income
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Applied
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Screening
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center">
                    <div className="flex justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                    <p className="mt-2 text-gray-500">Loading applications...</p>
                  </td>
                </tr>
              ) : applications.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                    No applications found. Create your first application to get started.
                  </td>
                </tr>
              ) : (
                applications.map((app) => (
                  <tr key={app.application_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {app.applicant_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {app.email}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {app.property_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(app.annual_income)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(app.status)}`}>
                        {(app.status || 'submitted').replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(app.application_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {app.latest_screening ? (
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            Score: {app.latest_screening.overall_score?.toFixed(1) || 'N/A'}/100
                          </div>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskLevelColor(app.latest_screening.risk_level)}`}>
                            {app.latest_screening.risk_level || 'unknown'}
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">Not screened</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => {
                          setSelectedApplication(app);
                          setShowScreeningDialog(true);
                        }}
                        className="text-blue-600 hover:text-blue-900"
                        title="Run Screening"
                      >
                        🔍 Screen
                      </button>
                      <button
                        onClick={() => setSelectedApplication(app)}
                        className="text-green-600 hover:text-green-900"
                        title="View Details"
                      >
                        👁️ View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const AnalyticsTab = () => {
    if (!analytics) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2">Loading analytics...</span>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Applications</h3>
            <p className="text-2xl font-bold text-gray-900">
              {analytics.volume_metrics?.total_applications || 0}
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Approval Rate</h3>
            <p className="text-2xl font-bold text-green-600">
              {(analytics.decision_metrics?.approval_rate || 0).toFixed(1)}%
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Avg Processing Time</h3>
            <p className="text-2xl font-bold text-blue-600">
              {(analytics.performance_metrics?.average_processing_time_seconds || 0).toFixed(1)}s
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">System Health</h3>
            <p className="text-2xl font-bold text-green-600">
              {analytics.system_health?.operational_status || 'Unknown'}
            </p>
          </div>
        </div>

        {/* Decision Breakdown */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {analytics.decision_metrics?.approved_count || 0}
              </div>
              <div className="text-sm text-gray-500">Approved</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {analytics.decision_metrics?.conditional_approved_count || 0}
              </div>
              <div className="text-sm text-gray-500">Conditional</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {analytics.decision_metrics?.declined_count || 0}
              </div>
              <div className="text-sm text-gray-500">Declined</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {analytics.decision_metrics?.cosigner_required_count || 0}
              </div>
              <div className="text-sm text-gray-500">Cosigner Req.</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI-Powered Tenant Screening</h1>
          <p className="text-gray-600">Intelligent tenant evaluation and risk assessment system</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setCurrentTab('applications')}
            className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
              currentTab === 'applications'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Applications
          </button>
          <button
            onClick={() => setCurrentTab('analytics')}
            className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm ${
              currentTab === 'analytics'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Analytics
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {currentTab === 'applications' && <ApplicationsTab />}
      {currentTab === 'analytics' && <AnalyticsTab />}

      {/* New Application Dialog */}
      {showNewApplicationDialog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-md shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">New Tenant Application</h3>
              <form onSubmit={handleCreateApplication} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Property ID</label>
                  <input
                    type="text"
                    required
                    value={newApplication.property_id}
                    onChange={(e) => setNewApplication(prev => ({ ...prev, property_id: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Applicant Name</label>
                  <input
                    type="text"
                    required
                    value={newApplication.applicant_name}
                    onChange={(e) => setNewApplication(prev => ({ ...prev, applicant_name: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <input
                    type="email"
                    required
                    value={newApplication.email}
                    onChange={(e) => setNewApplication(prev => ({ ...prev, email: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Phone Number</label>
                  <input
                    type="tel"
                    value={newApplication.phone_number}
                    onChange={(e) => setNewApplication(prev => ({ ...prev, phone_number: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Annual Income</label>
                  <input
                    type="number"
                    required
                    value={newApplication.annual_income}
                    onChange={(e) => setNewApplication(prev => ({ ...prev, annual_income: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Employment Type</label>
                  <select
                    value={newApplication.employment_type}
                    onChange={(e) => setNewApplication(prev => ({ ...prev, employment_type: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="full_time">Full Time</option>
                    <option value="part_time">Part Time</option>
                    <option value="contract">Contract</option>
                    <option value="self_employed">Self Employed</option>
                    <option value="unemployed">Unemployed</option>
                  </select>
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowNewApplicationDialog(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                  >
                    Create Application
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Screening Dialog */}
      {showScreeningDialog && selectedApplication && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-md shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Run AI Screening</h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium">Applicant: {selectedApplication.applicant_name}</h4>
                  <p className="text-sm text-gray-600">Property: {selectedApplication.property_id}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Screening Type</label>
                  <select
                    value={screeningRequest.screening_type}
                    onChange={(e) => setScreeningRequest(prev => ({ ...prev, screening_type: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="basic">Basic</option>
                    <option value="comprehensive">Comprehensive</option>
                    <option value="express">Express</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Priority</label>
                  <select
                    value={screeningRequest.priority}
                    onChange={(e) => setScreeningRequest(prev => ({ ...prev, priority: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <button
                    onClick={() => setShowScreeningDialog(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleRunScreening}
                    disabled={loading}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? 'Running...' : 'Run Screening'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Screening Results Dialog */}
      {screeningResults && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Screening Results</h3>
                <button
                  onClick={() => setScreeningResults(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              {screeningResults.success ? (
                <div className="space-y-6">
                  {/* Overall Score */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium mb-2">
                      Overall Score: {screeningResults.score?.overall_score?.toFixed(1) || 'N/A'}/100
                    </h4>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div 
                        className="bg-blue-600 h-2.5 rounded-full" 
                        style={{ width: `${screeningResults.score?.overall_score || 0}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between mt-2">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskLevelColor(screeningResults.score?.risk_level)}`}>
                        Risk: {screeningResults.score?.risk_level || 'unknown'}
                      </span>
                      <span className="text-sm text-gray-600">
                        Confidence: {((screeningResults.score?.confidence || 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Score Breakdown */}
                  <div>
                    <h4 className="font-medium mb-3">Score Breakdown</h4>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { label: 'Credit', value: screeningResults.score?.credit_score },
                        { label: 'Income', value: screeningResults.score?.income_score },
                        { label: 'Rental History', value: screeningResults.score?.rental_history_score },
                        { label: 'Employment', value: screeningResults.score?.employment_score }
                      ].map((item, index) => (
                        <div key={index}>
                          <div className="flex justify-between text-sm">
                            <span>{item.label}</span>
                            <span>{(item.value || 0).toFixed(1)}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                            <div 
                              className="bg-green-600 h-1.5 rounded-full" 
                              style={{ width: `${item.value || 0}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* AI Insights */}
                  {screeningResults.insights && (
                    <div>
                      <h4 className="font-medium mb-3">AI Insights</h4>
                      
                      {screeningResults.insights.strengths?.length > 0 && (
                        <div className="mb-3">
                          <h5 className="text-sm font-medium text-green-700 mb-1">Strengths:</h5>
                          <ul className="text-sm space-y-1">
                            {screeningResults.insights.strengths.map((strength, index) => (
                              <li key={index} className="text-gray-700">• {strength}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {screeningResults.insights.concerns?.length > 0 && (
                        <div className="mb-3">
                          <h5 className="text-sm font-medium text-red-700 mb-1">Concerns:</h5>
                          <ul className="text-sm space-y-1">
                            {screeningResults.insights.concerns.map((concern, index) => (
                              <li key={index} className="text-gray-700">• {concern}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {screeningResults.recommendations?.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-blue-700 mb-1">Recommendations:</h5>
                          <ul className="text-sm space-y-1">
                            {screeningResults.recommendations.map((recommendation, index) => (
                              <li key={index} className="text-gray-700">• {recommendation}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="flex justify-end space-x-2 pt-4 border-t">
                    <button
                      onClick={() => setScreeningResults(null)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                    >
                      Close
                    </button>
                    <button
                      onClick={() => {
                        setShowDecisionDialog(true);
                        setScreeningResults(null);
                      }}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                    >
                      Make Decision
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-red-600 text-lg mb-2">⚠️</div>
                  <p className="text-gray-700">Screening failed: {screeningResults.error || 'Unknown error'}</p>
                  <button
                    onClick={() => setScreeningResults(null)}
                    className="mt-4 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
                  >
                    Close
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Decision Dialog */}
      {showDecisionDialog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-md shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Make Final Decision</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Decision</label>
                  <select
                    value={decision.decision}
                    onChange={(e) => setDecision(prev => ({ ...prev, decision: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Decision</option>
                    <option value="approve">Approve</option>
                    <option value="conditional_approve">Conditional Approve</option>
                    <option value="decline">Decline</option>
                    <option value="require_cosigner">Require Cosigner</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Decision Notes</label>
                  <textarea
                    rows={4}
                    value={decision.notes}
                    onChange={(e) => setDecision(prev => ({ ...prev, notes: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter decision rationale..."
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-4">
                  <button
                    onClick={() => setShowDecisionDialog(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleMakeDecision}
                    disabled={!decision.decision}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    Confirm Decision
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TenantScreening;