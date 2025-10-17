import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import api from '../api';

const LiveCameraAnalysis = () => {
  const [cameraData, setCameraData] = useState({
    availableCameras: [],
    activeCameras: [],
    selectedProperty: null,
    loading: false
  });

  const [analysisResults, setAnalysisResults] = useState({});
  const [streamStats, setStreamStats] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [showAddCameraModal, setShowAddCameraModal] = useState(false);
  const [faultDetection, setFaultDetection] = useState({
    enabled: true,
    detectedFaults: [],
    lastChecked: null
  });
  const [newCameraForm, setNewCameraForm] = useState({
    name: '',
    ip_address: '',
    port: '8080',
    username: '',
    password: '',
    camera_type: 'ip_camera',
    quality: 'medium'
  });

  const videoRefs = useRef({});

  useEffect(() => {
    loadAvailableCameras();
    loadActiveCameras();
    
    // Set up periodic updates
    const interval = setInterval(() => {
      updateCameraStatuses();
      updateAnalysisResults();
      if (faultDetection.enabled) {
        performFaultDetection();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const loadAvailableCameras = async () => {
    try {
      setCameraData(prev => ({ ...prev, loading: true }));
      
      const response = await api.get('/api/camera/available');
      
      if (response.success) {
        setCameraData(prev => ({
          ...prev,
          availableCameras: response.cameras,
          loading: false
        }));
      } else {
        console.error('Failed to load cameras:', response.error);
        setCameraData(prev => ({ ...prev, loading: false }));
      }
    } catch (error) {
      console.error('Error loading cameras:', error);
      setCameraData(prev => ({ ...prev, loading: false }));
    }
  };

  const loadActiveCameras = () => {
    // This would typically load from a saved configuration
    const savedCameras = JSON.parse(localStorage.getItem('activeCameras') || '[]');
    setCameraData(prev => ({ ...prev, activeCameras: savedCameras }));
  };

  const addCamera = async (camera, propertyId) => {
    try {
      const response = await api.post('/api/camera/add', {
        camera_id: `camera_${camera.id}`,
        source: camera.source,
        property_id: propertyId,
        camera_type: camera.type,
        quality: 'medium'
      });
      
      if (response.success) {
        const newActiveCamera = {
          ...camera,
          camera_id: `camera_${camera.id}`,
          property_id: propertyId,
          status: 'added',
          analysis_active: false
        };
        
        setCameraData(prev => ({
          ...prev,
          activeCameras: [...prev.activeCameras, newActiveCamera]
        }));
        
        // Save to localStorage
        const updatedCameras = [...cameraData.activeCameras, newActiveCamera];
        localStorage.setItem('activeCameras', JSON.stringify(updatedCameras));
        
        addAlert('success', `Camera ${camera.id} added successfully`);
      } else {
        addAlert('error', `Failed to add camera: ${response.error}`);
      }
    } catch (error) {
      console.error('Error adding camera:', error);
      addAlert('error', 'Failed to add camera');
    }
  };

  const startCameraAnalysis = async (cameraId, analysisMode = 'interval') => {
    try {
      const response = await api.post(`/api/camera/${cameraId}/start`, {
        analysis_mode: analysisMode
      });
      
      if (response.success) {
        setCameraData(prev => ({
          ...prev,
          activeCameras: prev.activeCameras.map(camera => 
            camera.camera_id === cameraId 
              ? { ...camera, analysis_active: true, status: 'analyzing' }
              : camera
          )
        }));
        
        addAlert('success', `Live analysis started for ${cameraId}`);
      } else {
        addAlert('error', `Failed to start analysis: ${response.error}`);
      }
    } catch (error) {
      console.error('Error starting analysis:', error);
      addAlert('error', 'Failed to start camera analysis');
    }
  };

  const stopCameraAnalysis = async (cameraId) => {
    try {
      const response = await api.post(`/api/camera/${cameraId}/stop`);
      
      if (response.success) {
        setCameraData(prev => ({
          ...prev,
          activeCameras: prev.activeCameras.map(camera => 
            camera.camera_id === cameraId 
              ? { ...camera, analysis_active: false, status: 'inactive' }
              : camera
          )
        }));
        
        addAlert('success', `Analysis stopped for ${cameraId}`);
      } else {
        addAlert('error', `Failed to stop analysis: ${response.error}`);
      }
    } catch (error) {
      console.error('Error stopping analysis:', error);
      addAlert('error', 'Failed to stop camera analysis');
    }
  };

  const captureAndAnalyze = async (cameraId, propertyId) => {
    try {
      const response = await api.post(`/api/camera/${cameraId}/capture`, {
        property_id: propertyId,
        description: 'Manual capture from live camera interface'
      });
      
      if (response.success) {
        setAnalysisResults(prev => ({
          ...prev,
          [cameraId]: response.analysis
        }));
        
        addAlert('success', `Frame captured and analyzed for ${cameraId}`);
      } else {
        addAlert('error', `Failed to capture frame: ${response.error}`);
      }
    } catch (error) {
      console.error('Error capturing frame:', error);
      addAlert('error', 'Failed to capture and analyze frame');
    }
  };

  const removeCamera = async (cameraId) => {
    try {
      const response = await api.delete(`/api/camera/${cameraId}/remove`);
      
      if (response.success) {
        setCameraData(prev => ({
          ...prev,
          activeCameras: prev.activeCameras.filter(camera => camera.camera_id !== cameraId)
        }));
        
        // Update localStorage
        const updatedCameras = cameraData.activeCameras.filter(camera => camera.camera_id !== cameraId);
        localStorage.setItem('activeCameras', JSON.stringify(updatedCameras));
        
        // Clear analysis results for this camera
        setAnalysisResults(prev => {
          const { [cameraId]: removed, ...rest } = prev;
          return rest;
        });
        
        addAlert('success', `Camera ${cameraId} removed`);
      } else {
        addAlert('error', `Failed to remove camera: ${response.error}`);
      }
    } catch (error) {
      console.error('Error removing camera:', error);
      addAlert('error', 'Failed to remove camera');
    }
  };

  const updateCameraStatuses = async () => {
    // Update status for each active camera
    for (const camera of cameraData.activeCameras) {
      try {
        const response = await api.get(`/api/camera/${camera.camera_id}/status`);
        
        if (response.success) {
          setStreamStats(prev => ({
            ...prev,
            [camera.camera_id]: response.stream_data
          }));
        }
      } catch (error) {
        console.error(`Error updating status for ${camera.camera_id}:`, error);
      }
    }
  };

  const updateAnalysisResults = () => {
    // This function would be called by the periodic update
    // In a real implementation, you might use WebSockets for real-time updates
  };

  const performFaultDetection = async () => {
    try {
      const faults = [];
      
      // Check each active camera for faults
      for (const camera of cameraData.activeCameras) {
        const response = await api.post('/api/camera/fault-detection', {
          camera_id: camera.camera_id,
          property_id: camera.property_id
        });
        
        if (response.success && response.faults && response.faults.length > 0) {
          faults.push(...response.faults.map(fault => ({
            ...fault,
            camera_id: camera.camera_id,
            camera_name: camera.name || camera.camera_id,
            detected_at: new Date(),
            severity: fault.severity || 'medium'
          })));
        }
      }
      
      // Update fault detection state
      setFaultDetection(prev => ({
        ...prev,
        detectedFaults: faults,
        lastChecked: new Date()
      }));
      
      // Create alerts for new high-severity faults
      const highSeverityFaults = faults.filter(fault => fault.severity === 'high');
      highSeverityFaults.forEach(fault => {
        addAlert('error', `🚨 Critical fault detected: ${fault.description} on ${fault.camera_name}`);
      });
      
    } catch (error) {
      console.error('Error performing fault detection:', error);
    }
  };

  const toggleFaultDetection = () => {
    setFaultDetection(prev => ({
      ...prev,
      enabled: !prev.enabled
    }));
  };

  const addCustomCamera = async () => {
    if (!newCameraForm.name || !newCameraForm.ip_address || !cameraData.selectedProperty) {
      addAlert('error', 'Please fill in camera name, IP address, and select a property');
      return;
    }

    try {
      const customCamera = {
        id: `custom_${Date.now()}`,
        name: newCameraForm.name,
        type: newCameraForm.camera_type,
        source: `http://${newCameraForm.ip_address}:${newCameraForm.port}`,
        resolution: [1920, 1080],
        fps: 30,
        status: 'available',
        ip_address: newCameraForm.ip_address,
        port: newCameraForm.port,
        credentials: {
          username: newCameraForm.username,
          password: newCameraForm.password
        }
      };

      await addCamera(customCamera, cameraData.selectedProperty);
      setShowAddCameraModal(false);
      setNewCameraForm({
        name: '',
        ip_address: '',
        port: '8080',
        username: '',
        password: '',
        camera_type: 'ip_camera',
        quality: 'medium'
      });
    } catch (error) {
      addAlert('error', 'Failed to add custom camera');
    }
  };

  const addAlert = (type, message) => {
    const alert = {
      id: Date.now(),
      type,
      message,
      timestamp: new Date()
    };
    
    setAlerts(prev => [alert, ...prev.slice(0, 9)]); // Keep last 10 alerts
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setAlerts(prev => prev.filter(a => a.id !== alert.id));
    }, 5000);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'analyzing': return 'text-green-600 bg-green-100';
      case 'added': return 'text-blue-600 bg-blue-100';
      case 'inactive': return 'text-gray-600 bg-gray-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (cameraData.loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="h-96 bg-gray-200 rounded"></div>
            <div className="h-96 bg-gray-200 rounded"></div>
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
          <h1 className="text-3xl font-bold text-gray-900">Live Camera Analysis</h1>
          <p className="text-gray-600">Real-time property analysis using computer vision</p>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={loadAvailableCameras}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            📹 Detect Cameras
          </button>
          <button 
            onClick={() => setShowAddCameraModal(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            ➕ Add Camera
          </button>
          <button 
            onClick={toggleFaultDetection}
            className={`px-4 py-2 rounded-md ${
              faultDetection.enabled 
                ? 'bg-red-600 text-white hover:bg-red-700' 
                : 'bg-gray-600 text-white hover:bg-gray-700'
            }`}
          >
            {faultDetection.enabled ? '🚨 Fault Detection ON' : '⚠️ Fault Detection OFF'}
          </button>
          <select 
            value={cameraData.selectedProperty || ''}
            onChange={(e) => setCameraData(prev => ({ ...prev, selectedProperty: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">Select Property</option>
            <option value="1">Sunset Apartments</option>
            <option value="2">Oak Ridge Complex</option>
            <option value="3">Green Valley Homes</option>
          </select>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.slice(0, 3).map(alert => (
            <div
              key={alert.id}
              className={`p-3 rounded-md ${
                alert.type === 'success' 
                  ? 'bg-green-100 text-green-800 border border-green-200'
                  : 'bg-red-100 text-red-800 border border-red-200'
              }`}
            >
              <div className="flex justify-between items-start">
                <p className="text-sm">{alert.message}</p>
                <span className="text-xs">{formatTimestamp(alert.timestamp)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Fault Detection Status */}
      {faultDetection.enabled && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center">
                🚨 Real-Time Fault Detection 
                <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                  faultDetection.detectedFaults.length > 0 
                    ? 'bg-red-100 text-red-800' 
                    : 'bg-green-100 text-green-800'
                }`}>
                  {faultDetection.detectedFaults.length === 0 
                    ? 'All Clear' 
                    : `${faultDetection.detectedFaults.length} Fault${faultDetection.detectedFaults.length > 1 ? 's' : ''}`
                  }
                </span>
              </CardTitle>
              {faultDetection.lastChecked && (
                <span className="text-sm text-gray-500">
                  Last checked: {formatTimestamp(faultDetection.lastChecked)}
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {faultDetection.detectedFaults.length === 0 ? (
              <div className="text-center py-4">
                <div className="text-2xl mb-2">✅</div>
                <p className="text-gray-600">No faults detected across all active cameras</p>
              </div>
            ) : (
              <div className="space-y-3">
                {faultDetection.detectedFaults.map((fault, index) => (
                  <div key={index} className={`p-3 rounded-lg border ${
                    fault.severity === 'high' 
                      ? 'bg-red-50 border-red-200' 
                      : fault.severity === 'medium' 
                        ? 'bg-yellow-50 border-yellow-200' 
                        : 'bg-blue-50 border-blue-200'
                  }`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            fault.severity === 'high' 
                              ? 'bg-red-100 text-red-800' 
                              : fault.severity === 'medium' 
                                ? 'bg-yellow-100 text-yellow-800' 
                                : 'bg-blue-100 text-blue-800'
                          }`}>
                            {fault.severity.toUpperCase()}
                          </span>
                          <span className="font-medium">{fault.camera_name}</span>
                        </div>
                        <p className="text-sm text-gray-700 mt-1">{fault.description}</p>
                        {fault.recommendation && (
                          <p className="text-xs text-gray-600 mt-1">
                            <strong>Recommendation:</strong> {fault.recommendation}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(fault.detected_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Available Cameras */}
      <Card>
        <CardHeader>
          <CardTitle>Available Cameras ({cameraData.availableCameras.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {cameraData.availableCameras.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No cameras detected. Make sure cameras are connected and click "Detect Cameras".</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {cameraData.availableCameras.map((camera, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold">{camera.id}</h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(camera.status)}`}>
                      {camera.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>Type: {camera.type}</p>
                    <p>Resolution: {camera.resolution[0]}x{camera.resolution[1]}</p>
                    <p>FPS: {camera.fps}</p>
                  </div>
                  <button
                    onClick={() => addCamera(camera, 1)} // Default property ID
                    className="mt-3 w-full px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700"
                    disabled={cameraData.activeCameras.some(ac => ac.id === camera.id)}
                  >
                    {cameraData.activeCameras.some(ac => ac.id === camera.id) ? 'Already Added' : 'Add Camera'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Active Cameras */}
      <Card>
        <CardHeader>
          <CardTitle>Active Cameras ({cameraData.activeCameras.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {cameraData.activeCameras.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No active cameras. Add cameras from the available list above.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {cameraData.activeCameras.map((camera) => (
                <div key={camera.camera_id} className="border rounded-lg p-4">
                  {/* Camera Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold">{camera.camera_id}</h3>
                      <p className="text-sm text-gray-600">Property {camera.property_id}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(camera.status)}`}>
                        {camera.status}
                      </span>
                      <button
                        onClick={() => removeCamera(camera.camera_id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        ✕
                      </button>
                    </div>
                  </div>

                  {/* Camera Controls */}
                  <div className="flex space-x-2 mb-4">
                    {!camera.analysis_active ? (
                      <button
                        onClick={() => startCameraAnalysis(camera.camera_id)}
                        className="px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700"
                      >
                        Start Analysis
                      </button>
                    ) : (
                      <button
                        onClick={() => stopCameraAnalysis(camera.camera_id)}
                        className="px-3 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700"
                      >
                        Stop Analysis
                      </button>
                    )}
                    
                    <button
                      onClick={() => captureAndAnalyze(camera.camera_id, camera.property_id)}
                      className="px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                    >
                      📸 Capture & Analyze
                    </button>
                  </div>

                  {/* Stream Statistics */}
                  {streamStats[camera.camera_id] && (
                    <div className="bg-gray-50 rounded-lg p-3 mb-4">
                      <h4 className="font-medium text-sm mb-2">Stream Statistics</h4>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>FPS: {streamStats[camera.camera_id].stats?.average_fps?.toFixed(1) || 'N/A'}</div>
                        <div>Frames: {streamStats[camera.camera_id].stats?.total_frames_processed || 0}</div>
                        <div>Analyses: {streamStats[camera.camera_id].stats?.analysis_count || 0}</div>
                        <div>Detections: {streamStats[camera.camera_id].stats?.total_detections || 0}</div>
                      </div>
                    </div>
                  )}

                  {/* Latest Analysis */}
                  {analysisResults[camera.camera_id] && (
                    <div className="bg-blue-50 rounded-lg p-3">
                      <h4 className="font-medium text-sm mb-2">Latest Analysis</h4>
                      <div className="text-xs space-y-1">
                        <div className="flex justify-between">
                          <span>Confidence:</span>
                          <span className="font-medium">{(analysisResults[camera.camera_id].confidence_score * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Image Quality:</span>
                          <span className="font-medium">{analysisResults[camera.camera_id].image_quality_score?.toFixed(1) || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Objects Detected:</span>
                          <span className="font-medium">{analysisResults[camera.camera_id].objects_count || 0}</span>
                        </div>
                        {analysisResults[camera.camera_id].property_condition && (
                          <div className="flex justify-between">
                            <span>Property Condition:</span>
                            <span className="font-medium capitalize">{analysisResults[camera.camera_id].property_condition}</span>
                          </div>
                        )}
                        {analysisResults[camera.camera_id].damage_score && (
                          <div className="flex justify-between">
                            <span>Damage Score:</span>
                            <span className="font-medium">{analysisResults[camera.camera_id].damage_score.toFixed(1)}/100</span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span>Analysis Time:</span>
                          <span className="font-medium">{analysisResults[camera.camera_id].analysis_time?.toFixed(2) || 'N/A'}s</span>
                        </div>
                        <div className="text-xs text-gray-500 mt-2">
                          {new Date(analysisResults[camera.camera_id].timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Motion Detection Indicator */}
                  {streamStats[camera.camera_id]?.stats?.motion_events > 0 && (
                    <div className="mt-2 flex items-center text-xs">
                      <div className="w-2 h-2 bg-orange-500 rounded-full mr-2 animate-pulse"></div>
                      <span>Motion detected ({streamStats[camera.camera_id].stats.motion_events} events)</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analysis Summary */}
      {Object.keys(analysisResults).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {Object.keys(analysisResults).length}
                </div>
                <div className="text-sm text-gray-600">Cameras with Analysis</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {Object.values(analysisResults).reduce((sum, result) => sum + (result.objects_count || 0), 0)}
                </div>
                <div className="text-sm text-gray-600">Total Objects Detected</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {(Object.values(analysisResults).reduce((sum, result) => sum + (result.confidence_score || 0), 0) / Object.values(analysisResults).length * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Average Confidence</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {(Object.values(analysisResults).reduce((sum, result) => sum + (result.image_quality_score || 0), 0) / Object.values(analysisResults).length).toFixed(1)}
                </div>
                <div className="text-sm text-gray-600">Average Image Quality</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Live Camera Analysis Tips</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-medium mb-2">🎯 Best Practices:</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Ensure good lighting for optimal analysis</li>
                <li>• Position cameras to capture key property areas</li>
                <li>• Use interval mode to balance accuracy and performance</li>
                <li>• Regular manual captures for detailed analysis</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">⚙️ Analysis Modes:</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• <strong>Interval:</strong> Analyze every 2 seconds (recommended)</li>
                <li>• <strong>Continuous:</strong> Analyze every frame (resource intensive)</li>
                <li>• <strong>Motion Trigger:</strong> Analyze only when motion detected</li>
                <li>• <strong>Manual:</strong> Analyze only on button press</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">🚨 Fault Detection:</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• <strong>Real-time:</strong> Checks every 5 seconds automatically</li>
                <li>• <strong>Camera offline:</strong> Detects disconnected cameras</li>
                <li>• <strong>Poor image quality:</strong> Identifies blurry or dark feeds</li>
                <li>• <strong>Motion anomalies:</strong> Unusual movement patterns</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Add Camera Modal */}
      {showAddCameraModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setShowAddCameraModal(false)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Add New Camera</h3>
                  <button
                    onClick={() => setShowAddCameraModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Camera Name</label>
                  <input
                    type="text"
                    value={newCameraForm.name}
                    onChange={(e) => setNewCameraForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Front Entrance Camera"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">IP Address</label>
                  <input
                    type="text"
                    value={newCameraForm.ip_address}
                    onChange={(e) => setNewCameraForm(prev => ({ ...prev, ip_address: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="192.168.1.100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                  <input
                    type="text"
                    value={newCameraForm.port}
                    onChange={(e) => setNewCameraForm(prev => ({ ...prev, port: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="8080"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                    <input
                      type="text"
                      value={newCameraForm.username}
                      onChange={(e) => setNewCameraForm(prev => ({ ...prev, username: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="admin"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input
                      type="password"
                      value={newCameraForm.password}
                      onChange={(e) => setNewCameraForm(prev => ({ ...prev, password: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Camera Type</label>
                  <select
                    value={newCameraForm.camera_type}
                    onChange={(e) => setNewCameraForm(prev => ({ ...prev, camera_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="ip_camera">IP Camera</option>
                    <option value="webcam">Webcam</option>
                    <option value="security_camera">Security Camera</option>
                    <option value="ptz_camera">PTZ Camera</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Quality</label>
                  <select
                    value={newCameraForm.quality}
                    onChange={(e) => setNewCameraForm(prev => ({ ...prev, quality: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Low (480p)</option>
                    <option value="medium">Medium (720p)</option>
                    <option value="high">High (1080p)</option>
                    <option value="ultra">Ultra (4K)</option>
                  </select>
                </div>

                {!cameraData.selectedProperty && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p className="text-sm text-yellow-800">Please select a property first</p>
                  </div>
                )}
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => setShowAddCameraModal(false)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={addCustomCamera}
                  disabled={!newCameraForm.name || !newCameraForm.ip_address || !cameraData.selectedProperty}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Add Camera
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveCameraAnalysis;