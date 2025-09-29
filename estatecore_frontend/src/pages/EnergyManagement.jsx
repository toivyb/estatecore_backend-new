import React, { useState, useEffect } from 'react';

const EnergyManagement = () => {
  const [selectedProperty, setSelectedProperty] = useState('1');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardData, setDashboardData] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [simulateLoading, setSimulateLoading] = useState(false);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/energy/dashboard/${selectedProperty}`);
      const data = await response.json();
      
      if (data.success) {
        setDashboardData(data.dashboard);
      } else {
        console.error('Failed to fetch dashboard data:', data.error);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch forecast
  const fetchForecast = async (energyType = 'electricity', days = 7) => {
    try {
      const response = await fetch(`/api/energy/forecast/${selectedProperty}/${energyType}?days=${days}`);
      const data = await response.json();
      
      if (data.success) {
        setForecast(data);
      }
    } catch (error) {
      console.error('Error fetching forecast:', error);
    }
  };

  // Fetch recommendations
  const fetchRecommendations = async () => {
    try {
      const response = await fetch(`/api/energy/recommendations/${selectedProperty}`);
      const data = await response.json();
      
      if (data.success) {
        setRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  // Fetch alerts
  const fetchAlerts = async () => {
    try {
      const response = await fetch(`/api/energy/alerts?property_id=${selectedProperty}`);
      const data = await response.json();
      
      if (data.success) {
        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  // Simulate energy data
  const simulateEnergyData = async () => {
    setSimulateLoading(true);
    try {
      const response = await fetch(`/api/energy/simulate/${selectedProperty}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ days: 30 })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert(`Successfully simulated ${data.readings_added} energy readings with ${data.total_alerts_generated} alerts generated!`);
        // Refresh all data
        fetchDashboardData();
        fetchForecast();
        fetchRecommendations();
        fetchAlerts();
      } else {
        alert(`Failed to simulate data: ${data.error}`);
      }
    } catch (error) {
      console.error('Error simulating data:', error);
      alert('Failed to simulate energy data');
    } finally {
      setSimulateLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchForecast();
    fetchRecommendations();
    fetchAlerts();
  }, [selectedProperty]);

  // Dashboard Tab Component
  const DashboardTab = () => (
    <div className="space-y-6">
      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
          <button
            onClick={simulateEnergyData}
            disabled={simulateLoading}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {simulateLoading ? 'Simulating...' : '🔄 Simulate Energy Data'}
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">⚡</div>
            <div className="text-sm text-gray-600">Total Consumption</div>
            <div className="font-semibold text-blue-600">
              {dashboardData?.analytics?.total_consumption?.toFixed(1) || 'N/A'} kWh
            </div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">💰</div>
            <div className="text-sm text-gray-600">Total Cost</div>
            <div className="font-semibold text-green-600">
              ${dashboardData?.analytics?.total_cost?.toFixed(2) || 'N/A'}
            </div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-sm text-gray-600">Efficiency Score</div>
            <div className="font-semibold text-yellow-600">
              {dashboardData?.analytics?.efficiency_score || 'N/A'}%
            </div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">🚨</div>
            <div className="text-sm text-gray-600">Active Alerts</div>
            <div className="font-semibold text-red-600">
              {alerts.length}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      {alerts.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Alerts</h3>
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert, index) => (
              <div key={index} className={`p-4 rounded-lg border-l-4 ${
                alert.severity === 'critical' ? 'bg-red-50 border-red-500' :
                alert.severity === 'high' ? 'bg-orange-50 border-orange-500' :
                alert.severity === 'medium' ? 'bg-yellow-50 border-yellow-500' :
                'bg-blue-50 border-blue-500'
              }`}>
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium text-gray-900">{alert.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      {alert.energy_type} • Current: {alert.current_value} • Threshold: {alert.threshold_value}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded ${
                    alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                    alert.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                    alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {alert.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Optimization Opportunities</h3>
          <div className="space-y-4">
            {recommendations.slice(0, 3).map((rec, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium text-gray-900">{rec.title}</h4>
                  <span className="bg-green-100 text-green-800 px-2 py-1 text-xs font-medium rounded">
                    Priority: {rec.priority_score}/10
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">{rec.description}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Monthly Savings:</span>
                    <div className="font-medium text-green-600">${rec.potential_savings}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Implementation Cost:</span>
                    <div className="font-medium">${rec.implementation_cost}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Payback Period:</span>
                    <div className="font-medium">{rec.payback_period_months} months</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Energy Reduction:</span>
                    <div className="font-medium">{rec.energy_reduction_percent}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Forecast Tab Component
  const ForecastTab = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">7-Day Energy Forecast</h3>
          <div className="flex gap-2">
            <button
              onClick={() => fetchForecast('electricity', 7)}
              className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm"
            >
              Electricity
            </button>
            <button
              onClick={() => fetchForecast('gas', 7)}
              className="px-3 py-1 bg-green-100 text-green-800 rounded text-sm"
            >
              Gas
            </button>
            <button
              onClick={() => fetchForecast('hvac', 7)}
              className="px-3 py-1 bg-orange-100 text-orange-800 rounded text-sm"
            >
              HVAC
            </button>
          </div>
        </div>
        
        {forecast && forecast.success ? (
          <div>
            {/* Forecast Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-600">Total Predicted</div>
                <div className="font-semibold text-blue-600">
                  {forecast.summary?.total_predicted_consumption?.toFixed(1)} kWh
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-600">Total Cost</div>
                <div className="font-semibold text-green-600">
                  ${forecast.summary?.total_predicted_cost?.toFixed(2)}
                </div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-600">Daily Average</div>
                <div className="font-semibold text-yellow-600">
                  {forecast.summary?.average_daily_consumption?.toFixed(1)} kWh
                </div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-600">Peak Day</div>
                <div className="font-semibold text-red-600">
                  {forecast.summary?.peak_day}
                </div>
              </div>
            </div>

            {/* Daily Breakdown */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Predicted Consumption
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Predicted Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Confidence Range
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {forecast.forecast?.forecast_dates?.map((date, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {new Date(date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {forecast.forecast.predicted_consumption[index]?.toFixed(1)} kWh
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${forecast.forecast.predicted_cost[index]?.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {forecast.forecast.confidence_intervals[index] ? 
                          `${forecast.forecast.confidence_intervals[index][0]?.toFixed(1)} - ${forecast.forecast.confidence_intervals[index][1]?.toFixed(1)} kWh`
                          : 'N/A'
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-gray-500">No forecast data available. Try simulating some energy data first.</div>
          </div>
        )}
      </div>
    </div>
  );

  // Recommendations Tab Component
  const RecommendationsTab = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Powered Optimization Recommendations</h3>
        
        {recommendations.length > 0 ? (
          <div className="space-y-6">
            {recommendations.map((rec, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-medium text-gray-900">{rec.title}</h4>
                    <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 text-xs font-medium rounded mt-1">
                      {rec.recommendation_type.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-green-600">
                      Priority: {rec.priority_score}/10
                    </div>
                  </div>
                </div>
                
                <p className="text-gray-600 mb-4">{rec.description}</p>
                
                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="bg-green-50 p-3 rounded">
                    <div className="text-sm text-gray-600">Monthly Savings</div>
                    <div className="font-semibold text-green-600">${rec.potential_savings}</div>
                  </div>
                  <div className="bg-blue-50 p-3 rounded">
                    <div className="text-sm text-gray-600">Implementation Cost</div>
                    <div className="font-semibold text-blue-600">${rec.implementation_cost}</div>
                  </div>
                  <div className="bg-yellow-50 p-3 rounded">
                    <div className="text-sm text-gray-600">Payback Period</div>
                    <div className="font-semibold text-yellow-600">{rec.payback_period_months} months</div>
                  </div>
                  <div className="bg-purple-50 p-3 rounded">
                    <div className="text-sm text-gray-600">Energy Reduction</div>
                    <div className="font-semibold text-purple-600">{rec.energy_reduction_percent}%</div>
                  </div>
                </div>
                
                {/* Equipment Involved */}
                {rec.equipment_involved && rec.equipment_involved.length > 0 && (
                  <div className="mb-4">
                    <h5 className="font-medium text-gray-900 mb-2">Equipment Involved:</h5>
                    <div className="flex flex-wrap gap-2">
                      {rec.equipment_involved.map((equipment, i) => (
                        <span key={i} className="bg-gray-100 text-gray-800 px-2 py-1 text-sm rounded">
                          {equipment}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Implementation Steps */}
                {rec.implementation_steps && rec.implementation_steps.length > 0 && (
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2">Implementation Steps:</h5>
                    <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                      {rec.implementation_steps.map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-gray-500">No recommendations available. Try simulating some energy data first.</div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Smart Energy Management</h1>
              <p className="mt-2 text-sm text-gray-600">
                AI-powered energy optimization and consumption analysis
              </p>
            </div>
            <div>
              <select
                value={selectedProperty}
                onChange={(e) => setSelectedProperty(e.target.value)}
                className="block w-40 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="1">Property 1</option>
                <option value="2">Property 2</option>
                <option value="3">Property 3</option>
              </select>
            </div>
          </div>
          
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'dashboard', name: 'Dashboard', icon: '📊' },
                { id: 'forecast', name: 'Forecast', icon: '📈' },
                { id: 'recommendations', name: 'Recommendations', icon: '💡' },
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
                  {tab.icon} {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && <DashboardTab />}
            {activeTab === 'forecast' && <ForecastTab />}
            {activeTab === 'recommendations' && <RecommendationsTab />}
          </>
        )}
      </div>
    </div>
  );
};

export default EnergyManagement;