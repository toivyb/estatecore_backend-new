import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Toast from './ui/Toast';

const FinancialDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [reports, setReports] = useState([]);
  const [chartsData, setChartsData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [filter, setFilter] = useState({
    period: 'monthly',
    reportType: 'income_statement',
    startDate: '',
    endDate: ''
  });

  // Report type mapping
  const reportTypes = {
    'income_statement': 'Income Statement',
    'cash_flow': 'Cash Flow',
    'rent_roll': 'Rent Roll',
    'vacancy_report': 'Vacancy Analysis',
    'expense_summary': 'Expense Summary',
    'profit_loss': 'Profit & Loss'
  };

  const periodOptions = {
    'monthly': 'Monthly',
    'quarterly': 'Quarterly',
    'yearly': 'Yearly',
    'custom': 'Custom Period'
  };

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/financial/dashboard', {
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

  // Fetch charts data
  const fetchChartsData = async () => {
    try {
      const response = await fetch(`/api/financial/charts-data?period=${filter.period}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setChartsData(result.charts_data || []);
        }
      }
    } catch (error) {
      console.error('Error fetching charts data:', error);
    }
  };

  // Generate financial report
  const generateReport = async (reportData) => {
    setLoading(true);
    try {
      const response = await fetch('/api/financial/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(reportData)
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast(result.message, 'success');
        setSelectedReport(result.report);
        setShowReportModal(false);
        fetchDashboardData();
      } else {
        showToast(result.error || 'Failed to generate report', 'error');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      showToast('Failed to generate report', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Export report
  const exportReport = async (exportData) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/financial/export/${exportData.reportType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({ format: exportData.format })
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast(result.message, 'success');
        setShowExportModal(false);
        
        // Trigger download
        if (result.download_link) {
          window.open(result.download_link, '_blank');
        }
      } else {
        showToast(result.error || 'Failed to export report', 'error');
      }
    } catch (error) {
      console.error('Error exporting report:', error);
      showToast('Failed to export report', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch specific report
  const fetchReport = async (reportType) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        period: filter.period
      });
      
      if (filter.startDate) params.append('start_date', filter.startDate);
      if (filter.endDate) params.append('end_date', filter.endDate);

      const response = await fetch(`/api/financial/reports/${reportType}?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setSelectedReport(result);
        }
      }
    } catch (error) {
      console.error('Error fetching report:', error);
      showToast('Failed to fetch report', 'error');
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
    }).format(amount || 0);
  };

  // Format percentage
  const formatPercentage = (value) => {
    return `${(value || 0).toFixed(1)}%`;
  };

  useEffect(() => {
    fetchDashboardData();
    fetchChartsData();
  }, []);

  useEffect(() => {
    fetchChartsData();
  }, [filter.period]);

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
          <h2 className="text-2xl font-bold text-gray-900">Financial Dashboard</h2>
          <p className="text-gray-600">
            Comprehensive financial reporting and analytics
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={() => setShowReportModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Generate Report
          </Button>
          
          <Button
            onClick={() => setShowExportModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            Export Data
          </Button>
        </div>
      </div>

      {/* Key Financial Metrics */}
      {dashboardData?.overview_metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(dashboardData.overview_metrics.total_revenue)}
                </p>
              </div>
              <div className="text-3xl">💰</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">
                This period
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Net Income</p>
                <p className="text-2xl font-bold text-blue-600">
                  {formatCurrency(dashboardData.overview_metrics.net_income)}
                </p>
              </div>
              <div className="text-3xl">📈</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-green-600 font-medium">
                {formatPercentage(dashboardData.overview_metrics.profit_margin)} profit margin
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Cash Flow</p>
                <p className="text-2xl font-bold text-purple-600">
                  {formatCurrency(dashboardData.overview_metrics.cash_flow)}
                </p>
              </div>
              <div className="text-3xl">🔄</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">
                Operating cash flow
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Occupancy Rate</p>
                <p className="text-2xl font-bold text-orange-600">
                  {formatPercentage(dashboardData.overview_metrics.occupancy_rate)}
                </p>
              </div>
              <div className="text-3xl">🏠</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">
                {dashboardData.quick_stats?.units_count || 0} total units
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'income', label: 'Income Statement', icon: '💹' },
            { id: 'cashflow', label: 'Cash Flow', icon: '💰' },
            { id: 'rentroll', label: 'Rent Roll', icon: '📋' },
            { id: 'expenses', label: 'Expenses', icon: '📉' },
            { id: 'kpis', label: 'KPIs', icon: '🎯' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            {dashboardData?.quick_stats && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Portfolio Overview</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {dashboardData.quick_stats.properties_count}
                    </p>
                    <p className="text-sm text-gray-500">Properties</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">
                      {dashboardData.quick_stats.units_count}
                    </p>
                    <p className="text-sm text-gray-500">Units</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-600">
                      {dashboardData.quick_stats.tenants_count}
                    </p>
                    <p className="text-sm text-gray-500">Tenants</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-orange-600">
                      {dashboardData.quick_stats.maintenance_requests}
                    </p>
                    <p className="text-sm text-gray-500">Open Requests</p>
                  </div>
                </div>
              </Card>
            )}

            {/* Charts */}
            {chartsData.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {chartsData.slice(0, 4).map((chart, index) => (
                  <Card key={index} className="p-6">
                    <h4 className="text-md font-semibold mb-4">{chart.title}</h4>
                    <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
                      <div className="text-center">
                        <div className="text-4xl mb-2">📈</div>
                        <p className="text-gray-500">{chart.title}</p>
                        <p className="text-sm text-gray-400 mt-2">
                          Chart visualization would render here
                        </p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}

            {/* Financial Alerts */}
            {dashboardData?.alerts && dashboardData.alerts.length > 0 && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Financial Alerts</h3>
                <div className="space-y-3">
                  {dashboardData.alerts.map((alert, index) => (
                    <div
                      key={index}
                      className={`p-4 rounded-lg border-l-4 ${
                        alert.severity === 'high' ? 'bg-red-50 border-red-400' :
                        alert.severity === 'medium' ? 'bg-yellow-50 border-yellow-400' :
                        'bg-blue-50 border-blue-400'
                      }`}
                    >
                      <div className="flex">
                        <div className="flex-shrink-0">
                          <span className="text-xl">
                            {alert.type === 'warning' ? '⚠️' : 'ℹ️'}
                          </span>
                        </div>
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-gray-900">
                            {alert.title}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {alert.message}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'kpis' && dashboardData?.kpi_metrics && (
          <div className="space-y-6">
            {/* Financial KPIs */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Financial KPIs</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Object.entries(dashboardData.kpi_metrics.financial_kpis || {}).map(([key, value]) => (
                  <div key={key} className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">
                      {typeof value === 'number' ? formatPercentage(value) : value}
                    </p>
                    <p className="text-sm text-gray-600 capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                  </div>
                ))}
              </div>
            </Card>

            {/* Operational KPIs */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Operational KPIs</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Object.entries(dashboardData.kpi_metrics.operational_kpis || {}).map(([key, value]) => (
                  <div key={key} className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">
                      {key.includes('rate') || key.includes('percentage') ? 
                        formatPercentage(value) : 
                        key.includes('cost') || key.includes('revenue') ? 
                        formatCurrency(value) : value}
                    </p>
                    <p className="text-sm text-gray-600 capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                  </div>
                ))}
              </div>
            </Card>

            {/* Efficiency KPIs */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Efficiency KPIs</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Object.entries(dashboardData.kpi_metrics.efficiency_kpis || {}).map(([key, value]) => (
                  <div key={key} className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">
                      {key.includes('ratio') || key.includes('rate') ? 
                        formatPercentage(value) : 
                        formatCurrency(value)}
                    </p>
                    <p className="text-sm text-gray-600 capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* Other tab content would be implemented here */}
        {activeTab !== 'overview' && activeTab !== 'kpis' && (
          <Card className="p-8 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">
              {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Report
            </h3>
            <p className="text-gray-600 mb-4">
              Click "Generate Report" to view detailed {activeTab} analysis
            </p>
            <Button
              onClick={() => fetchReport(activeTab === 'income' ? 'income_statement' : 
                                      activeTab === 'cashflow' ? 'cash_flow' :
                                      activeTab === 'rentroll' ? 'rent_roll' :
                                      activeTab === 'expenses' ? 'expense_summary' : 'profit_loss')}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Load Report'}
            </Button>
          </Card>
        )}
      </div>

      {/* Recent Reports */}
      {dashboardData?.recent_reports && dashboardData.recent_reports.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Reports</h3>
          <div className="space-y-3">
            {dashboardData.recent_reports.map((report, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-medium">📊</span>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {report.type}
                    </div>
                    <div className="text-sm text-gray-500">
                      {report.period} • {new Date(report.generated_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    report.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {report.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Generate Report Modal */}
      <Modal
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
        title="Generate Financial Report"
      >
        <ReportGenerationForm
          onSubmit={generateReport}
          onCancel={() => setShowReportModal(false)}
          loading={loading}
        />
      </Modal>

      {/* Export Modal */}
      <Modal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title="Export Financial Data"
      >
        <ExportForm
          onSubmit={exportReport}
          onCancel={() => setShowExportModal(false)}
          loading={loading}
        />
      </Modal>
    </div>
  );
};

// Report Generation Form Component
const ReportGenerationForm = ({ onSubmit, onCancel, loading }) => {
  const [reportData, setReportData] = useState({
    report_type: 'income_statement',
    period: 'monthly',
    start_date: '',
    end_date: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(reportData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Report Type
        </label>
        <select
          value={reportData.report_type}
          onChange={(e) => setReportData({ ...reportData, report_type: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="income_statement">Income Statement</option>
          <option value="cash_flow">Cash Flow Statement</option>
          <option value="rent_roll">Rent Roll</option>
          <option value="vacancy_report">Vacancy Analysis</option>
          <option value="expense_summary">Expense Summary</option>
          <option value="profit_loss">Profit & Loss</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Period
        </label>
        <select
          value={reportData.period}
          onChange={(e) => setReportData({ ...reportData, period: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
          <option value="yearly">Yearly</option>
          <option value="custom">Custom Period</option>
        </select>
      </div>

      {reportData.period === 'custom' && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={reportData.start_date}
              onChange={(e) => setReportData({ ...reportData, start_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required={reportData.period === 'custom'}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              End Date
            </label>
            <input
              type="date"
              value={reportData.end_date}
              onChange={(e) => setReportData({ ...reportData, end_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required={reportData.period === 'custom'}
            />
          </div>
        </div>
      )}

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
          {loading ? 'Generating...' : 'Generate Report'}
        </Button>
      </div>
    </form>
  );
};

// Export Form Component
const ExportForm = ({ onSubmit, onCancel, loading }) => {
  const [exportData, setExportData] = useState({
    reportType: 'income_statement',
    format: 'pdf'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(exportData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Report Type
        </label>
        <select
          value={exportData.reportType}
          onChange={(e) => setExportData({ ...exportData, reportType: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="income_statement">Income Statement</option>
          <option value="cash_flow">Cash Flow Statement</option>
          <option value="rent_roll">Rent Roll</option>
          <option value="vacancy_report">Vacancy Analysis</option>
          <option value="expense_summary">Expense Summary</option>
          <option value="profit_loss">Profit & Loss</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Export Format
        </label>
        <select
          value={exportData.format}
          onChange={(e) => setExportData({ ...exportData, format: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="pdf">PDF</option>
          <option value="excel">Excel</option>
          <option value="csv">CSV</option>
        </select>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">Export Information</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• PDF: Formatted report suitable for presentation</li>
          <li>• Excel: Spreadsheet format with data tables</li>
          <li>• CSV: Raw data format for analysis</li>
        </ul>
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
          {loading ? 'Exporting...' : 'Export Report'}
        </Button>
      </div>
    </form>
  );
};

export default FinancialDashboard;