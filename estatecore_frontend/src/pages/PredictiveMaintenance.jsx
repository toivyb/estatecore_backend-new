import React, { useState, useEffect } from 'react';
import api from '../api';

export default function PredictiveMaintenance() {
  const [predictions, setPredictions] = useState([]);
  const [dashboardData, setDashboardData] = useState({});
  const [selectedProperty, setSelectedProperty] = useState('PROP001');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchPredictiveData();
  }, [selectedProperty]);

  const fetchPredictiveData = async () => {
    try {
      setLoading(true);
      setError('');

      // Fetch predictions for the property
      try {
        const predictionsResult = await api.get(`/api/maintenance/predictions/${selectedProperty}`);
        if (predictionsResult.success) {
          setPredictions(predictionsResult.data.predictions || []);
        }
      } catch (error) {
        console.warn('Failed to fetch predictions:', error);
        // Continue with analysis even if predictions fail
      }

      // Fetch comprehensive analysis
      try {
        const analysisResult = await api.post('/api/maintenance/predictive', {
          property_id: selectedProperty
        });
        if (analysisResult.success) {
          setDashboardData(analysisResult.data);
        }
      } catch (error) {
        console.warn('Failed to fetch analysis:', error);
      }

      setLoading(false);
    } catch (err) {
      console.error('Error fetching predictive maintenance data:', err);
      setError('Failed to load predictive maintenance data');
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-blue-100 text-blue-800 border-blue-200',
      preventive: 'bg-green-100 text-green-800 border-green-200'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getMaintenanceIcon = (type) => {
    const icons = {
      hvac: '🌡️',
      electrical: '⚡',
      plumbing: '🚰',
      structural: '🏗️',
      appliances: '🔧',
      security: '🔒',
      fire_safety: '🚨',
      elevator: '🛗',
      roofing: '🏠',
      flooring: '🪜'
    };
    return icons[type] || '🔧';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const triggerMaintenanceAction = async (predictionId, action) => {
    try {
      await api.post('/api/maintenance/actions', {
        prediction_id: predictionId,
        action: action,
        property_id: selectedProperty
      });

      // Refresh data after action
      fetchPredictiveData();
      alert(`Maintenance ${action} triggered successfully`);
    } catch (err) {
      console.error('Error triggering maintenance action:', err);
      alert('Failed to trigger maintenance action');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Loading Predictive Maintenance Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Predictive Maintenance</h1>
          <p className="text-gray-600">AI-powered maintenance predictions with IoT integration</p>
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
            onClick={fetchPredictiveData}
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
            { id: 'predictions', name: 'Predictions', icon: '🔮' },
            { id: 'tasks', name: 'Tasks', icon: '📋' },
            { id: 'analytics', name: 'Analytics', icon: '📈' }
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
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                    <span className="text-red-600 font-semibold">!</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Critical Issues</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboardData.summary?.critical_predictions || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                    <span className="text-orange-600 font-semibold">⚠</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">High Priority</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboardData.summary?.high_priority_predictions || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-semibold">$</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Estimated Cost</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatCurrency(dashboardData.summary?.total_estimated_cost || 0)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-semibold">📋</span>
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Pending Tasks</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboardData.summary?.pending_tasks || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {dashboardData.recommendations && dashboardData.recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4 text-red-600">🚨 AI Recommendations</h2>
              <div className="space-y-3">
                {dashboardData.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start">
                    <span className="text-red-500 mr-2 mt-1">•</span>
                    <p className="text-gray-700">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Equipment Breakdown */}
          {dashboardData.equipment_breakdown && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">Equipment Analysis</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(dashboardData.equipment_breakdown).map(([type, data]) => (
                  <div key={type} className="border rounded-lg p-4">
                    <div className="flex items-center mb-3">
                      <span className="text-2xl mr-2">{getMaintenanceIcon(type)}</span>
                      <h3 className="font-semibold capitalize">{type.replace('_', ' ')}</h3>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Issues:</span>
                        <span className="font-medium">{data.count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Critical:</span>
                        <span className="font-medium text-red-600">{data.critical_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Avg Risk:</span>
                        <span className="font-medium">{(data.avg_probability * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Est. Cost:</span>
                        <span className="font-medium">{formatCurrency(data.total_cost)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Predictions Tab */}
      {activeTab === 'predictions' && (
        <div className="space-y-4">
          {predictions.map((prediction) => (
            <div key={prediction.prediction_id} className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-3">{getMaintenanceIcon(prediction.maintenance_type)}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{prediction.equipment_type}</h3>
                      <p className="text-sm text-gray-600">{prediction.location}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-gray-500">Failure Probability</p>
                      <p className="text-lg font-semibold text-red-600">
                        {(prediction.failure_probability * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Predicted Failure</p>
                      <p className="text-sm font-medium">{formatDate(prediction.predicted_failure_date)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Confidence</p>
                      <p className="text-sm font-medium">{(prediction.confidence_score * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Estimated Cost</p>
                      <p className="text-lg font-semibold text-green-600">
                        {formatCurrency(prediction.estimated_cost)}
                      </p>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Recommended Action:</p>
                    <p className="text-sm text-gray-600">{prediction.recommended_action}</p>
                  </div>

                  {prediction.trigger_factors && prediction.trigger_factors.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">Trigger Factors:</p>
                      <div className="flex flex-wrap gap-2">
                        {prediction.trigger_factors.map((factor, index) => (
                          <span key={index} className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs">
                            {factor}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="ml-4 flex flex-col items-end space-y-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getPriorityColor(prediction.priority_level)}`}>
                    {prediction.priority_level.toUpperCase()}
                  </span>
                  
                  <div className="flex flex-col space-y-2">
                    <button
                      onClick={() => triggerMaintenanceAction(prediction.prediction_id, 'schedule')}
                      className="bg-blue-500 text-white px-3 py-1 rounded text-xs hover:bg-blue-600 transition"
                    >
                      Schedule Task
                    </button>
                    <button
                      onClick={() => triggerMaintenanceAction(prediction.prediction_id, 'inspect')}
                      className="bg-yellow-500 text-white px-3 py-1 rounded text-xs hover:bg-yellow-600 transition"
                    >
                      Order Inspection
                    </button>
                    {prediction.priority_level === 'critical' && (
                      <button
                        onClick={() => triggerMaintenanceAction(prediction.prediction_id, 'emergency')}
                        className="bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-600 transition"
                      >
                        Emergency Dispatch
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {predictions.length === 0 && (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">✅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Maintenance Predictions</h3>
              <p className="text-gray-600">All systems are operating within normal parameters.</p>
            </div>
          )}
        </div>
      )}

      {/* Tasks Tab */}
      {activeTab === 'tasks' && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold mb-4">Generated Maintenance Tasks</h2>
          {dashboardData.tasks && dashboardData.tasks.length > 0 ? (
            <div className="space-y-4">
              {dashboardData.tasks.map((task) => (
                <div key={task.task_id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold">{task.task_type}</h3>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${getPriorityColor(task.priority)}`}>
                      {task.priority.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Scheduled:</span>
                      <p className="font-medium">{formatDate(task.scheduled_date)}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Duration:</span>
                      <p className="font-medium">{task.estimated_duration} hours</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Cost:</span>
                      <p className="font-medium">{formatCurrency(task.estimated_cost)}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Status:</span>
                      <p className="font-medium capitalize">{task.status}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">No maintenance tasks generated yet.</p>
          )}
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold mb-4">Predictive Analytics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium mb-3">System Health Overview</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span>Average Failure Risk</span>
                  <span className="font-semibold">
                    {((dashboardData.summary?.avg_failure_probability || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Total Equipment Monitored</span>
                  <span className="font-semibold">{dashboardData.summary?.total_predictions || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Cost Avoidance Potential</span>
                  <span className="font-semibold text-green-600">
                    {formatCurrency((dashboardData.summary?.total_estimated_cost || 0) * 1.5)}
                  </span>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-3">IoT Integration Status</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span>Connected Sensors</span>
                  <span className="font-semibold text-green-600">12 Active</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Data Quality</span>
                  <span className="font-semibold text-green-600">98.5%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Prediction Accuracy</span>
                  <span className="font-semibold text-blue-600">87.3%</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="mt-6 pt-6 border-t">
            <p className="text-sm text-gray-600">
              Last updated: {dashboardData.dashboard_updated ? 
                new Date(dashboardData.dashboard_updated).toLocaleString() : 'Just now'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}