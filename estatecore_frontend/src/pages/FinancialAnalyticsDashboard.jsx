import React, { useState, useEffect } from 'react';

const FinancialAnalyticsDashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState(30);
  const [selectedProperties, setSelectedProperties] = useState('all');
  const [reportsData, setReportsData] = useState([]);
  const [budgetsData, setBudgetsData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    fetchReports();
    fetchBudgets();
  }, [selectedPeriod, selectedProperties]);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      
      // Mock data - replace with actual API calls
      const mockDashboardData = {
        period: {
          start_date: new Date(Date.now() - selectedPeriod * 24 * 60 * 60 * 1000).toISOString(),
          end_date: new Date().toISOString(),
          days: selectedPeriod
        },
        summary: {
          total_income: 285600,
          total_expenses: 142800,
          net_income: 142800,
          net_margin: 0.50
        },
        income_breakdown: {
          rent_income: 240000,
          late_fees: 8500,
          other_income: 37100
        },
        expense_breakdown: {
          maintenance: 45200,
          utilities: 32800,
          insurance: 28400,
          property_tax: 36400
        },
        monthly_trends: [
          { month: '2024-07', income: 95200, expenses: 47600, net_income: 47600 },
          { month: '2024-08', income: 98400, expenses: 49200, net_income: 49200 },
          { month: '2024-09', income: 91800, expenses: 46000, net_income: 45800 }
        ],
        occupancy_metrics: {
          occupancy_rate: 92.5,
          average_rent: 2350,
          vacancy_loss: 1200,
          total_units: 156,
          occupied_units: 144,
          vacant_units: 12
        },
        kpis: {
          gross_rental_yield: 8.5,
          net_operating_income: 142800,
          cap_rate: 6.2,
          cash_on_cash_return: 12.8,
          expense_ratio: 0.50,
          rent_growth_rate: 3.2
        }
      };
      
      setDashboardData(mockDashboardData);
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchReports = async () => {
    try {
      // Mock reports data
      const mockReports = [
        {
          report_id: 'rpt_001',
          report_type: 'income_statement',
          period_start: '2024-07-01T00:00:00Z',
          period_end: '2024-09-30T00:00:00Z',
          generated_at: '2024-09-28T10:30:00Z',
          summary: { total_income: 285600, total_expenses: 142800, net_income: 142800 }
        },
        {
          report_id: 'rpt_002',
          report_type: 'cash_flow',
          period_start: '2024-09-01T00:00:00Z',
          period_end: '2024-09-30T00:00:00Z',
          generated_at: '2024-09-28T14:15:00Z',
          summary: { net_operating_cash_flow: 48500, net_cash_flow: 41000 }
        }
      ];
      
      setReportsData(mockReports);
      
    } catch (error) {
      console.error('Error fetching reports:', error);
    }
  };

  const fetchBudgets = async () => {
    try {
      // Mock budgets data
      const mockBudgets = [
        {
          budget_id: 'bgt_001',
          property_id: 123,
          year: 2024,
          budget_data: { rental_income: 300000, maintenance: 50000, utilities: 35000 },
          actual_data: { rental_income: 285600, maintenance: 45200, utilities: 32800 },
          variance_data: { rental_income: -14400, maintenance: -4800, utilities: -2200 }
        }
      ];
      
      setBudgetsData(mockBudgets);
      
    } catch (error) {
      console.error('Error fetching budgets:', error);
    }
  };

  const generateReport = async (reportType) => {
    try {
      setIsGeneratingReport(true);
      
      // Mock report generation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      console.log('Generating report:', reportType);
      alert(`${reportType.replace('_', ' ')} report generated successfully!`);
      
      // Refresh reports list
      await fetchReports();
      
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Failed to generate report. Please try again.');
    } finally {
      setIsGeneratingReport(false);
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

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatDate = (dateString) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(new Date(dateString));
  };

  const getVarianceColor = (variance) => {
    if (variance > 0) return 'text-green-600 bg-green-100';
    if (variance < 0) return 'text-red-600 bg-red-100';
    return 'text-gray-600 bg-gray-100';
  };

  const MetricCard = ({ title, value, subtitle, icon, color = 'blue', trend = null, onClick = null }) => (
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
              <span className="text-xl mr-1">{trend > 0 ? '📈' : '📉'}</span>
              <span className="text-sm font-medium">{Math.abs(trend).toFixed(1)}%</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full bg-${color}-100 dark:bg-${color}-900/20`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </div>
  );

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
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Financial Analytics</h1>
              <p className="text-gray-600 dark:text-gray-400">Comprehensive financial reporting and analytics</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(Number(e.target.value))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
              
              <button
                onClick={fetchDashboardData}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <span className="text-lg mr-2">🔄</span>
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Metrics */}
        {dashboardData?.summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Total Income"
              value={formatCurrency(dashboardData.summary.total_income)}
              subtitle={`Last ${selectedPeriod} days`}
              icon="💰"
              color="green"
            />
            <MetricCard
              title="Total Expenses"
              value={formatCurrency(dashboardData.summary.total_expenses)}
              subtitle="Operating costs"
              icon="📄"
              color="red"
            />
            <MetricCard
              title="Net Income"
              value={formatCurrency(dashboardData.summary.net_income)}
              subtitle={`${formatPercentage(dashboardData.summary.net_margin)} margin`}
              icon="📈"
              color="blue"
              trend={5.2}
            />
            <MetricCard
              title="Cash Flow"
              value={formatCurrency(dashboardData.summary.net_income * 0.85)}
              subtitle="After financing"
              icon="📊"
              color="purple"
            />
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'dashboard', label: 'Dashboard', icon: '📊' },
                { id: 'income-expenses', label: 'Income & Expenses', icon: '🥧' },
                { id: 'reports', label: 'Reports', icon: '📄' },
                { id: 'budgets', label: 'Budgets', icon: '🎯' },
                { id: 'trends', label: 'Trends', icon: '📈' }
              ].map(tab => {
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
                    <span className="text-lg mr-2">{tab.icon}</span>
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'dashboard' && dashboardData && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* KPIs */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Key Performance Indicators</h3>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Cap Rate:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{dashboardData.kpis.cap_rate}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Cash-on-Cash Return:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{dashboardData.kpis.cash_on_cash_return}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Expense Ratio:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{formatPercentage(dashboardData.kpis.expense_ratio)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Rent Growth Rate:</span>
                    <span className="font-medium text-green-600">{dashboardData.kpis.rent_growth_rate}%</span>
                  </div>
                </div>
              </div>

              {/* Occupancy Metrics */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Occupancy Overview</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Occupancy Rate:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{dashboardData.occupancy_metrics.occupancy_rate}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${dashboardData.occupancy_metrics.occupancy_rate}%` }}
                    ></div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">{dashboardData.occupancy_metrics.total_units}</div>
                      <div className="text-xs text-gray-500">Total Units</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-green-600">{dashboardData.occupancy_metrics.occupied_units}</div>
                      <div className="text-xs text-gray-500">Occupied</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-orange-600">{dashboardData.occupancy_metrics.vacant_units}</div>
                      <div className="text-xs text-gray-500">Vacant</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Monthly Trends */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Monthly Trends</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {dashboardData.monthly_trends.map((month, index) => (
                  <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                      {new Date(month.month + '-01').toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-500">Income:</span>
                        <span className="text-xs font-medium text-green-600">{formatCurrency(month.income)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-500">Expenses:</span>
                        <span className="text-xs font-medium text-red-600">{formatCurrency(month.expenses)}</span>
                      </div>
                      <div className="flex justify-between border-t border-gray-200 pt-2">
                        <span className="text-xs font-medium text-gray-700">Net:</span>
                        <span className="text-xs font-bold text-blue-600">{formatCurrency(month.net_income)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'income-expenses' && dashboardData && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Income Breakdown */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Income Breakdown</h3>
                <div className="space-y-3">
                  {Object.entries(dashboardData.income_breakdown).map(([category, amount]) => {
                    const percentage = (amount / dashboardData.summary.total_income) * 100;
                    return (
                      <div key={category}>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                            {category.replace('_', ' ')}
                          </span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {formatCurrency(amount)} ({percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Expense Breakdown */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Expense Breakdown</h3>
                <div className="space-y-3">
                  {Object.entries(dashboardData.expense_breakdown).map(([category, amount]) => {
                    const percentage = (amount / dashboardData.summary.total_expenses) * 100;
                    return (
                      <div key={category}>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                            {category.replace('_', ' ')}
                          </span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {formatCurrency(amount)} ({percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-red-600 h-2 rounded-full" 
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Financial Reports</h3>
              
              <div className="flex items-center space-x-4">
                <select 
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  onChange={(e) => e.target.value && generateReport(e.target.value)}
                  value=""
                >
                  <option value="">Generate Report</option>
                  <option value="income_statement">Income Statement</option>
                  <option value="cash_flow">Cash Flow Report</option>
                  <option value="rent_roll">Rent Roll</option>
                  <option value="expense_analysis">Expense Analysis</option>
                  <option value="portfolio_performance">Portfolio Performance</option>
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 gap-4">
              {reportsData.map(report => (
                <div key={report.report_id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white capitalize">
                        {report.report_type.replace('_', ' ')} Report
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(report.period_start)} - {formatDate(report.period_end)}
                      </p>
                      <p className="text-xs text-gray-500">
                        Generated on {formatDate(report.generated_at)}
                      </p>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      {report.summary && (
                        <div className="text-right">
                          {report.summary.total_income && (
                            <div className="text-sm font-medium text-green-600">
                              Income: {formatCurrency(report.summary.total_income)}
                            </div>
                          )}
                          {report.summary.net_income && (
                            <div className="text-sm font-medium text-blue-600">
                              Net: {formatCurrency(report.summary.net_income)}
                            </div>
                          )}
                        </div>
                      )}
                      
                      <button className="flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                        <span className="text-lg mr-1">📥</span>
                        Download
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'budgets' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Budget Management</h3>
              
              <button className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                <span className="text-lg mr-2">➕</span>
                Create Budget
              </button>
            </div>
            
            <div className="grid grid-cols-1 gap-6">
              {budgetsData.map(budget => (
                <div key={budget.budget_id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        Property {budget.property_id} - {budget.year} Budget
                      </h4>
                    </div>
                    
                    <button className="flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                      <span className="text-lg mr-1">🧮</span>
                      View Analysis
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(budget.budget_data).map(([category, budgeted]) => {
                      const actual = budget.actual_data?.[category] || 0;
                      const variance = budget.variance_data?.[category] || 0;
                      const variancePercent = budgeted !== 0 ? (variance / budgeted) * 100 : 0;
                      
                      return (
                        <div key={category} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                          <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 capitalize">
                            {category.replace('_', ' ')}
                          </div>
                          
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-xs text-gray-500">Budget:</span>
                              <span className="text-xs font-medium">{formatCurrency(budgeted)}</span>
                            </div>
                            
                            <div className="flex justify-between">
                              <span className="text-xs text-gray-500">Actual:</span>
                              <span className="text-xs font-medium">{formatCurrency(actual)}</span>
                            </div>
                            
                            <div className="flex justify-between border-t border-gray-200 pt-2">
                              <span className="text-xs text-gray-500">Variance:</span>
                              <span className={`text-xs font-bold px-2 py-1 rounded-full ${getVarianceColor(variance)}`}>
                                {variance > 0 ? '+' : ''}{formatCurrency(variance)} ({variancePercent.toFixed(1)}%)
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Loading overlay for report generation */}
        {isGeneratingReport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white rounded-lg p-6 flex items-center space-x-4">
              <span className="text-2xl animate-spin">🔄</span>
              <span className="text-lg font-medium">Generating report...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialAnalyticsDashboard;