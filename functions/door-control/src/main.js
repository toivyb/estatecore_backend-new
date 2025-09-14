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
    const { door_id, action, tenant_id, reason } = body;

    if (!door_id || !action) {
      return res.json({
        success: false,
        error: 'Missing required parameters: door_id and action'
      }, 400);
    }

    log(`Door control request: ${action} for door ${door_id}`);

    // Get door details
    const door = await databases.getDocument(DATABASE_ID, 'access_doors', door_id);
    
    if (!door) {
      return res.json({
        success: false,
        error: 'Door not found'
      }, 404);
    }

    if (!door.is_active) {
      return res.json({
        success: false,
        error: 'Door is not active'
      }, 400);
    }

    // Simulate door control operations
    let result = {};
    let updateData = {};
    let eventType = '';
    let eventResult = '';

    switch (action) {
      case 'lock':
        log(`Locking door: ${door.name}`);
        updateData = {
          status: 'locked',
          updated_at: new Date().toISOString()
        };
        result = {
          door_id,
          action: 'lock',
          status: 'locked',
          message: 'Door locked successfully'
        };
        eventType = 'manual_lock';
        eventResult = 'success';
        break;

      case 'unlock':
        log(`Unlocking door: ${door.name}`);
        updateData = {
          status: 'unlocked',
          updated_at: new Date().toISOString()
        };
        result = {
          door_id,
          action: 'unlock',
          status: 'unlocked',
          message: 'Door unlocked successfully'
        };
        eventType = 'manual_unlock';
        eventResult = 'success';
        break;

      case 'temp_unlock':
        log(`Temporarily unlocking door: ${door.name}`);
        // Door will auto-lock after 10 seconds in a real implementation
        updateData = {
          status: 'temp_unlocked',
          updated_at: new Date().toISOString()
        };
        result = {
          door_id,
          action: 'temp_unlock',
          status: 'temp_unlocked',
          auto_lock_seconds: 10,
          message: 'Door temporarily unlocked (will auto-lock in 10 seconds)'
        };
        eventType = 'temporary_unlock';
        eventResult = 'success';
        break;

      case 'emergency_unlock':
        log(`Emergency unlock for door: ${door.name}`);
        updateData = {
          status: 'emergency_unlocked',
          updated_at: new Date().toISOString()
        };
        result = {
          door_id,
          action: 'emergency_unlock',
          status: 'emergency_unlocked',
          message: 'Door emergency unlocked - requires manual lock reset'
        };
        eventType = 'emergency_unlock';
        eventResult = 'success';
        break;

      case 'status_check':
        log(`Checking status for door: ${door.name}`);
        result = {
          door_id,
          action: 'status_check',
          status: door.status,
          is_active: door.is_active,
          door_type: door.door_type,
          access_method: door.access_method,
          message: 'Door status retrieved successfully'
        };
        // No database update needed for status check
        break;

      default:
        return res.json({
          success: false,
          error: `Unknown action: ${action}. Supported actions: lock, unlock, temp_unlock, emergency_unlock, status_check`
        }, 400);
    }

    // Update door status in database (except for status_check)
    if (Object.keys(updateData).length > 0) {
      await databases.updateDocument(DATABASE_ID, 'access_doors', door_id, updateData);
    }

    // Create access event log (except for status_check)
    if (eventType) {
      await databases.createDocument(DATABASE_ID, 'access_events', 'unique()', {
        door_id,
        tenant_id: tenant_id || null,
        event_type: eventType,
        access_method: 'manual_control',
        result: eventResult,
        timestamp: new Date().toISOString(),
        notes: reason || `Manual ${action} operation`,
        created_at: new Date().toISOString()
      });
    }

    // Log the action for audit purposes
    await databases.createDocument(DATABASE_ID, 'audit_logs', 'unique()', {
      action: `door_${action}`,
      resource_type: 'access_door',
      resource_id: door_id,
      details: `Door ${action} executed for ${door.name} (${door.location})${tenant_id ? ` by tenant ${tenant_id}` : ''}`,
      timestamp: new Date().toISOString(),
      created_at: new Date().toISOString()
    });

    result.timestamp = new Date().toISOString();
    result.door_name = door.name;
    result.door_location = door.location;
    result.door_type = door.door_type;

    log(`Door control completed: ${JSON.stringify(result)}`);

    return res.json({
      success: true,
      data: result,
      timestamp: new Date().toISOString()
    });

  } catch (err) {
    error(`Error controlling door: ${err.message}`);
    
    // Log failed attempt
    try {
      await databases.createDocument(DATABASE_ID, 'access_events', 'unique()', {
        door_id: door_id || 'unknown',
        event_type: 'control_failure',
        result: 'error',
        timestamp: new Date().toISOString(),
        notes: `Door control failed: ${err.message}`,
        created_at: new Date().toISOString()
      });
    } catch (logError) {
      error(`Failed to log error event: ${logError.message}`);
    }

    return res.json({
      success: false,
      error: err.message,
      timestamp: new Date().toISOString()
    }, 500);
  }
};