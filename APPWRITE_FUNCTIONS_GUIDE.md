# Appwrite Functions Setup Guide

## Required Appwrite Functions for EstateCore

Your EstateCore application relies on several Appwrite Functions to handle complex operations. These functions need to be created and deployed in your Appwrite project.

### 1. Dashboard Metrics Function
**Function Name:** `dashboard-metrics`
**Purpose:** Calculate and return dashboard metrics (total tenants, properties, work orders, etc.)

```javascript
// Function code for dashboard-metrics
import { Client, Databases } from 'appwrite';

export default async function ({ req, res, log }) {
  const client = new Client()
    .setEndpoint(process.env.APPWRITE_ENDPOINT)
    .setProject(process.env.APPWRITE_FUNCTION_PROJECT_ID)
    .setKey(process.env.APPWRITE_API_KEY);

  const databases = new Databases(client);
  const DATABASE_ID = 'estatecore_main';
  
  try {
    const [tenants, properties, workorders] = await Promise.all([
      databases.listDocuments(DATABASE_ID, 'tenants'),
      databases.listDocuments(DATABASE_ID, 'properties'),
      databases.listDocuments(DATABASE_ID, 'workorders')
    ]);

    const metrics = {
      total_tenants: tenants.total,
      total_properties: properties.total,
      open_workorders: workorders.documents.filter(wo => wo.status === 'open').length,
      total_workorders: workorders.total
    };

    return res.json(metrics);
  } catch (error) {
    return res.json({ error: error.message }, 500);
  }
}
```

### 2. Camera Stream Control Function
**Function Name:** `camera-stream-control`
**Purpose:** Start/stop camera streams for VMS

```javascript
// Function code for camera-stream-control
export default async function ({ req, res, log }) {
  const { camera_id, action } = JSON.parse(req.body);
  
  // Implement camera control logic here
  // This would interface with your camera hardware/software
  
  try {
    // Placeholder implementation
    const result = {
      camera_id,
      action,
      status: action === 'start' ? 'streaming' : 'stopped',
      timestamp: new Date().toISOString()
    };

    return res.json(result);
  } catch (error) {
    return res.json({ error: error.message }, 500);
  }
}
```

### 3. Door Control Function
**Function Name:** `door-control`
**Purpose:** Control door locks for access control system

```javascript
// Function code for door-control
export default async function ({ req, res, log }) {
  const { door_id, action } = JSON.parse(req.body);
  
  try {
    // Implement door control logic here
    // This would interface with your access control hardware
    
    const result = {
      door_id,
      action,
      status: action === 'lock' ? 'locked' : 'unlocked',
      timestamp: new Date().toISOString()
    };

    return res.json(result);
  } catch (error) {
    return res.json({ error: error.message }, 500);
  }
}
```

### 4. Tenant Access Status Function
**Function Name:** `tenant-access-status`
**Purpose:** Get comprehensive access status for a tenant

```javascript
// Function code for tenant-access-status
import { Client, Databases } from 'appwrite';

export default async function ({ req, res, log }) {
  const { tenant_id } = JSON.parse(req.body);
  
  const client = new Client()
    .setEndpoint(process.env.APPWRITE_ENDPOINT)
    .setProject(process.env.APPWRITE_FUNCTION_PROJECT_ID)
    .setKey(process.env.APPWRITE_API_KEY);

  const databases = new Databases(client);
  const DATABASE_ID = 'estatecore_main';
  
  try {
    // Get tenant's access events and door permissions
    const [tenant, accessEvents] = await Promise.all([
      databases.getDocument(DATABASE_ID, 'tenants', tenant_id),
      databases.listDocuments(DATABASE_ID, 'access_events', [
        Query.equal('tenant_id', tenant_id),
        Query.orderDesc('$createdAt'),
        Query.limit(10)
      ])
    ]);

    const accessStatus = {
      tenant_id,
      active_lease: tenant.lease_status === 'active',
      recent_access: accessEvents.documents,
      permissions: tenant.access_permissions || []
    };

    return res.json(accessStatus);
  } catch (error) {
    return res.json({ error: error.message }, 500);
  }
}
```

## Setup Instructions

1. **Access your Appwrite Console**: Go to https://cloud.appwrite.io
2. **Navigate to Functions**: In your EstateCore project, go to the Functions section
3. **Create each function**: 
   - Click "Create Function"
   - Set the function name (e.g., `dashboard-metrics`)
   - Choose Node.js runtime
   - Deploy the function code above
4. **Set Environment Variables**: For each function, add these environment variables:
   - `APPWRITE_ENDPOINT`: Your Appwrite endpoint URL
   - `APPWRITE_FUNCTION_PROJECT_ID`: Your project ID
   - `APPWRITE_API_KEY`: A server API key with appropriate permissions

## Database Collections Required

Make sure these collections exist in your Appwrite database `estatecore_main`:

- `users`
- `tenants`
- `properties`
- `leases`
- `workorders`
- `payments`
- `cameras`
- `recordings`
- `motion_events`
- `access_doors`
- `access_events`
- `audit_logs`

## Permissions Setup

Each collection should have appropriate permissions set:
- Read/Write access for authenticated users
- Admin users should have full access
- Consider role-based permissions for different user types

## Testing Functions

After deployment, test each function using the Appwrite console or by calling them from your frontend application. Monitor the function logs for any errors.

## Production Considerations

- Implement proper error handling in all functions
- Add logging for debugging and monitoring
- Consider rate limiting for security
- Implement proper validation for all inputs
- Set up monitoring and alerts for function failures