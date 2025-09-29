import React, { useState, useEffect } from 'react';

const AdvancedAnalyticsDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [propertyAnalytics, setPropertyAnalytics] = useState(null);
  const [financialAnalytics, setFinancialAnalytics] = useState(null);
  const [maintenanceAnalytics, setMaintenanceAnalytics] = useState(null);
  const [recentReports, setRecentReports] = useState([]);

  useEffect(() => {
    loadDashboardData();
    loadRecentReports();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/analytics/dashboard-overview');
      const result = await response.json();
      
      if (result.success) {
        setDashboardData(result.dashboard);
      } else {
        console.error('Failed to load dashboard data:', result.error);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentReports = async () => {
    try {
      const response = await fetch('/api/analytics/reports');
      const result = await response.json();
      
      if (result.success) {
        setRecentReports(result.reports);
      }
    } catch (error) {
      console.error('Error loading recent reports:', error);
    }
  };

  const loadPropertyAnalytics = async (timeFrame = 'monthly') => {
    setLoading(true);
    try {
      const response = await fetch(`/api/analytics/property-performance?time_frame=${timeFrame}`);
      const result = await response.json();
      
      if (result.success) {
        setPropertyAnalytics(result.analytics);
      }
    } catch (error) {
      console.error('Error loading property analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFinancialAnalytics = async (timeFrame = 'quarterly') => {
    setLoading(true);
    try {
      const response = await fetch(`/api/analytics/financial-trends?time_frame=${timeFrame}`);
      const result = await response.json();
      
      if (result.success) {
        setFinancialAnalytics(result.analytics);
      }
    } catch (error) {
      console.error('Error loading financial analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMaintenanceAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/analytics/predictive-maintenance');
      const result = await response.json();
      
      if (result.success) {
        setMaintenanceAnalytics(result.analytics);
      }
    } catch (error) {
      console.error('Error loading maintenance analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  const getMetricChangeIcon = (changePercent) => {
    if (changePercent > 0) return '📈';
    if (changePercent < 0) return '📉';
    return '➡️';
  };

  const getMetricChangeColor = (changePercent) => {
    if (changePercent > 0) return 'text-green-600 dark:text-green-400';
    if (changePercent < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const MetricCard = ({ metric }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {metric.name}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {metric.unit === '$' ? formatCurrency(metric.value) : 
             metric.unit === '%' ? formatPercentage(metric.value) :
             metric.value.toFixed(2)}
          </p>
        </div>
        <div className="text-right">
          <div className={`flex items-center ${getMetricChangeColor(metric.change_percent)}`}>
            <span className="mr-1">{getMetricChangeIcon(metric.change_percent)}</span>
            <span className="text-sm font-medium">
              {Math.abs(metric.change_percent).toFixed(1)}%
            </span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Confidence: {(metric.confidence_score * 100).toFixed(0)}%
          </p>
        </div>
      </div>
      <div className="mt-2">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {metric.data_points} data points • Updated {formatDate(metric.last_updated)}
        </p>
      </div>
    </div>
  );

  const InsightCard = ({ insight }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {insight.title}
          </h4>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {insight.description}
          </p>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Probability</p>
              <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                {(insight.probability * 100).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Time Horizon</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {insight.time_horizon}
              </p>
            </div>
          </div>
          
          {insight.recommendations && (
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                Recommendations:
              </p>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                {insight.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <div className="ml-4">
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
            insight.probability > 0.7 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
            insight.probability > 0.5 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
            'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
          }`}>
            {insight.probability > 0.7 ? 'High Confidence' :
             insight.probability > 0.5 ? 'Medium Confidence' : 'Low Confidence'}
          </span>
        </div>
      </div>
    </div>
  );

  const ChartCard = ({ title, data, type = 'bar' }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        {title}
      </h4>
      
      {/* Simple chart representation */}
      <div className="space-y-3">
        {data.labels && data.values && data.labels.map((label, index) => {
          const value = data.values[index];
          const maxValue = Math.max(...data.values);
          const percentage = (value / maxValue) * 100;
          
          return (
            <div key={index} className="flex items-center">
              <div className="w-20 text-sm text-gray-600 dark:text-gray-400">
                {label}
              </div>
              <div className="flex-1 mx-3">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
              <div className="w-16 text-sm font-medium text-gray-900 dark:text-gray-100 text-right">
                {typeof value === 'number' ? 
                  (value % 1 === 0 ? value : value.toFixed(1)) : 
                  value}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  if (loading && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading Advanced Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            📊 Advanced Analytics & Reporting
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            AI-powered insights and predictive analytics for property portfolio optimization
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-8">
          <div className="flex space-x-1 bg-white dark:bg-gray-800 rounded-lg p-1 shadow">
            {[
              { id: 'overview', label: '🏠 Overview', action: loadDashboardData },
              { id: 'property', label: '🏢 Property Performance', action: () => loadPropertyAnalytics() },
              { id: 'financial', label: '💰 Financial Trends', action: () => loadFinancialAnalytics() },
              { id: 'maintenance', label: '🔧 Predictive Maintenance', action: () => loadMaintenanceAnalytics() },
              { id: 'reports', label: '📋 Reports', action: loadRecentReports }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  if (tab.action) tab.action();
                }}
                className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'overview' && dashboardData && (
          <div className="space-y-8">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Reports Generated</h3>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {dashboardData.summary.total_reports_generated}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">This session</p>
              </div>
              
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Accuracy Score</h3>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {(dashboardData.summary.accuracy_score * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Model accuracy</p>
              </div>
              
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Data Freshness</h3>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {dashboardData.summary.data_freshness}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Live updates</p>
              </div>
              
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Last Updated</h3>
                <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {formatDate(dashboardData.summary.last_updated)}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">System time</p>
              </div>
            </div>

            {/* Key Insights */}
            {dashboardData.key_insights && dashboardData.key_insights.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  🔍 Key Insights
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {dashboardData.key_insights.slice(0, 4).map((insight, index) => (
                    <InsightCard key={index} insight={insight} />
                  ))}
                </div>
              </div>
            )}

            {/* Charts Overview */}
            {dashboardData.charts_overview && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  📈 Analytics Overview
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <ChartCard 
                    title="Property ROI Trend" 
                    data={dashboardData.charts_overview.property_performance.roi_trend}
                  />
                  <ChartCard 
                    title="Revenue Breakdown" 
                    data={dashboardData.charts_overview.property_performance.occupancy_summary}
                  />
                  <ChartCard 
                    title="Maintenance Categories" 
                    data={dashboardData.charts_overview.maintenance_patterns.categories}
                  />
                </div>
              </div>
            )}

            {/* Recent Reports */}
            {dashboardData.recent_reports && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  📄 Recent Reports
                </h2>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Report
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Generated
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {dashboardData.recent_reports.map((report) => (
                          <tr key={report.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                {report.title}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                ID: {report.id}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                                {report.type.replace('_', ' ')}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {formatDate(report.generated_at)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <button className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">
                                View Details
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Property Performance Tab */}
        {activeTab === 'property' && propertyAnalytics && (
          <div className="space-y-8">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Property Performance Analytics
              </h2>
              <div className="flex space-x-2">
                <select 
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  onChange={(e) => loadPropertyAnalytics(e.target.value)}
                >
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {propertyAnalytics.key_metrics.map((metric, index) => (
                <MetricCard key={index} metric={metric} />
              ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartCard 
                title="ROI Trend" 
                data={propertyAnalytics.charts_data.roi_trend}
              />
              <ChartCard 
                title="Occupancy Distribution" 
                data={propertyAnalytics.charts_data.occupancy_distribution}
              />
            </div>

            {/* Insights */}
            {propertyAnalytics.insights && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Predictive Insights
                </h3>
                <div className="space-y-6">
                  {propertyAnalytics.insights.map((insight, index) => (
                    <InsightCard key={index} insight={insight} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Financial Trends Tab */}
        {activeTab === 'financial' && financialAnalytics && (
          <div className="space-y-8">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Financial Trends Analytics
              </h2>
              <div className="flex space-x-2">
                <select 
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  onChange={(e) => loadFinancialAnalytics(e.target.value)}
                >
                  <option value="quarterly">Quarterly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {financialAnalytics.key_metrics.map((metric, index) => (
                <MetricCard key={index} metric={metric} />
              ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartCard 
                title="Revenue Trend" 
                data={financialAnalytics.charts_data.revenue_trend}
              />
              <ChartCard 
                title="Expense Breakdown" 
                data={financialAnalytics.charts_data.expense_breakdown}
              />
            </div>

            {/* Insights */}
            {financialAnalytics.insights && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Financial Insights
                </h3>
                <div className="space-y-6">
                  {financialAnalytics.insights.map((insight, index) => (
                    <InsightCard key={index} insight={insight} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Maintenance Tab */}
        {activeTab === 'maintenance' && maintenanceAnalytics && (
          <div className="space-y-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Predictive Maintenance Analytics
            </h2>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {maintenanceAnalytics.key_metrics.map((metric, index) => (
                <MetricCard key={index} metric={metric} />
              ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartCard 
                title="Maintenance Categories" 
                data={maintenanceAnalytics.charts_data.maintenance_categories}
              />
              <ChartCard 
                title="Cost Trend" 
                data={maintenanceAnalytics.charts_data.cost_trend}
              />
            </div>

            {/* Insights */}
            {maintenanceAnalytics.insights && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Maintenance Insights
                </h3>
                <div className="space-y-6">
                  {maintenanceAnalytics.insights.map((insight, index) => (
                    <InsightCard key={index} insight={insight} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Analytics Reports
              </h2>
              <button 
                onClick={loadRecentReports}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                🔄 Refresh
              </button>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Report
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Generated
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {recentReports.map((report) => (
                      <tr key={report.report_id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {report.title}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {report.report_id}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                            {report.report_type.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            report.status === 'active' 
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          }`}>
                            {report.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(report.generated_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">
                              View
                            </button>
                            <button className="text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300">
                              Download
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {recentReports.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <p className="text-lg mb-2">📄 No reports available</p>
                  <p>Generate some analytics reports to see them here.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedAnalyticsDashboard;