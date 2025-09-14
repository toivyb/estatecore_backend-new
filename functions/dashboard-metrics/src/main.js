import { Client, Databases, Query } from 'appwrite';

// This is your Appwrite Function
// Docs: https://appwrite.io/docs/functions

export default async ({ req, res, log, error }) => {
  // Initialize Appwrite client
  const client = new Client()
    .setEndpoint(process.env.APPWRITE_ENDPOINT || 'https://nyc.cloud.appwrite.io/v1')
    .setProject(process.env.APPWRITE_FUNCTION_PROJECT_ID || '68b6e4240013f757c47b')
    .setKey(process.env.APPWRITE_API_KEY);

  const databases = new Databases(client);
  const DATABASE_ID = '68b72cd60024e95cea71';

  try {
    log('Fetching dashboard metrics...');

    // Fetch all required data in parallel
    const [tenants, properties, workorders, payments, cameras, accessEvents] = await Promise.all([
      databases.listDocuments(DATABASE_ID, 'tenants'),
      databases.listDocuments(DATABASE_ID, 'properties'),
      databases.listDocuments(DATABASE_ID, 'workorders'),
      databases.listDocuments(DATABASE_ID, 'payments'),
      databases.listDocuments(DATABASE_ID, 'cameras'),
      databases.listDocuments(DATABASE_ID, 'access_events', [
        Query.greaterThan('timestamp', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
      ])
    ]);

    // Calculate metrics
    const metrics = {
      total_tenants: tenants.total || 0,
      active_tenants: tenants.documents.filter(t => t.lease_status === 'active').length,
      total_properties: properties.total || 0,
      occupied_properties: properties.documents.filter(p => 
        tenants.documents.some(t => t.lease_status === 'active' && 
        workorders.documents.some(w => w.property_id === p.$id && w.tenant_id === t.$id)
      )).length,
      
      // Work Orders
      total_workorders: workorders.total || 0,
      open_workorders: workorders.documents.filter(wo => wo.status === 'open').length,
      in_progress_workorders: workorders.documents.filter(wo => wo.status === 'in_progress').length,
      completed_workorders: workorders.documents.filter(wo => wo.status === 'completed').length,
      high_priority_workorders: workorders.documents.filter(wo => wo.priority === 'high' && wo.status !== 'completed').length,
      
      // Payments
      total_payments: payments.total || 0,
      pending_payments: payments.documents.filter(p => p.status === 'pending').length,
      overdue_payments: payments.documents.filter(p => 
        p.status === 'pending' && p.due_date && new Date(p.due_date) < new Date()
      ).length,
      total_revenue: payments.documents
        .filter(p => p.status === 'paid')
        .reduce((sum, p) => sum + (p.amount || 0), 0),
      
      // VMS
      total_cameras: cameras.total || 0,
      online_cameras: cameras.documents.filter(c => c.status === 'online').length,
      recording_cameras: cameras.documents.filter(c => c.recording_enabled).length,
      
      // Access Control
      access_events_today: accessEvents.total || 0,
      successful_access_today: accessEvents.documents.filter(e => e.result === 'granted').length,
      denied_access_today: accessEvents.documents.filter(e => e.result === 'denied').length,
      
      // Calculated percentages
      occupancy_rate: properties.total > 0 ? 
        Math.round((tenants.documents.filter(t => t.lease_status === 'active').length / properties.total) * 100) : 0,
      collection_rate: payments.documents.length > 0 ? 
        Math.round((payments.documents.filter(p => p.status === 'paid').length / payments.documents.length) * 100) : 0,
      camera_uptime: cameras.total > 0 ? 
        Math.round((cameras.documents.filter(c => c.status === 'online').length / cameras.total) * 100) : 0,
      
      // Timestamps
      last_updated: new Date().toISOString(),
      data_freshness: 'real-time'
    };

    log(`Calculated metrics: ${JSON.stringify(metrics, null, 2)}`);

    return res.json({
      success: true,
      data: metrics,
      timestamp: new Date().toISOString()
    });

  } catch (err) {
    error(`Error calculating dashboard metrics: ${err.message}`);
    return res.json({
      success: false,
      error: err.message,
      timestamp: new Date().toISOString()
    }, 500);
  }
};