import React, { useState, useEffect } from 'react';

const AutomationDashboard = () => {
  const [workflows, setWorkflows] = useState([]);
  const [executionHistory, setExecutionHistory] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [activeTab, setActiveTab] = useState('workflows');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAutomationData();
    const interval = setInterval(fetchAutomationData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAutomationData = async () => {
    try {
      setIsLoading(true);
      
      // Mock data - replace with actual API calls
      const mockWorkflows = [
        {
          id: 'wf-001',
          name: 'Rent Payment Reminder',
          description: 'Send automated rent payment reminders to tenants',
          status: 'active',
          trigger_type: 'time_based',
          created_at: '2024-09-20T10:00:00Z',
          last_run: '2024-09-27T09:00:00Z',
          run_count: 147,
          success_count: 142,
          failure_count: 5,
          success_rate: 0.966,
          next_run: '2024-09-28T09:00:00Z'
        },
        {
          id: 'wf-002',
          name: 'Maintenance Escalation',
          description: 'Escalate overdue maintenance requests to managers',
          status: 'active',
          trigger_type: 'condition_based',
          created_at: '2024-09-21T14:30:00Z',
          last_run: '2024-09-27T16:45:00Z',
          run_count: 23,
          success_count: 21,
          failure_count: 2,
          success_rate: 0.913,
          next_run: null
        },
        {
          id: 'wf-003',
          name: 'Lease Renewal Process',
          description: 'Automate lease renewal notifications 60 days before expiry',
          status: 'paused',
          trigger_type: 'time_based',
          created_at: '2024-09-15T11:15:00Z',
          last_run: '2024-09-25T10:00:00Z',
          run_count: 8,
          success_count: 8,
          failure_count: 0,
          success_rate: 1.0,
          next_run: null
        },
        {
          id: 'wf-004',
          name: 'Payment Processing',
          description: 'Process and confirm payments automatically',
          status: 'active',
          trigger_type: 'event_based',
          created_at: '2024-09-18T16:20:00Z',
          last_run: '2024-09-27T14:22:00Z',
          run_count: 312,
          success_count: 308,
          failure_count: 4,
          success_rate: 0.987,
          next_run: null
        }
      ];

      const mockExecutions = [
        {
          id: 'exec-001',
          workflow_id: 'wf-001',
          workflow_name: 'Rent Payment Reminder',
          execution_time: '2024-09-27T09:00:00Z',
          duration: 2.3,
          status: 'success',
          actions_executed: 25,
          context: { tenants_notified: 25 }
        },
        {
          id: 'exec-002',
          workflow_id: 'wf-004',
          workflow_name: 'Payment Processing',
          execution_time: '2024-09-27T14:22:00Z',
          duration: 0.8,
          status: 'success',
          actions_executed: 3,
          context: { payment_id: 'pay-12345', amount: 1200 }
        },
        {
          id: 'exec-003',
          workflow_id: 'wf-002',
          workflow_name: 'Maintenance Escalation',
          execution_time: '2024-09-27T16:45:00Z',
          duration: 1.5,
          status: 'failed',
          actions_executed: 1,
          error: 'Failed to send notification to manager',
          context: { request_id: 'req-789', days_overdue: 3 }
        }
      ];

      setWorkflows(mockWorkflows);
      setExecutionHistory(mockExecutions);
    } catch (error) {
      console.error('Error fetching automation data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100 border-green-200';
      case 'paused': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'inactive': return 'text-gray-600 bg-gray-100 border-gray-200';
      case 'failed': return 'text-red-600 bg-red-100 border-red-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getTriggerIcon = (type) => {
    switch (type) {
      case 'time_based': return '🕐';
      case 'event_based': return '⚡';
      case 'condition_based': return '🚨';
      default: return '⚙️';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(new Date(timestamp));
  };

  const formatDuration = (seconds) => {
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(1)}s`;
  };

  const pauseWorkflow = async (workflowId) => {
    try {
      // Mock API call
      console.log('Pausing workflow:', workflowId);
      setWorkflows(prev => prev.map(wf => 
        wf.id === workflowId ? { ...wf, status: 'paused' } : wf
      ));
    } catch (error) {
      console.error('Error pausing workflow:', error);
    }
  };

  const resumeWorkflow = async (workflowId) => {
    try {
      // Mock API call
      console.log('Resuming workflow:', workflowId);
      setWorkflows(prev => prev.map(wf => 
        wf.id === workflowId ? { ...wf, status: 'active' } : wf
      ));
    } catch (error) {
      console.error('Error resuming workflow:', error);
    }
  };

  const deleteWorkflow = async (workflowId) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return;
    
    try {
      // Mock API call
      console.log('Deleting workflow:', workflowId);
      setWorkflows(prev => prev.filter(wf => wf.id !== workflowId));
    } catch (error) {
      console.error('Error deleting workflow:', error);
    }
  };

  const StatCard = ({ title, value, icon, color = 'blue', subtitle = null }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-full bg-${color}-100 dark:bg-${color}-900/20`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </div>
  );

  const WorkflowCard = ({ workflow }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start space-x-3">
          <div className={`p-2 rounded-full bg-blue-100 dark:bg-blue-900/20`}>
            <span className="text-lg">{getTriggerIcon(workflow.trigger_type)}</span>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{workflow.name}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">{workflow.description}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(workflow.status)}`}>
            {workflow.status}
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <span className="text-gray-500 dark:text-gray-400">Last Run:</span>
          <p className="font-medium text-gray-900 dark:text-white">{formatTimestamp(workflow.last_run)}</p>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Next Run:</span>
          <p className="font-medium text-gray-900 dark:text-white">{formatTimestamp(workflow.next_run)}</p>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Total Runs:</span>
          <p className="font-medium text-gray-900 dark:text-white">{workflow.run_count}</p>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">Success Rate:</span>
          <p className="font-medium text-gray-900 dark:text-white">{(workflow.success_rate * 100).toFixed(1)}%</p>
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
          <span>Success Rate</span>
          <span>{workflow.success_count}/{workflow.run_count}</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div 
            className="bg-green-500 h-2 rounded-full" 
            style={{ width: `${workflow.success_rate * 100}%` }}
          ></div>
        </div>
      </div>
      
      <div className="flex justify-between items-center">
        <div className="flex space-x-2">
          {workflow.status === 'active' ? (
            <button
              onClick={() => pauseWorkflow(workflow.id)}
              className="flex items-center px-3 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700"
            >
              <span className="mr-1">⏸️</span>
              Pause
            </button>
          ) : (
            <button
              onClick={() => resumeWorkflow(workflow.id)}
              className="flex items-center px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
            >
              <span className="mr-1">▶️</span>
              Resume
            </button>
          )}
          
          <button
            onClick={() => setSelectedWorkflow(workflow)}
            className="flex items-center px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <span className="mr-1">👁️</span>
            View
          </button>
        </div>
        
        <div className="flex space-x-1">
          <button
            onClick={() => console.log('Edit workflow:', workflow.id)}
            className="p-2 text-gray-400 hover:text-blue-600 rounded"
          >
            <span className="text-lg">✏️</span>
          </button>
          <button
            onClick={() => deleteWorkflow(workflow.id)}
            className="p-2 text-gray-400 hover:text-red-600 rounded"
          >
            <span className="text-lg">🗑️</span>
          </button>
        </div>
      </div>
    </div>
  );

  const ExecutionCard = ({ execution }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-medium text-gray-900 dark:text-white">{execution.workflow_name}</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">{formatTimestamp(execution.execution_time)}</p>
        </div>
        
        <div className="flex items-center space-x-2">
          {execution.status === 'success' ? (
            <span className="text-green-500 text-lg">✅</span>
          ) : (
            <span className="text-red-500 text-lg">❌</span>
          )}
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            {formatDuration(execution.duration)}
          </span>
        </div>
      </div>
      
      <div className="text-sm text-gray-600 dark:text-gray-400">
        <p>Actions: {execution.actions_executed}</p>
        {execution.error && (
          <p className="text-red-600 dark:text-red-400 mt-1">{execution.error}</p>
        )}
      </div>
    </div>
  );

  const filteredWorkflows = workflows.filter(workflow => {
    if (filterStatus !== 'all' && workflow.status !== filterStatus) return false;
    if (searchQuery && !workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) && 
        !workflow.description.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const activeWorkflows = workflows.filter(wf => wf.status === 'active').length;
  const totalExecutions = workflows.reduce((sum, wf) => sum + wf.run_count, 0);
  const totalSuccesses = workflows.reduce((sum, wf) => sum + wf.success_count, 0);
  const overallSuccessRate = totalExecutions > 0 ? (totalSuccesses / totalExecutions) : 0;

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
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Automation Dashboard</h1>
              <p className="text-gray-600 dark:text-gray-400">Manage and monitor automated workflows</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <span className="text-lg mr-2">➕</span>
                Create Workflow
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Active Workflows"
            value={activeWorkflows}
            icon="📊"
            color="green"
            subtitle={`of ${workflows.length} total`}
          />
          <StatCard
            title="Total Executions"
            value={totalExecutions.toLocaleString()}
            icon="📈"
            color="blue"
            subtitle="All time"
          />
          <StatCard
            title="Success Rate"
            value={`${(overallSuccessRate * 100).toFixed(1)}%`}
            icon="📈"
            color="purple"
            subtitle={`${totalSuccesses} successful`}
          />
          <StatCard
            title="Last 24h Runs"
            value="47"
            icon="🕐"
            color="orange"
            subtitle="12 scheduled, 35 triggered"
          />
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'workflows', label: 'Workflows', icon: '⚙️' },
                { id: 'executions', label: 'Execution History', icon: '📊' },
                { id: 'templates', label: 'Templates', icon: '📋' }
              ].map(tab => {
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
                    <span className="text-lg mr-2">{tab.icon}</span>
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Workflows Tab */}
        {activeTab === 'workflows' && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search workflows..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>

            {/* Workflows Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {filteredWorkflows.map(workflow => (
                <WorkflowCard key={workflow.id} workflow={workflow} />
              ))}
            </div>
          </div>
        )}

        {/* Execution History Tab */}
        {activeTab === 'executions' && (
          <div className="space-y-4">
            {executionHistory.map(execution => (
              <ExecutionCard key={execution.id} execution={execution} />
            ))}
          </div>
        )}

        {/* Workflow Details Modal */}
        {selectedWorkflow && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen px-4">
              <div className="fixed inset-0 bg-black opacity-50" onClick={() => setSelectedWorkflow(null)}></div>
              <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedWorkflow.name}
                    </h3>
                    <button
                      onClick={() => setSelectedWorkflow(null)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                
                <div className="px-6 py-4 max-h-96 overflow-y-auto">
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">Description</h4>
                      <p className="text-gray-600 dark:text-gray-400">{selectedWorkflow.description}</p>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Statistics</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span>Total Runs:</span>
                            <span className="font-medium">{selectedWorkflow.run_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Successful:</span>
                            <span className="font-medium text-green-600">{selectedWorkflow.success_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Failed:</span>
                            <span className="font-medium text-red-600">{selectedWorkflow.failure_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Success Rate:</span>
                            <span className="font-medium">{(selectedWorkflow.success_rate * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Timing</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span>Created:</span>
                            <span className="font-medium">{formatTimestamp(selectedWorkflow.created_at)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Last Run:</span>
                            <span className="font-medium">{formatTimestamp(selectedWorkflow.last_run)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Next Run:</span>
                            <span className="font-medium">{formatTimestamp(selectedWorkflow.next_run)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
                  <button
                    onClick={() => setSelectedWorkflow(null)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  >
                    Close
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

export default AutomationDashboard;