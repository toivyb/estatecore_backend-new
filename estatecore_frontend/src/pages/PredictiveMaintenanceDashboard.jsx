import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

const PredictiveMaintenanceDashboard = () => {
  const [activeTab, setActiveTab] = useState('predict');
  const [propertyId, setPropertyId] = useState('1');
  const [predictions, setPredictions] = useState([]);
  const [optimization, setOptimization] = useState(null);
  const [insights, setInsights] = useState(null);
  const [costAnalysis, setCostAnalysis] = useState(null);
  const [equipment, setEquipment] = useState([]);
  const [loading, setLoading] = useState(false);

  const tabs = [
    { id: 'predict', label: 'Maintenance Predictions', icon: '🔮' },
    { id: 'optimize', label: 'Cost Optimization', icon: '💰' },
    { id: 'insights', label: 'Property Insights', icon: '📊' },
    { id: 'equipment', label: 'Equipment Management', icon: '🔧' },
    { id: 'history', label: 'Maintenance History', icon: '📋' }
  ];

  const maintenanceTypes = [
    'hvac', 'plumbing', 'electrical', 'appliance', 'structural', 
    'roofing', 'flooring', 'painting', 'landscaping', 'security'
  ];

  const optimizationStrategies = [
    { value: 'cost_minimization', label: 'Cost Minimization' },
    { value: 'time_efficiency', label: 'Time Efficiency' },
    { value: 'resource_balancing', label: 'Resource Balancing' },
    { value: 'tenant_impact_minimization', label: 'Minimize Tenant Impact' }
  ];

  useEffect(() => {
    if (activeTab === 'predict') {
      predictMaintenance();
    } else if (activeTab === 'insights') {
      getPropertyInsights();
    }
  }, [activeTab, propertyId]);

  const predictMaintenance = async () => {
    setLoading(true);

    try {
      const response = await fetch('/api/maintenance/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_id: parseInt(propertyId),
          prediction_days: 90
        })
      });

      const result = await response.json();
      if (result.success) {
        setPredictions(result.predictions || []);
      } else {
        alert(result.error || 'Failed to predict maintenance needs');
      }
    } catch (error) {
      console.error('Error predicting maintenance:', error);
      alert('Error predicting maintenance needs');
    } finally {
      setLoading(false);
    }
  };

  const optimizeCosts = async (strategy = 'cost_minimization') => {
    setLoading(true);

    try {
      const response = await fetch('/api/maintenance/optimize-costs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_id: parseInt(propertyId),
          strategy: strategy,
          prediction_days: 90
        })
      });

      const result = await response.json();
      if (result.success) {
        setOptimization(result.optimization_result);
      } else {
        alert(result.error || 'Failed to optimize costs');
      }
    } catch (error) {
      console.error('Error optimizing costs:', error);
      alert('Error optimizing costs');
    } finally {
      setLoading(false);
    }
  };

  const getPropertyInsights = async () => {
    setLoading(true);

    try {
      const response = await fetch(`/api/maintenance/insights/${propertyId}`);
      const result = await response.json();
      if (result.success) {
        setInsights(result.insights);
      } else {
        alert(result.error || 'Failed to get insights');
      }
    } catch (error) {
      console.error('Error getting insights:', error);
      alert('Error getting property insights');
    } finally {
      setLoading(false);
    }
  };

  const getCostAnalysis = async () => {
    setLoading(true);

    try {
      const response = await fetch('/api/maintenance/cost-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_id: parseInt(propertyId),
          prediction_days: 90
        })
      });

      const result = await response.json();
      if (result.success) {
        setCostAnalysis(result.cost_analysis_report);
      } else {
        alert(result.error || 'Failed to get cost analysis');
      }
    } catch (error) {
      console.error('Error getting cost analysis:', error);
      alert('Error getting cost analysis');
    } finally {
      setLoading(false);
    }
  };

  const addEquipment = async (equipmentData) => {
    try {
      const response = await fetch('/api/maintenance/equipment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(equipmentData)
      });

      const result = await response.json();
      if (result.success) {
        alert('Equipment added successfully');
      } else {
        alert(result.error || 'Failed to add equipment');
      }
    } catch (error) {
      console.error('Error adding equipment:', error);
      alert('Error adding equipment');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-100 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-100 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-100 border-green-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const renderPredictTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Maintenance Predictions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-4 mb-4">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2">Property ID</label>
              <input
                type="number"
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter property ID"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={predictMaintenance}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Predicting...' : 'Predict Maintenance'}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {predictions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Predicted Maintenance Items ({predictions.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {predictions.map((prediction, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-lg capitalize">
                        {prediction.maintenance_type.replace('_', ' ')}
                      </h3>
                      <p className="text-sm text-gray-600">{prediction.reason}</p>
                    </div>
                    <div className="text-right">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getPriorityColor(prediction.priority)}`}>
                        {prediction.priority}
                      </span>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(prediction.predicted_date)}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <div className="font-semibold text-blue-600">
                        {(prediction.confidence_score * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-600">Confidence</div>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <div className="font-semibold text-green-600">
                        ${prediction.estimated_cost_range[0]} - ${prediction.estimated_cost_range[1]}
                      </div>
                      <div className="text-xs text-gray-600">Est. Cost</div>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <div className="font-semibold text-purple-600">
                        {prediction.estimated_duration_hours}h
                      </div>
                      <div className="text-xs text-gray-600">Duration</div>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <div className="font-semibold text-red-600">
                        ${prediction.cost_impact_if_delayed?.toFixed(0)}
                      </div>
                      <div className="text-xs text-gray-600">If Delayed</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {prediction.preventive_actions && prediction.preventive_actions.length > 0 && (
                      <div>
                        <h4 className="font-medium text-sm mb-2 text-green-700">Preventive Actions:</h4>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {prediction.preventive_actions.map((action, i) => (
                            <li key={i} className="flex items-start">
                              <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2 mt-1.5 flex-shrink-0"></span>
                              {action}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {prediction.warning_signs && prediction.warning_signs.length > 0 && (
                      <div>
                        <h4 className="font-medium text-sm mb-2 text-orange-700">Warning Signs:</h4>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {prediction.warning_signs.map((sign, i) => (
                            <li key={i} className="flex items-start">
                              <span className="w-1.5 h-1.5 bg-orange-500 rounded-full mr-2 mt-1.5 flex-shrink-0"></span>
                              {sign}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex justify-between items-center text-xs text-gray-500">
                      <span>Model: {prediction.model_version}</span>
                      <span>
                        Optimal window: {formatDate(prediction.optimal_window_start)} - {formatDate(prediction.optimal_window_end)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderOptimizeTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Cost Optimization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Property ID</label>
                <input
                  type="number"
                  value={propertyId}
                  onChange={(e) => setPropertyId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter property ID"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Optimization Strategy</label>
                <select 
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onChange={(e) => optimizeCosts(e.target.value)}
                >
                  {optimizationStrategies.map(strategy => (
                    <option key={strategy.value} value={strategy.value}>
                      {strategy.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={getCostAnalysis}
                  disabled={loading}
                  className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Analyzing...' : 'Get Cost Analysis'}
                </button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {optimization && (
        <Card>
          <CardHeader>
            <CardTitle>Optimization Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    ${optimization.original_total_cost?.toFixed(0)}
                  </div>
                  <div className="text-sm text-gray-600">Original Cost</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    ${optimization.optimized_total_cost?.toFixed(0)}
                  </div>
                  <div className="text-sm text-gray-600">Optimized Cost</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    ${optimization.cost_savings?.toFixed(0)}
                  </div>
                  <div className="text-sm text-gray-600">Savings</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {optimization.savings_percentage?.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-600">Savings %</div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="font-bold text-gray-700">{optimization.total_project_duration_days}</div>
                  <div className="text-sm text-gray-600">Project Days</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="font-bold text-gray-700">{optimization.tenant_disruption_hours}</div>
                  <div className="text-sm text-gray-600">Disruption Hours</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="font-bold text-gray-700">{optimization.optimized_schedule?.length || 0}</div>
                  <div className="text-sm text-gray-600">Scheduled Items</div>
                </div>
              </div>

              {optimization.optimized_schedule && optimization.optimized_schedule.length > 0 && (
                <div>
                  <h3 className="font-medium mb-3">Optimized Schedule</h3>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {optimization.optimized_schedule.map((item, index) => (
                      <div key={index} className="flex justify-between items-center p-3 border border-gray-200 rounded">
                        <div>
                          <div className="font-medium capitalize">{item.maintenance_type.replace('_', ' ')}</div>
                          <div className="text-sm text-gray-600">
                            {formatDate(item.scheduled_date)} • {item.estimated_duration}h
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">${item.estimated_cost?.toFixed(0)}</div>
                          <div className="text-xs text-gray-500">{item.contractor_id}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {optimization.recommendations && optimization.recommendations.length > 0 && (
                <div>
                  <h3 className="font-medium mb-3">Recommendations</h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                    {optimization.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {costAnalysis && (
        <Card>
          <CardHeader>
            <CardTitle>Cost Analysis Report</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {costAnalysis.executive_summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded">
                    <div className="font-bold text-blue-600">
                      ${costAnalysis.executive_summary.total_expected_costs?.toFixed(0)}
                    </div>
                    <div className="text-xs text-gray-600">Expected Costs</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded">
                    <div className="font-bold text-green-600">
                      ${costAnalysis.executive_summary.optimization_potential?.toFixed(0)}
                    </div>
                    <div className="text-xs text-gray-600">Optimization Potential</div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded">
                    <div className="font-bold text-red-600">
                      {costAnalysis.executive_summary.critical_items_count}
                    </div>
                    <div className="text-xs text-gray-600">Critical Items</div>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded">
                    <div className="font-bold text-purple-600">
                      {costAnalysis.executive_summary.timeline_span_days}
                    </div>
                    <div className="text-xs text-gray-600">Timeline Days</div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderInsightsTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Property Maintenance Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-4 mb-4">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2">Property ID</label>
              <input
                type="number"
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter property ID"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={getPropertyInsights}
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Loading...' : 'Get Insights'}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {insights && (
        <div className="space-y-6">
          {insights.upcoming_maintenance && insights.upcoming_maintenance.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Upcoming Maintenance (Next 5 Items)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {insights.upcoming_maintenance.map((item, index) => (
                    <div key={index} className="flex justify-between items-center p-3 border border-gray-200 rounded">
                      <div>
                        <div className="font-medium capitalize">{item.type.replace('_', ' ')}</div>
                        <div className="text-sm text-gray-600">{formatDate(item.predicted_date)}</div>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(item.priority)}`}>
                          {item.priority}
                        </span>
                        <div className="text-sm text-gray-600 mt-1">
                          ${item.estimated_cost_range[0]} - ${item.estimated_cost_range[1]}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {insights.metrics && (
            <Card>
              <CardHeader>
                <CardTitle>Property Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">📊</div>
                  <p>Property metrics will be displayed here</p>
                  <p className="text-sm">Including maintenance frequency, cost trends, and performance indicators</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );

  const renderEquipmentTab = () => {
    const [equipmentForm, setEquipmentForm] = useState({
      equipment_id: '',
      property_id: propertyId,
      equipment_type: 'hvac',
      brand: '',
      model: '',
      installation_date: '',
      operating_hours: 0,
      replacement_cost: 0
    });

    const handleEquipmentSubmit = async (e) => {
      e.preventDefault();
      await addEquipment(equipmentForm);
      setEquipmentForm({
        equipment_id: '',
        property_id: propertyId,
        equipment_type: 'hvac',
        brand: '',
        model: '',
        installation_date: '',
        operating_hours: 0,
        replacement_cost: 0
      });
    };

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Add Equipment</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleEquipmentSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Equipment ID</label>
                  <input
                    type="text"
                    value={equipmentForm.equipment_id}
                    onChange={(e) => setEquipmentForm({...equipmentForm, equipment_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Property ID</label>
                  <input
                    type="number"
                    value={equipmentForm.property_id}
                    onChange={(e) => setEquipmentForm({...equipmentForm, property_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Equipment Type</label>
                  <select
                    value={equipmentForm.equipment_type}
                    onChange={(e) => setEquipmentForm({...equipmentForm, equipment_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {maintenanceTypes.map(type => (
                      <option key={type} value={type} className="capitalize">
                        {type.replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Brand</label>
                  <input
                    type="text"
                    value={equipmentForm.brand}
                    onChange={(e) => setEquipmentForm({...equipmentForm, brand: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Model</label>
                  <input
                    type="text"
                    value={equipmentForm.model}
                    onChange={(e) => setEquipmentForm({...equipmentForm, model: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Installation Date</label>
                  <input
                    type="date"
                    value={equipmentForm.installation_date}
                    onChange={(e) => setEquipmentForm({...equipmentForm, installation_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Operating Hours</label>
                  <input
                    type="number"
                    value={equipmentForm.operating_hours}
                    onChange={(e) => setEquipmentForm({...equipmentForm, operating_hours: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Replacement Cost ($)</label>
                  <input
                    type="number"
                    value={equipmentForm.replacement_cost}
                    onChange={(e) => setEquipmentForm({...equipmentForm, replacement_cost: parseFloat(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
              >
                Add Equipment
              </button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderHistoryTab = () => (
    <Card>
      <CardHeader>
        <CardTitle>Maintenance History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-4">📋</div>
          <p>Maintenance history will appear here</p>
          <p className="text-sm">Track completed maintenance work and performance metrics</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Predictive Maintenance Dashboard</h1>
        <p className="text-gray-600">AI-powered maintenance prediction and cost optimization</p>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
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
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'predict' && renderPredictTab()}
        {activeTab === 'optimize' && renderOptimizeTab()}
        {activeTab === 'insights' && renderInsightsTab()}
        {activeTab === 'equipment' && renderEquipmentTab()}
        {activeTab === 'history' && renderHistoryTab()}
      </div>
    </div>
  );
};

export default PredictiveMaintenanceDashboard;