/**
 * Offline Storage Service for EstateCore Mobile PWA
 * Advanced IndexedDB management with sync capabilities
 */

class OfflineStorageService {
  constructor() {
    this.dbName = 'EstateCoreMobile';
    this.dbVersion = 1;
    this.db = null;
    this.isOnline = navigator.onLine;
    
    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.triggerSync();
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
    
    this.init();
  }

  async init() {
    try {
      this.db = await this.openDatabase();
      console.log('OfflineStorageService initialized');
    } catch (error) {
      console.error('Failed to initialize OfflineStorageService:', error);
    }
  }

  openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Properties store
        if (!db.objectStoreNames.contains('properties')) {
          const propertyStore = db.createObjectStore('properties', { keyPath: 'id' });
          propertyStore.createIndex('status', 'status', { unique: false });
          propertyStore.createIndex('lastModified', 'lastModified', { unique: false });
        }

        // Tenants store
        if (!db.objectStoreNames.contains('tenants')) {
          const tenantStore = db.createObjectStore('tenants', { keyPath: 'id' });
          tenantStore.createIndex('propertyId', 'propertyId', { unique: false });
          tenantStore.createIndex('status', 'status', { unique: false });
        }

        // Maintenance requests store
        if (!db.objectStoreNames.contains('maintenance')) {
          const maintenanceStore = db.createObjectStore('maintenance', { keyPath: 'id' });
          maintenanceStore.createIndex('propertyId', 'propertyId', { unique: false });
          maintenanceStore.createIndex('status', 'status', { unique: false });
          maintenanceStore.createIndex('priority', 'priority', { unique: false });
        }

        // Inspections store
        if (!db.objectStoreNames.contains('inspections')) {
          const inspectionStore = db.createObjectStore('inspections', { keyPath: 'id' });
          inspectionStore.createIndex('propertyId', 'propertyId', { unique: false });
          inspectionStore.createIndex('date', 'date', { unique: false });
          inspectionStore.createIndex('type', 'type', { unique: false });
        }

        // Photos/attachments store
        if (!db.objectStoreNames.contains('attachments')) {
          const attachmentStore = db.createObjectStore('attachments', { keyPath: 'id' });
          attachmentStore.createIndex('entityType', 'entityType', { unique: false });
          attachmentStore.createIndex('entityId', 'entityId', { unique: false });
        }

        // Messages store for collaboration
        if (!db.objectStoreNames.contains('messages')) {
          const messageStore = db.createObjectStore('messages', { keyPath: 'id' });
          messageStore.createIndex('channelId', 'channelId', { unique: false });
          messageStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Pending sync operations
        if (!db.objectStoreNames.contains('pendingSync')) {
          const syncStore = db.createObjectStore('pendingSync', { keyPath: 'id' });
          syncStore.createIndex('operation', 'operation', { unique: false });
          syncStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Cache metadata
        if (!db.objectStoreNames.contains('cacheMetadata')) {
          const metaStore = db.createObjectStore('cacheMetadata', { keyPath: 'key' });
          metaStore.createIndex('expiry', 'expiry', { unique: false });
        }
      };
    });
  }

  // Generic CRUD operations
  async save(storeName, data) {
    try {
      if (!this.db) await this.init();
      
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      
      // Add offline metadata
      const enrichedData = {
        ...data,
        lastModified: new Date().toISOString(),
        isOffline: !this.isOnline,
        needsSync: !this.isOnline || data.needsSync
      };
      
      const result = await this.promisifyRequest(store.put(enrichedData));
      
      // Queue for sync if offline
      if (!this.isOnline) {
        await this.queueForSync('save', storeName, enrichedData);
      }
      
      return result;
    } catch (error) {
      console.error(`Error saving to ${storeName}:`, error);
      throw error;
    }
  }

  async get(storeName, id) {
    try {
      if (!this.db) await this.init();
      
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      
      return await this.promisifyRequest(store.get(id));
    } catch (error) {
      console.error(`Error getting from ${storeName}:`, error);
      return null;
    }
  }

  async getAll(storeName, indexName = null, value = null) {
    try {
      if (!this.db) await this.init();
      
      const transaction = this.db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      
      if (indexName && value !== null) {
        const index = store.index(indexName);
        return await this.promisifyRequest(index.getAll(value));
      } else {
        return await this.promisifyRequest(store.getAll());
      }
    } catch (error) {
      console.error(`Error getting all from ${storeName}:`, error);
      return [];
    }
  }

  async delete(storeName, id) {
    try {
      if (!this.db) await this.init();
      
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      
      const result = await this.promisifyRequest(store.delete(id));
      
      // Queue for sync if offline
      if (!this.isOnline) {
        await this.queueForSync('delete', storeName, { id });
      }
      
      return result;
    } catch (error) {
      console.error(`Error deleting from ${storeName}:`, error);
      throw error;
    }
  }

  // Property-specific operations
  async saveProperty(property) {
    return this.save('properties', property);
  }

  async getProperty(id) {
    return this.get('properties', id);
  }

  async getAllProperties() {
    return this.getAll('properties');
  }

  async getPropertiesByStatus(status) {
    return this.getAll('properties', 'status', status);
  }

  // Tenant-specific operations
  async saveTenant(tenant) {
    return this.save('tenants', tenant);
  }

  async getTenant(id) {
    return this.get('tenants', id);
  }

  async getTenantsByProperty(propertyId) {
    return this.getAll('tenants', 'propertyId', propertyId);
  }

  // Maintenance-specific operations
  async saveMaintenanceRequest(request) {
    return this.save('maintenance', request);
  }

  async getMaintenanceRequest(id) {
    return this.get('maintenance', id);
  }

  async getMaintenanceByProperty(propertyId) {
    return this.getAll('maintenance', 'propertyId', propertyId);
  }

  async getMaintenanceByStatus(status) {
    return this.getAll('maintenance', 'status', status);
  }

  // Inspection-specific operations
  async saveInspection(inspection) {
    return this.save('inspections', inspection);
  }

  async getInspection(id) {
    return this.get('inspections', id);
  }

  async getInspectionsByProperty(propertyId) {
    return this.getAll('inspections', 'propertyId', propertyId);
  }

  // Attachment operations
  async saveAttachment(attachment) {
    try {
      // Convert File/Blob to base64 for storage
      if (attachment.file instanceof File || attachment.file instanceof Blob) {
        attachment.data = await this.fileToBase64(attachment.file);
        attachment.size = attachment.file.size;
        attachment.type = attachment.file.type;
        attachment.name = attachment.file.name || 'attachment';
        delete attachment.file; // Remove the file object
      }
      
      return this.save('attachments', attachment);
    } catch (error) {
      console.error('Error saving attachment:', error);
      throw error;
    }
  }

  async getAttachment(id) {
    const attachment = await this.get('attachments', id);
    
    // Convert base64 back to blob if needed
    if (attachment && attachment.data && attachment.type) {
      attachment.blob = this.base64ToBlob(attachment.data, attachment.type);
    }
    
    return attachment;
  }

  async getAttachmentsByEntity(entityType, entityId) {
    const attachments = await this.getAll('attachments', 'entityType', entityType);
    return attachments.filter(att => att.entityId === entityId);
  }

  // Message operations for collaboration
  async saveMessage(message) {
    return this.save('messages', message);
  }

  async getMessagesByChannel(channelId) {
    return this.getAll('messages', 'channelId', channelId);
  }

  // Sync operations
  async queueForSync(operation, storeName, data) {
    try {
      const syncItem = {
        id: `${operation}_${storeName}_${data.id}_${Date.now()}`,
        operation,
        storeName,
        data,
        timestamp: new Date().toISOString(),
        retryCount: 0
      };
      
      return this.save('pendingSync', syncItem);
    } catch (error) {
      console.error('Error queuing for sync:', error);
    }
  }

  async getPendingSyncItems() {
    return this.getAll('pendingSync');
  }

  async removeSyncItem(id) {
    return this.delete('pendingSync', id);
  }

  async triggerSync() {
    if (!this.isOnline) return;
    
    try {
      const pendingItems = await this.getPendingSyncItems();
      console.log(`Syncing ${pendingItems.length} pending items`);
      
      for (const item of pendingItems) {
        try {
          await this.syncItem(item);
          await this.removeSyncItem(item.id);
        } catch (error) {
          console.error('Sync item failed:', item.id, error);
          
          // Increment retry count
          item.retryCount = (item.retryCount || 0) + 1;
          
          // Remove if too many retries
          if (item.retryCount > 3) {
            await this.removeSyncItem(item.id);
          } else {
            await this.save('pendingSync', item);
          }
        }
      }
    } catch (error) {
      console.error('Sync process failed:', error);
    }
  }

  async syncItem(item) {
    const { operation, storeName, data } = item;
    
    switch (operation) {
      case 'save':
        if (storeName === 'properties') {
          await this.syncProperty(data);
        } else if (storeName === 'maintenance') {
          await this.syncMaintenanceRequest(data);
        } else if (storeName === 'inspections') {
          await this.syncInspection(data);
        }
        break;
        
      case 'delete':
        await this.syncDelete(storeName, data.id);
        break;
    }
  }

  async syncProperty(property) {
    const response = await fetch('/api/properties/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(property)
    });
    
    if (!response.ok) {
      throw new Error(`Sync failed: ${response.statusText}`);
    }
    
    const synced = await response.json();
    
    // Update local data with server response
    if (synced.success && synced.property) {
      await this.save('properties', { ...synced.property, needsSync: false });
    }
  }

  async syncMaintenanceRequest(request) {
    const response = await fetch('/api/maintenance/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      throw new Error(`Sync failed: ${response.statusText}`);
    }
    
    const synced = await response.json();
    
    if (synced.success && synced.maintenance) {
      await this.save('maintenance', { ...synced.maintenance, needsSync: false });
    }
  }

  async syncInspection(inspection) {
    const response = await fetch('/api/inspections/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inspection)
    });
    
    if (!response.ok) {
      throw new Error(`Sync failed: ${response.statusText}`);
    }
    
    const synced = await response.json();
    
    if (synced.success && synced.inspection) {
      await this.save('inspections', { ...synced.inspection, needsSync: false });
    }
  }

  async syncDelete(storeName, id) {
    const response = await fetch(`/api/${storeName}/${id}`, {
      method: 'DELETE'
    });
    
    if (!response.ok && response.status !== 404) {
      throw new Error(`Delete sync failed: ${response.statusText}`);
    }
  }

  // Cache management
  async setCacheItem(key, data, ttlMinutes = 60) {
    const expiryTime = new Date(Date.now() + (ttlMinutes * 60 * 1000));
    
    const cacheItem = {
      key,
      data,
      expiry: expiryTime.toISOString(),
      cached: new Date().toISOString()
    };
    
    return this.save('cacheMetadata', cacheItem);
  }

  async getCacheItem(key) {
    const cacheItem = await this.get('cacheMetadata', key);
    
    if (!cacheItem) return null;
    
    // Check if expired
    if (new Date() > new Date(cacheItem.expiry)) {
      await this.delete('cacheMetadata', key);
      return null;
    }
    
    return cacheItem.data;
  }

  async clearExpiredCache() {
    try {
      const transaction = this.db.transaction(['cacheMetadata'], 'readwrite');
      const store = transaction.objectStore('cacheMetadata');
      const index = store.index('expiry');
      
      const now = new Date().toISOString();
      const range = IDBKeyRange.upperBound(now);
      
      const request = index.openCursor(range);
      
      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        }
      };
    } catch (error) {
      console.error('Error clearing expired cache:', error);
    }
  }

  // Utility methods
  promisifyRequest(request) {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  }

  // Database statistics
  async getStorageStats() {
    const stats = {};
    
    const storeNames = ['properties', 'tenants', 'maintenance', 'inspections', 'attachments', 'messages'];
    
    for (const storeName of storeNames) {
      const items = await this.getAll(storeName);
      stats[storeName] = {
        count: items.length,
        needsSync: items.filter(item => item.needsSync).length
      };
    }
    
    const pendingSync = await this.getPendingSyncItems();
    stats.pendingSync = pendingSync.length;
    
    return stats;
  }

  // Clear all data (for testing/reset)
  async clearAllData() {
    const storeNames = [
      'properties', 'tenants', 'maintenance', 'inspections', 
      'attachments', 'messages', 'pendingSync', 'cacheMetadata'
    ];
    
    for (const storeName of storeNames) {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      await this.promisifyRequest(store.clear());
    }
  }
}

// Export singleton instance
const offlineStorage = new OfflineStorageService();
export default offlineStorage;