import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

const BetaTestingDashboard = () => {
  const [testingData, setTestingData] = useState({
    phase: 'Phase 5C AI Intelligence',
    version: '5.0.0-beta.1',
    status: 'active',
    participants: [],
    testResults: [],
    features: [],
    feedback: [],
    metrics: {},
    loading: true
  });

  useEffect(() => {
    loadBetaTestingData();
  }, []);

  const loadBetaTestingData = async () => {
    try {
      // Simulate loading beta testing data
      const participants = [
        {
          id: 1,
          name: 'Acme Property Management',
          email: 'beta@acmeproperties.com',
          properties: 45,
          status: 'active',
          joinedDate: '2024-01-15',
          lastActivity: new Date().toISOString(),
          completionRate: 78,
          feedbackCount: 12
        },
        {
          id: 2,
          name: 'Central City Rentals',
          email: 'test@centralcityrentals.com',
          properties: 23,
          status: 'active',
          joinedDate: '2024-01-18',
          lastActivity: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
          completionRate: 65,
          feedbackCount: 8
        },
        {
          id: 3,
          name: 'Metro Housing Group',
          email: 'beta@metrohousing.com',
          properties: 67,
          status: 'inactive',
          joinedDate: '2024-01-12',
          lastActivity: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
          completionRate: 42,
          feedbackCount: 5
        }
      ];

      const features = [
        {
          id: 'smart-energy',
          name: 'Smart Energy Management',
          description: 'AI-powered energy monitoring and optimization',
          status: 'testing',
          testCoverage: 85,
          bugCount: 2,
          severity: 'low',
          completionRate: 78
        },
        {
          id: 'ai-dashboard',
          name: 'AI Management Dashboard',
          description: 'Central hub for monitoring all AI systems',
          status: 'testing',
          testCoverage: 92,
          bugCount: 1,
          severity: 'low',
          completionRate: 89
        },
        {
          id: 'compliance-ai',
          name: 'Automated Compliance Monitoring',
          description: 'AI-powered compliance tracking and alerts',
          status: 'completed',
          testCoverage: 95,
          bugCount: 0,
          severity: 'none',
          completionRate: 100
        },
        {
          id: 'tenant-screening',
          name: 'Predictive Tenant Screening',
          description: 'ML-based tenant risk assessment',
          status: 'completed',
          testCoverage: 88,
          bugCount: 1,
          severity: 'low',
          completionRate: 94
        }
      ];

      const testResults = [
        {
          id: 1,
          feature: 'Smart Energy Management',
          testCase: 'Energy consumption forecasting accuracy',
          status: 'passed',
          score: 87.2,
          notes: 'Predictions within 5% of actual consumption',
          tester: 'Acme Property Management',
          date: '2024-01-20'
        },
        {
          id: 2,
          feature: 'AI Management Dashboard',
          testCase: 'Real-time system monitoring',
          status: 'passed',
          score: 94.5,
          notes: 'Dashboard updates correctly, all metrics displayed',
          tester: 'Central City Rentals',
          date: '2024-01-19'
        },
        {
          id: 3,
          feature: 'Smart Energy Management',
          testCase: 'Optimization recommendations quality',
          status: 'failed',
          score: 65.3,
          notes: 'Some recommendations not practical for smaller properties',
          tester: 'Central City Rentals',
          date: '2024-01-18'
        }
      ];

      const feedback = [
        {
          id: 1,
          participant: 'Acme Property Management',
          feature: 'Smart Energy Management',
          type: 'positive',
          rating: 4,
          comment: 'The energy forecasting has helped us reduce costs by 12%. Very impressed with the AI accuracy.',
          date: '2024-01-20',
          category: 'functionality'
        },
        {
          id: 2,
          participant: 'Central City Rentals',
          feature: 'AI Management Dashboard',
          type: 'suggestion',
          rating: 4,
          comment: 'Dashboard is great but could use more filtering options for alerts. Overall very useful.',
          date: '2024-01-19',
          category: 'usability'
        },
        {
          id: 3,
          participant: 'Metro Housing Group',
          feature: 'Tenant Screening',
          type: 'issue',
          rating: 2,
          comment: 'The screening process is too slow for our volume. Takes 5+ minutes per application.',
          date: '2024-01-17',
          category: 'performance'
        }
      ];

      const metrics = {
        totalParticipants: participants.length,
        activeParticipants: participants.filter(p => p.status === 'active').length,
        averageCompletion: Math.round(participants.reduce((sum, p) => sum + p.completionRate, 0) / participants.length),
        totalFeedback: feedback.length,
        averageRating: (feedback.reduce((sum, f) => sum + f.rating, 0) / feedback.length).toFixed(1),
        bugsFound: features.reduce((sum, f) => sum + f.bugCount, 0),
        featuresCompleted: features.filter(f => f.status === 'completed').length,
        overallProgress: Math.round(features.reduce((sum, f) => sum + f.completionRate, 0) / features.length)
      };

      setTestingData({
        phase: 'Phase 5C AI Intelligence',
        version: '5.0.0-beta.1',
        status: 'active',
        participants,
        testResults,
        features,
        feedback,
        metrics,
        loading: false
      });

    } catch (error) {
      console.error('Failed to load beta testing data:', error);
      setTestingData(prev => ({ ...prev, loading: false }));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': 
      case 'passed': 
      case 'completed': return 'text-green-600 bg-green-100';
      case 'testing': return 'text-blue-600 bg-blue-100';
      case 'failed': 
      case 'inactive': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getFeedbackTypeColor = (type) => {
    switch (type) {
      case 'positive': return 'text-green-700 bg-green-100 border-green-200';
      case 'suggestion': return 'text-blue-700 bg-blue-100 border-blue-200';
      case 'issue': return 'text-red-700 bg-red-100 border-red-200';
      default: return 'text-gray-700 bg-gray-100 border-gray-200';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
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

  if (testingData.loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{testingData.phase} Beta Testing</h1>
          <p className="text-gray-600">Version {testingData.version} • Status: 
            <span className={`ml-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(testingData.status)}`}>
              {testingData.status.toUpperCase()}
            </span>
          </p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            Export Report
          </button>
          <button 
            onClick={loadBetaTestingData}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Refresh Data
          </button>
        </div>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Participants</p>
                <p className="text-2xl font-bold text-gray-900">
                  {testingData.metrics.activeParticipants}/{testingData.metrics.totalParticipants}
                </p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-xl">👥</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overall Progress</p>
                <p className="text-2xl font-bold text-gray-900">{testingData.metrics.overallProgress}%</p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 text-xl">📊</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Average Rating</p>
                <p className="text-2xl font-bold text-gray-900">{testingData.metrics.averageRating}/5</p>
              </div>
              <div className="h-12 w-12 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 text-xl">⭐</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Bugs Found</p>
                <p className="text-2xl font-bold text-gray-900">{testingData.metrics.bugsFound}</p>
              </div>
              <div className="h-12 w-12 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-red-600 text-xl">🐛</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Beta Participants and Features */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Beta Participants</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {testingData.participants.map((participant) => (
                <div key={participant.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{participant.name}</h3>
                    <p className="text-sm text-gray-600">{participant.properties} properties</p>
                    <div className="flex items-center space-x-4 mt-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(participant.status)}`}>
                        {participant.status}
                      </span>
                      <span className="text-xs text-gray-500">
                        Last active: {formatDate(participant.lastActivity)}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">{participant.completionRate}%</div>
                    <div className="text-xs text-gray-500">{participant.feedbackCount} feedback</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Feature Testing Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {testingData.features.map((feature) => (
                <div key={feature.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{feature.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{feature.description}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(feature.status)}`}>
                          {feature.status}
                        </span>
                        <span className="text-xs text-gray-600">
                          Coverage: {feature.testCoverage}%
                        </span>
                        {feature.bugCount > 0 && (
                          <span className="text-xs text-red-600">
                            {feature.bugCount} bugs ({feature.severity})
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{feature.completionRate}%</div>
                      <div className="w-16 h-2 bg-gray-200 rounded-full mt-1">
                        <div 
                          className="h-2 bg-blue-600 rounded-full" 
                          style={{ width: `${feature.completionRate}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Test Results and Feedback */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Test Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {testingData.testResults.map((result) => (
                <div key={result.id} className="p-3 border rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{result.testCase}</h4>
                      <p className="text-sm text-gray-600">{result.feature}</p>
                      <p className="text-xs text-gray-500 mt-1">{result.notes}</p>
                      <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs text-gray-500">By {result.tester}</span>
                        <span className="text-xs text-gray-500">• {result.date}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(result.status)}`}>
                        {result.status}
                      </span>
                      <div className="text-sm font-medium mt-1">{result.score}%</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Beta Feedback</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {testingData.feedback.map((feedback) => (
                <div key={feedback.id} className={`p-3 border rounded-lg ${getFeedbackTypeColor(feedback.type)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium">{feedback.feature}</span>
                        <div className="flex">
                          {[...Array(5)].map((_, i) => (
                            <span key={i} className={`text-xs ${i < feedback.rating ? 'text-yellow-400' : 'text-gray-300'}`}>
                              ★
                            </span>
                          ))}
                        </div>
                      </div>
                      <p className="text-sm mt-1">{feedback.comment}</p>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-xs">{feedback.participant}</span>
                        <span className="text-xs">• {feedback.date}</span>
                      </div>
                    </div>
                    <span className="text-xs font-medium capitalize">
                      {feedback.type}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Beta Testing Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="p-4 text-left bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors">
              <div className="text-xl mb-2">📧</div>
              <div className="font-medium">Send Update</div>
              <div className="text-sm opacity-75">Notify participants</div>
            </button>
            <button className="p-4 text-left bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors">
              <div className="text-xl mb-2">📋</div>
              <div className="font-medium">Create Survey</div>
              <div className="text-sm opacity-75">Gather feedback</div>
            </button>
            <button className="p-4 text-left bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors">
              <div className="text-xl mb-2">🎯</div>
              <div className="font-medium">Add Test Case</div>
              <div className="text-sm opacity-75">Define new tests</div>
            </button>
            <button className="p-4 text-left bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 transition-colors">
              <div className="text-xl mb-2">📊</div>
              <div className="font-medium">Analytics Report</div>
              <div className="text-sm opacity-75">Detailed insights</div>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BetaTestingDashboard;