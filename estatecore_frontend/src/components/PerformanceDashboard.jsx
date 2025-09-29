import React, { useState, useEffect } from 'react';

const PerformanceDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [performanceData, setPerformanceData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [settings, setSettings] = useState({});
  const [slowEndpoints, setSlowEndpoints] = useState([]);
  const [slowQueries, setSlowQueries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPerformanceData();
  }, []);

  const fetchPerformanceData = async () => {
    try {
      setLoading(true);
      
      // Fetch all performance data in parallel
      const [summaryRes, recommendationsRes, settingsRes, endpointsRes, queriesRes] = await Promise.all([
        fetch('/api/performance/summary'),
        fetch('/api/performance/recommendations'),
        fetch('/api/performance/settings'),
        fetch('/api/performance/slow-endpoints'),
        fetch('/api/performance/slow-queries')
      ]);

      if (summaryRes.ok) {
        const summary = await summaryRes.json();
        setPerformanceData(summary);
      }

      if (recommendationsRes.ok) {
        const recs = await recommendationsRes.json();
        setRecommendations(recs.recommendations || []);
      }

      if (settingsRes.ok) {
        const settingsData = await settingsRes.json();
        setSettings(settingsData);
      }

      if (endpointsRes.ok) {
        const endpoints = await endpointsRes.json();
        setSlowEndpoints(endpoints.slow_endpoints || []);
      }

      if (queriesRes.ok) {
        const queries = await queriesRes.json();
        setSlowQueries(queries.slow_queries || []);
      }

    } catch (error) {
      console.error('Error fetching performance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    try {
      const response = await fetch('/api/performance/cache/clear', {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        alert(result.message || 'Cache cleared successfully');
        fetchPerformanceData(); // Refresh data
      } else {
        alert('Failed to clear cache');
      }
    } catch (error) {
      console.error('Error clearing cache:', error);
      alert('Failed to clear cache');
    }
  };

  const handleSettingsUpdate = async (newSettings) => {
    try {
      const response = await fetch('/api/performance/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSettings)
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          alert('Settings updated successfully');
          setSettings({...settings, ...newSettings});
        } else {
          alert(`Failed to update settings: ${result.error}`);
        }
      }
    } catch (error) {
      console.error('Error updating settings:', error);
      alert('Failed to update settings');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (ms) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
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
        <h1 className="text-2xl font-bold text-gray-900">Performance Dashboard</h1>
        <div className="flex gap-2">
          <button
            onClick={handleClearCache}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
          >
            🗑️ Clear Cache
          </button>
          <button
            onClick={fetchPerformanceData}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'recommendations', label: 'Recommendations', icon: '💡' },
            { id: 'endpoints', label: 'Slow Endpoints', icon: '🐌' },
            { id: 'queries', label: 'Slow Queries', icon: '🗃️' },
            { id: 'settings', label: 'Settings', icon: '⚙️' }
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
              {tab.icon} {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && performanceData && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Total Requests</h3>
              <p className="text-2xl font-bold text-gray-900">
                {performanceData.request_stats?.total_requests || 0}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Error Rate</h3>
              <p className="text-2xl font-bold text-red-600">
                {((performanceData.request_stats?.error_rate || 0) * 100).toFixed(2)}%
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Cache Enabled</h3>
              <p className="text-2xl font-bold text-green-600">
                {performanceData.cache_stats?.enabled ? 'Yes' : 'No'}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Cache Keys</h3>
              <p className="text-2xl font-bold text-blue-600">
                {performanceData.cache_stats?.total_keys || 0}
              </p>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Performance Summary</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Slow Endpoints</h4>
                  <p className="text-sm text-gray-600">
                    {performanceData.slow_endpoints?.length || 0} endpoints performing slowly
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Slow Queries</h4>
                  <p className="text-sm text-gray-600">
                    {performanceData.slow_queries?.length || 0} database queries performing slowly
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations Tab */}
      {activeTab === 'recommendations' && (
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Optimization Recommendations ({recommendations.length})
              </h3>
            </div>
            <div className="divide-y divide-gray-200">
              {recommendations.length === 0 ? (
                <div className="p-6 text-center text-gray-500">
                  🎉 No performance issues detected! Your system is running optimally.
                </div>
              ) : (
                recommendations.map((rec, index) => (
                  <div key={index} className="p-6">
                    <div className="flex items-start space-x-3">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(rec.priority)}`}>
                        {rec.priority}
                      </span>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{rec.title}</h4>
                        <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                        <p className="text-sm font-medium text-blue-600 mt-2">
                          💡 Action: {rec.action}
                        </p>
                        {rec.affected_endpoints && (
                          <div className="mt-2">
                            <span className="text-xs text-gray-500">Affected endpoints: </span>
                            <span className="text-xs text-gray-700">
                              {rec.affected_endpoints.join(', ')}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Slow Endpoints Tab */}
      {activeTab === 'endpoints' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              Slow Endpoints ({slowEndpoints.length})
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Endpoint
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Requests
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Error Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    P95 Duration
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {slowEndpoints.map((endpoint, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {endpoint.endpoint}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDuration(endpoint.avg_duration * 1000)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {endpoint.total_requests}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        endpoint.error_rate > 0.1 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {(endpoint.error_rate * 100).toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDuration(endpoint.p95_duration * 1000)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Slow Queries Tab */}
      {activeTab === 'queries' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              Slow Database Queries ({slowQueries.length})
            </h3>
          </div>
          <div className="divide-y divide-gray-200">
            {slowQueries.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                No slow queries detected
              </div>
            ) : (
              slowQueries.map((query, index) => (
                <div key={index} className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900">Query #{index + 1}</span>
                        <span className="text-sm text-gray-500">
                          ({query.execution_count} executions)
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1 font-mono bg-gray-50 p-2 rounded">
                        {query.query_preview}...
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-red-600">
                        {formatDuration(query.avg_duration_ms)}
                      </div>
                      <div className="text-xs text-gray-500">avg duration</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Performance Settings</h3>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cache Enabled
                </label>
                <select
                  value={settings.cache_enabled ? 'true' : 'false'}
                  onChange={(e) => handleSettingsUpdate({cache_enabled: e.target.value === 'true'})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cache Default TTL (seconds)
                </label>
                <input
                  type="number"
                  value={settings.cache_default_ttl || 300}
                  onChange={(e) => handleSettingsUpdate({cache_default_ttl: parseInt(e.target.value)})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  min="30"
                  max="3600"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slow Query Threshold (ms)
                </label>
                <input
                  type="number"
                  value={settings.slow_query_threshold_ms || 500}
                  onChange={(e) => handleSettingsUpdate({slow_query_threshold_ms: parseInt(e.target.value)})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  min="100"
                  max="5000"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slow Endpoint Threshold (ms)
                </label>
                <input
                  type="number"
                  value={settings.slow_endpoint_threshold_ms || 1000}
                  onChange={(e) => handleSettingsUpdate({slow_endpoint_threshold_ms: parseInt(e.target.value)})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  min="200"
                  max="10000"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Query Caching
                </label>
                <select
                  value={settings.enable_query_caching ? 'true' : 'false'}
                  onChange={(e) => handleSettingsUpdate({enable_query_caching: e.target.value === 'true'})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GZIP Compression
                </label>
                <select
                  value={settings.enable_gzip_compression ? 'true' : 'false'}
                  onChange={(e) => handleSettingsUpdate({enable_gzip_compression: e.target.value === 'true'})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Help Section */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-2">Performance Optimization Tips</h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p><strong>Cache Management:</strong> Enable caching for frequently accessed data. Adjust TTL based on data freshness requirements.</p>
          <p><strong>Database Optimization:</strong> Monitor slow queries and add indexes where needed. Consider query caching for expensive operations.</p>
          <p><strong>API Performance:</strong> Watch for slow endpoints and implement pagination or caching as needed.</p>
          <p><strong>Regular Monitoring:</strong> Check recommendations regularly and clear cache when deploying updates.</p>
        </div>
      </div>
    </div>
  );
};

export default PerformanceDashboard;