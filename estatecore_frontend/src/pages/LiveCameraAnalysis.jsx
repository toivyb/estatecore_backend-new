import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

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

  const videoRefs = useRef({});

  useEffect(() => {
    loadAvailableCameras();
    loadActiveCameras();
    
    // Set up periodic updates
    const interval = setInterval(() => {
      updateCameraStatuses();
      updateAnalysisResults();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const loadAvailableCameras = async () => {
    try {
      setCameraData(prev => ({ ...prev, loading: true }));
      
      const response = await fetch('/api/camera/available');
      const data = await response.json();
      
      if (data.success) {
        setCameraData(prev => ({
          ...prev,
          availableCameras: data.cameras,
          loading: false
        }));
      } else {
        console.error('Failed to load cameras:', data.error);
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
      const response = await fetch('/api/camera/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          camera_id: `camera_${camera.id}`,
          source: camera.source,
          property_id: propertyId,
          camera_type: camera.type,
          quality: 'medium'
        })
      });

      const data = await response.json();
      
      if (data.success) {
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
        addAlert('error', `Failed to add camera: ${data.error}`);
      }
    } catch (error) {
      console.error('Error adding camera:', error);
      addAlert('error', 'Failed to add camera');
    }
  };

  const startCameraAnalysis = async (cameraId, analysisMode = 'interval') => {
    try {
      const response = await fetch(`/api/camera/${cameraId}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_mode: analysisMode
        })
      });

      const data = await response.json();
      
      if (data.success) {
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
        addAlert('error', `Failed to start analysis: ${data.error}`);
      }
    } catch (error) {
      console.error('Error starting analysis:', error);
      addAlert('error', 'Failed to start camera analysis');
    }
  };

  const stopCameraAnalysis = async (cameraId) => {
    try {
      const response = await fetch(`/api/camera/${cameraId}/stop`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
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
        addAlert('error', `Failed to stop analysis: ${data.error}`);
      }
    } catch (error) {
      console.error('Error stopping analysis:', error);
      addAlert('error', 'Failed to stop camera analysis');
    }
  };

  const captureAndAnalyze = async (cameraId, propertyId) => {
    try {
      const response = await fetch(`/api/camera/${cameraId}/capture`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_id: propertyId,
          description: 'Manual capture from live camera interface'
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setAnalysisResults(prev => ({
          ...prev,
          [cameraId]: data.analysis
        }));
        
        addAlert('success', `Frame captured and analyzed for ${cameraId}`);
      } else {
        addAlert('error', `Failed to capture frame: ${data.error}`);
      }
    } catch (error) {
      console.error('Error capturing frame:', error);
      addAlert('error', 'Failed to capture and analyze frame');
    }
  };

  const removeCamera = async (cameraId) => {
    try {
      const response = await fetch(`/api/camera/${cameraId}/remove`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
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
        addAlert('error', `Failed to remove camera: ${data.error}`);
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
        const response = await fetch(`/api/camera/${camera.camera_id}/status`);
        const data = await response.json();
        
        if (data.success) {
          setStreamStats(prev => ({
            ...prev,
            [camera.camera_id]: data.stream_data
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
            Detect Cameras
          </button>
          <select className="px-3 py-2 border border-gray-300 rounded-md">
            <option value="">Select Property</option>
            <option value="1">Property 1</option>
            <option value="2">Property 2</option>
            <option value="3">Property 3</option>
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
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
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LiveCameraAnalysis;