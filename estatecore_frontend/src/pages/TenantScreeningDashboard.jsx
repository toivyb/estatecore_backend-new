import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserCheck,
  UserX,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  CreditCard,
  Shield,
  FileText,
  Eye,
  RefreshCw,
  Download,
  Upload,
  Filter,
  Search,
  Plus,
  Edit,
  BarChart3,
  PieChart,
  Activity,
  DollarSign,
  Calendar,
  Star,
  AlertTriangle
} from 'lucide-react';

const TenantScreeningDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [screeningData, setScreeningData] = useState(null);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isScreening, setIsScreening] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchScreeningData();
  }, []);

  const fetchScreeningData = async () => {
    try {
      setIsLoading(true);
      
      // Mock data - replace with actual API calls
      const mockData = {
        overview: {
          total_applications: 127,
          pending_applications: 18,
          in_progress_applications: 8,
          approved_applications: 89,
          rejected_applications: 12,
          requires_review: 4,
          approval_rate: 0.78,
          rejection_rate: 0.12
        },
        recent_applications: [
          {
            application_id: 'app_001',
            applicant_name: 'Sarah Johnson',
            applicant_email: 'sarah.johnson@email.com',
            property_id: 123,
            monthly_income: 5200,
            desired_move_in_date: '2024-10-15T00:00:00Z',
            status: 'approved',
            submitted_at: '2024-09-27T10:30:00Z',
            credit_summary: {
              credit_score: 742,
              credit_grade: 'good'
            },
            screening_result: {
              overall_score: 85,
              decision: 'approve',
              risk_factors: [],
              positive_factors: ['Excellent credit score', 'Stable employment', 'Strong rental history']
            }
          },
          {
            application_id: 'app_002',
            applicant_name: 'Michael Chen',
            applicant_email: 'michael.chen@email.com',
            property_id: 456,
            monthly_income: 4800,
            desired_move_in_date: '2024-11-01T00:00:00Z',
            status: 'in_progress',
            submitted_at: '2024-09-27T14:15:00Z',
            credit_summary: {
              credit_score: 678,
              credit_grade: 'fair'
            }
          },
          {
            application_id: 'app_003',
            applicant_name: 'Emma Williams',
            applicant_email: 'emma.williams@email.com',
            property_id: 789,
            monthly_income: 3900,
            desired_move_in_date: '2024-10-20T00:00:00Z',
            status: 'requires_review',
            submitted_at: '2024-09-26T16:45:00Z',
            credit_summary: {
              credit_score: 620,
              credit_grade: 'poor'
            },
            screening_result: {
              overall_score: 62,
              decision: 'requires_manual_review',
              risk_factors: ['Low credit score', 'Short employment history'],
              positive_factors: ['No eviction history', 'Good references']
            }
          }
        ],
        status_breakdown: {
          pending: 18,
          in_progress: 8,
          approved: 89,
          rejected: 12,
          requires_review: 4
        },
        credit_distribution: {
          excellent: 45,
          good: 38,
          fair: 28,
          poor: 12,
          bad: 4
        },
        processing_metrics: {
          average_processing_time_hours: 24,
          fastest_processing_time_hours: 4,
          slowest_processing_time_hours: 72,
          applications_processed_today: 5
        },
        trends: {
          applications_growth: 0.12,
          approval_rate_trend: 0.03,
          processing_time_trend: -0.08
        }
      };
      
      setScreeningData(mockData);
      
    } catch (error) {
      console.error('Error fetching screening data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startScreening = async (applicationId) => {
    try {
      setIsScreening(true);
      
      console.log('Starting screening for application:', applicationId);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Update the application status in the list
      setScreeningData(prev => ({
        ...prev,
        recent_applications: prev.recent_applications.map(app => 
          app.application_id === applicationId 
            ? { ...app, status: 'in_progress' }
            : app
        )
      }));
      
      alert('Screening process started successfully!');
      
    } catch (error) {
      console.error('Error starting screening:', error);
      alert('Failed to start screening. Please try again.');
    } finally {
      setIsScreening(false);
    }
  };

  const updateApplicationStatus = async (applicationId, newStatus) => {
    try {
      console.log('Updating application status:', applicationId, newStatus);
      
      // Update the application status in the list
      setScreeningData(prev => ({
        ...prev,
        recent_applications: prev.recent_applications.map(app => 
          app.application_id === applicationId 
            ? { ...app, status: newStatus }
            : app
        )
      }));
      
      alert(`Application status updated to ${newStatus}`);
      
    } catch (error) {
      console.error('Error updating application status:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(new Date(dateString));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'text-green-600 bg-green-100 border-green-200';
      case 'rejected': return 'text-red-600 bg-red-100 border-red-200';
      case 'in_progress': return 'text-blue-600 bg-blue-100 border-blue-200';
      case 'pending': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'requires_review': return 'text-orange-600 bg-orange-100 border-orange-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getCreditGradeColor = (grade) => {
    switch (grade) {
      case 'excellent': return 'text-green-600 bg-green-100';
      case 'good': return 'text-blue-600 bg-blue-100';
      case 'fair': return 'text-yellow-600 bg-yellow-100';
      case 'poor': return 'text-orange-600 bg-orange-100';
      case 'bad': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'rejected': return <XCircle className="w-4 h-4 text-red-600" />;
      case 'in_progress': return <Clock className="w-4 h-4 text-blue-600" />;
      case 'pending': return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      case 'requires_review': return <AlertTriangle className="w-4 h-4 text-orange-600" />;
      default: return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const StatCard = ({ title, value, subtitle, icon: Icon, color = 'blue', trend = null, onClick = null }) => (
    <div 
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 ${onClick ? 'cursor-pointer hover:shadow-lg transition-shadow' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
          )}
          {trend && (
            <div className={`flex items-center mt-2 ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend > 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
              <span className="text-sm font-medium">{Math.abs(trend * 100).toFixed(1)}%</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full bg-${color}-100 dark:bg-${color}-900/20`}>
          <Icon className={`w-6 h-6 text-${color}-600 dark:text-${color}-400`} />
        </div>
      </div>
    </div>
  );

  const ApplicationCard = ({ application }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-medium text-gray-900 dark:text-white">{application.applicant_name}</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">{application.applicant_email}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Property #{application.property_id}</p>
        </div>
        
        <div className="flex flex-col items-end space-y-1">
          <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(application.status)}`}>
            {application.status.replace('_', ' ')}
          </span>
          {application.credit_summary && (
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCreditGradeColor(application.credit_summary.credit_grade)}`}>
              {application.credit_summary.credit_score}
            </span>
          )}
        </div>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">Monthly Income:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {formatCurrency(application.monthly_income)}
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">Move-in Date:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {formatDate(application.desired_move_in_date)}
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">Submitted:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {formatDate(application.submitted_at)}
          </span>
        </div>
        
        {application.screening_result && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-500 dark:text-gray-400">Score:</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {application.screening_result.overall_score}/100
            </span>
          </div>
        )}
      </div>
      
      <div className="flex justify-between space-x-2">
        {application.status === 'pending' && (
          <button
            onClick={() => startScreening(application.application_id)}
            disabled={isScreening}
            className="flex items-center px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isScreening ? (
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
            ) : (
              <Shield className="w-3 h-3 mr-1" />
            )}
            {isScreening ? 'Screening...' : 'Start Screening'}
          </button>
        )}
        
        <button
          onClick={() => setSelectedApplication(application)}
          className="flex items-center px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          <Eye className="w-3 h-3 mr-1" />
          View Details
        </button>
        
        {application.status === 'requires_review' && (
          <div className="flex space-x-1">
            <button
              onClick={() => updateApplicationStatus(application.application_id, 'approved')}
              className="flex items-center px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
            >
              <CheckCircle className="w-3 h-3" />
            </button>
            <button
              onClick={() => updateApplicationStatus(application.application_id, 'rejected')}
              className="flex items-center px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
            >
              <XCircle className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>
    </div>
  );

  const filteredApplications = screeningData?.recent_applications?.filter(app => {
    const matchesSearch = app.applicant_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         app.applicant_email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || app.status === statusFilter;
    return matchesSearch && matchesStatus;
  }) || [];

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Tenant Screening</h1>
              <p className="text-gray-600 dark:text-gray-400">AI-powered tenant screening and credit analysis</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={fetchScreeningData}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Data
              </button>
              <button className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                <Plus className="w-4 h-4 mr-2" />
                New Application
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Stats */}
        {screeningData?.overview && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total Applications"
              value={screeningData.overview.total_applications}
              subtitle="All time"
              icon={Users}
              color="blue"
            />
            <StatCard
              title="Approval Rate"
              value={`${(screeningData.overview.approval_rate * 100).toFixed(0)}%`}
              subtitle="Last 30 days"
              icon={UserCheck}
              color="green"
              trend={screeningData.trends.approval_rate_trend}
            />
            <StatCard
              title="Pending Review"
              value={screeningData.overview.pending_applications + screeningData.overview.requires_review}
              subtitle="Needs attention"
              icon={AlertCircle}
              color="yellow"
            />
            <StatCard
              title="Processing Time"
              value={`${screeningData.processing_metrics.average_processing_time_hours}h`}
              subtitle="Average"
              icon={Clock}
              color="purple"
              trend={screeningData.trends.processing_time_trend}
            />
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: BarChart3 },
                { id: 'applications', label: 'Applications', icon: FileText },
                { id: 'analytics', label: 'Analytics', icon: PieChart },
                { id: 'criteria', label: 'Screening Criteria', icon: Shield }
              ].map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Application Status</h3>
                <div className="space-y-3">
                  {Object.entries(screeningData?.status_breakdown || {}).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(status)}
                        <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                          {status.replace('_', ' ')}
                        </span>
                      </div>
                      <span className="font-medium text-gray-900 dark:text-white">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Credit Score Distribution</h3>
                <div className="space-y-3">
                  {Object.entries(screeningData?.credit_distribution || {}).map(([grade, count]) => (
                    <div key={grade} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <CreditCard className="w-4 h-4" />
                        <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{grade}</span>
                      </div>
                      <span className="font-medium text-gray-900 dark:text-white">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Applications</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {screeningData?.recent_applications?.slice(0, 6).map(application => (
                  <ApplicationCard key={application.application_id} application={application} />
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'applications' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">All Applications</h3>
              
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search applications..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="requires_review">Requires Review</option>
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredApplications.map(application => (
                <ApplicationCard key={application.application_id} application={application} />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Processing Metrics</h3>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Average Processing Time:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {screeningData?.processing_metrics?.average_processing_time_hours}h
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Fastest Processing:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {screeningData?.processing_metrics?.fastest_processing_time_hours}h
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Applications Today:</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {screeningData?.processing_metrics?.applications_processed_today}
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Trends</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Applications Growth:</span>
                    <div className="flex items-center text-green-600">
                      <TrendingUp className="w-4 h-4 mr-1" />
                      <span className="font-medium">
                        {(screeningData?.trends?.applications_growth * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Approval Rate:</span>
                    <div className="flex items-center text-green-600">
                      <TrendingUp className="w-4 h-4 mr-1" />
                      <span className="font-medium">
                        {(screeningData?.trends?.approval_rate_trend * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Processing Time:</span>
                    <div className="flex items-center text-green-600">
                      <TrendingDown className="w-4 h-4 mr-1" />
                      <span className="font-medium">
                        {Math.abs(screeningData?.trends?.processing_time_trend * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Application Details Modal */}
        {selectedApplication && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen px-4">
              <div className="fixed inset-0 bg-black opacity-50" onClick={() => setSelectedApplication(null)}></div>
              <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Application Details
                    </h3>
                    <button
                      onClick={() => setSelectedApplication(null)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                
                <div className="px-6 py-4 max-h-96 overflow-y-auto">
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Applicant Information</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Name:</span>
                            <span className="font-medium">{selectedApplication.applicant_name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Email:</span>
                            <span className="font-medium">{selectedApplication.applicant_email}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Income:</span>
                            <span className="font-medium">{formatCurrency(selectedApplication.monthly_income)}/mo</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Application Status</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Status:</span>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedApplication.status)}`}>
                              {selectedApplication.status.replace('_', ' ')}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Submitted:</span>
                            <span className="font-medium">{formatDate(selectedApplication.submitted_at)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {selectedApplication.credit_summary && (
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Credit Summary</h4>
                        <div className="flex items-center space-x-4">
                          <span className="text-2xl font-bold text-gray-900 dark:text-white">
                            {selectedApplication.credit_summary.credit_score}
                          </span>
                          <span className={`px-3 py-1 text-sm font-medium rounded-full ${getCreditGradeColor(selectedApplication.credit_summary.credit_grade)}`}>
                            {selectedApplication.credit_summary.credit_grade.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    )}
                    
                    {selectedApplication.screening_result && (
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Screening Results</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Overall Score:</span>
                            <span className="text-xl font-bold text-gray-900 dark:text-white">
                              {selectedApplication.screening_result.overall_score}/100
                            </span>
                          </div>
                          
                          {selectedApplication.screening_result.positive_factors?.length > 0 && (
                            <div>
                              <span className="text-sm font-medium text-green-600">Positive Factors:</span>
                              <ul className="mt-1 space-y-1">
                                {selectedApplication.screening_result.positive_factors.map((factor, index) => (
                                  <li key={index} className="text-sm text-gray-600 dark:text-gray-400">• {factor}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {selectedApplication.screening_result.risk_factors?.length > 0 && (
                            <div>
                              <span className="text-sm font-medium text-red-600">Risk Factors:</span>
                              <ul className="mt-1 space-y-1">
                                {selectedApplication.screening_result.risk_factors.map((factor, index) => (
                                  <li key={index} className="text-sm text-gray-600 dark:text-gray-400">• {factor}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
                  {selectedApplication.status === 'requires_review' && (
                    <>
                      <button
                        onClick={() => {
                          updateApplicationStatus(selectedApplication.application_id, 'approved');
                          setSelectedApplication(null);
                        }}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => {
                          updateApplicationStatus(selectedApplication.application_id, 'rejected');
                          setSelectedApplication(null);
                        }}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                      >
                        Reject
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => setSelectedApplication(null)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TenantScreeningDashboard;