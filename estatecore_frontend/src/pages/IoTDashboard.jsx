import React, { useState, useEffect } from 'react';
import api from '../api';

export default function IoTDashboard() {
  const [sensorData, setSensorData] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [pipelineStatus, setPipelineStatus] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState('PROP001');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchDashboardData, 10000); // Refresh every 10 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [selectedProperty, autoRefresh]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      // Fetch sensor data
      const sensorResponse = await fetch(`${api.BASE}/api/iot/sensors?property_id=${selectedProperty}`, {
        headers
      });
      
      if (sensorResponse.ok) {
        const sensorResult = await sensorResponse.json();
        if (sensorResult.success && sensorResult.data) {
          setSensorData(sensorResult.data.current_readings || []);
          setAlerts([]); // No alerts in current API response
        }
      }

      // Fetch analytics
      const analyticsResponse = await fetch(`${api.BASE}/api/iot/analytics`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          property_id: selectedProperty,
          hours_back: 24
        })
      });
      
      if (analyticsResponse.ok) {
        const analyticsResult = await analyticsResponse.json();
        if (analyticsResult.success && analyticsResult.data) {
          setAnalytics(analyticsResult.data);
        }
      }

      // Fetch pipeline status
      const pipelineResponse = await fetch(`${api.BASE}/api/realtime/pipeline/status`, {
        headers
      });
      
      if (pipelineResponse.ok) {
        const pipelineResult = await pipelineResponse.json();
        if (pipelineResult.success && pipelineResult.data) {
          setPipelineStatus(pipelineResult.data.analytics_summary || pipelineResult.data);
        }
      }

      setLoading(false);
      setError('');
    } catch (err) {
      console.error('Error fetching IoT dashboard data:', err);
      setError('Failed to load dashboard data');
      setLoading(false);
    }
  };

  const getSensorIcon = (type) => {
    const icons = {
      temperature: '🌡️',
      humidity: '💧',
      occupancy: '👥',
      air_quality: '🌬️',
      energy: '⚡',
      water: '🚰',
      security: '🔒',
      noise: '🔊',
      light: '💡',
      motion: '🚶'
    };
    return icons[type] || '📊';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-blue-100 text-blue-800 border-blue-200'
    };
    return colors[severity] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatValue = (value, unit) => {
    if (typeof value === 'number') {
      return `${value.toFixed(1)} ${unit}`;
    }
    return `${value} ${unit}`;
  };

  const getStatusColor = (status) => {
    return status === 'active' ? 'text-green-600' : 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Loading IoT Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">IoT Dashboard</h1>
          <p className="text-gray-600">Real-time sensor monitoring and analytics</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <label className="mr-2 text-sm">Auto Refresh:</label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
          </div>
          
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
            onClick={fetchDashboardData}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Pipeline Status */}
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Pipeline Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {pipelineStatus.total_streams || 0}
            </div>
            <div className="text-sm text-gray-600">Active Streams</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {pipelineStatus.total_events_processed || 0}
            </div>
            <div className="text-sm text-gray-600">Events Processed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {pipelineStatus.total_subscribers || 0}
            </div>
            <div className="text-sm text-gray-600">Subscribers</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${pipelineStatus.pipeline_status === 'running' ? 'text-green-600' : 'text-red-600'}`}>
              {pipelineStatus.pipeline_status || 'Unknown'}
            </div>
            <div className="text-sm text-gray-600">Pipeline Status</div>
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-red-600">Active Alerts</h2>
          <div className="space-y-3">
            {alerts.map((alert, index) => (
              <div key={index} className={`p-3 rounded border ${getSeverityColor(alert.severity)}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">{alert.sensor_type} Alert</div>
                    <div className="text-sm">{alert.location}</div>
                    <div className="text-sm mt-1">
                      Current: {alert.current_value}, Threshold: {alert.threshold_value}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sensor Readings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        {sensorData.map((sensor, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <span className="text-2xl mr-3">{getSensorIcon(sensor.sensor_type)}</span>
                <div>
                  <h3 className="font-semibold text-gray-900 capitalize">
                    {sensor.sensor_type.replace('_', ' ')}
                  </h3>
                  <p className="text-sm text-gray-600">{sensor.location}</p>
                </div>
              </div>
              <div className={`w-3 h-3 rounded-full ${sensor.alert_triggered ? 'bg-red-500' : 'bg-green-500'}`}></div>
            </div>
            
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {formatValue(sensor.value, sensor.unit)}
            </div>
            
            <div className="flex justify-between text-sm text-gray-600">
              <span>Quality: {sensor.quality}</span>
              <span>{new Date(sensor.timestamp).toLocaleTimeString()}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Analytics Summary */}
      {analytics.sensor_analysis && (
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Analytics Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(analytics.sensor_analysis).map(([sensorType, data]) => (
              <div key={sensorType} className="border rounded-lg p-4">
                <h3 className="font-medium mb-3 capitalize flex items-center">
                  <span className="mr-2">{getSensorIcon(sensorType)}</span>
                  {sensorType.replace('_', ' ')}
                </h3>
                
                {data.average_temperature && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Average:</span>
                      <span className="font-medium">{data.average_temperature}°F</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Range:</span>
                      <span className="font-medium">{data.min_temperature}°F - {data.max_temperature}°F</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Comfort:</span>
                      <span className="font-medium">{data.comfort_percentage}%</span>
                    </div>
                  </div>
                )}
                
                {data.average_humidity && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Average:</span>
                      <span className="font-medium">{data.average_humidity}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Mold Risk:</span>
                      <span className={`font-medium ${data.mold_risk === 'high' ? 'text-red-600' : 'text-green-600'}`}>
                        {data.mold_risk}
                      </span>
                    </div>
                  </div>
                )}
                
                {data.occupancy_rate !== undefined && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Occupancy Rate:</span>
                      <span className="font-medium">{data.occupancy_rate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Pattern:</span>
                      <span className="font-medium capitalize">{data.utilization_pattern?.replace('_', ' ')}</span>
                    </div>
                  </div>
                )}
                
                {data.efficiency_score !== undefined && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Efficiency:</span>
                      <span className="font-medium">{data.efficiency_score}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Monthly Cost:</span>
                      <span className="font-medium">${data.estimated_monthly_cost}</span>
                    </div>
                  </div>
                )}
                
                {data.air_quality_category && (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Category:</span>
                      <span className="font-medium capitalize">{data.air_quality_category.replace('_', ' ')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Average AQI:</span>
                      <span className="font-medium">{data.average_aqi}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insights */}
      {analytics.overall_insights && analytics.overall_insights.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold mb-4">AI Insights</h2>
          <div className="space-y-2">
            {analytics.overall_insights.map((insight, index) => (
              <div key={index} className="flex items-start">
                <span className="text-blue-500 mr-2">💡</span>
                <p className="text-gray-700">{insight}</p>
              </div>
            ))}
          </div>
          
          {analytics.data_quality_score && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Data Quality Score:</span>
                <span className="font-semibold text-lg">{analytics.data_quality_score}%</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}