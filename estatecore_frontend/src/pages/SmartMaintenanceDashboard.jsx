import React, { useState, useEffect } from 'react';

const SmartMaintenanceDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [maintenanceData, setMaintenanceData] = useState(null);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGeneratingPredictions, setIsGeneratingPredictions] = useState(false);

  useEffect(() => {
    fetchMaintenanceData();
  }, []);

  const fetchMaintenanceData = async () => {
    try {
      setIsLoading(true);
      
      // Mock data - replace with actual API calls
      const mockData = {
        overview: {
          total_maintenance_items: 47,
          pending_items: 12,
          completed_items: 28,
          overdue_items: 3,
          completion_rate: 0.82,
          total_estimated_cost: 24500,
          total_actual_cost: 22750
        },
        recent_maintenance: [
          {
            id: 'maint_001',
            property_id: 123,
            title: 'HVAC Filter Replacement',
            category: 'hvac',
            priority: 'medium',
            status: 'scheduled',
            scheduled_date: '2024-09-30T10:00:00Z',
            estimated_cost: 75,
            assigned_contractor: 'HVAC Pro Services',
            ai_generated: true,
            confidence_score: 0.92
          },
          {
            id: 'maint_002',
            property_id: 123,
            title: 'Plumbing Leak Repair',
            category: 'plumbing',
            priority: 'high',
            status: 'in_progress',
            scheduled_date: '2024-09-28T14:00:00Z',
            estimated_cost: 250,
            assigned_contractor: 'Elite Plumbing Co',
            ai_generated: false,
            confidence_score: 0.0
          },
          {
            id: 'maint_003',
            property_id: 456,
            title: 'Electrical Panel Inspection',
            category: 'electrical',
            priority: 'high',
            status: 'completed',
            scheduled_date: '2024-09-25T09:00:00Z',
            estimated_cost: 200,
            actual_cost: 185,
            assigned_contractor: 'Spark Electric',
            ai_generated: true,
            confidence_score: 0.88
          }
        ],
        equipment_summary: {
          total_equipment: 156,
          equipment_by_category: {
            'hvac': 24,
            'plumbing': 18,
            'electrical': 32,
            'appliances': 45,
            'security': 12,
            'general': 25
          },
          equipment_needing_attention: [
            {
              id: 'eq_001',
              name: 'Central HVAC Unit #1',
              category: 'hvac',
              property_id: 123,
              predicted_failure_date: '2024-11-15',
              confidence: 0.85,
              recommended_action: 'Schedule maintenance'
            },
            {
              id: 'eq_002',
              name: 'Water Heater #2',
              category: 'plumbing',
              property_id: 456,
              predicted_failure_date: '2024-12-01',
              confidence: 0.78,
              recommended_action: 'Monitor closely'
            }
          ]
        },
        upcoming_maintenance: [
          {
            id: 'maint_004',
            title: 'Roof Inspection',
            category: 'roofing',
            priority: 'medium',
            scheduled_date: '2024-10-01T08:00:00Z',
            estimated_cost: 300,
            property_address: '123 Main St'
          },
          {
            id: 'maint_005',
            title: 'Landscaping Maintenance',
            category: 'landscaping',
            priority: 'low',
            scheduled_date: '2024-10-02T10:00:00Z',
            estimated_cost: 150,
            property_address: '456 Oak Ave'
          }
        ],
        predictions: [
          {
            prediction_id: 'pred_001',
            property_id: 123,
            equipment_id: 'eq_001',
            predicted_failure_date: '2024-11-15T00:00:00Z',
            confidence_score: 0.85,
            risk_factors: ['Equipment age', 'Usage patterns'],
            recommended_actions: ['Schedule maintenance', 'Replace filters'],
            estimated_cost: 400,
            severity_level: 'high',
            maintenance_category: 'hvac'
          },
          {
            prediction_id: 'pred_002',
            property_id: 456,
            equipment_id: 'eq_002',
            predicted_failure_date: '2024-12-01T00:00:00Z',
            confidence_score: 0.78,
            risk_factors: ['Normal wear', 'Temperature fluctuations'],
            recommended_actions: ['Monitor temperature', 'Check pressure'],
            estimated_cost: 200,
            severity_level: 'medium',
            maintenance_category: 'plumbing'
          }
        ]
      };
      
      setMaintenanceData(mockData);
      
    } catch (error) {
      console.error('Error fetching maintenance data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generatePredictiveMaintenance = async (propertyId) => {
    try {
      setIsGeneratingPredictions(true);
      
      console.log('Generating predictive maintenance for property:', propertyId);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Mock successful prediction generation
      alert(`Generated 5 new maintenance predictions for property ${propertyId}!`);
      
      // Refresh data
      await fetchMaintenanceData();
      
    } catch (error) {
      console.error('Error generating predictions:', error);
      alert('Failed to generate predictions. Please try again.');
    } finally {
      setIsGeneratingPredictions(false);
    }
  };

  const optimizeSchedule = async (propertyId) => {
    try {
      console.log('Optimizing maintenance schedule for property:', propertyId);
      alert(`Found 3 optimization opportunities that could save $250 in costs!`);
    } catch (error) {
      console.error('Error optimizing schedule:', error);
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

  const formatDate = (dateString) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(new Date(dateString));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100 border-green-200';
      case 'in_progress': return 'text-blue-600 bg-blue-100 border-blue-200';
      case 'scheduled': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'overdue': return 'text-red-600 bg-red-100 border-red-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      case 'emergency': return 'text-purple-600 bg-purple-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'hvac': return <Settings className="w-4 h-4" />;
      case 'plumbing': return <Wrench className="w-4 h-4" />;
      case 'electrical': return <Zap className="w-4 h-4" />;
      case 'roofing': return <Activity className="w-4 h-4" />;
      case 'appliances': return <Tool className="w-4 h-4" />;
      default: return <Wrench className="w-4 h-4" />;
    }
  };

  const StatCard = ({ title, value, subtitle, icon: Icon, color = 'blue', trend = null, onClick = null }) => (
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
              <TrendingUp className="w-4 h-4 mr-1" />
              <span className="text-sm font-medium">{Math.abs(trend)}%</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full bg-${color}-100 dark:bg-${color}-900/20`}>
          <Icon className={`w-6 h-6 text-${color}-600 dark:text-${color}-400`} />
        </div>
      </div>
    </div>
  );

  const MaintenanceCard = ({ item }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-full bg-blue-100 dark:bg-blue-900/20">
            {getCategoryIcon(item.category)}
          </div>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white">{item.title}</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">Property #{item.property_id}</p>
            {item.ai_generated && (
              <div className="flex items-center mt-1">
                <Brain className="w-3 h-3 text-purple-500 mr-1" />
                <span className="text-xs text-purple-600">AI Generated ({(item.confidence_score * 100).toFixed(0)}%)</span>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex flex-col items-end space-y-1">
          <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(item.status)}`}>
            {item.status.replace('_', ' ')}
          </span>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getPriorityColor(item.priority)}`}>
            {item.priority}
          </span>
        </div>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">Estimated Cost:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {formatCurrency(item.estimated_cost)}
          </span>
        </div>
        
        {item.actual_cost && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-500 dark:text-gray-400">Actual Cost:</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {formatCurrency(item.actual_cost)}
            </span>
          </div>
        )}
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">Scheduled:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {formatDate(item.scheduled_date)}
          </span>
        </div>
        
        {item.assigned_contractor && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-500 dark:text-gray-400">Contractor:</span>
            <span className="font-medium text-gray-900 dark:text-white">
              {item.assigned_contractor}
            </span>
          </div>
        )}
      </div>
      
      <div className="flex justify-between space-x-2">
        <button
          onClick={() => setSelectedItem(item)}
          className="flex items-center px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Eye className="w-3 h-3 mr-1" />
          View Details
        </button>
        <button
          className="flex items-center px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          <Edit className="w-3 h-3 mr-1" />
          Edit
        </button>
      </div>
    </div>
  );

  const PredictionCard = ({ prediction }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border-l-4 border-orange-500">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-medium text-gray-900 dark:text-white">
            Equipment Alert
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {prediction.maintenance_category.replace('_', ' ').toUpperCase()} System
          </p>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          prediction.severity_level === 'high' ? 'bg-red-100 text-red-800' :
          prediction.severity_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
          'bg-green-100 text-green-800'
        }`}>
          {prediction.severity_level} risk
        </span>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">Predicted Failure:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {formatDate(prediction.predicted_failure_date)}
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">Confidence:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {(prediction.confidence_score * 100).toFixed(0)}%
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500 dark:text-gray-400">Est. Cost:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {formatCurrency(prediction.estimated_cost)}
          </span>
        </div>
      </div>
      
      <div className="mb-4">
        <h5 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Recommended Actions:</h5>
        <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
          {prediction.recommended_actions.map((action, index) => (
            <li key={index}>• {action}</li>
          ))}
        </ul>
      </div>
      
      <button className="w-full flex items-center justify-center px-3 py-2 bg-orange-600 text-white text-xs rounded hover:bg-orange-700">
        <Calendar className="w-3 h-3 mr-1" />
        Schedule Maintenance
      </button>
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
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Smart Maintenance</h1>
              <p className="text-gray-600 dark:text-gray-400">AI-powered maintenance scheduling and predictive analytics</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => generatePredictiveMaintenance(123)}
                disabled={isGeneratingPredictions}
                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {isGeneratingPredictions ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Brain className="w-4 h-4 mr-2" />
                )}
                {isGeneratingPredictions ? 'Generating...' : 'AI Predictions'}
              </button>
              <button
                onClick={() => optimizeSchedule(123)}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <Zap className="w-4 h-4 mr-2" />
                Optimize Schedule
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Stats */}
        {maintenanceData?.overview && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total Items"
              value={maintenanceData.overview.total_maintenance_items}
              subtitle="All maintenance tasks"
              icon={Wrench}
              color="blue"
            />
            <StatCard
              title="Pending"
              value={maintenanceData.overview.pending_items}
              subtitle="Scheduled maintenance"
              icon={Clock}
              color="yellow"
            />
            <StatCard
              title="Completion Rate"
              value={`${(maintenanceData.overview.completion_rate * 100).toFixed(0)}%`}
              subtitle="Tasks completed on time"
              icon={CheckCircle}
              color="green"
              trend={5}
            />
            <StatCard
              title="Total Cost"
              value={formatCurrency(maintenanceData.overview.total_actual_cost || maintenanceData.overview.total_estimated_cost)}
              subtitle="Maintenance expenses"
              icon={DollarSign}
              color="purple"
            />
          </div>
        )}

        {/* Alerts */}
        {maintenanceData?.overview?.overdue_items > 0 && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
              <span className="text-red-800 dark:text-red-200 font-medium">
                {maintenanceData.overview.overdue_items} overdue maintenance item(s) require immediate attention
              </span>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: BarChart3 },
                { id: 'maintenance', label: 'Maintenance Items', icon: Wrench },
                { id: 'predictions', label: 'AI Predictions', icon: Brain },
                { id: 'equipment', label: 'Equipment', icon: Settings },
                { id: 'analytics', label: 'Analytics', icon: PieChart }
              ].map(tab => {
                const Icon = tab.icon;
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
                    <Icon className="w-4 h-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Maintenance</h3>
                <div className="space-y-4">
                  {maintenanceData?.recent_maintenance?.slice(0, 3).map(item => (
                    <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
                      <div className="flex items-center space-x-3">
                        {getCategoryIcon(item.category)}
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{item.title}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {formatDate(item.scheduled_date)}
                          </p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(item.status)}`}>
                        {item.status.replace('_', ' ')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Equipment Alerts</h3>
                <div className="space-y-4">
                  {maintenanceData?.equipment_summary?.equipment_needing_attention?.map((equipment, index) => (
                    <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800">
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{equipment.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {equipment.recommended_action} - {(equipment.confidence * 100).toFixed(0)}% confidence
                        </p>
                      </div>
                      <Alert className="w-5 h-5 text-orange-600" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'maintenance' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Maintenance Items</h3>
              <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Schedule Maintenance
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {maintenanceData?.recent_maintenance?.map(item => (
                <MaintenanceCard key={item.id} item={item} />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'predictions' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Predictions</h3>
              <button
                onClick={() => generatePredictiveMaintenance(123)}
                disabled={isGeneratingPredictions}
                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {isGeneratingPredictions ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Brain className="w-4 h-4 mr-2" />
                )}
                Generate Predictions
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {maintenanceData?.predictions?.map(prediction => (
                <PredictionCard key={prediction.prediction_id} prediction={prediction} />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'equipment' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Equipment Overview</h3>
              <button className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                <Plus className="w-4 h-4 mr-2" />
                Add Equipment
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(maintenanceData?.equipment_summary?.equipment_by_category || {}).map(([category, count]) => (
                <div key={category} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white capitalize">
                        {category.replace('_', ' ')}
                      </h4>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{count}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">units</p>
                    </div>
                    <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900/20">
                      {getCategoryIcon(category)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Item Details Modal */}
        {selectedItem && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen px-4">
              <div className="fixed inset-0 bg-black opacity-50" onClick={() => setSelectedItem(null)}></div>
              <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Maintenance Details
                    </h3>
                    <button
                      onClick={() => setSelectedItem(null)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                
                <div className="px-6 py-4 space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">{selectedItem.title}</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Property #{selectedItem.property_id}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-500 dark:text-gray-400">Category</label>
                      <p className="font-medium text-gray-900 dark:text-white capitalize">{selectedItem.category}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500 dark:text-gray-400">Priority</label>
                      <p className="font-medium text-gray-900 dark:text-white capitalize">{selectedItem.priority}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500 dark:text-gray-400">Status</label>
                      <p className="font-medium text-gray-900 dark:text-white capitalize">{selectedItem.status.replace('_', ' ')}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500 dark:text-gray-400">Scheduled Date</label>
                      <p className="font-medium text-gray-900 dark:text-white">{formatDate(selectedItem.scheduled_date)}</p>
                    </div>
                  </div>
                  
                  {selectedItem.assigned_contractor && (
                    <div>
                      <label className="text-sm text-gray-500 dark:text-gray-400">Assigned Contractor</label>
                      <p className="font-medium text-gray-900 dark:text-white">{selectedItem.assigned_contractor}</p>
                    </div>
                  )}
                  
                  {selectedItem.ai_generated && (
                    <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <div className="flex items-center">
                        <Brain className="w-4 h-4 text-purple-600 mr-2" />
                        <span className="text-sm font-medium text-purple-800 dark:text-purple-200">
                          AI Generated Task - {(selectedItem.confidence_score * 100).toFixed(0)}% Confidence
                        </span>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
                  <button
                    onClick={() => setSelectedItem(null)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  >
                    Close
                  </button>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Edit Item
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SmartMaintenanceDashboard;