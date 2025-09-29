import React, { useState, useEffect } from 'react';

const SecurityDashboard = () => {
  const [securityData, setSecurityData] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [filterLevel, setFilterLevel] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchSecurityData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchSecurityData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchSecurityData = async () => {
    try {
      setIsLoading(true);
      // Mock data - replace with actual API call
      const mockData = {
        alert_stats: {
          total_alerts: 147,
          alerts_24h: 23,
          critical_alerts: 2,
          high_alerts: 5,
          unresolved_alerts: 8
        },
        recent_alerts: [
          {
            id: 'SEC_20240927120001',
            alert_type: 'brute_force',
            threat_level: 'critical',
            title: 'Brute Force Attack Detected',
            description: 'Multiple failed login attempts from IP 192.168.1.100',
            source_ip: '192.168.1.100',
            user_id: null,
            timestamp: new Date(Date.now() - 300000).toISOString(),
            is_resolved: false,
            metadata: {
              failed_attempts: 15,
              target_emails: ['admin@test.com', 'user@test.com']
            }
          },
          {
            id: 'SEC_20240927120002',
            alert_type: 'sql_injection',
            threat_level: 'critical',
            title: 'SQL Injection Attempt',
            description: 'Malicious SQL patterns found in request',
            source_ip: '10.0.0.50',
            user_id: 15,
            timestamp: new Date(Date.now() - 600000).toISOString(),
            is_resolved: false,
            metadata: {
              pattern_matched: 'union select',
              request_snippet: '/api/users?id=1 UNION SELECT...'
            }
          },
          {
            id: 'SEC_20240927120003',
            alert_type: 'suspicious_login',
            threat_level: 'high',
            title: 'Login from New Location',
            description: 'User logged in from previously unseen IP address',
            source_ip: '203.0.113.45',
            user_id: 23,
            timestamp: new Date(Date.now() - 900000).toISOString(),
            is_resolved: true,
            metadata: {
              email: 'john.doe@test.com',
              previous_ips: ['192.168.1.10', '192.168.1.15']
            }
          }
        ],
        top_threat_ips: [
          ['192.168.1.100', 15],
          ['10.0.0.50', 8],
          ['203.0.113.45', 3],
          ['198.51.100.25', 2]
        ],
        alert_types: {
          brute_force: 8,
          sql_injection: 3,
          suspicious_login: 6,
          privilege_escalation: 2,
          xss_attempt: 1,
          rate_limit_exceeded: 3
        },
        recent_access_logs: [
          {
            id: 1,
            user_id: 15,
            action: 'read',
            resource: 'users',
            access_granted: true,
            ip_address: '192.168.1.10',
            timestamp: new Date(Date.now() - 120000).toISOString()
          },
          {
            id: 2,
            user_id: 23,
            action: 'update',
            resource: 'properties',
            access_granted: false,
            ip_address: '192.168.1.15',
            timestamp: new Date(Date.now() - 180000).toISOString()
          }
        ]
      };
      
      setSecurityData(mockData);
    } catch (error) {
      console.error('Error fetching security data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getThreatLevelColor = (level) => {
    switch (level) {
      case 'critical': return 'text-red-600 bg-red-100 border-red-200 dark:bg-red-900/20 dark:border-red-800';
      case 'high': return 'text-orange-600 bg-orange-100 border-orange-200 dark:bg-orange-900/20 dark:border-orange-800';
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800';
      case 'low': return 'text-blue-600 bg-blue-100 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800';
      default: return 'text-gray-600 bg-gray-100 border-gray-200 dark:bg-gray-900/20 dark:border-gray-800';
    }
  };

  const getAlertTypeIcon = (type) => {
    switch (type) {
      case 'brute_force': return '🔒';
      case 'sql_injection': return '⚠️';
      case 'suspicious_login': return '👤';
      case 'privilege_escalation': return '📈';
      case 'xss_attempt': return '🌐';
      case 'rate_limit_exceeded': return '📊';
      default: return '🛡️';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(new Date(timestamp));
  };

  const resolveAlert = async (alertId) => {
    try {
      // Mock API call
      console.log('Resolving alert:', alertId);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update local state
      setSecurityData(prev => ({
        ...prev,
        recent_alerts: prev.recent_alerts.map(alert =>
          alert.id === alertId ? { ...alert, is_resolved: true } : alert
        ),
        alert_stats: {
          ...prev.alert_stats,
          unresolved_alerts: prev.alert_stats.unresolved_alerts - 1
        }
      }));
      
      setSelectedAlert(null);
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const blockIP = async (ipAddress) => {
    try {
      // Mock API call
      console.log('Blocking IP:', ipAddress);
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert(`IP ${ipAddress} has been blocked`);
    } catch (error) {
      console.error('Error blocking IP:', error);
    }
  };

  const StatCard = ({ title, value, icon, color = 'blue', trend = null }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <div className="flex items-center space-x-2">
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
            {trend && (
              <div className={`flex items-center ${trend > 0 ? 'text-red-500' : 'text-green-500'}`}>
                <span className="text-xl">{trend > 0 ? '📈' : '📉'}</span>
                <span className="text-sm font-medium">{Math.abs(trend)}%</span>
              </div>
            )}
          </div>
        </div>
        <div className={`p-3 rounded-full bg-${color}-100 dark:bg-${color}-900/20`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </div>
  );

  const AlertModal = ({ alert, onClose, onResolve, onBlockIP }) => (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black opacity-50" onClick={onClose}></div>
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Security Alert Details
              </h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
          </div>
          
          <div className="px-6 py-4 space-y-4">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getThreatLevelColor(alert.threat_level)}`}>
              <span className="text-lg mr-2">{getAlertTypeIcon(alert.alert_type)}</span>
              <span className="capitalize">{alert.threat_level} Priority</span>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white">{alert.title}</h4>
              <p className="text-gray-600 dark:text-gray-400 mt-1">{alert.description}</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Source IP:</span>
                <p className="text-sm text-gray-900 dark:text-white">{alert.source_ip}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Timestamp:</span>
                <p className="text-sm text-gray-900 dark:text-white">{formatTimestamp(alert.timestamp)}</p>
              </div>
              {alert.user_id && (
                <div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">User ID:</span>
                  <p className="text-sm text-gray-900 dark:text-white">{alert.user_id}</p>
                </div>
              )}
            </div>
            
            {alert.metadata && (
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Additional Details:</span>
                <pre className="mt-2 text-xs bg-gray-100 dark:bg-gray-700 p-3 rounded-lg overflow-auto">
                  {JSON.stringify(alert.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
          
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
            <button
              onClick={() => onBlockIP(alert.source_ip)}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              <span className="text-lg mr-2">🚫</span>
              Block IP
            </button>
            {!alert.is_resolved && (
              <button
                onClick={() => onResolve(alert.id)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <span className="text-lg mr-2">✅</span>
                Resolve Alert
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  if (isLoading || !securityData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const filteredAlerts = securityData.recent_alerts.filter(alert => {
    if (filterLevel !== 'all' && alert.threat_level !== filterLevel) return false;
    if (searchQuery && !alert.title.toLowerCase().includes(searchQuery.toLowerCase()) && 
        !alert.description.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Security Dashboard</h1>
              <p className="text-gray-600 dark:text-gray-400">Monitor threats and security events</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`flex items-center px-3 py-2 rounded-lg ${
                  autoRefresh ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                }`}
              >
                <span className={`text-lg mr-2 ${autoRefresh ? 'animate-spin' : ''}`}>🔄</span>
                Auto Refresh
              </button>
              
              <button
                onClick={fetchSecurityData}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <span className="text-lg mr-2">🔄</span>
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatCard
            title="Total Alerts"
            value={securityData.alert_stats.total_alerts}
            icon="🛡️"
            color="blue"
          />
          <StatCard
            title="24h Alerts"
            value={securityData.alert_stats.alerts_24h}
            icon="📊"
            color="yellow"
            trend={12}
          />
          <StatCard
            title="Critical"
            value={securityData.alert_stats.critical_alerts}
            icon="⚠️"
            color="red"
          />
          <StatCard
            title="High Priority"
            value={securityData.alert_stats.high_alerts}
            icon="🚨"
            color="orange"
          />
          <StatCard
            title="Unresolved"
            value={securityData.alert_stats.unresolved_alerts}
            icon="🕐"
            color="purple"
            trend={-5}
          />
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: '👁️' },
                { id: 'alerts', label: 'Alerts', icon: '⚠️' },
                { id: 'access-logs', label: 'Access Logs', icon: '📊' },
                { id: 'threat-intel', label: 'Threat Intelligence', icon: '🌐' }
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

        {/* Content based on active tab */}
        {activeTab === 'alerts' && (
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
                    placeholder="Search alerts..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                <select
                  value={filterLevel}
                  onChange={(e) => setFilterLevel(e.target.value)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                >
                  <option value="all">All Levels</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            {/* Alerts List */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredAlerts.map(alert => (
                  <div
                    key={alert.id}
                    className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                    onClick={() => setSelectedAlert(alert)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4">
                        <div className={`p-2 rounded-full ${getThreatLevelColor(alert.threat_level)}`}>
                          <span className="text-lg">{getAlertTypeIcon(alert.alert_type)}</span>
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h3 className="font-semibold text-gray-900 dark:text-white">{alert.title}</h3>
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium capitalize ${getThreatLevelColor(alert.threat_level)}`}>
                              {alert.threat_level}
                            </span>
                            {alert.is_resolved && (
                              <span className="text-green-500">✅</span>
                            )}
                          </div>
                          <p className="text-gray-600 dark:text-gray-400 mt-1">{alert.description}</p>
                          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500 dark:text-gray-400">
                            <span className="flex items-center">
                              <span className="mr-1">📍</span>
                              {alert.source_ip}
                            </span>
                            <span className="flex items-center">
                              <span className="mr-1">🕐</span>
                              {formatTimestamp(alert.timestamp)}
                            </span>
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

        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Threat IPs */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Threat IPs</h3>
              <div className="space-y-3">
                {securityData.top_threat_ips.map(([ip, count]) => (
                  <div key={ip} className="flex items-center justify-between">
                    <span className="text-gray-900 dark:text-white font-medium">{ip}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600 dark:text-gray-400">{count} alerts</span>
                      <button
                        onClick={() => blockIP(ip)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Block
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Alert Types Breakdown */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Alert Types (24h)</h3>
              <div className="space-y-3">
                {Object.entries(securityData.alert_types).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getAlertTypeIcon(type)}</span>
                      <span className="text-gray-900 dark:text-white capitalize">
                        {type.replace('_', ' ')}
                      </span>
                    </div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Alert Modal */}
        {selectedAlert && (
          <AlertModal
            alert={selectedAlert}
            onClose={() => setSelectedAlert(null)}
            onResolve={resolveAlert}
            onBlockIP={blockIP}
          />
        )}
      </div>
    </div>
  );
};

export default SecurityDashboard;