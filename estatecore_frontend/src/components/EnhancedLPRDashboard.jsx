import React, { useState, useEffect } from 'react';

const EnhancedLPRDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [cameras, setCameras] = useState([]);
  const [detections, setDetections] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(true);
  const [showAddCamera, setShowAddCamera] = useState(false);
  const [showAddVehicle, setShowAddVehicle] = useState(false);
  const [searchFilters, setSearchFilters] = useState({
    hours: 24,
    license_plate: '',
    camera_id: '',
    property_id: ''
  });
  const [newCamera, setNewCamera] = useState({
    name: '',
    location: '',
    camera_type: 'entrance',
    rtsp_url: '',
    property_id: 1,
    provider: 'mock',
    confidence_threshold: 0.8
  });
  const [newVehicle, setNewVehicle] = useState({
    license_plate: '',
    owner_name: '',
    tenant_id: '',
    property_id: 1,
    status: 'authorized',
    valid_from: new Date().toISOString().split('T')[0],
    valid_until: '',
    notes: ''
  });

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchDetectionsAndAlerts, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchCameras(),
        fetchVehicles(),
        fetchDetections(),
        fetchStatistics(),
        fetchAlerts()
      ]);
    } catch (error) {
      console.error('Error fetching LPR data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCameras = async () => {
    try {
      const response = await fetch('/api/lpr/cameras');
      if (response.ok) {
        const data = await response.json();
        setCameras(data.cameras || []);
      }
    } catch (error) {
      console.error('Error fetching cameras:', error);
    }
  };

  const fetchVehicles = async () => {
    try {
      const response = await fetch('/api/lpr/vehicles');
      if (response.ok) {
        const data = await response.json();
        setVehicles(data.vehicles || []);
      }
    } catch (error) {
      console.error('Error fetching vehicles:', error);
    }
  };

  const fetchDetections = async () => {
    try {
      const params = new URLSearchParams();
      if (searchFilters.hours) params.append('hours', searchFilters.hours);
      if (searchFilters.license_plate) params.append('license_plate', searchFilters.license_plate);
      if (searchFilters.camera_id) params.append('camera_id', searchFilters.camera_id);
      if (searchFilters.property_id) params.append('property_id', searchFilters.property_id);

      const response = await fetch(`/api/lpr/detections?${params}`);
      if (response.ok) {
        const data = await response.json();
        setDetections(data.detections || []);
      }
    } catch (error) {
      console.error('Error fetching detections:', error);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/lpr/statistics');
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/lpr/alerts?hours=24');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const fetchDetectionsAndAlerts = async () => {
    await Promise.all([fetchDetections(), fetchAlerts(), fetchStatistics()]);
  };

  const handleAddCamera = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/lpr/cameras', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newCamera)
      });

      if (response.ok) {
        const data = await response.json();
        alert('Camera added successfully!');
        setShowAddCamera(false);
        setNewCamera({
          name: '',
          location: '',
          camera_type: 'entrance',
          rtsp_url: '',
          property_id: 1,
          provider: 'mock',
          confidence_threshold: 0.8
        });
        fetchCameras();
      } else {
        alert('Failed to add camera');
      }
    } catch (error) {
      console.error('Error adding camera:', error);
      alert('Failed to add camera');
    }
  };

  const handleAddVehicle = async (e) => {
    e.preventDefault();
    try {
      const vehicleData = {
        ...newVehicle,
        tenant_id: newVehicle.tenant_id ? parseInt(newVehicle.tenant_id) : null,
        valid_from: new Date(newVehicle.valid_from).toISOString(),
        valid_until: newVehicle.valid_until ? new Date(newVehicle.valid_until).toISOString() : null
      };

      const response = await fetch('/api/lpr/vehicles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(vehicleData)
      });

      if (response.ok) {
        alert('Vehicle record added successfully!');
        setShowAddVehicle(false);
        setNewVehicle({
          license_plate: '',
          owner_name: '',
          tenant_id: '',
          property_id: 1,
          status: 'authorized',
          valid_from: new Date().toISOString().split('T')[0],
          valid_until: '',
          notes: ''
        });
        fetchVehicles();
      } else {
        alert('Failed to add vehicle record');
      }
    } catch (error) {
      console.error('Error adding vehicle:', error);
      alert('Failed to add vehicle record');
    }
  };

  const startAllCameras = async () => {
    try {
      const response = await fetch('/api/lpr/cameras/start-all', {
        method: 'POST'
      });

      if (response.ok) {
        alert('All cameras started successfully!');
        fetchCameras();
      } else {
        alert('Failed to start cameras');
      }
    } catch (error) {
      console.error('Error starting cameras:', error);
      alert('Failed to start cameras');
    }
  };

  const stopAllCameras = async () => {
    try {
      const response = await fetch('/api/lpr/cameras/stop-all', {
        method: 'POST'
      });

      if (response.ok) {
        alert('All cameras stopped successfully!');
        fetchCameras();
      } else {
        alert('Failed to stop cameras');
      }
    } catch (error) {
      console.error('Error stopping cameras:', error);
      alert('Failed to stop cameras');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'authorized': return 'bg-green-100 text-green-800';
      case 'visitor': return 'bg-blue-100 text-blue-800';
      case 'blacklisted': return 'bg-red-100 text-red-800';
      case 'unknown': return 'bg-gray-100 text-gray-800';
      case 'expired': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'allow': return 'bg-green-100 text-green-800';
      case 'deny': return 'bg-red-100 text-red-800';
      case 'alert': return 'bg-yellow-100 text-yellow-800';
      case 'log_only': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Enhanced LPR System</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddCamera(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            📷 Add Camera
          </button>
          <button
            onClick={() => setShowAddVehicle(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
          >
            🚗 Add Vehicle
          </button>
          <button
            onClick={startAllCameras}
            className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700"
          >
            ▶️ Start All
          </button>
          <button
            onClick={stopAllCameras}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
          >
            ⏹️ Stop All
          </button>
          <button
            onClick={fetchAllData}
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
            { id: 'cameras', label: 'Cameras', icon: '📷' },
            { id: 'detections', label: 'Detections', icon: '🔍' },
            { id: 'vehicles', label: 'Vehicles', icon: '🚗' },
            { id: 'alerts', label: 'Alerts', icon: '🚨' }
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
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Total Cameras</h3>
              <p className="text-2xl font-bold text-blue-600">
                {statistics.total_cameras || 0}
              </p>
              <p className="text-xs text-gray-500">
                {statistics.active_cameras || 0} active
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Total Detections</h3>
              <p className="text-2xl font-bold text-green-600">
                {statistics.total_detections || 0}
              </p>
              <p className="text-xs text-gray-500">All time</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Authorized Vehicles</h3>
              <p className="text-2xl font-bold text-green-600">
                {statistics.authorized_vehicles || 0}
              </p>
              <p className="text-xs text-gray-500">
                {statistics.authorized_vehicles_count || 0} registered
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Security Alerts</h3>
              <p className="text-2xl font-bold text-red-600">
                {statistics.alerts_generated || 0}
              </p>
              <p className="text-xs text-gray-500">
                {alerts.length} in 24h
              </p>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Recent Detections</h3>
              </div>
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {detections.slice(0, 10).map((detection, index) => (
                  <div key={index} className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium text-gray-900">{detection.license_plate}</div>
                        <div className="text-sm text-gray-500">{detection.metadata?.camera_name}</div>
                        <div className="text-xs text-gray-400">
                          {new Date(detection.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-1">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(detection.vehicle_status)}`}>
                          {detection.vehicle_status}
                        </span>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionColor(detection.access_action)}`}>
                          {detection.access_action}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Security Alerts</h3>
              </div>
              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {alerts.slice(0, 10).map((alert, index) => (
                  <div key={index} className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium text-red-600">{alert.license_plate}</div>
                        <div className="text-sm text-gray-500">{alert.metadata?.camera_name}</div>
                        <div className="text-xs text-gray-400">
                          {new Date(alert.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(alert.vehicle_status)}`}>
                          {alert.vehicle_status}
                        </span>
                        <div className="text-xs text-gray-500 mt-1">
                          {(alert.confidence * 100).toFixed(1)}% confidence
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cameras Tab */}
      {activeTab === 'cameras' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Camera Management</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Camera</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Detections</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Detection</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {cameras.map((camera) => (
                  <tr key={camera.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{camera.name}</div>
                        <div className="text-sm text-gray-500">{camera.location}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {camera.camera_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        camera.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {camera.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {camera.total_detections}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {camera.last_detection ? new Date(camera.last_detection).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex gap-2">
                        <button className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                          Configure
                        </button>
                        <button className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                          Start
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detections Tab */}
      {activeTab === 'detections' && (
        <div className="space-y-4">
          {/* Search Filters */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Search Filters</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Time Range (hours)</label>
                <select
                  value={searchFilters.hours}
                  onChange={(e) => setSearchFilters({...searchFilters, hours: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="1">Last Hour</option>
                  <option value="24">Last 24 Hours</option>
                  <option value="168">Last Week</option>
                  <option value="720">Last Month</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">License Plate</label>
                <input
                  type="text"
                  value={searchFilters.license_plate}
                  onChange={(e) => setSearchFilters({...searchFilters, license_plate: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  placeholder="Enter license plate..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Camera</label>
                <select
                  value={searchFilters.camera_id}
                  onChange={(e) => setSearchFilters({...searchFilters, camera_id: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="">All Cameras</option>
                  {cameras.map(camera => (
                    <option key={camera.id} value={camera.id}>{camera.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={fetchDetections}
                  className="w-full bg-blue-600 text-white p-2 rounded-md hover:bg-blue-700"
                >
                  🔍 Search
                </button>
              </div>
            </div>
          </div>

          {/* Detections Table */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Detection History ({detections.length})</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">License Plate</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Camera</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {detections.map((detection, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{detection.license_plate}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{detection.metadata?.camera_name || detection.camera_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{new Date(detection.timestamp).toLocaleString()}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(detection.vehicle_status)}`}>
                          {detection.vehicle_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionColor(detection.access_action)}`}>
                          {detection.access_action}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {(detection.confidence * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Vehicles Tab */}
      {activeTab === 'vehicles' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Vehicle Records ({vehicles.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">License Plate</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Valid Until</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Property</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Notes</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {vehicles.map((vehicle, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{vehicle.license_plate}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{vehicle.owner_name || 'N/A'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(vehicle.status)}`}>
                        {vehicle.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {vehicle.valid_until ? new Date(vehicle.valid_until).toLocaleDateString() : 'Permanent'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      Property {vehicle.property_id}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {vehicle.notes || 'No notes'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Security Alerts ({alerts.length})</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {alerts.map((alert, index) => (
              <div key={index} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                        <span className="text-red-600 font-bold">🚨</span>
                      </div>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-lg font-medium text-gray-900">{alert.license_plate}</h4>
                      <p className="text-sm text-gray-500">
                        Detected by {alert.metadata?.camera_name || alert.camera_id}
                      </p>
                      <p className="text-sm text-gray-500">
                        {new Date(alert.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end space-y-2">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(alert.vehicle_status)}`}>
                      {alert.vehicle_status}
                    </span>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionColor(alert.access_action)}`}>
                      {alert.access_action}
                    </span>
                    <div className="text-xs text-gray-500">
                      {(alert.confidence * 100).toFixed(1)}% confidence
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Camera Modal */}
      {showAddCamera && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Add New Camera</h3>
            </div>
            <form onSubmit={handleAddCamera} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Camera Name</label>
                <input
                  type="text"
                  value={newCamera.name}
                  onChange={(e) => setNewCamera({...newCamera, name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={newCamera.location}
                  onChange={(e) => setNewCamera({...newCamera, location: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Camera Type</label>
                <select
                  value={newCamera.camera_type}
                  onChange={(e) => setNewCamera({...newCamera, camera_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="entrance">Entrance</option>
                  <option value="exit">Exit</option>
                  <option value="parking">Parking</option>
                  <option value="perimeter">Perimeter</option>
                  <option value="general">General</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">RTSP URL</label>
                <input
                  type="text"
                  value={newCamera.rtsp_url}
                  onChange={(e) => setNewCamera({...newCamera, rtsp_url: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  placeholder="rtsp://192.168.1.100:554/stream"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Property ID</label>
                <input
                  type="number"
                  value={newCamera.property_id}
                  onChange={(e) => setNewCamera({...newCamera, property_id: parseInt(e.target.value)})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Add Camera
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddCamera(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Vehicle Modal */}
      {showAddVehicle && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Add Vehicle Record</h3>
            </div>
            <form onSubmit={handleAddVehicle} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">License Plate</label>
                <input
                  type="text"
                  value={newVehicle.license_plate}
                  onChange={(e) => setNewVehicle({...newVehicle, license_plate: e.target.value.toUpperCase()})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  placeholder="ABC123"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Owner Name</label>
                <input
                  type="text"
                  value={newVehicle.owner_name}
                  onChange={(e) => setNewVehicle({...newVehicle, owner_name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={newVehicle.status}
                  onChange={(e) => setNewVehicle({...newVehicle, status: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="authorized">Authorized</option>
                  <option value="visitor">Visitor</option>
                  <option value="blacklisted">Blacklisted</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Valid From</label>
                <input
                  type="date"
                  value={newVehicle.valid_from}
                  onChange={(e) => setNewVehicle({...newVehicle, valid_from: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Valid Until (Optional)</label>
                <input
                  type="date"
                  value={newVehicle.valid_until}
                  onChange={(e) => setNewVehicle({...newVehicle, valid_until: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={newVehicle.notes}
                  onChange={(e) => setNewVehicle({...newVehicle, notes: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  rows="3"
                />
              </div>
              
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
                >
                  Add Vehicle
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddVehicle(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedLPRDashboard;