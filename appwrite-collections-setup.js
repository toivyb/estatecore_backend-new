/**
 * Appwrite Collections Setup Configuration
 * 
 * This file contains the complete configuration for all Appwrite collections
 * needed for the EstateCore application. Use this as a reference when creating
 * collections in the Appwrite console.
 * 
 * Instructions:
 * 1. Log into your Appwrite console
 * 2. Navigate to your EstateCore database (ID: 68b72cd60024e95cea71)
 * 3. For each collection below, create it with the specified attributes, indexes, and permissions
 */

// Database Configuration
const DATABASE_ID = '68b72cd60024e95cea71';

// Collection Definitions
const COLLECTIONS_CONFIG = {
  // Core Collections
  USERS: {
    collectionId: 'users',
    name: 'Users',
    attributes: [
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'email', type: 'string', size: 255, required: true },
      { key: 'role', type: 'string', size: 50, required: true, default: 'tenant' }, // super_admin, admin, manager, tenant, vendor
      { key: 'phone', type: 'string', size: 20, required: false },
      { key: 'status', type: 'string', size: 20, required: true, default: 'active' }, // active, inactive, suspended
      { key: 'profile_image', type: 'string', size: 500, required: false },
      { key: 'last_login', type: 'datetime', required: false },
      { key: 'created_by', type: 'string', size: 36, required: false },
      { key: 'updated_by', type: 'string', size: 36, required: false }
    ],
    indexes: [
      { key: 'email_index', type: 'unique', attributes: ['email'] },
      { key: 'role_index', type: 'key', attributes: ['role'] },
      { key: 'status_index', type: 'key', attributes: ['status'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager'],
      create: ['role:super_admin', 'role:admin'],
      update: ['role:super_admin', 'role:admin', 'users'],
      delete: ['role:super_admin']
    }
  },

  TENANTS: {
    collectionId: 'tenants',
    name: 'Tenants',
    attributes: [
      { key: 'user_id', type: 'string', size: 36, required: true },
      { key: 'first_name', type: 'string', size: 100, required: true },
      { key: 'last_name', type: 'string', size: 100, required: true },
      { key: 'email', type: 'string', size: 255, required: true },
      { key: 'phone', type: 'string', size: 20, required: false },
      { key: 'emergency_contact_name', type: 'string', size: 255, required: false },
      { key: 'emergency_contact_phone', type: 'string', size: 20, required: false },
      { key: 'employment_info', type: 'string', size: 1000, required: false },
      { key: 'monthly_income', type: 'float', required: false },
      { key: 'credit_score', type: 'integer', required: false },
      { key: 'background_check', type: 'string', size: 20, required: false }, // pending, approved, rejected
      { key: 'status', type: 'string', size: 20, required: true, default: 'active' }, // active, inactive, evicted
      { key: 'move_in_date', type: 'datetime', required: false },
      { key: 'move_out_date', type: 'datetime', required: false },
      { key: 'notes', type: 'string', size: 2000, required: false }
    ],
    indexes: [
      { key: 'user_id_index', type: 'key', attributes: ['user_id'] },
      { key: 'email_index', type: 'key', attributes: ['email'] },
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'name_index', type: 'fulltext', attributes: ['first_name', 'last_name'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager', 'users'],
      create: ['role:super_admin', 'role:admin'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  PROPERTIES: {
    collectionId: 'properties',
    name: 'Properties',
    attributes: [
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'address', type: 'string', size: 500, required: true },
      { key: 'city', type: 'string', size: 100, required: true },
      { key: 'state', type: 'string', size: 50, required: true },
      { key: 'zip_code', type: 'string', size: 10, required: true },
      { key: 'property_type', type: 'string', size: 50, required: true }, // apartment, house, commercial, etc.
      { key: 'total_units', type: 'integer', required: true, default: 1 },
      { key: 'year_built', type: 'integer', required: false },
      { key: 'square_footage', type: 'integer', required: false },
      { key: 'lot_size', type: 'float', required: false },
      { key: 'amenities', type: 'string', size: 2000, required: false }, // JSON string of amenities
      { key: 'description', type: 'string', size: 2000, required: false },
      { key: 'purchase_price', type: 'float', required: false },
      { key: 'current_value', type: 'float', required: false },
      { key: 'status', type: 'string', size: 20, required: true, default: 'active' }, // active, inactive, sold
      { key: 'manager_id', type: 'string', size: 36, required: false },
      { key: 'images', type: 'string', size: 2000, required: false }, // JSON array of image URLs
      { key: 'created_by', type: 'string', size: 36, required: false }
    ],
    indexes: [
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'property_type_index', type: 'key', attributes: ['property_type'] },
      { key: 'manager_id_index', type: 'key', attributes: ['manager_id'] },
      { key: 'location_index', type: 'key', attributes: ['city', 'state'] },
      { key: 'name_index', type: 'fulltext', attributes: ['name', 'address'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager', 'role:tenant'],
      create: ['role:super_admin', 'role:admin'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  UNITS: {
    collectionId: 'units',
    name: 'Units',
    attributes: [
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'unit_number', type: 'string', size: 20, required: true },
      { key: 'apartment_number', type: 'string', size: 20, required: false },
      { key: 'floor', type: 'integer', required: false },
      { key: 'bedrooms', type: 'integer', required: true, default: 1 },
      { key: 'bathrooms', type: 'float', required: true, default: 1.0 },
      { key: 'square_footage', type: 'integer', required: false },
      { key: 'rent_amount', type: 'float', required: true },
      { key: 'security_deposit', type: 'float', required: false },
      { key: 'status', type: 'string', size: 20, required: true, default: 'vacant' }, // vacant, occupied, maintenance, unavailable
      { key: 'furnished', type: 'boolean', required: false, default: false },
      { key: 'pet_friendly', type: 'boolean', required: false, default: false },
      { key: 'amenities', type: 'string', size: 1000, required: false }, // JSON string
      { key: 'description', type: 'string', size: 1000, required: false },
      { key: 'images', type: 'string', size: 1000, required: false }, // JSON array of image URLs
      { key: 'last_renovated', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'unit_number_index', type: 'key', attributes: ['unit_number'] },
      { key: 'property_unit_index', type: 'unique', attributes: ['property_id', 'unit_number'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager', 'role:tenant'],
      create: ['role:super_admin', 'role:admin'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  LEASES: {
    collectionId: 'leases',
    name: 'Leases',
    attributes: [
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'unit_id', type: 'string', size: 36, required: false },
      { key: 'tenant_id', type: 'string', size: 36, required: true },
      { key: 'lease_type', type: 'string', size: 20, required: true }, // fixed, month-to-month
      { key: 'start_date', type: 'datetime', required: true },
      { key: 'end_date', type: 'datetime', required: false },
      { key: 'monthly_rent', type: 'float', required: true },
      { key: 'security_deposit', type: 'float', required: false },
      { key: 'pet_deposit', type: 'float', required: false },
      { key: 'late_fee', type: 'float', required: false },
      { key: 'grace_period', type: 'integer', required: false, default: 5 }, // days
      { key: 'status', type: 'string', size: 20, required: true, default: 'active' }, // active, expired, terminated, pending
      { key: 'terms_and_conditions', type: 'string', size: 5000, required: false },
      { key: 'special_conditions', type: 'string', size: 2000, required: false },
      { key: 'auto_renew', type: 'boolean', required: false, default: false },
      { key: 'lease_document_url', type: 'string', size: 500, required: false },
      { key: 'signed_date', type: 'datetime', required: false },
      { key: 'created_by', type: 'string', size: 36, required: false }
    ],
    indexes: [
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'tenant_id_index', type: 'key', attributes: ['tenant_id'] },
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'date_range_index', type: 'key', attributes: ['start_date', 'end_date'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager', 'users'],
      create: ['role:super_admin', 'role:admin', 'role:manager'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  WORKORDERS: {
    collectionId: 'workorders',
    name: 'Work Orders',
    attributes: [
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'unit_id', type: 'string', size: 36, required: false },
      { key: 'tenant_id', type: 'string', size: 36, required: false },
      { key: 'assigned_to', type: 'string', size: 36, required: false }, // vendor or staff user_id
      { key: 'title', type: 'string', size: 255, required: true },
      { key: 'description', type: 'string', size: 2000, required: true },
      { key: 'category', type: 'string', size: 50, required: true }, // plumbing, electrical, hvac, etc.
      { key: 'priority', type: 'string', size: 20, required: true, default: 'medium' }, // low, medium, high, emergency
      { key: 'status', type: 'string', size: 20, required: true, default: 'open' }, // open, in_progress, completed, cancelled
      { key: 'estimated_cost', type: 'float', required: false },
      { key: 'actual_cost', type: 'float', required: false },
      { key: 'scheduled_date', type: 'datetime', required: false },
      { key: 'completed_date', type: 'datetime', required: false },
      { key: 'completion_notes', type: 'string', size: 2000, required: false },
      { key: 'tenant_access_required', type: 'boolean', required: false, default: false },
      { key: 'images', type: 'string', size: 1000, required: false }, // JSON array of image URLs
      { key: 'created_by', type: 'string', size: 36, required: false },
      { key: 'updated_by', type: 'string', size: 36, required: false }
    ],
    indexes: [
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'priority_index', type: 'key', attributes: ['priority'] },
      { key: 'assigned_to_index', type: 'key', attributes: ['assigned_to'] },
      { key: 'category_index', type: 'key', attributes: ['category'] },
      { key: 'tenant_id_index', type: 'key', attributes: ['tenant_id'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager', 'role:tenant', 'role:vendor'],
      create: ['role:super_admin', 'role:admin', 'role:manager', 'role:tenant'],
      update: ['role:super_admin', 'role:admin', 'role:manager', 'role:vendor'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  PAYMENTS: {
    collectionId: 'payments',
    name: 'Payments',
    attributes: [
      { key: 'tenant_id', type: 'string', size: 36, required: true },
      { key: 'lease_id', type: 'string', size: 36, required: false },
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'amount', type: 'float', required: true },
      { key: 'payment_type', type: 'string', size: 20, required: true }, // rent, deposit, fee, etc.
      { key: 'payment_method', type: 'string', size: 20, required: true }, // cash, check, online, etc.
      { key: 'payment_date', type: 'datetime', required: true },
      { key: 'due_date', type: 'datetime', required: false },
      { key: 'status', type: 'string', size: 20, required: true, default: 'pending' }, // pending, completed, failed, refunded
      { key: 'reference_number', type: 'string', size: 100, required: false },
      { key: 'check_number', type: 'string', size: 50, required: false },
      { key: 'notes', type: 'string', size: 1000, required: false },
      { key: 'late_fee', type: 'float', required: false, default: 0.0 },
      { key: 'receipt_url', type: 'string', size: 500, required: false },
      { key: 'processed_by', type: 'string', size: 36, required: false }
    ],
    indexes: [
      { key: 'tenant_id_index', type: 'key', attributes: ['tenant_id'] },
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'payment_date_index', type: 'key', attributes: ['payment_date'] },
      { key: 'payment_type_index', type: 'key', attributes: ['payment_type'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager', 'users'],
      create: ['role:super_admin', 'role:admin', 'role:manager', 'role:tenant'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  VENDORS: {
    collectionId: 'vendors',
    name: 'Vendors',
    attributes: [
      { key: 'company_name', type: 'string', size: 255, required: true },
      { key: 'contact_name', type: 'string', size: 255, required: false },
      { key: 'email', type: 'string', size: 255, required: false },
      { key: 'phone', type: 'string', size: 20, required: false },
      { key: 'address', type: 'string', size: 500, required: false },
      { key: 'services', type: 'string', size: 1000, required: false }, // JSON array of services
      { key: 'hourly_rate', type: 'float', required: false },
      { key: 'rating', type: 'float', required: false }, // 1-5 stars
      { key: 'status', type: 'string', size: 20, required: true, default: 'active' }, // active, inactive, blacklisted
      { key: 'license_number', type: 'string', size: 100, required: false },
      { key: 'insurance_expiry', type: 'datetime', required: false },
      { key: 'notes', type: 'string', size: 2000, required: false },
      { key: 'created_by', type: 'string', size: 36, required: false }
    ],
    indexes: [
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'services_index', type: 'fulltext', attributes: ['services'] },
      { key: 'company_name_index', type: 'fulltext', attributes: ['company_name'] },
      { key: 'rating_index', type: 'key', attributes: ['rating'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager'],
      create: ['role:super_admin', 'role:admin'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  // VMS Collections
  CAMERAS: {
    collectionId: 'cameras',
    name: 'Cameras',
    attributes: [
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'location', type: 'string', size: 255, required: true },
      { key: 'ip_address', type: 'string', size: 15, required: false },
      { key: 'model', type: 'string', size: 100, required: false },
      { key: 'serial_number', type: 'string', size: 100, required: false },
      { key: 'status', type: 'string', size: 20, required: true, default: 'offline' }, // online, offline, maintenance
      { key: 'recording_enabled', type: 'boolean', required: false, default: true },
      { key: 'motion_detection', type: 'boolean', required: false, default: true },
      { key: 'night_vision', type: 'boolean', required: false, default: false },
      { key: 'resolution', type: 'string', size: 20, required: false }, // 720p, 1080p, 4K
      { key: 'fps', type: 'integer', required: false, default: 30 },
      { key: 'stream_url', type: 'string', size: 500, required: false },
      { key: 'last_ping', type: 'datetime', required: false },
      { key: 'installation_date', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'location_index', type: 'fulltext', attributes: ['location'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager'],
      create: ['role:super_admin', 'role:admin'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  RECORDINGS: {
    collectionId: 'recordings',
    name: 'Recordings',
    attributes: [
      { key: 'camera_id', type: 'string', size: 36, required: true },
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'filename', type: 'string', size: 255, required: true },
      { key: 'file_path', type: 'string', size: 500, required: true },
      { key: 'file_size', type: 'integer', required: false }, // bytes
      { key: 'duration', type: 'integer', required: false }, // seconds
      { key: 'start_time', type: 'datetime', required: true },
      { key: 'end_time', type: 'datetime', required: true },
      { key: 'recording_type', type: 'string', size: 20, required: true }, // continuous, motion, event
      { key: 'quality', type: 'string', size: 20, required: false },
      { key: 'thumbnail_path', type: 'string', size: 500, required: false },
      { key: 'archived', type: 'boolean', required: false, default: false },
      { key: 'deleted', type: 'boolean', required: false, default: false }
    ],
    indexes: [
      { key: 'camera_id_index', type: 'key', attributes: ['camera_id'] },
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'time_range_index', type: 'key', attributes: ['start_time', 'end_time'] },
      { key: 'recording_type_index', type: 'key', attributes: ['recording_type'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager'],
      create: ['role:super_admin', 'role:admin', 'role:manager'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  MOTION_EVENTS: {
    collectionId: 'motion_events',
    name: 'Motion Events',
    attributes: [
      { key: 'camera_id', type: 'string', size: 36, required: true },
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'event_time', type: 'datetime', required: true },
      { key: 'confidence', type: 'float', required: false }, // 0-1 confidence score
      { key: 'recording_id', type: 'string', size: 36, required: false },
      { key: 'snapshot_path', type: 'string', size: 500, required: false },
      { key: 'processed', type: 'boolean', required: false, default: false },
      { key: 'alert_sent', type: 'boolean', required: false, default: false }
    ],
    indexes: [
      { key: 'camera_id_index', type: 'key', attributes: ['camera_id'] },
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'event_time_index', type: 'key', attributes: ['event_time'] },
      { key: 'processed_index', type: 'key', attributes: ['processed'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager'],
      create: ['role:super_admin', 'role:admin', 'role:manager'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  // Access Control Collections
  ACCESS_DOORS: {
    collectionId: 'access_doors',
    name: 'Access Doors',
    attributes: [
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'location', type: 'string', size: 255, required: true },
      { key: 'door_type', type: 'string', size: 50, required: true }, // main_entrance, unit_door, garage, etc.
      { key: 'controller_id', type: 'string', size: 100, required: false },
      { key: 'ip_address', type: 'string', size: 15, required: false },
      { key: 'status', type: 'string', size: 20, required: true, default: 'locked' }, // locked, unlocked, maintenance
      { key: 'lock_type', type: 'string', size: 50, required: false }, // keypad, card, biometric, etc.
      { key: 'auto_lock_delay', type: 'integer', required: false, default: 5 }, // seconds
      { key: 'last_ping', type: 'datetime', required: false },
      { key: 'installation_date', type: 'datetime', required: false }
    ],
    indexes: [
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'door_type_index', type: 'key', attributes: ['door_type'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager'],
      create: ['role:super_admin', 'role:admin'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  ACCESS_EVENTS: {
    collectionId: 'access_events',
    name: 'Access Events',
    attributes: [
      { key: 'door_id', type: 'string', size: 36, required: true },
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'user_id', type: 'string', size: 36, required: false },
      { key: 'event_type', type: 'string', size: 20, required: true }, // unlock, lock, denied, forced
      { key: 'event_time', type: 'datetime', required: true },
      { key: 'access_method', type: 'string', size: 20, required: false }, // keypad, card, mobile, etc.
      { key: 'success', type: 'boolean', required: true },
      { key: 'reason', type: 'string', size: 255, required: false }, // why access was denied
      { key: 'visitor_name', type: 'string', size: 255, required: false }
    ],
    indexes: [
      { key: 'door_id_index', type: 'key', attributes: ['door_id'] },
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'user_id_index', type: 'key', attributes: ['user_id'] },
      { key: 'event_time_index', type: 'key', attributes: ['event_time'] },
      { key: 'event_type_index', type: 'key', attributes: ['event_type'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager'],
      create: ['role:super_admin', 'role:admin', 'role:manager'],
      update: ['role:super_admin', 'role:admin'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  VISITOR_PASSES: {
    collectionId: 'visitor_passes',
    name: 'Visitor Passes',
    attributes: [
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'tenant_id', type: 'string', size: 36, required: true },
      { key: 'visitor_name', type: 'string', size: 255, required: true },
      { key: 'visitor_phone', type: 'string', size: 20, required: false },
      { key: 'pin_code', type: 'string', size: 10, required: true },
      { key: 'valid_from', type: 'datetime', required: true },
      { key: 'valid_until', type: 'datetime', required: true },
      { key: 'access_doors', type: 'string', size: 500, required: false }, // JSON array of door IDs
      { key: 'status', type: 'string', size: 20, required: true, default: 'active' }, // active, expired, revoked
      { key: 'uses_remaining', type: 'integer', required: false }, // null = unlimited
      { key: 'purpose', type: 'string', size: 255, required: false },
      { key: 'created_by', type: 'string', size: 36, required: false }
    ],
    indexes: [
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'tenant_id_index', type: 'key', attributes: ['tenant_id'] },
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'valid_dates_index', type: 'key', attributes: ['valid_from', 'valid_until'] },
      { key: 'pin_code_index', type: 'key', attributes: ['pin_code'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager', 'users'],
      create: ['role:super_admin', 'role:admin', 'role:manager', 'role:tenant'],
      update: ['role:super_admin', 'role:admin', 'role:manager', 'users'],
      delete: ['role:super_admin', 'role:admin', 'role:manager']
    }
  },

  // Additional Collections
  AUDIT_LOGS: {
    collectionId: 'audit_logs',
    name: 'Audit Logs',
    attributes: [
      { key: 'user_id', type: 'string', size: 36, required: false },
      { key: 'action', type: 'string', size: 100, required: true }, // create, update, delete, login, etc.
      { key: 'resource_type', type: 'string', size: 50, required: true }, // user, property, tenant, etc.
      { key: 'resource_id', type: 'string', size: 36, required: false },
      { key: 'details', type: 'string', size: 2000, required: false }, // JSON string with change details
      { key: 'ip_address', type: 'string', size: 45, required: false },
      { key: 'user_agent', type: 'string', size: 500, required: false },
      { key: 'timestamp', type: 'datetime', required: true }
    ],
    indexes: [
      { key: 'user_id_index', type: 'key', attributes: ['user_id'] },
      { key: 'action_index', type: 'key', attributes: ['action'] },
      { key: 'resource_index', type: 'key', attributes: ['resource_type', 'resource_id'] },
      { key: 'timestamp_index', type: 'key', attributes: ['timestamp'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin'],
      create: ['role:super_admin', 'role:admin', 'role:manager'],
      update: ['role:super_admin'],
      delete: ['role:super_admin']
    }
  },

  RENT_RECORDS: {
    collectionId: 'rent_records',
    name: 'Rent Records',
    attributes: [
      { key: 'lease_id', type: 'string', size: 36, required: true },
      { key: 'tenant_id', type: 'string', size: 36, required: true },
      { key: 'property_id', type: 'string', size: 36, required: true },
      { key: 'month_year', type: 'string', size: 7, required: true }, // YYYY-MM format
      { key: 'amount_due', type: 'float', required: true },
      { key: 'amount_paid', type: 'float', required: false, default: 0.0 },
      { key: 'due_date', type: 'datetime', required: true },
      { key: 'paid_date', type: 'datetime', required: false },
      { key: 'late_fee', type: 'float', required: false, default: 0.0 },
      { key: 'status', type: 'string', size: 20, required: true, default: 'pending' }, // pending, paid, late, partial
      { key: 'payment_method', type: 'string', size: 20, required: false },
      { key: 'notes', type: 'string', size: 1000, required: false }
    ],
    indexes: [
      { key: 'lease_id_index', type: 'key', attributes: ['lease_id'] },
      { key: 'tenant_id_index', type: 'key', attributes: ['tenant_id'] },
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'status_index', type: 'key', attributes: ['status'] },
      { key: 'month_year_index', type: 'key', attributes: ['month_year'] },
      { key: 'due_date_index', type: 'key', attributes: ['due_date'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager', 'users'],
      create: ['role:super_admin', 'role:admin', 'role:manager'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  },

  NOTIFICATIONS: {
    collectionId: 'notifications',
    name: 'Notifications',
    attributes: [
      { key: 'user_id', type: 'string', size: 36, required: true },
      { key: 'title', type: 'string', size: 255, required: true },
      { key: 'message', type: 'string', size: 2000, required: true },
      { key: 'type', type: 'string', size: 50, required: true }, // info, warning, error, maintenance, payment, etc.
      { key: 'priority', type: 'string', size: 20, required: true, default: 'normal' }, // low, normal, high, urgent
      { key: 'read', type: 'boolean', required: false, default: false },
      { key: 'read_at', type: 'datetime', required: false },
      { key: 'action_url', type: 'string', size: 500, required: false },
      { key: 'expires_at', type: 'datetime', required: false },
      { key: 'sent_via', type: 'string', size: 100, required: false }, // app, email, sms
      { key: 'related_resource_type', type: 'string', size: 50, required: false },
      { key: 'related_resource_id', type: 'string', size: 36, required: false }
    ],
    indexes: [
      { key: 'user_id_index', type: 'key', attributes: ['user_id'] },
      { key: 'type_index', type: 'key', attributes: ['type'] },
      { key: 'priority_index', type: 'key', attributes: ['priority'] },
      { key: 'read_index', type: 'key', attributes: ['read'] },
      { key: 'created_at_index', type: 'key', attributes: ['$createdAt'] }
    ],
    permissions: {
      read: ['users'],
      create: ['role:super_admin', 'role:admin', 'role:manager'],
      update: ['users'],
      delete: ['role:super_admin', 'role:admin', 'users']
    }
  },

  DOCUMENTS: {
    collectionId: 'documents',
    name: 'Documents',
    attributes: [
      { key: 'name', type: 'string', size: 255, required: true },
      { key: 'document_type', type: 'string', size: 50, required: true }, // lease, invoice, receipt, maintenance, etc.
      { key: 'file_path', type: 'string', size: 500, required: true },
      { key: 'file_size', type: 'integer', required: false },
      { key: 'mime_type', type: 'string', size: 100, required: false },
      { key: 'property_id', type: 'string', size: 36, required: false },
      { key: 'tenant_id', type: 'string', size: 36, required: false },
      { key: 'lease_id', type: 'string', size: 36, required: false },
      { key: 'workorder_id', type: 'string', size: 36, required: false },
      { key: 'expires_on', type: 'datetime', required: false },
      { key: 'tags', type: 'string', size: 500, required: false }, // JSON array of tags
      { key: 'description', type: 'string', size: 1000, required: false },
      { key: 'uploaded_by', type: 'string', size: 36, required: false },
      { key: 'is_public', type: 'boolean', required: false, default: false }
    ],
    indexes: [
      { key: 'document_type_index', type: 'key', attributes: ['document_type'] },
      { key: 'property_id_index', type: 'key', attributes: ['property_id'] },
      { key: 'tenant_id_index', type: 'key', attributes: ['tenant_id'] },
      { key: 'lease_id_index', type: 'key', attributes: ['lease_id'] },
      { key: 'workorder_id_index', type: 'key', attributes: ['workorder_id'] },
      { key: 'expires_on_index', type: 'key', attributes: ['expires_on'] },
      { key: 'name_index', type: 'fulltext', attributes: ['name'] }
    ],
    permissions: {
      read: ['role:super_admin', 'role:admin', 'role:manager', 'users'],
      create: ['role:super_admin', 'role:admin', 'role:manager', 'role:tenant'],
      update: ['role:super_admin', 'role:admin', 'role:manager'],
      delete: ['role:super_admin', 'role:admin']
    }
  }
};

// Export for use in other scripts
export { DATABASE_ID, COLLECTIONS_CONFIG };

/**
 * SETUP INSTRUCTIONS FOR APPWRITE CONSOLE:
 * 
 * 1. Log into your Appwrite Console
 * 2. Navigate to your database: 68b72cd60024e95cea71
 * 3. For each collection in COLLECTIONS_CONFIG:
 *    a) Click "Create Collection"
 *    b) Set Collection ID to the collectionId value
 *    c) Set Name to the name value
 *    d) Add all attributes as specified
 *    e) Create all indexes as specified
 *    f) Set permissions as specified
 * 
 * IMPORTANT NOTES:
 * - Ensure all attribute sizes are exactly as specified
 * - Pay attention to required vs optional attributes
 * - Index types: 'key' = regular index, 'unique' = unique constraint, 'fulltext' = search index
 * - Permission format: ['role:role_name'] or ['users'] for authenticated users
 * - Some collections may reference others - create core collections first
 * 
 * RECOMMENDED CREATION ORDER:
 * 1. USERS (core authentication)
 * 2. PROPERTIES (base entity)
 * 3. UNITS (references properties)
 * 4. TENANTS (references users)
 * 5. LEASES (references properties, units, tenants)
 * 6. WORKORDERS (references properties, units, tenants)
 * 7. PAYMENTS (references tenants, leases, properties)
 * 8. VENDORS
 * 9. VMS collections (CAMERAS, RECORDINGS, MOTION_EVENTS)
 * 10. Access Control collections (ACCESS_DOORS, ACCESS_EVENTS, VISITOR_PASSES)
 * 11. Additional collections (AUDIT_LOGS, RENT_RECORDS, NOTIFICATIONS, DOCUMENTS)
 */