import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Toast from './ui/Toast';

const SecurityDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [securityEvents, setSecurityEvents] = useState([]);
  const [securityAlerts, setSecurityAlerts] = useState([]);
  const [activeSessions, setActiveSessions] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [rateLimits, setRateLimits] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [showSessionModal, setShowSessionModal] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [filter, setFilter] = useState({
    eventType: 'all',
    threatLevel: 'all',
    timeRange: '24h',
    alertSeverity: 'all',
    resolved: 'all'
  });

  // Threat level colors
  const threatLevelColors = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800'
  };

  const eventTypeColors = {
    login_success: 'bg-green-100 text-green-800',
    login_failure: 'bg-red-100 text-red-800',
    session_created: 'bg-blue-100 text-blue-800',
    session_expired: 'bg-gray-100 text-gray-800',
    permission_denied: 'bg-orange-100 text-orange-800',
    suspicious_activity: 'bg-red-100 text-red-800',
    api_key_created: 'bg-green-100 text-green-800',
    api_key_revoked: 'bg-red-100 text-red-800'
  };

  // Fetch dashboard overview data
  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/security/dashboard', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setDashboardData(result.data);
        }
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      showToast('Failed to fetch dashboard data', 'error');
    }
  };

  // Fetch security events
  const fetchSecurityEvents = async () => {
    try {
      const params = new URLSearchParams({
        limit: '50'
      });
      
      if (filter.eventType !== 'all') params.append('event_type', filter.eventType);
      if (filter.threatLevel !== 'all') params.append('threat_level', filter.threatLevel);

      const response = await fetch(`/api/security/events?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setSecurityEvents(result.events || []);
        }
      }
    } catch (error) {
      console.error('Error fetching security events:', error);
    }
  };

  // Fetch security alerts
  const fetchSecurityAlerts = async () => {
    try {
      const params = new URLSearchParams({
        limit: '20'
      });
      
      if (filter.alertSeverity !== 'all') params.append('severity', filter.alertSeverity);
      if (filter.resolved !== 'all') params.append('resolved', filter.resolved);

      const response = await fetch(`/api/security/alerts?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setSecurityAlerts(result.alerts || []);
        }
      }
    } catch (error) {
      console.error('Error fetching security alerts:', error);
    }
  };

  // Fetch active sessions
  const fetchActiveSessions = async () => {
    try {
      const response = await fetch('/api/security/sessions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setActiveSessions(result.sessions || []);
        }
      }
    } catch (error) {
      console.error('Error fetching active sessions:', error);
    }
  };

  // Fetch API keys
  const fetchApiKeys = async () => {
    try {
      const response = await fetch('/api/security/api-keys', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setApiKeys(result.api_keys || []);
        }
      }
    } catch (error) {
      console.error('Error fetching API keys:', error);
    }
  };

  // Fetch rate limit status
  const fetchRateLimits = async () => {
    try {
      const response = await fetch('/api/security/rate-limits', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setRateLimits(result);
        }
      }
    } catch (error) {
      console.error('Error fetching rate limits:', error);
    }
  };

  // Revoke session
  const revokeSession = async (sessionId) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/security/sessions/${sessionId}/revoke`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast('Session revoked successfully', 'success');
        fetchActiveSessions();
        fetchDashboardData();
      } else {
        showToast(result.error || 'Failed to revoke session', 'error');
      }
    } catch (error) {
      console.error('Error revoking session:', error);
      showToast('Failed to revoke session', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Create API key
  const createApiKey = async (apiKeyData) => {
    setLoading(true);
    try {
      const response = await fetch('/api/security/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(apiKeyData)
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast('API key created successfully', 'success');
        setShowApiKeyModal(false);
        fetchApiKeys();
        fetchDashboardData();
        
        // Show the API key (only shown once)
        if (result.api_key) {
          alert(`API Key Created:\n\n${result.api_key}\n\nPlease save this key as it will not be shown again.`);
        }
      } else {
        showToast(result.error || 'Failed to create API key', 'error');
      }
    } catch (error) {
      console.error('Error creating API key:', error);
      showToast('Failed to create API key', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Revoke API key
  const revokeApiKey = async (keyId) => {
    if (!confirm('Are you sure you want to revoke this API key?')) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/security/api-keys/${keyId}/revoke`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast('API key revoked successfully', 'success');
        fetchApiKeys();
        fetchDashboardData();
      } else {
        showToast(result.error || 'Failed to revoke API key', 'error');
      }
    } catch (error) {
      console.error('Error revoking API key:', error);
      showToast('Failed to revoke API key', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Resolve security alert
  const resolveAlert = async (alertId) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/security/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast('Security alert resolved', 'success');
        fetchSecurityAlerts();
        fetchDashboardData();
      } else {
        showToast(result.error || 'Failed to resolve alert', 'error');
      }
    } catch (error) {
      console.error('Error resolving alert:', error);
      showToast('Failed to resolve alert', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Test security alert
  const testAlert = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/security/test-alert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          type: 'test_alert',
          severity: 'medium'
        })
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        showToast('Test alert generated successfully', 'success');
        fetchSecurityEvents();
        fetchSecurityAlerts();
        fetchDashboardData();
      } else {
        showToast(result.error || 'Failed to generate test alert', 'error');
      }
    } catch (error) {
      console.error('Error generating test alert:', error);
      showToast('Failed to generate test alert', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Show toast notification
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  useEffect(() => {
    fetchDashboardData();
    fetchSecurityEvents();
    fetchSecurityAlerts();
    fetchActiveSessions();
    fetchApiKeys();
    fetchRateLimits();
  }, []);

  useEffect(() => {
    fetchSecurityEvents();
    fetchSecurityAlerts();
  }, [filter]);

  return (
    <div className="space-y-6">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Security Dashboard</h2>
          <p className="text-gray-600">
            Advanced security monitoring and threat detection
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={() => setShowApiKeyModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Create API Key
          </Button>
          
          <Button
            onClick={testAlert}
            disabled={loading}
            className="bg-orange-600 hover:bg-orange-700 text-white"
          >
            Test Alert
          </Button>
        </div>
      </div>

      {/* Security Overview Metrics */}
      {dashboardData?.overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Sessions</p>
                <p className="text-2xl font-bold text-blue-600">
                  {dashboardData.overview.active_sessions}
                </p>
              </div>
              <div className="text-3xl">🔒</div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Security Alerts</p>
                <p className="text-2xl font-bold text-red-600">
                  {dashboardData.overview.security_alerts}
                </p>
              </div>
              <div className="text-3xl">🚨</div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Events (24h)</p>
                <p className="text-2xl font-bold text-purple-600">
                  {dashboardData.overview.events_24h}
                </p>
              </div>
              <div className="text-3xl">📊</div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Events (7d)</p>
                <p className="text-2xl font-bold text-green-600">
                  {dashboardData.overview.events_7d}
                </p>
              </div>
              <div className="text-3xl">📈</div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">API Keys</p>
                <p className="text-2xl font-bold text-orange-600">
                  {dashboardData.overview.api_keys_active}
                </p>
              </div>
              <div className="text-3xl">🔑</div>
            </div>
          </Card>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: '🔍' },
            { id: 'events', label: 'Security Events', icon: '📋' },
            { id: 'alerts', label: 'Alerts', icon: '🚨' },
            { id: 'sessions', label: 'Active Sessions', icon: '🔒' },
            { id: 'apikeys', label: 'API Keys', icon: '🔑' },
            { id: 'monitoring', label: 'Monitoring', icon: '📊' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
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
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Event Breakdown */}
            {dashboardData?.event_breakdown && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">Events by Type</h3>
                  <div className="space-y-3">
                    {Object.entries(dashboardData.event_breakdown.by_type || {}).map(([type, count]) => (
                      <div key={type} className="flex items-center justify-between">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          eventTypeColors[type] || 'bg-gray-100 text-gray-800'
                        }`}>
                          {type.replace('_', ' ')}
                        </span>
                        <span className="font-bold">{count}</span>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">Threat Levels</h3>
                  <div className="space-y-3">
                    {Object.entries(dashboardData.event_breakdown.by_threat_level || {}).map(([level, count]) => (
                      <div key={level} className="flex items-center justify-between">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          threatLevelColors[level] || 'bg-gray-100 text-gray-800'
                        }`}>
                          {level.toUpperCase()}
                        </span>
                        <span className="font-bold">{count}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )}

            {/* Recent Events Preview */}
            {dashboardData?.recent_events && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Recent Security Events</h3>
                <div className="space-y-3">
                  {dashboardData.recent_events.slice(0, 5).map((event) => (
                    <div key={event.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          threatLevelColors[event.threat_level] || 'bg-gray-100 text-gray-800'
                        }`}>
                          {event.threat_level.toUpperCase()}
                        </span>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {event.type.replace('_', ' ')}
                          </div>
                          <div className="text-sm text-gray-500">
                            {event.ip_address} • User {event.user_id || 'Unknown'}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">
                          {formatDate(event.timestamp)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'events' && (
          <div className="space-y-6">
            {/* Filters */}
            <Card className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Event Type
                  </label>
                  <select
                    value={filter.eventType}
                    onChange={(e) => setFilter({ ...filter, eventType: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Types</option>
                    <option value="login_success">Login Success</option>
                    <option value="login_failure">Login Failure</option>
                    <option value="session_created">Session Created</option>
                    <option value="permission_denied">Permission Denied</option>
                    <option value="suspicious_activity">Suspicious Activity</option>
                    <option value="api_key_created">API Key Created</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Threat Level
                  </label>
                  <select
                    value={filter.threatLevel}
                    onChange={(e) => setFilter({ ...filter, threatLevel: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Levels</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time Range
                  </label>
                  <select
                    value={filter.timeRange}
                    onChange={(e) => setFilter({ ...filter, timeRange: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="24h">Last 24 Hours</option>
                    <option value="7d">Last 7 Days</option>
                    <option value="30d">Last 30 Days</option>
                  </select>
                </div>
              </div>
            </Card>

            {/* Events Table */}
            <Card className="p-4">
              <h3 className="text-lg font-semibold mb-4">Security Events</h3>
              {securityEvents.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-6xl mb-4">🔍</div>
                  <p className="text-gray-600">No security events found</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Event
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          User/IP
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Threat Level
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Timestamp
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {securityEvents.map((event) => (
                        <tr key={event.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {event.event_type.replace('_', ' ')}
                            </div>
                            <div className="text-sm text-gray-500">
                              {event.endpoint || 'N/A'}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              User: {event.user_id || 'Unknown'}
                            </div>
                            <div className="text-sm text-gray-500">
                              IP: {event.ip_address}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              threatLevelColors[event.threat_level] || 'bg-gray-100 text-gray-800'
                            }`}>
                              {event.threat_level.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(event.timestamp)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              event.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {event.success ? 'Success' : 'Failed'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="space-y-6">
            {/* Alert Filters */}
            <Card className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Severity
                  </label>
                  <select
                    value={filter.alertSeverity}
                    onChange={(e) => setFilter({ ...filter, alertSeverity: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Severities</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <select
                    value={filter.resolved}
                    onChange={(e) => setFilter({ ...filter, resolved: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Alerts</option>
                    <option value="false">Open</option>
                    <option value="true">Resolved</option>
                  </select>
                </div>
              </div>
            </Card>

            {/* Alerts List */}
            <Card className="p-4">
              <h3 className="text-lg font-semibold mb-4">Security Alerts</h3>
              {securityAlerts.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-6xl mb-4">🚨</div>
                  <p className="text-gray-600">No security alerts found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {securityAlerts.map((alert) => (
                    <div key={alert.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            threatLevelColors[alert.severity] || 'bg-gray-100 text-gray-800'
                          }`}>
                            {alert.severity.toUpperCase()}
                          </span>
                          <div>
                            <h4 className="text-sm font-medium text-gray-900">
                              {alert.alert_type.replace('_', ' ')}
                            </h4>
                            <p className="text-sm text-gray-600">{alert.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {alert.resolved ? (
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                              Resolved
                            </span>
                          ) : (
                            <Button
                              onClick={() => resolveAlert(alert.id)}
                              disabled={loading}
                              size="sm"
                              className="bg-green-600 hover:bg-green-700 text-white"
                            >
                              Resolve
                            </Button>
                          )}
                        </div>
                      </div>
                      <div className="mt-2 text-sm text-gray-500">
                        {formatDate(alert.timestamp)} • IP: {alert.ip_address}
                        {alert.user_id && ` • User: ${alert.user_id}`}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}

        {activeTab === 'sessions' && (
          <div className="space-y-6">
            <Card className="p-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Active Sessions ({activeSessions.length})</h3>
              </div>
              
              {activeSessions.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-6xl mb-4">🔒</div>
                  <p className="text-gray-600">No active sessions found</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          IP Address
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Created
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Last Accessed
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {activeSessions.map((session) => (
                        <tr key={session.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              User {session.user_id}
                            </div>
                            <div className="text-sm text-gray-500">
                              {session.status}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {session.ip_address}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(session.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(session.last_accessed)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <Button
                              onClick={() => revokeSession(session.id)}
                              disabled={loading}
                              size="sm"
                              className="bg-red-600 hover:bg-red-700 text-white"
                            >
                              Revoke
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        )}

        {activeTab === 'apikeys' && (
          <div className="space-y-6">
            <Card className="p-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">API Keys ({apiKeys.length})</h3>
              </div>
              
              {apiKeys.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-6xl mb-4">🔑</div>
                  <p className="text-gray-600">No API keys found</p>
                  <Button
                    onClick={() => setShowApiKeyModal(true)}
                    className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Create First API Key
                  </Button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Created
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Last Used
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {apiKeys.map((key) => (
                        <tr key={key.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {key.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              Rate limit: {key.rate_limit}/hour
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            User {key.user_id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(key.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {key.last_used ? formatDate(key.last_used) : 'Never'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              key.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {key.is_active ? 'Active' : 'Revoked'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            {key.is_active && (
                              <Button
                                onClick={() => revokeApiKey(key.id)}
                                disabled={loading}
                                size="sm"
                                className="bg-red-600 hover:bg-red-700 text-white"
                              >
                                Revoke
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        )}

        {activeTab === 'monitoring' && rateLimits && (
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Rate Limiting Rules</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Endpoint
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Max Requests
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Time Window
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Scope
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {rateLimits.rules?.map((rule, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {rule.endpoint}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {rule.max_requests}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {rule.time_window}s
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {rule.per_user ? 'Per User' : rule.per_ip ? 'Per IP' : 'Global'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {rateLimits.current_limits?.length > 0 && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Current Rate Limit Status</h3>
                <div className="space-y-3">
                  {rateLimits.current_limits.map((limit, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{limit.key}</div>
                        <div className="text-sm text-gray-500">
                          Current requests: {limit.current_requests}
                        </div>
                      </div>
                      <div>
                        {limit.is_blocked ? (
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                            Blocked
                          </span>
                        ) : (
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}
      </div>

      {/* API Key Creation Modal */}
      <Modal
        isOpen={showApiKeyModal}
        onClose={() => setShowApiKeyModal(false)}
        title="Create API Key"
      >
        <ApiKeyForm
          onSubmit={createApiKey}
          onCancel={() => setShowApiKeyModal(false)}
          loading={loading}
        />
      </Modal>
    </div>
  );
};

// API Key Form Component
const ApiKeyForm = ({ onSubmit, onCancel, loading }) => {
  const [apiKeyData, setApiKeyData] = useState({
    name: '',
    permissions: [],
    rate_limit: 1000,
    expires_at: ''
  });

  const availablePermissions = [
    'read_property',
    'write_property',
    'read_tenant',
    'write_tenant',
    'read_financial',
    'write_financial',
    'read_lease',
    'write_lease',
    'read_payment',
    'write_payment'
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(apiKeyData);
  };

  const togglePermission = (permission) => {
    const newPermissions = apiKeyData.permissions.includes(permission)
      ? apiKeyData.permissions.filter(p => p !== permission)
      : [...apiKeyData.permissions, permission];
    
    setApiKeyData({ ...apiKeyData, permissions: newPermissions });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          API Key Name
        </label>
        <input
          type="text"
          value={apiKeyData.name}
          onChange={(e) => setApiKeyData({ ...apiKeyData, name: e.target.value })}
          placeholder="e.g., Mobile App API Key"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Permissions
        </label>
        <div className="grid grid-cols-2 gap-2">
          {availablePermissions.map((permission) => (
            <label key={permission} className="flex items-center">
              <input
                type="checkbox"
                checked={apiKeyData.permissions.includes(permission)}
                onChange={() => togglePermission(permission)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-900">
                {permission.replace('_', ' ')}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Rate Limit (requests per hour)
        </label>
        <input
          type="number"
          value={apiKeyData.rate_limit}
          onChange={(e) => setApiKeyData({ ...apiKeyData, rate_limit: parseInt(e.target.value) })}
          min="1"
          max="10000"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Expiration Date (Optional)
        </label>
        <input
          type="datetime-local"
          value={apiKeyData.expires_at}
          onChange={(e) => setApiKeyData({ ...apiKeyData, expires_at: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex justify-end space-x-3">
        <Button
          type="button"
          onClick={onCancel}
          variant="outline"
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={loading || !apiKeyData.name || apiKeyData.permissions.length === 0}
        >
          {loading ? 'Creating...' : 'Create API Key'}
        </Button>
      </div>
    </form>
  );
};

export default SecurityDashboard;