import React, { useState, useEffect } from 'react';

const SimpleSmartMaintenance = () => {
  const [maintenanceData, setMaintenanceData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simple mock data for demonstration
    setTimeout(() => {
      setMaintenanceData({
        overview: {
          total_maintenance_items: 47,
          pending_items: 12,
          completed_items: 28,
          completion_rate: 0.82,
          total_estimated_cost: 24500
        },
        recent_maintenance: [
          {
            id: 'maint_001',
            title: 'HVAC Filter Replacement',
            category: 'hvac',
            priority: 'medium',
            status: 'scheduled',
            estimated_cost: 75
          },
          {
            id: 'maint_002',
            title: 'Plumbing Leak Repair',
            category: 'plumbing',
            priority: 'high',
            status: 'in_progress',
            estimated_cost: 250
          }
        ]
      });
      setLoading(false);
    }, 1000);
  }, []);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'scheduled': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading maintenance data...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">Smart Maintenance Dashboard</h1>
            <p className="text-gray-600">Simplified maintenance management system</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Stats */}
        {maintenanceData?.overview && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Items</p>
                  <p className="text-2xl font-bold text-gray-900">{maintenanceData.overview.total_maintenance_items}</p>
                  <p className="text-sm text-gray-500">All maintenance tasks</p>
                </div>
                <div className="p-3 rounded-full bg-blue-100">
                  <span className="text-blue-600 text-2xl">🔧</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Pending</p>
                  <p className="text-2xl font-bold text-gray-900">{maintenanceData.overview.pending_items}</p>
                  <p className="text-sm text-gray-500">Scheduled maintenance</p>
                </div>
                <div className="p-3 rounded-full bg-yellow-100">
                  <span className="text-yellow-600 text-2xl">⏰</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Completion Rate</p>
                  <p className="text-2xl font-bold text-gray-900">{(maintenanceData.overview.completion_rate * 100).toFixed(0)}%</p>
                  <p className="text-sm text-gray-500">Tasks completed on time</p>
                </div>
                <div className="p-3 rounded-full bg-green-100">
                  <span className="text-green-600 text-2xl">✅</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Cost</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(maintenanceData.overview.total_estimated_cost)}</p>
                  <p className="text-sm text-gray-500">Maintenance expenses</p>
                </div>
                <div className="p-3 rounded-full bg-purple-100">
                  <span className="text-purple-600 text-2xl">💰</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recent Maintenance */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Maintenance Items</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {maintenanceData?.recent_maintenance?.map((item) => (
                <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{item.title}</h4>
                      <p className="text-sm text-gray-600 capitalize">{item.category} maintenance</p>
                      <div className="mt-2 flex items-center space-x-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(item.status)}`}>
                          {item.status.replace('_', ' ')}
                        </span>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(item.priority)}`}>
                          {item.priority} priority
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-900">{formatCurrency(item.estimated_cost)}</p>
                      <p className="text-sm text-gray-500">estimated cost</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex flex-wrap gap-4">
          <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            📝 Schedule Maintenance
          </button>
          <button className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
            🤖 AI Predictions
          </button>
          <button className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
            📊 View Analytics
          </button>
        </div>

        {/* Note */}
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-blue-800 text-sm">
            <strong>Note:</strong> This is a simplified version of the Smart Maintenance Dashboard. 
            The full version is temporarily unavailable due to technical issues.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SimpleSmartMaintenance;