import React, { useState, useEffect } from 'react';
import api from '../api';

export default function EnvironmentalDashboard() {
  const [environmentalData, setEnvironmentalData] = useState({});
  const [sustainabilityReport, setSustainabilityReport] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [realTimeStatus, setRealTimeStatus] = useState({});
  const [selectedProperty, setSelectedProperty] = useState('PROP001');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchEnvironmentalData();
    const interval = setInterval(fetchRealTimeStatus, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [selectedProperty]);

  const fetchEnvironmentalData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      // Fetch environmental monitoring data
      const response = await fetch(`${api.BASE}/api/environmental/status/${selectedProperty}`, {
        headers
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setRealTimeStatus(result.data);
        }
      }

      // Fetch sustainability report
      const reportResponse = await fetch(`${api.BASE}/api/environmental/sustainability-report/${selectedProperty}`, {
        headers
      });

      if (reportResponse.ok) {
        const reportResult = await reportResponse.json();
        if (reportResult.success) {
          setSustainabilityReport(reportResult.data);
        }
      }

      // Fetch environmental alerts
      const alertsResponse = await fetch(`${api.BASE}/api/environmental/alerts/${selectedProperty}`, {
        headers
      });

      if (alertsResponse.ok) {
        const alertsResult = await alertsResponse.json();
        if (alertsResult.success) {
          setAlerts(alertsResult.data);
        }
      }

      setLoading(false);
      setError('');
    } catch (err) {
      console.error('Error fetching environmental data:', err);
      setError('Failed to load environmental data');
      setLoading(false);
    }
  };

  const fetchRealTimeStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      const response = await fetch(`${api.BASE}/api/environmental/status/${selectedProperty}`, {
        headers
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setRealTimeStatus(result.data);
        }
      }
    } catch (err) {
      console.error('Error fetching real-time status:', err);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      normal: 'bg-green-100 text-green-800 border-green-200',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      critical: 'bg-red-100 text-red-800 border-red-200',
      emergency: 'bg-red-200 text-red-900 border-red-300'
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getAlertIcon = (level) => {
    const icons = {
      normal: '✅',
      warning: '⚠️',
      critical: '🚨',
      emergency: '🆘'
    };
    return icons[level] || '📊';
  };

  const getMetricIcon = (metric) => {
    const icons = {
      air_quality: '🌬️',
      indoor_air_quality: '🏠',
      noise_level: '🔊',
      water_quality: '💧',
      energy_efficiency: '⚡',
      carbon_footprint: '🌱',
      water_consumption: '🚿',
      renewable_energy: '☀️',
      waste_management: '♻️',
      light_pollution: '💡'
    };
    return icons[metric] || '📊';
  };

  const getSustainabilityGrade = (score) => {
    if (score >= 90) return { grade: 'A+', color: 'text-green-600' };
    if (score >= 80) return { grade: 'A', color: 'text-green-600' };
    if (score >= 70) return { grade: 'B', color: 'text-blue-600' };
    if (score >= 60) return { grade: 'C', color: 'text-yellow-600' };
    if (score >= 50) return { grade: 'D', color: 'text-orange-600' };
    return { grade: 'F', color: 'text-red-600' };
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Loading Environmental Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Environmental Monitoring</h1>
          <p className="text-gray-600">Comprehensive sustainability analytics and environmental insights</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select
            value={selectedProperty}
            onChange={(e) => setSelectedProperty(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="PROP001">Property 001</option>
            <option value="PROP002">Property 002</option>
            <option value="PROP003">Property 003</option>
          </select>
          
          <button
            onClick={fetchEnvironmentalData}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition"
          >
            🔄 Refresh Data
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Real-time Status Banner */}
      {realTimeStatus.overall_status && (
        <div className={`border rounded-lg p-4 mb-6 ${getStatusColor(realTimeStatus.overall_status)}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-2xl mr-3">{getAlertIcon(realTimeStatus.overall_status)}</span>
              <div>
                <h3 className="font-semibold capitalize">
                  Environmental Status: {realTimeStatus.overall_status}
                </h3>
                <p className="text-sm">
                  Last updated: {new Date(realTimeStatus.last_updated).toLocaleString()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="font-semibold">Active Alerts: {realTimeStatus.active_alerts_count || 0}</div>
              <div className="text-sm">Critical: {realTimeStatus.critical_alerts || 0}</div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: '🌍' },
            { id: 'metrics', name: 'Environmental Metrics', icon: '📊' },
            { id: 'sustainability', name: 'Sustainability Report', icon: '🌱' },
            { id: 'alerts', name: 'Alerts & Actions', icon: '🚨' },
            { id: 'trends', name: 'Trends & Insights', icon: '📈' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Environmental Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-semibold">🌬️</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Air Quality Index</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {realTimeStatus.metrics?.air_quality?.current_value || 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {realTimeStatus.metrics?.air_quality?.status || 'Unknown'}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-semibold">⚡</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Energy Efficiency</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {realTimeStatus.metrics?.energy_efficiency?.current_value || 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500">kWh/sqft</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <span className="text-purple-600 font-semibold">🌱</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Sustainability Score</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {sustainabilityReport.overall_sustainability_score || 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {sustainabilityReport.sustainability_rating || 'Calculating...'}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                    <span className="text-orange-600 font-semibold">💰</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Potential Savings</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(sustainabilityReport.sustainability_cost_savings || 0)}
                  </p>
                  <p className="text-xs text-gray-500">Monthly</p>
                </div>
              </div>
            </div>
          </div>

          {/* Environmental Performance Summary */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">🎯 Environmental Performance</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-4xl font-bold mb-2">
                  {sustainabilityReport.overall_sustainability_score ? (
                    <span className={getSustainabilityGrade(sustainabilityReport.overall_sustainability_score).color}>
                      {getSustainabilityGrade(sustainabilityReport.overall_sustainability_score).grade}
                    </span>
                  ) : 'N/A'}
                </div>
                <h3 className="font-semibold">Overall Grade</h3>
                <p className="text-sm text-gray-600">
                  {sustainabilityReport.overall_sustainability_score?.toFixed(1) || 'N/A'}/100
                </p>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-green-600 mb-2">
                  {sustainabilityReport.regulatory_violations || 0}
                </div>
                <h3 className="font-semibold">Compliance Violations</h3>
                <p className="text-sm text-gray-600">Regulatory issues</p>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-600 mb-2">
                  {sustainabilityReport.improvement_percentage > 0 ? '+' : ''}{sustainabilityReport.improvement_percentage?.toFixed(1) || 0}%
                </div>
                <h3 className="font-semibold">Period Improvement</h3>
                <p className="text-sm text-gray-600">vs. last period</p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">⚡ Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <button className="bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg p-4 text-left transition">
                <div className="text-2xl mb-2">📋</div>
                <h3 className="font-semibold text-blue-800">Generate Report</h3>
                <p className="text-sm text-blue-600">Create sustainability report</p>
              </button>
              <button className="bg-green-50 hover:bg-green-100 border border-green-200 rounded-lg p-4 text-left transition">
                <div className="text-2xl mb-2">🔧</div>
                <h3 className="font-semibold text-green-800">Optimize Settings</h3>
                <p className="text-sm text-green-600">Auto-optimize systems</p>
              </button>
              <button className="bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-lg p-4 text-left transition">
                <div className="text-2xl mb-2">📊</div>
                <h3 className="font-semibold text-purple-800">View Analytics</h3>
                <p className="text-sm text-purple-600">Detailed insights</p>
              </button>
              <button className="bg-orange-50 hover:bg-orange-100 border border-orange-200 rounded-lg p-4 text-left transition">
                <div className="text-2xl mb-2">🎯</div>
                <h3 className="font-semibold text-orange-800">Set Goals</h3>
                <p className="text-sm text-orange-600">Environmental targets</p>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Environmental Metrics Tab */}
      {activeTab === 'metrics' && realTimeStatus.metrics && (
        <div className="space-y-4">
          {Object.entries(realTimeStatus.metrics).map(([metric, data]) => (
            <div key={metric} className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-3">
                    <span className="text-2xl mr-3">{getMetricIcon(metric)}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 capitalize">
                        {metric.replace('_', ' ')}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Current: {data.current_value} {data.unit}
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-gray-500">Status</p>
                      <p className={`text-sm font-semibold capitalize ${
                        data.status === 'normal' ? 'text-green-600' :
                        data.status === 'warning' ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {data.status}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Trend</p>
                      <p className={`text-sm font-semibold capitalize ${
                        data.trend === 'improving' ? 'text-green-600' :
                        data.trend === 'stable' ? 'text-blue-600' :
                        'text-red-600'
                      }`}>
                        {data.trend === 'improving' ? '📈' : data.trend === 'stable' ? '➡️' : '📉'} {data.trend}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Deviation from Baseline</p>
                      <p className={`text-sm font-semibold ${
                        data.deviation_from_baseline > 0 ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {data.deviation_from_baseline > 0 ? '+' : ''}{data.deviation_from_baseline}%
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="ml-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(data.status)}`}>
                    {data.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          ))}

          {(!realTimeStatus.metrics || Object.keys(realTimeStatus.metrics).length === 0) && (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Environmental Data</h3>
              <p className="text-gray-600">Environmental metrics will appear here once sensors are connected.</p>
            </div>
          )}
        </div>
      )}

      {/* Sustainability Report Tab */}
      {activeTab === 'sustainability' && sustainabilityReport && (
        <div className="space-y-6">
          {/* Sustainability Scores */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6 text-center">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Air Quality</h4>
              <div className="text-2xl font-bold text-blue-600">
                {sustainabilityReport.air_quality_score?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500">/100</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-6 text-center">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Energy Efficiency</h4>
              <div className="text-2xl font-bold text-green-600">
                {sustainabilityReport.energy_efficiency_score?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500">/100</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-6 text-center">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Water Conservation</h4>
              <div className="text-2xl font-bold text-cyan-600">
                {sustainabilityReport.water_conservation_score?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500">/100</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-6 text-center">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Waste Management</h4>
              <div className="text-2xl font-bold text-purple-600">
                {sustainabilityReport.waste_management_score?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500">/100</div>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-6 text-center">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Carbon Footprint</h4>
              <div className="text-2xl font-bold text-orange-600">
                {sustainabilityReport.carbon_footprint_score?.toFixed(1) || 'N/A'}
              </div>
              <div className="text-xs text-gray-500">/100</div>
            </div>
          </div>

          {/* ESG Compliance */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">🏛️ ESG Compliance</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h3 className="font-medium mb-3">Compliance Score</h3>
                <div className="text-3xl font-bold text-blue-600 mb-2">
                  {sustainabilityReport.esg_compliance_score?.toFixed(1) || 'N/A'}/100
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${sustainabilityReport.esg_compliance_score || 0}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <h3 className="font-medium mb-3">Regulatory Violations</h3>
                <div className="text-3xl font-bold text-red-600 mb-2">
                  {sustainabilityReport.regulatory_violations || 0}
                </div>
                <p className="text-sm text-gray-600">Active violations requiring attention</p>
              </div>
              <div>
                <h3 className="font-medium mb-3">Certifications Eligible</h3>
                <div className="space-y-1">
                  {sustainabilityReport.certifications_eligible?.map((cert, index) => (
                    <span key={index} className="inline-block bg-green-100 text-green-800 px-2 py-1 rounded text-xs mr-1">
                      {cert}
                    </span>
                  )) || <span className="text-gray-500">None available</span>}
                </div>
              </div>
            </div>
          </div>

          {/* Financial Impact */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">💰 Financial Impact</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(sustainabilityReport.sustainability_cost_savings || 0)}
                </div>
                <div className="text-sm text-green-800 font-medium">Cost Savings</div>
                <div className="text-xs text-gray-600">Monthly</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {formatCurrency(sustainabilityReport.environmental_penalties || 0)}
                </div>
                <div className="text-sm text-red-800 font-medium">Penalties</div>
                <div className="text-xs text-gray-600">This period</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {formatCurrency(sustainabilityReport.green_incentives_earned || 0)}
                </div>
                <div className="text-sm text-blue-800 font-medium">Green Incentives</div>
                <div className="text-xs text-gray-600">Earned</div>
              </div>
            </div>
          </div>

          {/* Investment Recommendations */}
          {sustainabilityReport.investment_recommendations && sustainabilityReport.investment_recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">📈 Investment Recommendations</h2>
              <div className="space-y-4">
                {sustainabilityReport.investment_recommendations.map((investment, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold">{investment.investment}</h3>
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        {investment.category}
                      </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Investment:</span>
                        <div className="font-semibold">{formatCurrency(investment.cost)}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Annual Savings:</span>
                        <div className="font-semibold text-green-600">{formatCurrency(investment.annual_savings)}</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Payback:</span>
                        <div className="font-semibold">{investment.payback_months} months</div>
                      </div>
                      <div>
                        <span className="text-gray-500">Impact:</span>
                        <div className="text-sm">{investment.environmental_impact}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          {alerts && alerts.length > 0 ? (
            alerts.map((alert) => (
              <div key={alert.alert_id} className={`rounded-lg shadow-sm border p-6 ${getStatusColor(alert.alert_level)}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <span className="text-2xl mr-3">{getAlertIcon(alert.alert_level)}</span>
                      <div>
                        <h3 className="text-lg font-semibold capitalize">
                          {alert.metric_type.replace('_', ' ')} Alert
                        </h3>
                        <p className="text-sm">
                          Current: {alert.current_value} | Threshold: {alert.threshold_value}
                        </p>
                      </div>
                    </div>
                    
                    <div className="mb-4">
                      <h4 className="font-medium mb-1">Health Impact:</h4>
                      <p className="text-sm">{alert.health_impact}</p>
                    </div>

                    <div className="mb-4">
                      <h4 className="font-medium mb-1">Environmental Impact:</h4>
                      <p className="text-sm">{alert.environmental_impact}</p>
                    </div>

                    {alert.immediate_actions && alert.immediate_actions.length > 0 && (
                      <div className="mb-4">
                        <h4 className="font-medium mb-2">Immediate Actions:</h4>
                        <ul className="list-disc list-inside space-y-1">
                          {alert.immediate_actions.map((action, index) => (
                            <li key={index} className="text-sm">{action}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {alert.long_term_solutions && alert.long_term_solutions.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Long-term Solutions:</h4>
                        <ul className="list-disc list-inside space-y-1">
                          {alert.long_term_solutions.map((solution, index) => (
                            <li key={index} className="text-sm">{solution}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="ml-4 text-right">
                    <div className="text-lg font-semibold">
                      Severity: {alert.severity_score?.toFixed(1)}/100
                    </div>
                    <div className="text-sm">
                      Est. Cost: {formatCurrency(alert.estimated_cost)}
                    </div>
                    <div className="text-xs text-gray-600 mt-2">
                      {new Date(alert.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">✅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Alerts</h3>
              <p className="text-gray-600">All environmental parameters are within normal ranges.</p>
            </div>
          )}
        </div>
      )}

      {/* Trends Tab */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          {/* Priority Improvements */}
          {sustainabilityReport.priority_improvements && sustainabilityReport.priority_improvements.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">🎯 Priority Improvements</h2>
              <div className="space-y-3">
                {sustainabilityReport.priority_improvements.map((improvement, index) => (
                  <div key={index} className="flex items-center p-3 bg-yellow-50 border border-yellow-200 rounded">
                    <span className="text-yellow-600 mr-3">⚠️</span>
                    <span className="text-sm">{improvement}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Environmental Performance Trends */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">📈 Performance Trends</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium mb-3">Recent Changes</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Overall Sustainability</span>
                    <span className={`text-sm font-semibold ${
                      sustainabilityReport.improvement_percentage > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {sustainabilityReport.improvement_percentage > 0 ? '+' : ''}{sustainabilityReport.improvement_percentage?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Energy Efficiency</span>
                    <span className="text-sm font-semibold text-green-600">+5.2%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Air Quality</span>
                    <span className="text-sm font-semibold text-blue-600">+2.1%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Water Conservation</span>
                    <span className="text-sm font-semibold text-red-600">-1.3%</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-medium mb-3">Certification Progress</h3>
                <div className="space-y-3">
                  {sustainabilityReport.certification_opportunities?.map((cert, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm">{cert}</span>
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                        Eligible
                      </span>
                    </div>
                  )) || (
                    <p className="text-sm text-gray-600">
                      Continue improving to unlock certification opportunities
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Action Items */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">✅ Recommended Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h3 className="font-medium mb-3 text-red-600">🚨 High Priority</h3>
                <ul className="space-y-2">
                  <li className="text-sm">• Install air quality monitoring sensors</li>
                  <li className="text-sm">• Upgrade HVAC filtration system</li>
                  <li className="text-sm">• Implement energy management system</li>
                </ul>
              </div>
              <div>
                <h3 className="font-medium mb-3 text-yellow-600">⚡ Quick Wins</h3>
                <ul className="space-y-2">
                  <li className="text-sm">• LED lighting retrofit</li>
                  <li className="text-sm">• Smart thermostat installation</li>
                  <li className="text-sm">• Water-efficient fixtures</li>
                </ul>
              </div>
              <div>
                <h3 className="font-medium mb-3 text-blue-600">🎯 Long-term</h3>
                <ul className="space-y-2">
                  <li className="text-sm">• Solar panel installation</li>
                  <li className="text-sm">• Green roof implementation</li>
                  <li className="text-sm">• Building automation system</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}