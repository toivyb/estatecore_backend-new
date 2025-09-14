#!/usr/bin/env node
/**
 * Appwrite Database Setup Script
 * Run this script to automatically create all required collections
 * 
 * Prerequisites:
 * - Install Appwrite CLI: npm install -g appwrite-cli
 * - Login to Appwrite: appwrite login
 * - Set your project: appwrite client --endpoint https://nyc.cloud.appwrite.io/v1 --projectId 68b6e4240013f757c47b
 * 
 * Usage: node setup-appwrite.js
 */

const { execSync } = require('child_process');

const PROJECT_ID = '68b6e4240013f757c47b';
const DATABASE_ID = '68b72cd60024e95cea71';
const ENDPOINT = 'https://nyc.cloud.appwrite.io/v1';

// Collection definitions
const collections = [
  {
    id: 'users',
    name: 'Users',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'email', type: 'string', size: 320, required: true },
      { key: 'role', type: 'string', size: 50, required: true, default: 'user' },
      { key: 'is_active', type: 'boolean', required: true, default: true },
      { key: 'created_at', type: 'datetime', required: false },
      { key: 'updated_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'email', type: 'unique', attributes: ['email'] }
    ]
  },
  {
    id: 'tenants',
    name: 'Tenants',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'email', type: 'string', size: 320, required: true },
      { key: 'phone', type: 'string', size: 20, required: false },
      { key: 'emergency_contact_name', type: 'string', size: 255, required: false },
      { key: 'emergency_contact_phone', type: 'string', size: 20, required: false },
      { key: 'lease_status', type: 'string', size: 20, required: true, default: 'inactive' },
      { key: 'move_in_date', type: 'datetime', required: false },
      { key: 'move_out_date', type: 'datetime', required: false },
      { key: 'notes', type: 'string', size: 2000, required: false },
      { key: 'access_permissions', type: 'string', size: 1000, required: false, array: true },
      { key: 'created_at', type: 'datetime', required: false },
      { key: 'updated_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'email', type: 'unique', attributes: ['email'] },
      { key: 'lease_status', type: 'key', attributes: ['lease_status'] }
    ]
  },
  {
    id: 'properties',
    name: 'Properties',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'address', type: 'string', size: 500, required: true },
      { key: 'city', type: 'string', size: 100, required: true },
      { key: 'state', type: 'string', size: 50, required: true },
      { key: 'zip_code', type: 'string', size: 10, required: true },
      { key: 'property_type', type: 'string', size: 50, required: true, default: 'apartment' },
      { key: 'total_units', type: 'integer', required: true, default: 1 },
      { key: 'description', type: 'string', size: 2000, required: false },
      { key: 'amenities', type: 'string', size: 1000, required: false, array: true },
      { key: 'monthly_rent', type: 'double', required: false, default: 0 },
      { key: 'deposit_amount', type: 'double', required: false, default: 0 },
      { key: 'is_active', type: 'boolean', required: true, default: true },
      { key: 'created_at', type: 'datetime', required: false },
      { key: 'updated_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'city', type: 'key', attributes: ['city'] },
      { key: 'property_type', type: 'key', attributes: ['property_type'] },
      { key: 'is_active', type: 'key', attributes: ['is_active'] }
    ]
  },
  {
    id: 'leases',
    name: 'Leases',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'tenant_id', type: 'string', size: 36, required: true },
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'unit_number', type: 'string', size: 10, required: false },
      { key: 'start_date', type: 'datetime', required: true },
      { key: 'end_date', type: 'datetime', required: true },
      { key: 'monthly_rent', type: 'double', required: true },
      { key: 'deposit_amount', type: 'double', required: true },
      { key: 'status', type: 'string', size: 20, required: true, default: 'draft' },
      { key: 'lease_terms', type: 'string', size: 5000, required: false },
      { key: 'notes', type: 'string', size: 2000, required: false },
      { key: 'created_at', type: 'datetime', required: false },
      { key: 'updated_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'tenant_id', type: 'key', attributes: ['tenant_id'] },
      { key: 'property_id', type: 'key', attributes: ['property_id'] },
      { key: 'status', type: 'key', attributes: ['status'] },
      { key: 'start_date', type: 'key', attributes: ['start_date'] },
      { key: 'end_date', type: 'key', attributes: ['end_date'] }
    ]
  },
  {
    id: 'workorders',
    name: 'Work Orders',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'title', type: 'string', size: 255, required: true },
      { key: 'description', type: 'string', size: 2000, required: true },
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'tenant_id', type: 'string', size: 36, required: false },
      { key: 'assigned_to', type: 'string', size: 255, required: false },
      { key: 'priority', type: 'string', size: 20, required: true, default: 'medium' },
      { key: 'status', type: 'string', size: 20, required: true, default: 'open' },
      { key: 'category', type: 'string', size: 50, required: true, default: 'general' },
      { key: 'estimated_cost', type: 'double', required: false, default: 0 },
      { key: 'actual_cost', type: 'double', required: false, default: 0 },
      { key: 'due_date', type: 'datetime', required: false },
      { key: 'completed_date', type: 'datetime', required: false },
      { key: 'photos', type: 'string', size: 500, required: false, array: true },
      { key: 'notes', type: 'string', size: 2000, required: false },
      { key: 'created_at', type: 'datetime', required: false },
      { key: 'updated_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'property_id', type: 'key', attributes: ['property_id'] },
      { key: 'tenant_id', type: 'key', attributes: ['tenant_id'] },
      { key: 'status', type: 'key', attributes: ['status'] },
      { key: 'priority', type: 'key', attributes: ['priority'] },
      { key: 'due_date', type: 'key', attributes: ['due_date'] }
    ]
  },
  {
    id: 'payments',
    name: 'Payments',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'tenant_id', type: 'string', size: 36, required: true },
      { key: 'lease_id', type: 'string', size: 36, required: true },
      { key: 'amount', type: 'double', required: true },
      { key: 'payment_type', type: 'string', size: 50, required: true, default: 'rent' },
      { key: 'payment_method', type: 'string', size: 50, required: true, default: 'online' },
      { key: 'payment_date', type: 'datetime', required: true },
      { key: 'due_date', type: 'datetime', required: false },
      { key: 'status', type: 'string', size: 20, required: true, default: 'pending' },
      { key: 'transaction_id', type: 'string', size: 255, required: false },
      { key: 'notes', type: 'string', size: 1000, required: false },
      { key: 'created_at', type: 'datetime', required: false },
      { key: 'updated_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'tenant_id', type: 'key', attributes: ['tenant_id'] },
      { key: 'lease_id', type: 'key', attributes: ['lease_id'] },
      { key: 'payment_date', type: 'key', attributes: ['payment_date'] },
      { key: 'due_date', type: 'key', attributes: ['due_date'] },
      { key: 'status', type: 'key', attributes: ['status'] }
    ]
  },
  {
    id: 'cameras',
    name: 'Cameras',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'location', type: 'string', size: 255, required: true },
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'ip_address', type: 'string', size: 45, required: true },
      { key: 'port', type: 'integer', required: false, default: 554 },
      { key: 'username', type: 'string', size: 100, required: false },
      { key: 'password', type: 'string', size: 100, required: false },
      { key: 'stream_url', type: 'string', size: 500, required: false },
      { key: 'status', type: 'string', size: 20, required: true, default: 'offline' },
      { key: 'recording_enabled', type: 'boolean', required: true, default: false },
      { key: 'motion_detection', type: 'boolean', required: true, default: false },
      { key: 'resolution', type: 'string', size: 20, required: false, default: '1080p' },
      { key: 'fps', type: 'integer', required: false, default: 30 },
      { key: 'created_at', type: 'datetime', required: false },
      { key: 'updated_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'property_id', type: 'key', attributes: ['property_id'] },
      { key: 'status', type: 'key', attributes: ['status'] },
      { key: 'ip_address', type: 'key', attributes: ['ip_address'] }
    ]
  },
  {
    id: 'recordings',
    name: 'Recordings',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'camera_id', type: 'string', size: 36, required: true },
      { key: 'filename', type: 'string', size: 255, required: true },
      { key: 'file_path', type: 'string', size: 500, required: true },
      { key: 'file_size', type: 'integer', required: false, default: 0 },
      { key: 'duration', type: 'integer', required: false, default: 0 },
      { key: 'start_time', type: 'datetime', required: true },
      { key: 'end_time', type: 'datetime', required: true },
      { key: 'recording_type', type: 'string', size: 50, required: true, default: 'scheduled' },
      { key: 'status', type: 'string', size: 20, required: true, default: 'active' },
      { key: 'thumbnail_path', type: 'string', size: 500, required: false },
      { key: 'created_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'camera_id', type: 'key', attributes: ['camera_id'] },
      { key: 'start_time', type: 'key', attributes: ['start_time'] },
      { key: 'recording_type', type: 'key', attributes: ['recording_type'] }
    ]
  },
  {
    id: 'motion_events',
    name: 'Motion Events',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'camera_id', type: 'string', size: 36, required: true },
      { key: 'detected_at', type: 'datetime', required: true },
      { key: 'confidence', type: 'double', required: false, default: 0 },
      { key: 'bounding_box', type: 'string', size: 200, required: false },
      { key: 'snapshot_path', type: 'string', size: 500, required: false },
      { key: 'recording_id', type: 'string', size: 36, required: false },
      { key: 'processed', type: 'boolean', required: true, default: false },
      { key: 'created_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'camera_id', type: 'key', attributes: ['camera_id'] },
      { key: 'detected_at', type: 'key', attributes: ['detected_at'] },
      { key: 'processed', type: 'key', attributes: ['processed'] }
    ]
  },
  {
    id: 'access_doors',
    name: 'Access Doors',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'location', type: 'string', size: 255, required: true },
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'door_type', type: 'string', size: 50, required: true, default: 'entry' },
      { key: 'access_method', type: 'string', size: 50, required: true, default: 'keycard' },
      { key: 'status', type: 'string', size: 20, required: true, default: 'locked' },
      { key: 'is_active', type: 'boolean', required: true, default: true },
      { key: 'controller_ip', type: 'string', size: 45, required: false },
      { key: 'controller_port', type: 'integer', required: false, default: 4370 },
      { key: 'created_at', type: 'datetime', required: false },
      { key: 'updated_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'property_id', type: 'key', attributes: ['property_id'] },
      { key: 'status', type: 'key', attributes: ['status'] },
      { key: 'door_type', type: 'key', attributes: ['door_type'] }
    ]
  },
  {
    id: 'access_events',
    name: 'Access Events',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'door_id', type: 'string', size: 36, required: true },
      { key: 'tenant_id', type: 'string', size: 36, required: false },
      { key: 'event_type', type: 'string', size: 50, required: true, default: 'access_attempt' },
      { key: 'access_method', type: 'string', size: 50, required: false },
      { key: 'card_id', type: 'string', size: 100, required: false },
      { key: 'result', type: 'string', size: 20, required: true, default: 'denied' },
      { key: 'timestamp', type: 'datetime', required: true },
      { key: 'notes', type: 'string', size: 500, required: false },
      { key: 'created_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'door_id', type: 'key', attributes: ['door_id'] },
      { key: 'tenant_id', type: 'key', attributes: ['tenant_id'] },
      { key: 'timestamp', type: 'key', attributes: ['timestamp'] },
      { key: 'result', type: 'key', attributes: ['result'] }
    ]
  },
  {
    id: 'audit_logs',
    name: 'Audit Logs',
    permissions: ['read("users")', 'create("users")', 'update("users")', 'delete("role:admin")'],
    documentSecurity: true,
    attributes: [
      { key: 'user_id', type: 'string', size: 36, required: false },
      { key: 'action', type: 'string', size: 100, required: true },
      { key: 'resource_type', type: 'string', size: 50, required: true },
      { key: 'resource_id', type: 'string', size: 36, required: false },
      { key: 'details', type: 'string', size: 2000, required: false },
      { key: 'ip_address', type: 'string', size: 45, required: false },
      { key: 'user_agent', type: 'string', size: 500, required: false },
      { key: 'timestamp', type: 'datetime', required: true },
      { key: 'created_at', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'user_id', type: 'key', attributes: ['user_id'] },
      { key: 'action', type: 'key', attributes: ['action'] },
      { key: 'timestamp', type: 'key', attributes: ['timestamp'] },
      { key: 'resource_type', type: 'key', attributes: ['resource_type'] }
    ]
  }
];

function runCommand(command) {
  try {
    console.log(`Executing: ${command}`);
    const result = execSync(command, { encoding: 'utf8' });
    console.log(result);
    return result;
  } catch (error) {
    console.error(`Error executing: ${command}`);
    console.error(error.message);
    return null;
  }
}

function setupAppwrite() {
  console.log('🚀 Setting up EstateCore Appwrite Backend...\n');
  
  // Set client configuration
  console.log('📱 Configuring Appwrite client...');
  runCommand(`appwrite client --endpoint ${ENDPOINT} --projectId ${PROJECT_ID}`);
  
  // Create database
  console.log('🗄️ Creating database...');
  runCommand(`appwrite databases create --databaseId ${DATABASE_ID} --name "EstateCore Main Database"`);
  
  // Create collections
  console.log('📂 Creating collections...\n');
  
  collections.forEach(collection => {
    console.log(`Creating collection: ${collection.name}`);
    
    // Create collection
    const createCmd = `appwrite databases createCollection --databaseId ${DATABASE_ID} --collectionId ${collection.id} --name "${collection.name}" --documentSecurity ${collection.documentSecurity}`;
    runCommand(createCmd);
    
    // Add attributes
    collection.attributes.forEach(attr => {
      let attrCmd = `appwrite databases createStringAttribute --databaseId ${DATABASE_ID} --collectionId ${collection.id} --key ${attr.key}`;
      
      switch (attr.type) {
        case 'string':
          attrCmd = `appwrite databases createStringAttribute --databaseId ${DATABASE_ID} --collectionId ${collection.id} --key ${attr.key} --size ${attr.size} --required ${attr.required}`;
          if (attr.default) attrCmd += ` --default "${attr.default}"`;
          if (attr.array) attrCmd += ` --array true`;
          break;
        case 'integer':
          attrCmd = `appwrite databases createIntegerAttribute --databaseId ${DATABASE_ID} --collectionId ${collection.id} --key ${attr.key} --required ${attr.required}`;
          if (attr.default !== undefined) attrCmd += ` --default ${attr.default}`;
          break;
        case 'double':
          attrCmd = `appwrite databases createFloatAttribute --databaseId ${DATABASE_ID} --collectionId ${collection.id} --key ${attr.key} --required ${attr.required}`;
          if (attr.default !== undefined) attrCmd += ` --default ${attr.default}`;
          break;
        case 'boolean':
          attrCmd = `appwrite databases createBooleanAttribute --databaseId ${DATABASE_ID} --collectionId ${collection.id} --key ${attr.key} --required ${attr.required}`;
          if (attr.default !== undefined) attrCmd += ` --default ${attr.default}`;
          break;
        case 'datetime':
          attrCmd = `appwrite databases createDatetimeAttribute --databaseId ${DATABASE_ID} --collectionId ${collection.id} --key ${attr.key} --required ${attr.required}`;
          break;
      }
      
      runCommand(attrCmd);
    });
    
    // Create indexes
    if (collection.indexes) {
      collection.indexes.forEach(index => {
        const indexCmd = `appwrite databases createIndex --databaseId ${DATABASE_ID} --collectionId ${collection.id} --key ${index.key} --type ${index.type} --attributes ${index.attributes.join(',')}`;
        runCommand(indexCmd);
      });
    }
    
    // Set permissions
    const permissionsCmd = `appwrite databases updateCollection --databaseId ${DATABASE_ID} --collectionId ${collection.id} --permissions '${JSON.stringify(collection.permissions)}'`;
    runCommand(permissionsCmd);
    
    console.log(`✅ Collection ${collection.name} created successfully\n`);
  });
  
  console.log('🎉 All collections created successfully!');
  console.log('\n📋 Next steps:');
  console.log('1. Deploy Appwrite Functions using the provided function files');
  console.log('2. Configure authentication settings in Appwrite Console');
  console.log('3. Add your Netlify domain to allowed origins');
  console.log('4. Deploy your frontend to Netlify');
}

// Check if Appwrite CLI is available
try {
  execSync('appwrite --version', { encoding: 'utf8' });
  setupAppwrite();
} catch (error) {
  console.error('❌ Appwrite CLI not found!');
  console.log('Please install it first: npm install -g appwrite-cli');
  console.log('Then login: appwrite login');
  console.log('Then run this script again');
}