import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

const AIManagementDashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    systems: [],
    alerts: [],
    metrics: {},
    loading: true
  });

  const [selectedTimeframe, setSelectedTimeframe] = useState('24h');

  useEffect(() => {
    loadDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, [selectedTimeframe]);

  const loadDashboardData = async () => {
    try {
      setDashboardData(prev => ({ ...prev, loading: true }));
      
      // Simulate loading different AI systems data
      const systems = [
        {
          id: 'energy-management',
          name: 'Smart Energy Management',
          status: 'healthy',
          uptime: '99.8%',
          lastUpdate: new Date().toISOString(),
          metrics: {
            dataPoints: 850,
            predictions: 156,
            recommendations: 12,
            alerts: 3
          },
          performance: {
            accuracy: 87.2,
            responseTime: 145,
            throughput: 2.3
          }
        },
        {
          id: 'compliance-monitoring',
          name: 'Automated Compliance Monitoring',
          status: 'healthy',
          uptime: '99.9%',
          lastUpdate: new Date().toISOString(),
          metrics: {
            documentsProcessed: 1240,
            complianceChecks: 89,
            violations: 2,
            alerts: 1
          },
          performance: {
            accuracy: 94.7,
            responseTime: 89,
            throughput: 12.5
          }
        },
        {
          id: 'tenant-screening',
          name: 'Predictive Tenant Screening',
          status: 'healthy',
          uptime: '100%',
          lastUpdate: new Date().toISOString(),
          metrics: {
            applicationsProcessed: 342,
            riskAssessments: 298,
            recommendations: 67,
            alerts: 0
          },
          performance: {
            accuracy: 91.8,
            responseTime: 234,
            throughput: 8.7
          }
        },
        {
          id: 'lpr-system',
          name: 'License Plate Recognition',
          status: 'warning',
          uptime: '98.1%',
          lastUpdate: new Date().toISOString(),
          metrics: {
            vehiclesDetected: 5680,
            accessGrants: 5234,
            accessDenials: 89,
            alerts: 15
          },
          performance: {
            accuracy: 96.3,
            responseTime: 67,
            throughput: 45.2
          }
        }
      ];

      const alerts = [
        {
          id: 1,
          system: 'energy-management',
          type: 'performance',
          severity: 'medium',
          title: 'High Energy Consumption Detected',
          message: 'Property #1243 showing 25% higher than average consumption',
          timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
          status: 'active'
        },
        {
          id: 2,
          system: 'lpr-system',
          type: 'security',
          severity: 'high',
          title: 'Unauthorized Vehicle Alert',
          message: 'Unknown license plate ABC-1234 attempted entry at Gate A',
          timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
          status: 'active'
        },
        {
          id: 3,
          system: 'compliance-monitoring',
          type: 'compliance',
          severity: 'low',
          title: 'Document Review Required',
          message: 'Fire safety inspection certificate expires in 30 days',
          timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
          status: 'acknowledged'
        }
      ];

      const metrics = {
        totalSystems: systems.length,
        healthySystems: systems.filter(s => s.status === 'healthy').length,
        totalAlerts: alerts.filter(a => a.status === 'active').length,
        averageUptime: (systems.reduce((sum, s) => sum + parseFloat(s.uptime), 0) / systems.length).toFixed(1),
        totalDataPoints: systems.reduce((sum, s) => sum + s.metrics.dataPoints, 0),
        averageAccuracy: (systems.reduce((sum, s) => sum + s.performance.accuracy, 0) / systems.length).toFixed(1),
        systemLoad: {
          cpu: Math.floor(Math.random() * 30) + 15,
          memory: Math.floor(Math.random() * 40) + 30,
          storage: Math.floor(Math.random() * 20) + 45
        }
      };

      setDashboardData({
        systems,
        alerts,
        metrics,
        loading: false
      });

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setDashboardData(prev => ({ ...prev, loading: false }));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusDot = (status) => {
    switch (status) {
      case 'healthy': return 'bg-green-400';
      case 'warning': return 'bg-yellow-400';
      case 'error': return 'bg-red-400';
      default: return 'bg-gray-400';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffMinutes < 60) {
      return `${diffMinutes}m ago`;
    } else if (diffMinutes < 1440) {
      return `${Math.floor(diffMinutes / 60)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  if (dashboardData.loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-96 bg-gray-200 rounded"></div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">AI Management Dashboard</h1>
        <div className="flex items-center space-x-4">
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <button
            onClick={loadDashboardData}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Systems</p>
                <p className="text-2xl font-bold text-gray-900">
                  {dashboardData.metrics.healthySystems}/{dashboardData.metrics.totalSystems}
                </p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600">⚙️</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Average Uptime</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.metrics.averageUptime}%</p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600">⏱️</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Alerts</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.metrics.totalAlerts}</p>
              </div>
              <div className="h-12 w-12 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-red-600">🚨</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Accuracy</p>
                <p className="text-2xl font-bold text-gray-900">{dashboardData.metrics.averageAccuracy}%</p>
              </div>
              <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-purple-600">🎯</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Status Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>AI System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.systems.map((system) => (
                <div key={system.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${getStatusDot(system.status)}`}></div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{system.name}</h3>
                      <p className="text-sm text-gray-600">
                        Uptime: {system.uptime} • Accuracy: {system.performance.accuracy}%
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${getStatusColor(system.status)}`}>
                      {system.status.charAt(0).toUpperCase() + system.status.slice(1)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatTimestamp(system.lastUpdate)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboardData.alerts.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No recent alerts</p>
              ) : (
                dashboardData.alerts.map((alert) => (
                  <div key={alert.id} className="p-3 border rounded-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h4 className="font-medium text-gray-900">{alert.title}</h4>
                          <span className={`px-2 py-1 text-xs rounded-full border ${getSeverityColor(alert.severity)}`}>
                            {alert.severity}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTimestamp(alert.timestamp)} • {alert.system}
                        </p>
                      </div>
                      {alert.status === 'active' && (
                        <button className="text-blue-600 text-sm hover:underline">
                          Acknowledge
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>System Load</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">CPU Usage</span>
                <span className="text-sm font-medium">{dashboardData.metrics.systemLoad.cpu}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full" 
                  style={{ width: `${dashboardData.metrics.systemLoad.cpu}%` }}
                ></div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Memory Usage</span>
                <span className="text-sm font-medium">{dashboardData.metrics.systemLoad.memory}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-600 h-2 rounded-full" 
                  style={{ width: `${dashboardData.metrics.systemLoad.memory}%` }}
                ></div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Storage Usage</span>
                <span className="text-sm font-medium">{dashboardData.metrics.systemLoad.storage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-yellow-600 h-2 rounded-full" 
                  style={{ width: `${dashboardData.metrics.systemLoad.storage}%` }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data Processing</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-600">
                  {dashboardData.metrics.totalDataPoints.toLocaleString()}
                </p>
                <p className="text-sm text-gray-600">Total Data Points Processed</p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <p className="text-xl font-semibold text-gray-900">
                    {dashboardData.systems.reduce((sum, s) => sum + s.metrics.predictions, 0)}
                  </p>
                  <p className="text-xs text-gray-600">Predictions Made</p>
                </div>
                <div>
                  <p className="text-xl font-semibold text-gray-900">
                    {dashboardData.systems.reduce((sum, s) => sum + s.metrics.recommendations, 0)}
                  </p>
                  <p className="text-xs text-gray-600">Recommendations</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <button className="w-full px-4 py-2 text-left text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors">
                🔄 Restart All AI Services
              </button>
              <button className="w-full px-4 py-2 text-left text-sm bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors">
                📊 Generate Performance Report
              </button>
              <button className="w-full px-4 py-2 text-left text-sm bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors">
                ⚙️ Configure AI Settings
              </button>
              <button className="w-full px-4 py-2 text-left text-sm bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 transition-colors">
                🎯 Model Training Status
              </button>
              <button className="w-full px-4 py-2 text-left text-sm bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors">
                🚨 Emergency Stop All
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AIManagementDashboard;