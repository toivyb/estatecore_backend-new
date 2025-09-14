import { Client, Databases, Query } from 'appwrite';

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
    const { tenant_id } = body;

    if (!tenant_id) {
      return res.json({
        success: false,
        error: 'Missing required parameter: tenant_id'
      }, 400);
    }

    log(`Getting access status for tenant: ${tenant_id}`);

    // Get tenant details
    const tenant = await databases.getDocument(DATABASE_ID, 'tenants', tenant_id);
    
    if (!tenant) {
      return res.json({
        success: false,
        error: 'Tenant not found'
      }, 404);
    }

    // Get tenant's active lease
    const leases = await databases.listDocuments(DATABASE_ID, 'leases', [
      Query.equal('tenant_id', tenant_id),
      Query.equal('status', 'active')
    ]);

    const activeLease = leases.documents.length > 0 ? leases.documents[0] : null;

    // Get recent access events (last 30 days)
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    const accessEvents = await databases.listDocuments(DATABASE_ID, 'access_events', [
      Query.equal('tenant_id', tenant_id),
      Query.greaterThan('timestamp', thirtyDaysAgo.toISOString()),
      Query.orderDesc('timestamp'),
      Query.limit(50)
    ]);

    // Get property and door information if lease exists
    let property = null;
    let accessibleDoors = [];
    
    if (activeLease) {
      try {
        property = await databases.getDocument(DATABASE_ID, 'properties', activeLease.property_id);
        
        // Get doors for this property
        const propertyDoors = await databases.listDocuments(DATABASE_ID, 'access_doors', [
          Query.equal('property_id', activeLease.property_id),
          Query.equal('is_active', true)
        ]);
        
        accessibleDoors = propertyDoors.documents;
      } catch (err) {
        log(`Error fetching property/doors: ${err.message}`);
      }
    }

    // Calculate access statistics
    const totalAccess = accessEvents.documents.length;
    const successfulAccess = accessEvents.documents.filter(e => e.result === 'granted').length;
    const deniedAccess = accessEvents.documents.filter(e => e.result === 'denied').length;
    const emergencyAccess = accessEvents.documents.filter(e => e.event_type === 'emergency_unlock').length;

    // Get last access time
    const lastAccess = accessEvents.documents.length > 0 ? 
      accessEvents.documents[0].timestamp : null;

    // Group access events by door
    const accessByDoor = {};
    accessEvents.documents.forEach(event => {
      if (!accessByDoor[event.door_id]) {
        accessByDoor[event.door_id] = {
          total: 0,
          granted: 0,
          denied: 0,
          last_access: null
        };
      }
      accessByDoor[event.door_id].total++;
      if (event.result === 'granted') accessByDoor[event.door_id].granted++;
      if (event.result === 'denied') accessByDoor[event.door_id].denied++;
      if (!accessByDoor[event.door_id].last_access || 
          new Date(event.timestamp) > new Date(accessByDoor[event.door_id].last_access)) {
        accessByDoor[event.door_id].last_access = event.timestamp;
      }
    });

    // Determine access status
    let accessStatus = 'inactive';
    let accessReason = 'No active lease';
    
    if (activeLease && tenant.lease_status === 'active') {
      const now = new Date();
      const leaseStart = new Date(activeLease.start_date);
      const leaseEnd = new Date(activeLease.end_date);
      
      if (now >= leaseStart && now <= leaseEnd) {
        accessStatus = 'active';
        accessReason = 'Active lease in good standing';
      } else if (now < leaseStart) {
        accessStatus = 'pending';
        accessReason = 'Lease not yet started';
      } else if (now > leaseEnd) {
        accessStatus = 'expired';
        accessReason = 'Lease expired';
      }
    } else if (tenant.lease_status === 'terminated') {
      accessStatus = 'terminated';
      accessReason = 'Lease terminated';
    }

    // Build comprehensive status response
    const statusResponse = {
      tenant_id,
      tenant_info: {
        name: tenant.name,
        email: tenant.email,
        lease_status: tenant.lease_status,
        move_in_date: tenant.move_in_date,
        move_out_date: tenant.move_out_date
      },
      
      access_status: {
        status: accessStatus,
        reason: accessReason,
        is_active: accessStatus === 'active',
        permissions: tenant.access_permissions || []
      },
      
      lease_info: activeLease ? {
        lease_id: activeLease.$id,
        property_id: activeLease.property_id,
        property_name: property?.name || 'Unknown',
        unit_number: activeLease.unit_number,
        start_date: activeLease.start_date,
        end_date: activeLease.end_date,
        monthly_rent: activeLease.monthly_rent
      } : null,
      
      access_statistics: {
        total_access_attempts: totalAccess,
        successful_access: successfulAccess,
        denied_access: deniedAccess,
        emergency_access: emergencyAccess,
        success_rate: totalAccess > 0 ? Math.round((successfulAccess / totalAccess) * 100) : 0,
        last_access: lastAccess
      },
      
      accessible_doors: accessibleDoors.map(door => ({
        door_id: door.$id,
        name: door.name,
        location: door.location,
        door_type: door.door_type,
        access_method: door.access_method,
        status: door.status,
        access_stats: accessByDoor[door.$id] || {
          total: 0,
          granted: 0,
          denied: 0,
          last_access: null
        }
      })),
      
      recent_access_events: accessEvents.documents.slice(0, 10).map(event => ({
        timestamp: event.timestamp,
        door_id: event.door_id,
        event_type: event.event_type,
        result: event.result,
        access_method: event.access_method,
        notes: event.notes
      })),
      
      alerts: [],
      
      last_updated: new Date().toISOString()
    };

    // Add alerts based on access patterns
    if (deniedAccess > successfulAccess && totalAccess > 5) {
      statusResponse.alerts.push({
        type: 'warning',
        message: 'High number of denied access attempts',
        count: deniedAccess
      });
    }

    if (accessStatus === 'expired') {
      statusResponse.alerts.push({
        type: 'error',
        message: 'Lease has expired - access should be revoked',
        lease_end_date: activeLease?.end_date
      });
    }

    if (emergencyAccess > 0) {
      statusResponse.alerts.push({
        type: 'info',
        message: 'Emergency access events recorded',
        count: emergencyAccess
      });
    }

    // Log the audit trail
    await databases.createDocument(DATABASE_ID, 'audit_logs', 'unique()', {
      action: 'tenant_access_status_check',
      resource_type: 'tenant',
      resource_id: tenant_id,
      details: `Access status retrieved for tenant ${tenant.name} (${tenant.email})`,
      timestamp: new Date().toISOString(),
      created_at: new Date().toISOString()
    });

    log(`Access status compiled for tenant ${tenant.name}: ${accessStatus}`);

    return res.json({
      success: true,
      data: statusResponse,
      timestamp: new Date().toISOString()
    });

  } catch (err) {
    error(`Error getting tenant access status: ${err.message}`);
    return res.json({
      success: false,
      error: err.message,
      timestamp: new Date().toISOString()
    }, 500);
  }
};