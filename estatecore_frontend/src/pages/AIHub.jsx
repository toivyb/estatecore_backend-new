import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import api from '../api';

const AIHub = () => {
  const [systemStatus, setSystemStatus] = useState({
    computer_vision: 'checking',
    nlp: 'checking',
    predictive_maintenance: 'checking',
    live_cameras: 'checking'
  });

  useEffect(() => {
    checkSystemStatus();
  }, []);

  const checkSystemStatus = async () => {
    const newStatus = {};

    // Check Computer Vision (AI Status)
    try {
      const response = await api.get('/api/ai/status');
      newStatus.computer_vision = response.success ? 'operational' : 'error';
    } catch (error) {
      console.error('Computer Vision check failed:', error);
      newStatus.computer_vision = 'error';
    }

    // Check NLP (Document Processing)
    try {
      const response = await api.post('/api/document/process', { test: true });
      newStatus.nlp = response.success ? 'operational' : 'error';
    } catch (error) {
      console.error('NLP check failed:', error);
      newStatus.nlp = 'error';
    }

    // Check Predictive Maintenance
    try {
      const response = await api.post('/api/maintenance/predict', { test: true });
      newStatus.predictive_maintenance = response.success ? 'operational' : 'error';
    } catch (error) {
      console.error('Predictive Maintenance check failed:', error);
      newStatus.predictive_maintenance = 'error';
    }

    // Check Live Cameras
    try {
      const response = await api.post('/api/camera/available', { test: true });
      newStatus.live_cameras = (response && Array.isArray(response)) ? 'operational' : 'error';
    } catch (error) {
      console.error('Live Cameras check failed:', error);
      newStatus.live_cameras = 'error';
    }

    setSystemStatus(newStatus);
  };

  const aiFeatures = [
    {
      id: 'computer_vision',
      title: 'Computer Vision',
      description: 'Automated property analysis, damage detection, and image processing',
      icon: '👁️',
      status: systemStatus.computer_vision,
      features: [
        'Property condition assessment',
        'Damage detection and cost estimation',
        'Image quality enhancement',
        'Automated property analytics'
      ],
      route: '/ai/computer-vision',
      color: 'bg-blue-50 border-blue-200'
    },
    {
      id: 'live_cameras',
      title: 'Live Camera Analysis',
      description: 'Real-time camera monitoring with AI-powered analysis',
      icon: '📹',
      status: systemStatus.live_cameras,
      features: [
        'Live camera detection and setup',
        'Real-time property monitoring',
        'Motion detection and alerts',
        'Automated frame analysis'
      ],
      route: '/live-camera-analysis',
      color: 'bg-green-50 border-green-200'
    },
    {
      id: 'nlp',
      title: 'Document Processing',
      description: 'Natural language processing for lease agreements and legal documents',
      icon: '📄',
      status: systemStatus.nlp,
      features: [
        'Legal document analysis',
        'Entity extraction and classification',
        'Risk assessment and compliance',
        'Batch document processing'
      ],
      route: '/ai/document-processing',
      color: 'bg-purple-50 border-purple-200'
    },
    {
      id: 'predictive_maintenance',
      title: 'Predictive Maintenance',
      description: 'AI-powered maintenance prediction and cost optimization',
      icon: '🔧',
      status: systemStatus.predictive_maintenance,
      features: [
        'Maintenance need predictions',
        'Cost optimization strategies',
        'Equipment lifecycle management',
        'Scheduling optimization'
      ],
      route: '/ai/predictive-maintenance',
      color: 'bg-orange-50 border-orange-200'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational': return 'text-green-600 bg-green-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'checking': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'operational': return 'Operational';
      case 'error': return 'Error';
      case 'checking': return 'Checking...';
      default: return 'Unknown';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Intelligence Hub</h1>
            <p className="text-gray-600">Advanced AI capabilities for property management</p>
          </div>
          <button 
            onClick={checkSystemStatus}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Refresh Status
          </button>
        </div>
      </div>

      {/* System Status Overview */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(systemStatus).map(([system, status]) => (
              <div key={system} className="text-center">
                <div className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
                  {getStatusText(status)}
                </div>
                <div className="text-sm text-gray-600 mt-1 capitalize">
                  {system.replace('_', ' ')}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* AI Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {aiFeatures.map((feature) => (
          <Card key={feature.id} className={`${feature.color} hover:shadow-lg transition-shadow cursor-pointer`}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">{feature.icon}</div>
                  <div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                    <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium mt-1 ${getStatusColor(feature.status)}`}>
                      {getStatusText(feature.status)}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => window.location.href = feature.route}
                  className="px-3 py-1 bg-white text-gray-700 rounded-md text-sm hover:bg-gray-50 transition-colors"
                >
                  Launch
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 mb-4">{feature.description}</p>
              
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">Key Features:</h4>
                <ul className="space-y-1">
                  {feature.features.map((item, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-center">
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-2"></span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
              <div className="text-lg mb-2">📸</div>
              <div className="font-medium">Analyze Property</div>
              <div className="text-sm text-gray-600">Upload images for AI analysis</div>
            </button>
            
            <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
              <div className="text-lg mb-2">📋</div>
              <div className="font-medium">Process Document</div>
              <div className="text-sm text-gray-600">Analyze lease agreements</div>
            </button>
            
            <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
              <div className="text-lg mb-2">🔮</div>
              <div className="font-medium">Predict Maintenance</div>
              <div className="text-sm text-gray-600">Get maintenance forecasts</div>
            </button>
            
            <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
              <div className="text-lg mb-2">📊</div>
              <div className="font-medium">View Analytics</div>
              <div className="text-sm text-gray-600">AI-powered insights</div>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Recent AI Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div>
                  <div className="font-medium">Property analysis completed</div>
                  <div className="text-sm text-gray-600">AI detected minor roof damage - Priority: Medium</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">5 min ago</div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div>
                  <div className="font-medium">Document processed</div>
                  <div className="text-sm text-gray-600">Lease agreement analyzed - Risk score: Low</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">12 min ago</div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                <div>
                  <div className="font-medium">Maintenance prediction</div>
                  <div className="text-sm text-gray-600">HVAC maintenance recommended in 45 days</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">1 hour ago</div>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t">
            <button className="text-sm text-blue-600 hover:text-blue-800">
              View all activity →
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AIHub;