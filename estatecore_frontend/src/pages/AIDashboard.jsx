import React, { useEffect, useState } from 'react';
import api from '../api';

export default function AIDashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [assetHealth, setAssetHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAIDashboardData();
  }, []);

  const fetchAIDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch AI dashboard summary
      const summaryResponse = await fetch(`${api.BASE}/api/ai/dashboard-summary`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setDashboardData(summaryData.data);
      }

      // Fetch asset health for first property
      const assetResponse = await fetch(`${api.BASE}/api/ai/asset-health`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ property_id: 'prop_1' })
      });
      
      if (assetResponse.ok) {
        const assetData = await assetResponse.json();
        setAssetHealth(assetData.data);
      }

    } catch (err) {
      console.error('Error fetching AI dashboard data:', err);
      setError('Failed to load AI dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'Excellent': 'text-green-600 bg-green-100',
      'Good': 'text-blue-600 bg-blue-100',
      'Fair': 'text-yellow-600 bg-yellow-100',
      'Poor': 'text-red-600 bg-red-100'
    };
    return colors[status] || 'text-gray-600 bg-gray-100';
  };

  const getPriorityColor = (type) => {
    const colors = {
      'urgent': 'text-red-600 bg-red-100',
      'maintenance': 'text-orange-600 bg-orange-100',
      'tenant': 'text-blue-600 bg-blue-100'
    };
    return colors[type] || 'text-gray-600 bg-gray-100';
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">🤖 AI Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Artificial Intelligence insights and predictive analytics for your property portfolio
        </p>
      </div>

      {/* AI Metrics Overview */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Asset Health</h3>
            <p className="text-2xl font-bold text-green-600">{dashboardData.asset_health.average_score}</p>
            <p className="text-sm text-gray-500">
              {dashboardData.asset_health.properties_at_risk} at risk / {dashboardData.asset_health.total_properties} total
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Tenant Risk</h3>
            <p className="text-2xl font-bold text-blue-600">{dashboardData.tenant_risk.average_score}</p>
            <p className="text-sm text-gray-500">
              {dashboardData.tenant_risk.high_risk_tenants} high risk tenants
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-orange-500">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Maintenance Cost</h3>
            <p className="text-2xl font-bold text-orange-600">${dashboardData.maintenance_forecast.predicted_monthly_cost}</p>
            <p className="text-sm text-gray-500">
              ${dashboardData.maintenance_forecast.optimization_savings} potential savings
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Revenue Leakage</h3>
            <p className="text-2xl font-bold text-purple-600">${dashboardData.revenue_optimization.total_annual_leakage}</p>
            <p className="text-sm text-gray-500">
              {dashboardData.revenue_optimization.underpriced_units} underpriced units
            </p>
          </div>
        </div>
      )}

      {/* Asset Health Details */}
      {assetHealth && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Asset Health Score</h3>
            </div>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-3xl font-bold text-gray-900">{assetHealth.score}</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(assetHealth.status)}`}>
                  {assetHealth.status}
                </span>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Maintenance</span>
                  <span className="text-sm font-medium">{assetHealth.breakdown.maintenance}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Financial</span>
                  <span className="text-sm font-medium">{assetHealth.breakdown.financial}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Physical</span>
                  <span className="text-sm font-medium">{assetHealth.breakdown.physical}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Operational</span>
                  <span className="text-sm font-medium">{assetHealth.breakdown.operational}</span>
                </div>
              </div>
              
              <div className="mt-4 text-xs text-gray-500">
                Confidence: {assetHealth.confidence_level}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">AI Capabilities</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-medium text-gray-900">🏠</div>
                  <div className="text-sm text-gray-600 mt-1">Asset Health</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-medium text-gray-900">👤</div>
                  <div className="text-sm text-gray-600 mt-1">Tenant Scoring</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-medium text-gray-900">🔧</div>
                  <div className="text-sm text-gray-600 mt-1">Maintenance Forecast</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-medium text-gray-900">💰</div>
                  <div className="text-sm text-gray-600 mt-1">Revenue Optimization</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-medium text-gray-900">📊</div>
                  <div className="text-sm text-gray-600 mt-1">Predictive Analytics</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-medium text-gray-900">⚡</div>
                  <div className="text-sm text-gray-600 mt-1">Real-time Insights</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Recommendations */}
      {dashboardData && dashboardData.recommendations && (
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">AI Recommendations</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {dashboardData.recommendations.map((rec, index) => (
                <div key={index} className="flex items-start space-x-4 p-4 border border-gray-200 rounded-lg">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(rec.type)}`}>
                    {rec.type}
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{rec.title}</p>
                    <p className="text-sm text-gray-500 mt-1">Impact: {rec.impact}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Quick AI Actions</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              onClick={() => window.location.href = '/maintenance-forecast'}
            >
              🔧 Run Maintenance Forecast
            </button>
            <button 
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              onClick={() => window.location.href = '/tenant-scoring'}
            >
              👤 Analyze Tenant Risk
            </button>
            <button 
              className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              onClick={() => window.location.href = '/revenue-optimization'}
            >
              💰 Optimize Revenue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
