import React, { useState, useEffect } from 'react';
import api from '../api';

export default function OccupancyAnalytics() {
  const [analyticsData, setAnalyticsData] = useState({});
  const [occupancyReport, setOccupancyReport] = useState({});
  const [insights, setInsights] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState('PROP001');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchOccupancyData();
  }, [selectedProperty]);

  const fetchOccupancyData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      // Fetch analytics data
      const analyticsResponse = await fetch(`${api.BASE}/api/occupancy/analytics`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          property_id: selectedProperty
        })
      });

      if (analyticsResponse.ok) {
        const analyticsResult = await analyticsResponse.json();
        if (analyticsResult.success) {
          setAnalyticsData(analyticsResult.data);
        }
      }

      // Fetch detailed report
      const reportResponse = await fetch(`${api.BASE}/api/occupancy/report/${selectedProperty}`, {
        headers
      });

      if (reportResponse.ok) {
        const reportResult = await reportResponse.json();
        if (reportResult.success) {
          setOccupancyReport(reportResult.data);
        }
      }

      // Fetch actionable insights
      const insightsResponse = await fetch(`${api.BASE}/api/occupancy/insights/${selectedProperty}`, {
        headers
      });

      if (insightsResponse.ok) {
        const insightsResult = await insightsResponse.json();
        if (insightsResult.success) {
          setInsights(insightsResult.data);
        }
      }

      setLoading(false);
      setError('');
    } catch (err) {
      console.error('Error fetching occupancy data:', err);
      setError('Failed to load occupancy analytics data');
      setLoading(false);
    }
  };

  const getUtilizationColor = (rate) => {
    if (rate >= 0.8) return 'bg-red-100 text-red-800';
    if (rate >= 0.6) return 'bg-green-100 text-green-800';
    if (rate >= 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-blue-100 text-blue-800';
  };

  const getSpaceIcon = (spaceType) => {
    const icons = {
      residential_unit: '🏠',
      office_space: '🏢',
      common_area: '🏛️',
      amenity_space: '🏊‍♂️',
      parking_garage: '🅿️',
      lobby: '🚪',
      elevator: '🛗'
    };
    return icons[spaceType] || '📍';
  };

  const getInsightIcon = (insightType) => {
    const icons = {
      revenue_opportunity: '💰',
      cost_savings: '💵',
      operational_efficiency: '⚡',
      tenant_satisfaction: '😊',
      space_optimization: '📐',
      energy_savings: '🔋'
    };
    return icons[insightType] || '💡';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      High: 'bg-red-100 text-red-800 border-red-200',
      Medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      Low: 'bg-blue-100 text-blue-800 border-blue-200'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Loading Occupancy Analytics...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Occupancy Analytics</h1>
          <p className="text-gray-600">AI-powered space utilization insights and optimization</p>
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
            onClick={fetchOccupancyData}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
          >
            Refresh Analysis
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: '📊' },
            { id: 'spaces', name: 'Space Analysis', icon: '🏢' },
            { id: 'insights', name: 'Insights', icon: '💡' },
            { id: 'trends', name: 'Trends', icon: '📈' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
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
      {activeTab === 'overview' && analyticsData.summary && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-semibold">📍</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Spaces Analyzed</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {analyticsData.summary.total_spaces_analyzed || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-semibold">📊</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Avg Utilization</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatPercentage(analyticsData.summary.average_utilization_rate || 0)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                    <span className="text-yellow-600 font-semibold">💰</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Revenue Potential</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(analyticsData.summary.total_potential_revenue || 0)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                    <span className="text-red-600 font-semibold">💡</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Insights Generated</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {analyticsData.summary.total_insights_generated || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Space Type Breakdown */}
          {analyticsData.space_type_breakdown && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">Space Type Analysis</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(analyticsData.space_type_breakdown).map(([type, data]) => (
                  <div key={type} className="border rounded-lg p-4">
                    <div className="flex items-center mb-3">
                      <span className="text-2xl mr-2">{getSpaceIcon(type)}</span>
                      <h3 className="font-semibold capitalize">{type.replace('_', ' ')}</h3>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Count:</span>
                        <span className="font-medium">{data.count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg Utilization:</span>
                        <span className={`font-medium px-2 py-1 rounded text-xs ${getUtilizationColor(data.avg_utilization)}`}>
                          {formatPercentage(data.avg_utilization)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Revenue Potential:</span>
                        <span className="font-medium">{formatCurrency(data.avg_revenue_potential)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Efficiency:</span>
                        <span className="font-medium">{data.common_efficiency}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trending Patterns */}
          {analyticsData.trending_patterns && analyticsData.trending_patterns.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">🔍 Trending Patterns</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {analyticsData.trending_patterns.map((pattern, index) => (
                  <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-medium text-blue-800 capitalize">{pattern.replace('_', ' ')}</h3>
                    <p className="text-sm text-blue-600 mt-1">Detected across multiple spaces</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Space Analysis Tab */}
      {activeTab === 'spaces' && analyticsData.metrics && (
        <div className="space-y-4">
          {analyticsData.metrics.map((metrics) => (
            <div key={metrics.space_id} className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-3">{getSpaceIcon(metrics.space_type)}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{metrics.location}</h3>
                      <p className="text-sm text-gray-600 capitalize">{metrics.space_type.replace('_', ' ')}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-gray-500">Current Occupancy</p>
                      <p className="text-lg font-semibold text-blue-600">
                        {formatPercentage(metrics.current_occupancy_rate)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Peak Occupancy</p>
                      <p className="text-sm font-medium">{formatPercentage(metrics.peak_occupancy_rate)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Utilization Score</p>
                      <p className="text-sm font-medium">{(metrics.utilization_score * 100).toFixed(1)}/100</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Revenue/SqFt</p>
                      <p className="text-lg font-semibold text-green-600">
                        {formatCurrency(metrics.revenue_per_sqft)}
                      </p>
                    </div>
                  </div>

                  {metrics.peak_hours && metrics.peak_hours.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">Peak Hours:</p>
                      <div className="flex flex-wrap gap-2">
                        {metrics.peak_hours.map((hour, index) => (
                          <span key={index} className="bg-yellow-50 text-yellow-700 px-2 py-1 rounded text-xs">
                            {hour}:00
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {metrics.detected_patterns && metrics.detected_patterns.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">Detected Patterns:</p>
                      <div className="flex flex-wrap gap-2">
                        {metrics.detected_patterns.map((pattern, index) => (
                          <span key={index} className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs">
                            {pattern.replace('_', ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="ml-4 flex flex-col items-end">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold mb-2 ${
                    metrics.efficiency_rating === 'Excellent' ? 'bg-green-100 text-green-800' :
                    metrics.efficiency_rating === 'Good' ? 'bg-blue-100 text-blue-800' :
                    metrics.efficiency_rating === 'Fair' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {metrics.efficiency_rating}
                  </span>
                  
                  {metrics.capacity_optimization_potential > 0.1 && (
                    <div className="text-sm text-orange-600 font-medium">
                      {formatPercentage(metrics.capacity_optimization_potential)} optimization potential
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {(!analyticsData.metrics || analyticsData.metrics.length === 0) && (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Space Data Available</h3>
              <p className="text-gray-600">Space analysis will appear here once data is collected.</p>
            </div>
          )}
        </div>
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && (
        <div className="space-y-6">
          {/* Insights Summary */}
          {insights.total_insights > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                      <span className="text-red-600 font-semibold">🚨</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">High Priority</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {insights.high_priority_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <span className="text-green-600 font-semibold">💰</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Revenue Potential</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {formatCurrency(insights.total_potential_revenue || 0)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-semibold">💵</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Cost Savings</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {formatCurrency(insights.total_potential_savings || 0)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Individual Insights */}
          {insights.insights && insights.insights.length > 0 ? (
            <div className="space-y-4">
              {insights.insights.map((insight) => (
                <div key={insight.insight_id} className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="text-2xl mr-3">{getInsightIcon(insight.insight_type)}</span>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{insight.title}</h3>
                          <p className="text-sm text-gray-600">{insight.description}</p>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        <div>
                          <p className="text-xs text-gray-500">Potential Revenue</p>
                          <p className="text-lg font-semibold text-green-600">
                            {formatCurrency(insight.potential_revenue)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Implementation Cost</p>
                          <p className="text-sm font-medium">{formatCurrency(insight.implementation_cost)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Payback Period</p>
                          <p className="text-sm font-medium">{insight.payback_period_months} months</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Confidence</p>
                          <p className="text-sm font-medium">{(insight.confidence_score * 100).toFixed(1)}%</p>
                        </div>
                      </div>

                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-700 mb-2">Expected Outcome:</p>
                        <p className="text-sm text-gray-600">{insight.expected_outcome}</p>
                      </div>

                      {insight.recommended_actions && insight.recommended_actions.length > 0 && (
                        <div className="mb-4">
                          <p className="text-sm font-medium text-gray-700 mb-2">Recommended Actions:</p>
                          <ul className="list-disc list-inside space-y-1">
                            {insight.recommended_actions.map((action, index) => (
                              <li key={index} className="text-sm text-gray-600">{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <div className="ml-4 flex flex-col items-end">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getPriorityColor(insight.priority_level)}`}>
                        {insight.priority_level}
                      </span>
                      
                      <div className="mt-3 text-sm text-gray-500">
                        Type: {insight.insight_type.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">💡</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Actionable Insights</h3>
              <p className="text-gray-600">All spaces are optimally utilized. Check back later for new opportunities.</p>
            </div>
          )}
        </div>
      )}

      {/* Trends Tab */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          {/* Seasonal Trends */}
          {analyticsData.seasonal_insights && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">📅 Seasonal Utilization Trends</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {Object.entries(analyticsData.seasonal_insights).map(([season, utilization]) => (
                  <div key={season} className="text-center p-4 rounded-lg border">
                    <div className="text-2xl mb-2">
                      {season === 'spring' && '🌸'}
                      {season === 'summer' && '☀️'}
                      {season === 'fall' && '🍂'}
                      {season === 'winter' && '❄️'}
                    </div>
                    <h3 className="font-semibold capitalize">{season}</h3>
                    <p className="text-lg font-bold text-blue-600">{formatPercentage(utilization)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {analyticsData.recommendations && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {analyticsData.recommendations.high_priority_actions && analyticsData.recommendations.high_priority_actions.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <h3 className="text-lg font-semibold mb-4 text-red-600">🚨 High Priority Actions</h3>
                  <ul className="space-y-2">
                    {analyticsData.recommendations.high_priority_actions.map((action, index) => (
                      <li key={index} className="text-sm text-gray-700">
                        <span className="inline-block w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analyticsData.recommendations.quick_wins && analyticsData.recommendations.quick_wins.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <h3 className="text-lg font-semibold mb-4 text-green-600">⚡ Quick Wins</h3>
                  <ul className="space-y-2">
                    {analyticsData.recommendations.quick_wins.map((action, index) => (
                      <li key={index} className="text-sm text-gray-700">
                        <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analyticsData.recommendations.long_term_strategies && analyticsData.recommendations.long_term_strategies.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <h3 className="text-lg font-semibold mb-4 text-blue-600">🎯 Long-term Strategies</h3>
                  <ul className="space-y-2">
                    {analyticsData.recommendations.long_term_strategies.map((action, index) => (
                      <li key={index} className="text-sm text-gray-700">
                        <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Performance Summary */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">📊 Performance Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h3 className="font-medium mb-3">Utilization Distribution</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">High (80%+)</span>
                    <span className="text-sm font-medium text-red-600">
                      {analyticsData.metrics ? analyticsData.metrics.filter(m => m.average_occupancy_rate >= 0.8).length : 0} spaces
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Optimal (60-80%)</span>
                    <span className="text-sm font-medium text-green-600">
                      {analyticsData.metrics ? analyticsData.metrics.filter(m => m.average_occupancy_rate >= 0.6 && m.average_occupancy_rate < 0.8).length : 0} spaces
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Low (&lt;60%)</span>
                    <span className="text-sm font-medium text-yellow-600">
                      {analyticsData.metrics ? analyticsData.metrics.filter(m => m.average_occupancy_rate < 0.6).length : 0} spaces
                    </span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="font-medium mb-3">Efficiency Ratings</h3>
                <div className="space-y-2">
                  {['Excellent', 'Good', 'Fair', 'Poor'].map(rating => (
                    <div key={rating} className="flex justify-between">
                      <span className="text-sm">{rating}</span>
                      <span className="text-sm font-medium">
                        {analyticsData.metrics ? analyticsData.metrics.filter(m => m.efficiency_rating === rating).length : 0} spaces
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-medium mb-3">ROI Potential</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Total Revenue Opportunity</span>
                    <span className="text-sm font-medium text-green-600">
                      {formatCurrency(analyticsData.summary?.total_potential_revenue || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Implementation Investment</span>
                    <span className="text-sm font-medium">
                      {insights.insights ? formatCurrency(insights.insights.reduce((sum, i) => sum + i.implementation_cost, 0)) : '$0'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Net Opportunity</span>
                    <span className="text-sm font-medium text-blue-600">
                      {formatCurrency((analyticsData.summary?.total_potential_revenue || 0) - (insights.insights ? insights.insights.reduce((sum, i) => sum + i.implementation_cost, 0) : 0))}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}