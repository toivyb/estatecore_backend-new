import React, { useState, useEffect } from 'react';

const BulkOperationsDashboard = () => {
  const [activeTab, setActiveTab] = useState('operations');
  const [operations, setOperations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  
  const [importForm, setImportForm] = useState({
    entity_type: '',
    file_type: 'csv',
    operation_type: 'import'
  });

  const [updateForm, setUpdateForm] = useState({
    entity_type: '',
    record_ids: '',
    update_data: {}
  });

  const [exportForm, setExportForm] = useState({
    entity_type: '',
    format: 'csv',
    filters: {}
  });

  useEffect(() => {
    fetchOperations();
  }, []);

  const fetchOperations = async () => {
    try {
      const response = await fetch('/api/bulk-operations/operations');
      if (response.ok) {
        const data = await response.json();
        setOperations(data.operations || []);
      }
    } catch (error) {
      console.error('Error fetching operations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    setValidationResult(null);
  };

  const validateFile = async () => {
    if (!selectedFile || !importForm.entity_type) {
      alert('Please select a file and entity type');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('entity_type', importForm.entity_type);
      formData.append('file_type', importForm.file_type);

      const response = await fetch('/api/bulk-operations/validate', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setValidationResult(data);
      } else {
        const errorData = await response.json();
        alert(`Validation failed: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error validating file:', error);
      alert('Failed to validate file');
    }
  };

  const handleImport = async (e) => {
    e.preventDefault();
    
    if (!selectedFile || !importForm.entity_type) {
      alert('Please select a file and entity type');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('entity_type', importForm.entity_type);
      formData.append('file_type', importForm.file_type);
      formData.append('operation_type', importForm.operation_type);

      const response = await fetch('/api/bulk-operations/import', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Import ${data.success ? 'completed successfully' : 'completed with errors'}\nProcessed: ${data.total_processed}\nSuccessful: ${data.successful_count}\nFailed: ${data.failed_count}`);
        
        setShowImportModal(false);
        setSelectedFile(null);
        setValidationResult(null);
        setImportForm({
          entity_type: '',
          file_type: 'csv',
          operation_type: 'import'
        });
        fetchOperations();
      } else {
        const errorData = await response.json();
        alert(`Import failed: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error importing data:', error);
      alert('Failed to import data');
    }
  };

  const handleBulkUpdate = async (e) => {
    e.preventDefault();
    
    if (!updateForm.entity_type || !updateForm.record_ids) {
      alert('Please provide entity type and record IDs');
      return;
    }

    try {
      const record_ids = updateForm.record_ids.split(',').map(id => id.trim()).filter(id => id);
      
      const response = await fetch('/api/bulk-operations/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_type: updateForm.entity_type,
          record_ids: record_ids,
          update_data: updateForm.update_data
        })
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Update ${data.success ? 'completed successfully' : 'completed with errors'}\nProcessed: ${data.total_processed}\nSuccessful: ${data.successful_count}\nFailed: ${data.failed_count}`);
        
        setShowUpdateModal(false);
        setUpdateForm({
          entity_type: '',
          record_ids: '',
          update_data: {}
        });
        fetchOperations();
      } else {
        const errorData = await response.json();
        alert(`Update failed: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error updating data:', error);
      alert('Failed to update data');
    }
  };

  const handleExport = async (e) => {
    e.preventDefault();
    
    if (!exportForm.entity_type) {
      alert('Please select an entity type');
      return;
    }

    try {
      const response = await fetch('/api/bulk-operations/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportForm)
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Export completed successfully\nRecords exported: ${data.total_processed}\nFile path: ${data.output_file_path}`);
        
        setShowExportModal(false);
        setExportForm({
          entity_type: '',
          format: 'csv',
          filters: {}
        });
        fetchOperations();
      } else {
        const errorData = await response.json();
        alert(`Export failed: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error exporting data:', error);
      alert('Failed to export data');
    }
  };

  const downloadTemplate = async (entityType) => {
    try {
      const response = await fetch(`/api/bulk-operations/templates/${entityType}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${entityType}_template.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Error downloading template:', error);
      alert('Failed to download template');
    }
  };

  const cancelOperation = async (operationId) => {
    try {
      const response = await fetch(`/api/bulk-operations/operations/${operationId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        alert('Operation cancelled successfully');
        fetchOperations();
      } else {
        const errorData = await response.json();
        alert(`Failed to cancel operation: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error cancelling operation:', error);
      alert('Failed to cancel operation');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'queued': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      case 'partial_success': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Bulk Operations</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowImportModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            📥 Import Data
          </button>
          <button
            onClick={() => setShowUpdateModal(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
          >
            ✏️ Bulk Update
          </button>
          <button
            onClick={() => setShowExportModal(true)}
            className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700"
          >
            📤 Export Data
          </button>
          <button
            onClick={() => fetchOperations()}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['operations', 'templates'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Operations Tab */}
      {activeTab === 'operations' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Bulk Operations History</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Operation</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Records</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {operations.map((operation) => (
                  <tr key={operation.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{operation.operation_type.toUpperCase()}</div>
                        <div className="text-sm text-gray-500">{operation.entity_type.replace('_', ' ')}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {operation.operation_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(operation.status)}`}>
                        {operation.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${operation.progress_percentage}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-900">{Math.round(operation.progress_percentage)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        <div>Total: {operation.total_records}</div>
                        <div className="text-green-600">✓ {operation.successful_records}</div>
                        {operation.failed_records > 0 && (
                          <div className="text-red-600">✗ {operation.failed_records}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(operation.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex gap-2">
                        {(operation.status === 'queued' || operation.status === 'processing') && (
                          <button
                            onClick={() => cancelOperation(operation.id)}
                            className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                          >
                            Cancel
                          </button>
                        )}
                        <button
                          onClick={() => console.log('View details:', operation)}
                          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                        >
                          Details
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Download CSV Templates</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {['properties', 'tenants', 'maintenance_requests', 'users'].map((entityType) => (
                  <div key={entityType} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">
                      {entityType.replace('_', ' ').split(' ').map(word => 
                        word.charAt(0).toUpperCase() + word.slice(1)
                      ).join(' ')}
                    </h4>
                    <p className="text-sm text-gray-600 mb-4">
                      Template for bulk {entityType.replace('_', ' ')} operations
                    </p>
                    <button
                      onClick={() => downloadTemplate(entityType)}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 w-full"
                    >
                      📥 Download Template
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Bulk Operations Guide</h3>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">📥 Import Operations</h4>
                <p className="text-sm text-gray-600">
                  Upload CSV or JSON files to create multiple records at once. Files are validated before processing.
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">✏️ Bulk Updates</h4>
                <p className="text-sm text-gray-600">
                  Update multiple records with the same values. Provide record IDs and the fields to update.
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">📤 Export Operations</h4>
                <p className="text-sm text-gray-600">
                  Export data to CSV or JSON format with optional filters. Perfect for backups and data analysis.
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">⚠️ Important Notes</h4>
                <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
                  <li>Always validate your data before importing</li>
                  <li>Large operations are processed in chunks for better performance</li>
                  <li>You can cancel operations that are queued or in progress</li>
                  <li>Failed records are logged with detailed error information</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Import Data</h3>
            </div>
            <form onSubmit={handleImport} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Entity Type</label>
                <select
                  value={importForm.entity_type}
                  onChange={(e) => setImportForm({...importForm, entity_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                >
                  <option value="">Select Entity Type</option>
                  <option value="properties">Properties</option>
                  <option value="tenants">Tenants</option>
                  <option value="maintenance_requests">Maintenance Requests</option>
                  <option value="users">Users</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">File Type</label>
                <select
                  value={importForm.file_type}
                  onChange={(e) => setImportForm({...importForm, file_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">File</label>
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept={importForm.file_type === 'csv' ? '.csv' : '.json'}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>

              {selectedFile && importForm.entity_type && (
                <div>
                  <button
                    type="button"
                    onClick={validateFile}
                    className="w-full bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700"
                  >
                    🔍 Validate File
                  </button>
                </div>
              )}

              {validationResult && (
                <div className="bg-gray-50 p-4 rounded-md">
                  <h4 className="font-medium text-gray-900 mb-2">Validation Results</h4>
                  <div className="space-y-2 text-sm">
                    <div>Total Records: {validationResult.total_records}</div>
                    <div className="text-green-600">Valid Records: {validationResult.valid_records}</div>
                    {validationResult.invalid_records > 0 && (
                      <div className="text-red-600">Invalid Records: {validationResult.invalid_records}</div>
                    )}
                    {validationResult.errors.length > 0 && (
                      <div className="text-red-600">
                        <div>Errors:</div>
                        <ul className="list-disc list-inside">
                          {validationResult.errors.slice(0, 3).map((error, idx) => (
                            <li key={idx}>{error.message}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                  disabled={validationResult && !validationResult.is_valid}
                >
                  Import Data
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowImportModal(false);
                    setSelectedFile(null);
                    setValidationResult(null);
                  }}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Update Modal */}
      {showUpdateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Bulk Update</h3>
            </div>
            <form onSubmit={handleBulkUpdate} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Entity Type</label>
                <select
                  value={updateForm.entity_type}
                  onChange={(e) => setUpdateForm({...updateForm, entity_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                >
                  <option value="">Select Entity Type</option>
                  <option value="properties">Properties</option>
                  <option value="tenants">Tenants</option>
                  <option value="maintenance_requests">Maintenance Requests</option>
                  <option value="users">Users</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Record IDs (comma-separated)</label>
                <textarea
                  value={updateForm.record_ids}
                  onChange={(e) => setUpdateForm({...updateForm, record_ids: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  rows="3"
                  placeholder="1, 2, 3, 4, 5"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Update Data (JSON)</label>
                <textarea
                  value={JSON.stringify(updateForm.update_data, null, 2)}
                  onChange={(e) => {
                    try {
                      const data = JSON.parse(e.target.value);
                      setUpdateForm({...updateForm, update_data: data});
                    } catch (err) {
                      // Invalid JSON, but let user continue typing
                    }
                  }}
                  className="w-full p-2 border border-gray-300 rounded-md font-mono text-sm"
                  rows="4"
                  placeholder='{"status": "active", "updated_at": "2024-01-01"}'
                />
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
                >
                  Update Records
                </button>
                <button
                  type="button"
                  onClick={() => setShowUpdateModal(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Export Data</h3>
            </div>
            <form onSubmit={handleExport} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Entity Type</label>
                <select
                  value={exportForm.entity_type}
                  onChange={(e) => setExportForm({...exportForm, entity_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                >
                  <option value="">Select Entity Type</option>
                  <option value="properties">Properties</option>
                  <option value="tenants">Tenants</option>
                  <option value="maintenance_requests">Maintenance Requests</option>
                  <option value="users">Users</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Export Format</label>
                <select
                  value={exportForm.format}
                  onChange={(e) => setExportForm({...exportForm, format: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Filters (JSON, optional)</label>
                <textarea
                  value={JSON.stringify(exportForm.filters, null, 2)}
                  onChange={(e) => {
                    try {
                      const filters = JSON.parse(e.target.value);
                      setExportForm({...exportForm, filters});
                    } catch (err) {
                      // Invalid JSON, but let user continue typing
                    }
                  }}
                  className="w-full p-2 border border-gray-300 rounded-md font-mono text-sm"
                  rows="3"
                  placeholder='{"status": "active", "created_after": "2024-01-01"}'
                />
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700"
                >
                  Export Data
                </button>
                <button
                  type="button"
                  onClick={() => setShowExportModal(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkOperationsDashboard;