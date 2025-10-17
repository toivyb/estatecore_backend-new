import { useEffect, useState } from "react";
import api from '../api';

export default function AccessControl() {
  const [logs, setLogs] = useState([]);
  const [form, setForm] = useState({ user: "", location: "", action: "Property Access" });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('logs');
  const [platforms, setPlatforms] = useState([]);
  const [connectedDevices, setConnectedDevices] = useState([]);
  const [integrationSettings, setIntegrationSettings] = useState({
    platform: '',
    apiUrl: '',
    apiKey: '',
    enabled: false
  });

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    await Promise.all([
      loadLogs(),
      loadPlatforms(), 
      loadConnectedDevices()
    ]);
  };

  const loadLogs = async () => {
    try {
      const data = await api.get("/api/access-logs");
      if (Array.isArray(data)) {
        setLogs(data);
      } else if (data.logs) {
        setLogs(data.logs);
      }
    } catch (error) {
      console.error('Error loading access logs:', error);
      setLogs([]);
    }
  };

  const loadPlatforms = async () => {
    try {
      const data = await api.get("/api/access-control/platforms");
      if (data.success) {
        setPlatforms(data.data);
      }
    } catch (error) {
      console.error('Error loading platforms:', error);
    }
  };

  const loadConnectedDevices = async () => {
    try {
      const data = await api.get("/api/access-control/devices");
      if (data.success) {
        setConnectedDevices(data.data);
      }
    } catch (error) {
      console.error('Error loading devices:', error);
    }
  };

  const handleSimulate = async (e) => {
    e.preventDefault();
    if (!form.user.trim()) {
      alert('Please enter a user name');
      return;
    }
    
    setLoading(true);
    try {
      const response = await api.post("/api/access-logs/simulate", form);
      if (response.success) {
        // Reload logs to show the new simulated entry
        const data = await api.get("/api/access-logs");
        if (Array.isArray(data)) {
          setLogs(data);
        }
        setForm({ user: "", location: "", action: "Property Access" });
        alert(`Access log simulated successfully! Status: ${response.log.status}`);
      } else {
        alert(response.error || 'Failed to simulate access log');
      }
    } catch (error) {
      console.error('Error simulating access log:', error);
      alert('Failed to simulate access log');
    } finally {
      setLoading(false);
    }
  };

  const handlePlatformConnect = async (platformData) => {
    try {
      const response = await api.post("/api/access-control/platforms", platformData);
      if (response.success) {
        alert('Platform connected successfully!');
        loadPlatforms();
        loadConnectedDevices();
      } else {
        alert(response.error || 'Failed to connect platform');
      }
    } catch (error) {
      console.error('Error connecting platform:', error);
      alert('Failed to connect platform');
    }
  };

  const handleDeviceAction = async (deviceId, action) => {
    try {
      const response = await api.post(`/api/access-control/devices/${deviceId}/${action}`, {});
      if (response.success) {
        alert(`Device ${action} successful!`);
        loadConnectedDevices();
      } else {
        alert(response.error || `Failed to ${action} device`);
      }
    } catch (error) {
      console.error(`Error ${action} device:`, error);
      alert(`Failed to ${action} device`);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Access Control & Audit Logs</h2>
      
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'logs', name: 'Audit Logs', icon: '📋' },
            { id: 'integrations', name: 'Platform Integrations', icon: '🔗' },
            { id: 'devices', name: 'Connected Devices', icon: '📱' }
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
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <>
          {/* Simulate Access Log Form */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Simulate Access Log</h3>
            <form onSubmit={handleSimulate} className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User Name *
                </label>
                <input 
                  value={form.user} 
                  onChange={e => setForm({ ...form, user: e.target.value })} 
                  placeholder="John Doe"
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location
                </label>
                <input 
                  value={form.location} 
                  onChange={e => setForm({ ...form, location: e.target.value })} 
                  placeholder="Main Entrance"
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Action Type
                </label>
                <select 
                  value={form.action} 
                  onChange={e => setForm({ ...form, action: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="Property Access">Property Access</option>
                  <option value="Unit Access">Unit Access</option>
                  <option value="Attempted Access">Attempted Access</option>
                  <option value="Emergency Access">Emergency Access</option>
                </select>
              </div>
              
              <div className="flex items-end">
                <button 
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50" 
                  type="submit"
                  disabled={loading}
                >
                  {loading ? 'Simulating...' : '🔐 Simulate Access'}
                </button>
              </div>
            </form>
          </div>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Access Audit Logs</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Method
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.user}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.location}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.action}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                          {log.method}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          log.status === 'granted' 
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {log.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {logs.length === 0 && (
                    <tr>
                      <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                        No access logs found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Platform Integrations Tab */}
      {activeTab === 'integrations' && (
        <div className="space-y-6">
          {/* Add New Platform Integration */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Connect Access Control Platform</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              handlePlatformConnect(integrationSettings);
            }} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Platform *
                </label>
                <select 
                  value={integrationSettings.platform} 
                  onChange={e => setIntegrationSettings({ ...integrationSettings, platform: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                >
                  <option value="">Select Platform</option>
                  <option value="hartman">Hartman Systems</option>
                  <option value="akuvox">Akuvox</option>
                  <option value="kantech">Kantech</option>
                  <option value="lenel">Lenel OnGuard</option>
                  <option value="honeywell">Honeywell Pro-Watch</option>
                  <option value="genetec">Genetec Security Center</option>
                  <option value="ccure">C•CURE 9000</option>
                  <option value="avigilon">Avigilon</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API URL *
                </label>
                <input 
                  value={integrationSettings.apiUrl} 
                  onChange={e => setIntegrationSettings({ ...integrationSettings, apiUrl: e.target.value })}
                  placeholder="https://api.platform.com"
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key *
                </label>
                <input 
                  type="password"
                  value={integrationSettings.apiKey} 
                  onChange={e => setIntegrationSettings({ ...integrationSettings, apiKey: e.target.value })}
                  placeholder="Enter API Key"
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div className="flex items-center">
                <label className="flex items-center">
                  <input 
                    type="checkbox"
                    checked={integrationSettings.enabled}
                    onChange={e => setIntegrationSettings({ ...integrationSettings, enabled: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Enable Integration</span>
                </label>
              </div>
              
              <div className="flex items-end">
                <button 
                  className="w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700" 
                  type="submit"
                >
                  🔗 Connect Platform
                </button>
              </div>
            </form>
          </div>

          {/* Connected Platforms */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Connected Platforms</h3>
            </div>
            <div className="p-6">
              {platforms.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-lg mb-2">🔗 No platforms connected</p>
                  <p>Connect your first access control platform above to get started.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {platforms.map((platform, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium capitalize">{platform.name || platform.platform}</h4>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          platform.status === 'connected' 
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {platform.status || 'connected'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{platform.api_url || platform.apiUrl}</p>
                      <p className="text-xs text-gray-500">Connected: {new Date(platform.created_at || Date.now()).toLocaleDateString()}</p>
                      <div className="mt-3 flex gap-2">
                        <button className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded hover:bg-blue-200">
                          Test Connection
                        </button>
                        <button className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200">
                          Disconnect
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Connected Devices Tab */}
      {activeTab === 'devices' && (
        <div className="space-y-6">
          {/* Device Status Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow border">
              <div className="text-2xl font-bold text-green-600">{connectedDevices.filter(d => d.status === 'online').length}</div>
              <div className="text-sm text-gray-500">Online Devices</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border">
              <div className="text-2xl font-bold text-red-600">{connectedDevices.filter(d => d.status === 'offline').length}</div>
              <div className="text-sm text-gray-500">Offline Devices</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border">
              <div className="text-2xl font-bold text-yellow-600">{connectedDevices.filter(d => d.status === 'warning').length}</div>
              <div className="text-sm text-gray-500">Warning Status</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border">
              <div className="text-2xl font-bold text-blue-600">{connectedDevices.length}</div>
              <div className="text-sm text-gray-500">Total Devices</div>
            </div>
          </div>

          {/* Device List */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Connected Access Devices</h3>
            </div>
            <div className="p-6">
              {connectedDevices.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-lg mb-2">📱 No devices connected</p>
                  <p>Devices will appear here once you connect access control platforms.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {connectedDevices.map((device) => (
                    <div key={device.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium">{device.name}</h4>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          device.status === 'online' 
                            ? 'bg-green-100 text-green-800'
                            : device.status === 'offline'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {device.status}
                        </span>
                      </div>
                      <div className="space-y-1 text-sm text-gray-600">
                        <p>Type: {device.type}</p>
                        <p>Location: {device.location}</p>
                        <p>Platform: {device.platform}</p>
                        <p>Last Seen: {new Date(device.last_seen).toLocaleString()}</p>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <button 
                          onClick={() => handleDeviceAction(device.id, 'unlock')}
                          className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200"
                        >
                          🔓 Unlock
                        </button>
                        <button 
                          onClick={() => handleDeviceAction(device.id, 'lock')}
                          className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200"
                        >
                          🔒 Lock
                        </button>
                        <button 
                          onClick={() => handleDeviceAction(device.id, 'status')}
                          className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded hover:bg-blue-200"
                        >
                          📊 Status
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
