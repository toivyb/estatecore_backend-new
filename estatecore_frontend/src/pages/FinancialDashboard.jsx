import React, { useState, useEffect } from 'react';
import api from '../api';

export default function FinancialDashboard() {
  const [financialData, setFinancialData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFinancialData();
  }, []);

  const fetchFinancialData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/financial-analytics/dashboard');
      if (response.success) {
        setFinancialData(response.dashboard);
      } else {
        setError('Failed to load financial data');
      }
    } catch (error) {
      console.error('Error fetching financial data:', error);
      setError('Failed to connect to financial service');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800 font-medium">Error</div>
        <div className="text-red-600 text-sm">{error}</div>
      </div>
    );
  }

  if (!financialData) {
    return <div className="text-gray-600">No financial data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Financial Analytics Dashboard</h1>
        <div className="text-sm text-gray-600">
          Period: {financialData.period?.start_date} to {financialData.period?.end_date} 
          ({financialData.period?.days} days)
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Income</h3>
          <div className="text-3xl font-bold text-green-600">
            ${financialData.summary?.total_income?.toLocaleString() || '0'}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Expenses</h3>
          <div className="text-3xl font-bold text-red-600">
            ${financialData.summary?.total_expenses?.toLocaleString() || '0'}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Net Income</h3>
          <div className="text-3xl font-bold text-blue-600">
            ${financialData.summary?.net_income?.toLocaleString() || '0'}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Net Margin</h3>
          <div className="text-3xl font-bold text-purple-600">
            {((financialData.summary?.net_margin || 0) * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Income and Expense Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Income Breakdown */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 text-green-700">Income Breakdown</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-green-50 rounded">
              <span>Rent Income</span>
              <span className="font-semibold text-green-700">
                ${financialData.income_breakdown?.rent_income?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-green-50 rounded">
              <span>Late Fees</span>
              <span className="font-semibold text-green-700">
                ${financialData.income_breakdown?.late_fees?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-green-50 rounded">
              <span>Other Income</span>
              <span className="font-semibold text-green-700">
                ${financialData.income_breakdown?.other_income?.toLocaleString() || '0'}
              </span>
            </div>
          </div>
        </div>

        {/* Expense Breakdown */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 text-red-700">Expense Breakdown</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-red-50 rounded">
              <span>Maintenance</span>
              <span className="font-semibold text-red-700">
                ${financialData.expense_breakdown?.maintenance?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-red-50 rounded">
              <span>Utilities</span>
              <span className="font-semibold text-red-700">
                ${financialData.expense_breakdown?.utilities?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-red-50 rounded">
              <span>Insurance</span>
              <span className="font-semibold text-red-700">
                ${financialData.expense_breakdown?.insurance?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-red-50 rounded">
              <span>Property Tax</span>
              <span className="font-semibold text-red-700">
                ${financialData.expense_breakdown?.property_tax?.toLocaleString() || '0'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Monthly Trends */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Monthly Trends</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Month</th>
                <th className="text-right py-2">Income</th>
                <th className="text-right py-2">Expenses</th>
                <th className="text-right py-2">Net Income</th>
              </tr>
            </thead>
            <tbody>
              {financialData.monthly_trends?.map((month, index) => (
                <tr key={index} className="border-b">
                  <td className="py-2">{month.month}</td>
                  <td className="text-right py-2 text-green-600">
                    ${month.income?.toLocaleString() || '0'}
                  </td>
                  <td className="text-right py-2 text-red-600">
                    ${month.expenses?.toLocaleString() || '0'}
                  </td>
                  <td className="text-right py-2 text-blue-600 font-semibold">
                    ${month.net_income?.toLocaleString() || '0'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Key Performance Indicators</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">
              {financialData.kpis?.gross_rental_yield?.toFixed(1) || '0.0'}%
            </div>
            <div className="text-sm text-gray-600">Gross Rental Yield</div>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">
              ${financialData.kpis?.net_operating_income?.toLocaleString() || '0'}
            </div>
            <div className="text-sm text-gray-600">NOI</div>
          </div>

          <div className="text-center p-4 bg-purple-50 rounded">
            <div className="text-2xl font-bold text-purple-600">
              {financialData.kpis?.cap_rate?.toFixed(1) || '0.0'}%
            </div>
            <div className="text-sm text-gray-600">Cap Rate</div>
          </div>

          <div className="text-center p-4 bg-yellow-50 rounded">
            <div className="text-2xl font-bold text-yellow-600">
              {financialData.kpis?.cash_on_cash_return?.toFixed(1) || '0.0'}%
            </div>
            <div className="text-sm text-gray-600">Cash-on-Cash</div>
          </div>

          <div className="text-center p-4 bg-red-50 rounded">
            <div className="text-2xl font-bold text-red-600">
              {((financialData.kpis?.expense_ratio || 0) * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">Expense Ratio</div>
          </div>

          <div className="text-center p-4 bg-indigo-50 rounded">
            <div className="text-2xl font-bold text-indigo-600">
              {financialData.kpis?.rent_growth_rate?.toFixed(1) || '0.0'}%
            </div>
            <div className="text-sm text-gray-600">Rent Growth</div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="p-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-sm font-medium">Generate Report</div>
          </button>
          <button className="p-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
            <div className="text-2xl mb-2">📤</div>
            <div className="text-sm font-medium">Export Data</div>
          </button>
          <button className="p-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
            <div className="text-2xl mb-2">⚙️</div>
            <div className="text-sm font-medium">Settings</div>
          </button>
          <button 
            onClick={fetchFinancialData}
            className="p-4 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            <div className="text-2xl mb-2">🔄</div>
            <div className="text-sm font-medium">Refresh</div>
          </button>
        </div>
      </div>
    </div>
  );
}