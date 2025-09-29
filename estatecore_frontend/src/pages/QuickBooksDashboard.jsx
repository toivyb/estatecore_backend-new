import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent 
} from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { Toast } from '../components/ui/Toast';

const QuickBooksDashboard = () => {
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [integrationHealth, setIntegrationHealth] = useState(null);
  const [syncHistory, setSyncHistory] = useState([]);
  const [automationStatus, setAutomationStatus] = useState(null);
  const [dataQuality, setDataQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [toast, setToast] = useState(null);

  // Fetch integration data
  useEffect(() => {
    fetchIntegrationData();
    // Refresh data every 30 seconds
    const interval = setInterval(fetchIntegrationData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchIntegrationData = async () => {
    try {
      const [statusRes, healthRes, syncRes, automationRes, qualityRes] = await Promise.all([
        fetch('/api/quickbooks/status'),
        fetch('/api/quickbooks/health'),
        fetch('/api/quickbooks/sync/history?limit=10'),
        fetch('/api/quickbooks/automation/status'),
        fetch('/api/quickbooks/data-quality')
      ]);

      const [status, health, sync, automation, quality] = await Promise.all([
        statusRes.json(),
        healthRes.json(),
        syncRes.json(),
        automationRes.json(),
        qualityRes.json()
      ]);

      setConnectionStatus(status);
      setIntegrationHealth(health.health);
      setSyncHistory(sync.sync_history || []);
      setAutomationStatus(automation);
      setDataQuality(quality.data_quality);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching integration data:', error);
      setToast({ type: 'error', message: 'Failed to load integration data' });
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const response = await fetch('/api/quickbooks/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Redirect to QuickBooks OAuth
        window.location.href = result.authorization_url;
      } else {
        setToast({ type: 'error', message: result.error });
      }
    } catch (error) {
      setToast({ type: 'error', message: 'Failed to initiate connection' });
    }
  };

  const handleDisconnect = async () => {
    try {
      const response = await fetch('/api/quickbooks/disconnect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (result.success) {
        setToast({ type: 'success', message: 'Disconnected from QuickBooks' });
        fetchIntegrationData();
      } else {
        setToast({ type: 'error', message: result.error });
      }
    } catch (error) {
      setToast({ type: 'error', message: 'Failed to disconnect' });
    }
  };

  const handleSync = async (direction = 'both') => {
    try {
      setLoading(true);
      const response = await fetch('/api/quickbooks/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction })
      });
      
      const result = await response.json();
      
      if (result.success) {
        setToast({ type: 'success', message: 'Synchronization completed' });
        fetchIntegrationData();
      } else {
        setToast({ type: 'error', message: result.error });
      }
    } catch (error) {
      setToast({ type: 'error', message: 'Synchronization failed' });
    } finally {
      setLoading(false);
      setShowSyncModal(false);
    }
  };

  const handleEnableAutomation = async () => {
    try {
      const response = await fetch('/api/quickbooks/automation/enable', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (result.success) {
        setToast({ type: 'success', message: 'Automation enabled' });
        fetchIntegrationData();
      } else {
        setToast({ type: 'error', message: result.error });
      }
    } catch (error) {
      setToast({ type: 'error', message: 'Failed to enable automation' });
    }
  };

  const handleRunReconciliation = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/quickbooks/reconcile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (result.success) {
        setToast({ type: 'success', message: 'Reconciliation completed' });
        fetchIntegrationData();
      } else {
        setToast({ type: 'error', message: result.error });
      }
    } catch (error) {
      setToast({ type: 'error', message: 'Reconciliation failed' });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-green-600';
      case 'error': return 'text-red-600';
      case 'syncing': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getHealthScore = () => {
    if (!dataQuality) return 0;
    return dataQuality.integrity_score || 0;
  };

  const getHealthColor = (score) => {
    if (score >= 95) return 'text-green-600';
    if (score >= 85) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">QuickBooks Integration</h1>
        <div className="flex gap-2">
          {connectionStatus?.connected ? (
            <>
              <Button
                onClick={() => setShowSyncModal(true)}
                className="bg-blue-600 text-white hover:bg-blue-700"
              >
                Sync Now
              </Button>
              <Button
                onClick={handleDisconnect}
                className="bg-red-600 text-white hover:bg-red-700"
              >
                Disconnect
              </Button>
            </>
          ) : (
            <Button
              onClick={handleConnect}
              className="bg-green-600 text-white hover:bg-green-700"
            >
              Connect to QuickBooks
            </Button>
          )}
        </div>
      </div>

      {/* Connection Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Connection Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-lg font-semibold ${getStatusColor(integrationHealth?.status)}`}>
                  {integrationHealth?.status || 'Unknown'}
                </p>
                {connectionStatus?.company_name && (
                  <p className="text-sm text-gray-600">{connectionStatus.company_name}</p>
                )}
              </div>
              <div className={`w-4 h-4 rounded-full ${
                connectionStatus?.connected ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
            </div>
            {connectionStatus?.last_sync && (
              <p className="text-xs text-gray-500 mt-2">
                Last sync: {new Date(connectionStatus.last_sync).toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data Quality Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className={`text-3xl font-bold ${getHealthColor(getHealthScore())}`}>
                {getHealthScore().toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {dataQuality?.unresolved_discrepancies || 0} unresolved issues
              </p>
              {getHealthScore() < 95 && (
                <Button
                  onClick={handleRunReconciliation}
                  className="mt-2 bg-yellow-600 text-white hover:bg-yellow-700 text-xs"
                >
                  Run Reconciliation
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Automation Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className={`text-lg font-semibold ${
                automationStatus?.automation_enabled ? 'text-green-600' : 'text-gray-600'
              }`}>
                {automationStatus?.automation_enabled ? 'Enabled' : 'Disabled'}
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {automationStatus?.active_workflows || 0} active workflows
              </p>
              {!automationStatus?.automation_enabled && (
                <Button
                  onClick={handleEnableAutomation}
                  className="mt-2 bg-blue-600 text-white hover:bg-blue-700 text-xs"
                >
                  Enable Automation
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Sync History */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Recent Synchronization History</CardTitle>
        </CardHeader>
        <CardContent>
          {syncHistory.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Entity Type</th>
                    <th className="text-left py-2">Direction</th>
                    <th className="text-left py-2">Status</th>
                    <th className="text-left py-2">Timestamp</th>
                    <th className="text-left py-2">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {syncHistory.map((sync, index) => (
                    <tr key={index} className="border-b">
                      <td className="py-2">{sync.entity_type}</td>
                      <td className="py-2">
                        <span className="capitalize">{sync.direction?.replace('_', ' ')}</span>
                      </td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          sync.status === 'completed' 
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {sync.status}
                        </span>
                      </td>
                      <td className="py-2">
                        {new Date(sync.sync_timestamp).toLocaleString()}
                      </td>
                      <td className="py-2 text-red-600 text-xs">
                        {sync.error_message || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No synchronization history available</p>
          )}
        </CardContent>
      </Card>

      {/* Health Issues and Recommendations */}
      {integrationHealth?.issues?.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-red-600">Issues Requiring Attention</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1">
              {integrationHealth.issues.map((issue, index) => (
                <li key={index} className="text-sm text-red-600">{issue}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {integrationHealth?.recommendations?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-blue-600">Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1">
              {integrationHealth.recommendations.map((rec, index) => (
                <li key={index} className="text-sm text-blue-600">{rec}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Sync Modal */}
      <Modal 
        isOpen={showSyncModal} 
        onClose={() => setShowSyncModal(false)}
        title="Synchronize Data"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Choose the synchronization direction:
          </p>
          <div className="flex flex-col space-y-2">
            <Button
              onClick={() => handleSync('to_qb')}
              className="w-full bg-blue-600 text-white hover:bg-blue-700"
            >
              Sync EstateCore → QuickBooks
            </Button>
            <Button
              onClick={() => handleSync('from_qb')}
              className="w-full bg-green-600 text-white hover:bg-green-700"
            >
              Sync QuickBooks → EstateCore
            </Button>
            <Button
              onClick={() => handleSync('both')}
              className="w-full bg-purple-600 text-white hover:bg-purple-700"
            >
              Bidirectional Sync
            </Button>
          </div>
        </div>
      </Modal>

      {/* Toast Notifications */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default QuickBooksDashboard;