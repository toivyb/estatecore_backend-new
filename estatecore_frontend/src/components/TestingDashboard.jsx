import React, { useState, useEffect } from 'react';

const TestingDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [testResults, setTestResults] = useState(null);
  const [runningTests, setRunningTests] = useState(false);
  const [testHistory, setTestHistory] = useState([]);
  const [testCategories, setTestCategories] = useState({
    unit: { total: 45, passed: 42, failed: 3, status: 'warning' },
    integration: { total: 20, passed: 18, failed: 2, status: 'warning' },
    performance: { total: 15, passed: 15, failed: 0, status: 'success' },
    security: { total: 12, passed: 11, failed: 1, status: 'warning' },
    api: { total: 35, passed: 33, failed: 2, status: 'warning' }
  });
  const [testLogs, setTestLogs] = useState([]);
  const [selectedTestSuite, setSelectedTestSuite] = useState('all');

  useEffect(() => {
    fetchTestData();
  }, []);

  const fetchTestData = async () => {
    try {
      // In a real implementation, these would be actual API calls
      const mockResults = {
        summary: {
          total_tests: 127,
          passed: 119,
          failed: 8,
          skipped: 0,
          success_rate: 93.7,
          execution_time: '2m 45s',
          last_run: new Date().toISOString()
        },
        categories: testCategories,
        recent_failures: [
          {
            test_name: 'test_payment_processing_with_invalid_card',
            category: 'unit',
            error: 'AssertionError: Expected payment to fail with invalid card',
            file: 'test_rent_collection.py:145',
            duration: '0.12s'
          },
          {
            test_name: 'test_bulk_import_large_dataset',
            category: 'performance',
            error: 'Timeout: Test exceeded 30s execution time',
            file: 'test_bulk_operations.py:89',
            duration: '30.01s'
          }
        ]
      };

      setTestResults(mockResults);
      
      // Mock test history
      const mockHistory = [
        {
          id: 1,
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          total: 127,
          passed: 119,
          failed: 8,
          success_rate: 93.7,
          duration: '2m 45s',
          branch: 'main',
          commit: 'abc123f'
        },
        {
          id: 2,
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          total: 125,
          passed: 123,
          failed: 2,
          success_rate: 98.4,
          duration: '2m 32s',
          branch: 'main',
          commit: 'def456a'
        }
      ];
      
      setTestHistory(mockHistory);
      
    } catch (error) {
      console.error('Error fetching test data:', error);
    }
  };

  const runTests = async (testSuite = 'all') => {
    try {
      setRunningTests(true);
      setTestLogs([]);
      
      // Mock test execution with real-time logs
      const mockLogs = [
        { timestamp: new Date(), level: 'info', message: `Starting ${testSuite} test suite...` },
        { timestamp: new Date(), level: 'info', message: 'Setting up test environment...' },
        { timestamp: new Date(), level: 'success', message: 'Database connection established' },
        { timestamp: new Date(), level: 'info', message: 'Running unit tests...' },
        { timestamp: new Date(), level: 'success', message: 'test_database_service.py - 15/15 passed' },
        { timestamp: new Date(), level: 'warning', message: 'test_payment_processing.py - 8/10 passed (2 failed)' },
        { timestamp: new Date(), level: 'info', message: 'Running integration tests...' },
        { timestamp: new Date(), level: 'success', message: 'test_workflow_integration.py - 12/12 passed' }
      ];

      // Simulate real-time log updates
      for (let i = 0; i < mockLogs.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 500));
        setTestLogs(prev => [...prev, mockLogs[i]]);
      }

      // Update test results after completion
      setTimeout(() => {
        fetchTestData();
        setRunningTests(false);
        setTestLogs(prev => [...prev, {
          timestamp: new Date(),
          level: 'success',
          message: `Test suite completed: 119/127 tests passed (93.7% success rate)`
        }]);
      }, 1000);

    } catch (error) {
      console.error('Error running tests:', error);
      setRunningTests(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getLogLevelColor = (level) => {
    switch (level) {
      case 'success': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      case 'info': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Test Dashboard</h1>
        <div className="flex gap-2">
          <select
            value={selectedTestSuite}
            onChange={(e) => setSelectedTestSuite(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
            disabled={runningTests}
          >
            <option value="all">All Tests</option>
            <option value="unit">Unit Tests</option>
            <option value="integration">Integration Tests</option>
            <option value="performance">Performance Tests</option>
            <option value="security">Security Tests</option>
            <option value="api">API Tests</option>
          </select>
          <button
            onClick={() => runTests(selectedTestSuite)}
            disabled={runningTests}
            className={`px-4 py-2 rounded-md ${
              runningTests
                ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {runningTests ? '🔄 Running...' : '▶️ Run Tests'}
          </button>
          <button
            onClick={fetchTestData}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
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
            { id: 'results', label: 'Test Results', icon: '📋' },
            { id: 'history', label: 'Test History', icon: '📈' },
            { id: 'logs', label: 'Live Logs', icon: '📝' },
            { id: 'coverage', label: 'Coverage', icon: '🎯' }
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
      {activeTab === 'overview' && testResults && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Total Tests</h3>
              <p className="text-2xl font-bold text-gray-900">
                {testResults.summary.total_tests}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Passed</h3>
              <p className="text-2xl font-bold text-green-600">
                {testResults.summary.passed}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Failed</h3>
              <p className="text-2xl font-bold text-red-600">
                {testResults.summary.failed}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Success Rate</h3>
              <p className="text-2xl font-bold text-blue-600">
                {testResults.summary.success_rate}%
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Duration</h3>
              <p className="text-2xl font-bold text-purple-600">
                {testResults.summary.execution_time}
              </p>
            </div>
          </div>

          {/* Test Categories */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Test Categories</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(testCategories).map(([category, data]) => (
                  <div key={category} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium text-gray-900 capitalize">{category} Tests</h4>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(data.status)}`}>
                        {data.status}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>Total:</span>
                        <span>{data.total}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-green-600">Passed:</span>
                        <span>{data.passed}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-red-600">Failed:</span>
                        <span>{data.failed}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div 
                          className="bg-green-600 h-2 rounded-full" 
                          style={{ width: `${(data.passed / data.total) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Failures */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Test Failures</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {testResults.recent_failures?.length > 0 ? (
                testResults.recent_failures.map((failure, index) => (
                  <div key={index} className="p-6">
                    <div className="flex items-start space-x-3">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                        {failure.category}
                      </span>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{failure.test_name}</h4>
                        <p className="text-sm text-red-600 mt-1">{failure.error}</p>
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                          <span>📁 {failure.file}</span>
                          <span>⏱️ {failure.duration}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-6 text-center text-green-600">
                  🎉 No recent test failures! All tests are passing.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Test Results Tab */}
      {activeTab === 'results' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Detailed Test Results</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(testCategories).map(([category, data]) => (
                <div key={category} className="border border-gray-200 rounded-lg">
                  <div className="p-4 bg-gray-50 border-b border-gray-200">
                    <h4 className="font-medium text-gray-900 capitalize">{category} Tests</h4>
                  </div>
                  <div className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Total Tests:</span> {data.total}
                      </div>
                      <div>
                        <span className="font-medium text-green-600">Passed:</span> {data.passed}
                      </div>
                      <div>
                        <span className="font-medium text-red-600">Failed:</span> {data.failed}
                      </div>
                    </div>
                    <div className="mt-3">
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div 
                          className="bg-green-500 h-3 rounded-full flex items-center justify-center text-xs text-white font-medium"
                          style={{ width: `${(data.passed / data.total) * 100}%` }}
                        >
                          {Math.round((data.passed / data.total) * 100)}%
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Test History Tab */}
      {activeTab === 'history' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Test Execution History</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Branch/Commit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tests
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Success Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {testHistory.map((run) => (
                  <tr key={run.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(run.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{run.branch}</div>
                        <div className="text-gray-500">{run.commit}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex space-x-2">
                        <span className="text-green-600">{run.passed} passed</span>
                        <span className="text-red-600">{run.failed} failed</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        run.success_rate >= 95 ? 'bg-green-100 text-green-800' :
                        run.success_rate >= 85 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {run.success_rate}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {run.duration}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Live Logs Tab */}
      {activeTab === 'logs' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">Live Test Logs</h3>
              {runningTests && (
                <div className="flex items-center text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                  Running tests...
                </div>
              )}
            </div>
          </div>
          <div className="p-6">
            <div className="bg-black rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
              {testLogs.length === 0 ? (
                <div className="text-gray-400">No test logs available. Run tests to see live output.</div>
              ) : (
                testLogs.map((log, index) => (
                  <div key={index} className="mb-1">
                    <span className="text-gray-400">
                      [{log.timestamp.toLocaleTimeString()}]
                    </span>
                    <span className={`ml-2 ${getLogLevelColor(log.level)}`}>
                      {log.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Coverage Tab */}
      {activeTab === 'coverage' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Code Coverage Report</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">87.5%</div>
                  <div className="text-sm text-gray-500">Overall Coverage</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">92.1%</div>
                  <div className="text-sm text-gray-500">Lines Covered</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">84.3%</div>
                  <div className="text-sm text-gray-500">Functions Covered</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">79.8%</div>
                  <div className="text-sm text-gray-500">Branches Covered</div>
                </div>
              </div>
              
              <div className="space-y-4">
                {[
                  { file: 'database_service.py', coverage: 95.2 },
                  { file: 'permissions_service.py', coverage: 91.8 },
                  { file: 'rent_collection_service.py', coverage: 88.4 },
                  { file: 'security_service.py', coverage: 92.6 },
                  { file: 'maintenance_service.py', coverage: 83.1 },
                  { file: 'financial_reporting.py', coverage: 89.7 }
                ].map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="font-mono text-sm">{item.file}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            item.coverage >= 90 ? 'bg-green-500' :
                            item.coverage >= 80 ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${item.coverage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{item.coverage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Help Section */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-2">Testing Framework Guide</h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p><strong>Unit Tests:</strong> Test individual components and functions in isolation.</p>
          <p><strong>Integration Tests:</strong> Test interaction between multiple components and services.</p>
          <p><strong>Performance Tests:</strong> Validate system performance under various loads.</p>
          <p><strong>Security Tests:</strong> Test authentication, authorization, and security vulnerabilities.</p>
          <p><strong>API Tests:</strong> Test REST API endpoints and data validation.</p>
          <p><strong>Coverage:</strong> Aim for 80%+ coverage for critical business logic.</p>
        </div>
      </div>
    </div>
  );
};

export default TestingDashboard;