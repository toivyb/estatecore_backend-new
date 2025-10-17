import React, { useState, useEffect, useRef } from 'react';
import api from '../api';

const CameraManagement = () => {
  const [activeTab, setActiveTab] = useState('systems');
  const [cameraSystems, setCameraSystems] = useState([]);
  const [connectedCameras, setConnectedCameras] = useState([]);
  const [liveStreams, setLiveStreams] = useState({});
  const [loading, setLoading] = useState(false);
  const [systemIntegration, setSystemIntegration] = useState({
    platform: '',
    serverUrl: '',
    username: '',
    password: '',
    port: '',
    enabled: false,
    useSSL: true,
    connectionType: 'local', // 'local' or 'cloud'
    cloudRegion: 'us-east-1',
    apiKey: ''
  });

  const streamRefs = useRef({});
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [streamStatus, setStreamStatus] = useState({});

  useEffect(() => {
    loadAllData();
    // Set up periodic status updates
    const interval = setInterval(() => {
      updateStreamStatuses();
    }, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const loadAllData = async () => {
    await Promise.all([
      loadCameraSystems(),
      loadConnectedCameras()
    ]);
  };

  const loadCameraSystems = async () => {
    try {
      const data = await api.get("/api/camera-systems/platforms");
      if (data.success) {
        setCameraSystems(data.data);
      }
    } catch (error) {
      console.error('Error loading camera systems:', error);
    }
  };

  const loadConnectedCameras = async () => {
    try {
      const data = await api.get("/api/camera-systems/cameras");
      if (data.success) {
        setConnectedCameras(data.data);
      }
    } catch (error) {
      console.error('Error loading cameras:', error);
    }
  };

  const handleSystemConnect = async (systemData) => {
    try {
      setLoading(true);
      const response = await api.post("/api/camera-systems/platforms", systemData);
      if (response.success) {
        alert(`Successfully connected to ${systemData.platform}!`);
        loadCameraSystems();
        loadConnectedCameras();
      } else {
        alert(response.error || 'Failed to connect to camera system');
      }
    } catch (error) {
      console.error('Error connecting camera system:', error);
      alert('Failed to connect to camera system');
    } finally {
      setLoading(false);
    }
  };

  const startLiveStream = async (cameraId) => {
    try {
      const response = await api.post(`/api/camera-systems/cameras/${cameraId}/stream/start`);
      if (response.success) {
        setLiveStreams(prev => ({
          ...prev,
          [cameraId]: {
            url: response.data.stream_url,
            status: 'streaming',
            startTime: new Date()
          }
        }));
        setStreamStatus(prev => ({
          ...prev,
          [cameraId]: 'streaming'
        }));
      } else {
        alert('Failed to start live stream: ' + response.error);
      }
    } catch (error) {
      console.error('Error starting stream:', error);
      alert('Failed to start live stream');
    }
  };

  const stopLiveStream = async (cameraId) => {
    try {
      const response = await api.post(`/api/camera-systems/cameras/${cameraId}/stream/stop`);
      if (response.success) {
        setLiveStreams(prev => {
          const { [cameraId]: removed, ...rest } = prev;
          return rest;
        });
        setStreamStatus(prev => ({
          ...prev,
          [cameraId]: 'stopped'
        }));
      }
    } catch (error) {
      console.error('Error stopping stream:', error);
    }
  };

  const takeSnapshot = async (cameraId) => {
    try {
      const response = await api.post(`/api/camera-systems/cameras/${cameraId}/snapshot`);
      if (response.success) {
        alert('Snapshot captured successfully!');
        // You could download the snapshot or show it in a modal
        const link = document.createElement('a');
        link.href = response.data.snapshot_url;
        link.download = `snapshot_${cameraId}_${new Date().toISOString()}.jpg`;
        link.click();
      }
    } catch (error) {
      console.error('Error taking snapshot:', error);
      alert('Failed to take snapshot');
    }
  };

  const controlCamera = async (cameraId, action, params = {}) => {
    try {
      const response = await api.post(`/api/camera-systems/cameras/${cameraId}/control`, {
        action,
        ...params
      });
      if (response.success) {
        alert(`Camera control action "${action}" executed successfully`);
      } else {
        alert('Failed to execute camera control: ' + response.error);
      }
    } catch (error) {
      console.error('Error controlling camera:', error);
      alert('Failed to control camera');
    }
  };

  const updateStreamStatuses = async () => {
    for (const cameraId of Object.keys(liveStreams)) {
      try {
        const response = await api.get(`/api/camera-systems/cameras/${cameraId}/status`);
        if (response.success) {
          setStreamStatus(prev => ({
            ...prev,
            [cameraId]: response.data.status
          }));
        }
      } catch (error) {
        console.error(`Error updating status for camera ${cameraId}:`, error);
      }
    }
  };

  const getSystemIcon = (platform) => {
    const icons = {
      hikvision: '🔍',
      dahua: '👁️',
      axis: '📹',
      bosch: '🎯',
      panasonic: '📺',
      samsung: '🖥️',
      avigilon: '🛡️',
      milestone: '⏯️',
      genetec: '🔐',
      verkada: '☁️',
      ubiquiti: '📡',
      nx_witness: '👁️‍🗨️',
      foscam: '🏠',
      hik_connect: '☁️🔍',
      dw_cloud: '☁️👁️',
      eagle_eye: '🦅',
      verkada_cloud: '☁️📊',
      axis_companion: '☁️🎯',
      bosch_cloud: '☁️🛡️',
      hanwha_cloud: '☁️📺',
      ivideon: '☁️📹',
      camcloud: '☁️💾',
      rhombus: '☁️🔷'
    };
    return icons[platform] || '📷';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800';
      case 'streaming': return 'bg-blue-100 text-blue-800';
      case 'offline': return 'bg-red-100 text-red-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'stopped': return 'bg-gray-100 text-gray-800';
      case 'recording': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Camera System Management</h2>
      
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'systems', name: 'System Integrations', icon: '🔗' },
            { id: 'cameras', name: 'Connected Cameras', icon: '📹' },
            { id: 'liveview', name: 'Live View', icon: '📺' },
            { id: 'recordings', name: 'Recordings', icon: '📼' }
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

      {/* System Integrations Tab */}
      {activeTab === 'systems' && (
        <div className="space-y-6">
          {/* Add New System Integration */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Connect Camera System</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              handleSystemConnect(systemIntegration);
            }} className="space-y-4">
              
              {/* Connection Type Selector */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Connection Type *
                  </label>
                  <select 
                    value={systemIntegration.connectionType} 
                    onChange={e => setSystemIntegration({ 
                      ...systemIntegration, 
                      connectionType: e.target.value,
                      serverUrl: '', // Reset server URL when switching types
                      port: e.target.value === 'cloud' ? '' : systemIntegration.port
                    })}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  >
                    <option value="local">Local Network / On-Premise</option>
                    <option value="cloud">Cloud Service</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Platform *
                  </label>
                  <select 
                    value={systemIntegration.platform} 
                    onChange={e => setSystemIntegration({ ...systemIntegration, platform: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  >
                    <option value="">Select Platform</option>
                    {systemIntegration.connectionType === 'local' ? (
                      <>
                        <option value="hikvision">Hikvision</option>
                        <option value="dahua">Dahua</option>
                        <option value="axis">Axis Communications</option>
                        <option value="bosch">Bosch Security</option>
                        <option value="panasonic">Panasonic i-PRO</option>
                        <option value="samsung">Samsung Wisenet</option>
                        <option value="avigilon">Avigilon</option>
                        <option value="milestone">Milestone XProtect</option>
                        <option value="genetec">Genetec Security Center</option>
                        <option value="ubiquiti">Ubiquiti UniFi Protect</option>
                        <option value="nx_witness">DW Spectrum / Nx Witness</option>
                        <option value="foscam">Foscam</option>
                      </>
                    ) : (
                      <>
                        <option value="hik_connect">Hik-Connect Cloud</option>
                        <option value="dw_cloud">DW Cloud</option>
                        <option value="eagle_eye">Eagle Eye Networks</option>
                        <option value="verkada_cloud">Verkada Command</option>
                        <option value="axis_companion">AXIS Companion</option>
                        <option value="bosch_cloud">Bosch Video Cloud</option>
                        <option value="hanwha_cloud">Hanwha Wisenet WAVE</option>
                        <option value="ivideon">Ivideon Cloud</option>
                        <option value="camcloud">CamCloud</option>
                        <option value="rhombus">Rhombus Cloud</option>
                      </>
                    )}
                  </select>
                </div>
              </div>

              {/* Dynamic Form Fields Based on Connection Type */}
              {systemIntegration.connectionType === 'local' ? (
                /* Local Network Connection Fields */
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Server URL/IP *
                    </label>
                    <input 
                      value={systemIntegration.serverUrl} 
                      onChange={e => setSystemIntegration({ ...systemIntegration, serverUrl: e.target.value })}
                      placeholder="192.168.1.100 or nvr.company.com"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Port
                    </label>
                    <input 
                      value={systemIntegration.port} 
                      onChange={e => setSystemIntegration({ ...systemIntegration, port: e.target.value })}
                      placeholder="80, 443, 8080"
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Username *
                    </label>
                    <input 
                      type="text"
                      value={systemIntegration.username} 
                      onChange={e => setSystemIntegration({ ...systemIntegration, username: e.target.value })}
                      placeholder="admin"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password *
                    </label>
                    <input 
                      type="password"
                      value={systemIntegration.password} 
                      onChange={e => setSystemIntegration({ ...systemIntegration, password: e.target.value })}
                      placeholder="••••••••"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                </div>
              ) : (
                /* Cloud Service Connection Fields */
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Cloud Account Email *
                    </label>
                    <input 
                      type="email"
                      value={systemIntegration.username} 
                      onChange={e => setSystemIntegration({ ...systemIntegration, username: e.target.value })}
                      placeholder="admin@company.com"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password / API Key *
                    </label>
                    <input 
                      type="password"
                      value={systemIntegration.password} 
                      onChange={e => setSystemIntegration({ ...systemIntegration, password: e.target.value })}
                      placeholder="••••••••"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Cloud Region
                    </label>
                    <select 
                      value={systemIntegration.cloudRegion} 
                      onChange={e => setSystemIntegration({ ...systemIntegration, cloudRegion: e.target.value })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    >
                      <option value="us-east-1">US East (N. Virginia)</option>
                      <option value="us-west-1">US West (N. California)</option>
                      <option value="eu-west-1">EU West (Ireland)</option>
                      <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                      <option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
                      <option value="global">Global / Auto-Select</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Connection Options and Submit */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center space-x-4">
                  {systemIntegration.connectionType === 'local' && (
                    <label className="flex items-center">
                      <input 
                        type="checkbox"
                        checked={systemIntegration.useSSL}
                        onChange={e => setSystemIntegration({ ...systemIntegration, useSSL: e.target.checked })}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">Use SSL/HTTPS</span>
                    </label>
                  )}
                  <label className="flex items-center">
                    <input 
                      type="checkbox"
                      checked={systemIntegration.enabled}
                      onChange={e => setSystemIntegration({ ...systemIntegration, enabled: e.target.checked })}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Enable Integration</span>
                  </label>
                </div>
                
                <div className="flex justify-end">
                  <button 
                    className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400" 
                    type="submit"
                    disabled={loading}
                  >
                    {loading ? 'Connecting...' : `🔗 Connect ${systemIntegration.connectionType === 'cloud' ? 'Cloud' : 'System'}`}
                  </button>
                </div>
              </div>
            </form>
          </div>

          {/* Connected Systems */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Connected Camera Systems</h3>
            </div>
            <div className="p-6">
              {cameraSystems.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-lg mb-2">🔗 No camera systems connected</p>
                  <p>Connect your first surveillance system above to get started.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {cameraSystems.map((system, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <span className="text-2xl mr-2">{getSystemIcon(system.platform)}</span>
                          <h4 className="font-medium capitalize">{system.name || system.platform}</h4>
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          system.status === 'connected' 
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {system.status || 'connected'}
                        </span>
                      </div>
                      <div className="space-y-1 text-sm text-gray-600">
                        <p>Server: {system.server_url}</p>
                        <p>Cameras: {system.camera_count || 0}</p>
                        <p>Connected: {new Date(system.created_at || Date.now()).toLocaleDateString()}</p>
                        <p>Type: {system.connection_type === 'cloud' ? `☁️ Cloud (${system.cloud_region})` : `🏠 ${system.use_ssl ? 'HTTPS' : 'HTTP'}`}</p>
                        {system.connection_type === 'cloud' && (
                          <p>Region: {system.cloud_region}</p>
                        )}
                      </div>
                      <div className="mt-3 flex gap-2">
                        <button 
                          onClick={() => setSelectedSystem(system)}
                          className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded hover:bg-blue-200"
                        >
                          View Cameras
                        </button>
                        <button className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200">
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

      {/* Connected Cameras Tab */}
      {activeTab === 'cameras' && (
        <div className="space-y-6">
          {/* Camera Status Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow border">
              <div className="text-2xl font-bold text-green-600">{connectedCameras.filter(c => c.status === 'online').length}</div>
              <div className="text-sm text-gray-500">Online Cameras</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border">
              <div className="text-2xl font-bold text-blue-600">{connectedCameras.filter(c => c.status === 'recording').length}</div>
              <div className="text-sm text-gray-500">Recording</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border">
              <div className="text-2xl font-bold text-red-600">{connectedCameras.filter(c => c.status === 'offline').length}</div>
              <div className="text-sm text-gray-500">Offline</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border">
              <div className="text-2xl font-bold text-purple-600">{Object.keys(liveStreams).length}</div>
              <div className="text-sm text-gray-500">Live Streams</div>
            </div>
          </div>

          {/* Camera List */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Connected Cameras</h3>
            </div>
            <div className="p-6">
              {connectedCameras.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-lg mb-2">📹 No cameras connected</p>
                  <p>Cameras will appear here once you connect camera systems.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {connectedCameras.map((camera) => (
                    <div key={camera.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium">{camera.name}</h4>
                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(camera.status)}`}>
                          {camera.status}
                        </span>
                      </div>
                      <div className="space-y-1 text-sm text-gray-600 mb-3">
                        <p>Location: {camera.location}</p>
                        <p>System: {camera.system}</p>
                        <p>Resolution: {camera.resolution}</p>
                        <p>Type: {camera.type}</p>
                        <p>IP: {camera.ip_address}</p>
                      </div>
                      <div className="flex gap-2 flex-wrap">
                        <button 
                          onClick={() => startLiveStream(camera.id)}
                          disabled={liveStreams[camera.id]?.status === 'streaming'}
                          className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded hover:bg-blue-200 disabled:bg-gray-200"
                        >
                          📺 Live View
                        </button>
                        <button 
                          onClick={() => takeSnapshot(camera.id)}
                          className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200"
                        >
                          📸 Snapshot
                        </button>
                        {camera.capabilities?.includes('ptz') && (
                          <>
                            <button 
                              onClick={() => controlCamera(camera.id, 'pan', { direction: 'left' })}
                              className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded hover:bg-purple-200"
                            >
                              ← Pan
                            </button>
                            <button 
                              onClick={() => controlCamera(camera.id, 'zoom', { direction: 'in' })}
                              className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded hover:bg-orange-200"
                            >
                              🔍 Zoom
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Live View Tab */}
      {activeTab === 'liveview' && (
        <div className="space-y-6">
          {Object.keys(liveStreams).length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <div className="text-6xl mb-4">📺</div>
              <h3 className="text-xl font-medium mb-2">No Live Streams Active</h3>
              <p className="text-gray-600 mb-4">Start a live stream from the Connected Cameras tab to view it here.</p>
              <button 
                onClick={() => setActiveTab('cameras')}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Go to Cameras
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {Object.entries(liveStreams).map(([cameraId, stream]) => {
                const camera = connectedCameras.find(c => c.id === cameraId);
                return (
                  <div key={cameraId} className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="p-4 border-b border-gray-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{camera?.name || `Camera ${cameraId}`}</h4>
                          <p className="text-sm text-gray-600">{camera?.location}</p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(streamStatus[cameraId] || 'streaming')}`}>
                            {streamStatus[cameraId] || 'streaming'}
                          </span>
                          <button 
                            onClick={() => stopLiveStream(cameraId)}
                            className="text-red-600 hover:text-red-800 text-xs"
                          >
                            ✕ Stop
                          </button>
                        </div>
                      </div>
                    </div>
                    
                    {/* Video Stream */}
                    <div className="relative bg-black aspect-video">
                      {stream.url ? (
                        <img 
                          ref={el => streamRefs.current[cameraId] = el}
                          src={stream.url} 
                          alt={`Live stream from ${camera?.name || cameraId}`}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIyNSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMjI1IiBmaWxsPSIjMzMzIi8+CiAgICA8dGV4dCB4PSIyMDAiIHk9IjExMiIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5TdHJlYW0gVW5hdmFpbGFibGU8L3RleHQ+Cjwvc3ZnPg==';
                          }}
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <div className="text-center text-white">
                            <div className="text-4xl mb-2">📡</div>
                            <p>Loading stream...</p>
                          </div>
                        </div>
                      )}
                      
                      {/* Stream Controls Overlay */}
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                        <div className="flex items-center justify-between">
                          <div className="text-white text-sm">
                            <div className="flex items-center">
                              <div className="w-2 h-2 bg-red-500 rounded-full mr-2 animate-pulse"></div>
                              LIVE
                            </div>
                            <div className="text-xs opacity-75">
                              Started: {new Date(stream.startTime).toLocaleTimeString()}
                            </div>
                          </div>
                          <div className="flex space-x-2">
                            <button 
                              onClick={() => takeSnapshot(cameraId)}
                              className="bg-white/20 hover:bg-white/30 text-white px-2 py-1 rounded text-xs"
                            >
                              📸
                            </button>
                            {camera?.capabilities?.includes('ptz') && (
                              <>
                                <button 
                                  onClick={() => controlCamera(cameraId, 'pan', { direction: 'left' })}
                                  className="bg-white/20 hover:bg-white/30 text-white px-2 py-1 rounded text-xs"
                                >
                                  ←
                                </button>
                                <button 
                                  onClick={() => controlCamera(cameraId, 'pan', { direction: 'right' })}
                                  className="bg-white/20 hover:bg-white/30 text-white px-2 py-1 rounded text-xs"
                                >
                                  →
                                </button>
                                <button 
                                  onClick={() => controlCamera(cameraId, 'zoom', { direction: 'in' })}
                                  className="bg-white/20 hover:bg-white/30 text-white px-2 py-1 rounded text-xs"
                                >
                                  🔍+
                                </button>
                                <button 
                                  onClick={() => controlCamera(cameraId, 'zoom', { direction: 'out' })}
                                  className="bg-white/20 hover:bg-white/30 text-white px-2 py-1 rounded text-xs"
                                >
                                  🔍-
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Recordings Tab */}
      {activeTab === 'recordings' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center py-8">
            <div className="text-6xl mb-4">📼</div>
            <h3 className="text-xl font-medium mb-2">Recording Management</h3>
            <p className="text-gray-600 mb-4">
              Recording features will be available here including playback, download, and archive management.
            </p>
            <div className="text-sm text-gray-500">
              Coming soon: Timeline playback, motion detection clips, and cloud storage integration.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraManagement;