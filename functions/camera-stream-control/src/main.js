import { Client, Databases } from 'appwrite';

export default async ({ req, res, log, error }) => {
  const client = new Client()
    .setEndpoint(process.env.APPWRITE_ENDPOINT || 'https://nyc.cloud.appwrite.io/v1')
    .setProject(process.env.APPWRITE_FUNCTION_PROJECT_ID || '68b6e4240013f757c47b')
    .setKey(process.env.APPWRITE_API_KEY);

  const databases = new Databases(client);
  const DATABASE_ID = '68b72cd60024e95cea71';

  try {
    // Parse request body
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
    const { camera_id, action } = body;

    if (!camera_id || !action) {
      return res.json({
        success: false,
        error: 'Missing required parameters: camera_id and action'
      }, 400);
    }

    log(`Camera control request: ${action} for camera ${camera_id}`);

    // Get camera details
    const camera = await databases.getDocument(DATABASE_ID, 'cameras', camera_id);
    
    if (!camera) {
      return res.json({
        success: false,
        error: 'Camera not found'
      }, 404);
    }

    // Simulate camera control operations
    let result = {};
    let updateData = {};

    switch (action) {
      case 'start':
        log(`Starting stream for camera: ${camera.name}`);
        updateData = {
          status: 'streaming',
          updated_at: new Date().toISOString()
        };
        result = {
          camera_id,
          action: 'start',
          status: 'streaming',
          stream_url: camera.stream_url || `rtsp://${camera.ip_address}:${camera.port || 554}/live`,
          message: 'Camera stream started successfully'
        };
        break;

      case 'stop':
        log(`Stopping stream for camera: ${camera.name}`);
        updateData = {
          status: 'online',
          updated_at: new Date().toISOString()
        };
        result = {
          camera_id,
          action: 'stop',
          status: 'stopped',
          message: 'Camera stream stopped successfully'
        };
        break;

      case 'restart':
        log(`Restarting camera: ${camera.name}`);
        updateData = {
          status: 'online',
          updated_at: new Date().toISOString()
        };
        result = {
          camera_id,
          action: 'restart',
          status: 'online',
          message: 'Camera restarted successfully'
        };
        break;

      case 'enable_recording':
        log(`Enabling recording for camera: ${camera.name}`);
        updateData = {
          recording_enabled: true,
          updated_at: new Date().toISOString()
        };
        result = {
          camera_id,
          action: 'enable_recording',
          recording_enabled: true,
          message: 'Recording enabled successfully'
        };
        break;

      case 'disable_recording':
        log(`Disabling recording for camera: ${camera.name}`);
        updateData = {
          recording_enabled: false,
          updated_at: new Date().toISOString()
        };
        result = {
          camera_id,
          action: 'disable_recording',
          recording_enabled: false,
          message: 'Recording disabled successfully'
        };
        break;

      case 'enable_motion_detection':
        log(`Enabling motion detection for camera: ${camera.name}`);
        updateData = {
          motion_detection: true,
          updated_at: new Date().toISOString()
        };
        result = {
          camera_id,
          action: 'enable_motion_detection',
          motion_detection: true,
          message: 'Motion detection enabled successfully'
        };
        break;

      case 'disable_motion_detection':
        log(`Disabling motion detection for camera: ${camera.name}`);
        updateData = {
          motion_detection: false,
          updated_at: new Date().toISOString()
        };
        result = {
          camera_id,
          action: 'disable_motion_detection',
          motion_detection: false,
          message: 'Motion detection disabled successfully'
        };
        break;

      default:
        return res.json({
          success: false,
          error: `Unknown action: ${action}. Supported actions: start, stop, restart, enable_recording, disable_recording, enable_motion_detection, disable_motion_detection`
        }, 400);
    }

    // Update camera status in database
    if (Object.keys(updateData).length > 0) {
      await databases.updateDocument(DATABASE_ID, 'cameras', camera_id, updateData);
    }

    // Log the action for audit purposes
    await databases.createDocument(DATABASE_ID, 'audit_logs', 'unique()', {
      action: `camera_${action}`,
      resource_type: 'camera',
      resource_id: camera_id,
      details: `Camera ${action} executed for ${camera.name} (${camera.location})`,
      timestamp: new Date().toISOString(),
      created_at: new Date().toISOString()
    });

    result.timestamp = new Date().toISOString();
    result.camera_name = camera.name;
    result.camera_location = camera.location;

    log(`Camera control completed: ${JSON.stringify(result)}`);

    return res.json({
      success: true,
      data: result,
      timestamp: new Date().toISOString()
    });

  } catch (err) {
    error(`Error controlling camera: ${err.message}`);
    return res.json({
      success: false,
      error: err.message,
      timestamp: new Date().toISOString()
    }, 500);
  }
};