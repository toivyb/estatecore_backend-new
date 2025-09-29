import React, { useState, useEffect, useRef } from 'react';
import { Card } from './ui/Card';
import Button from './ui/Button';
import Modal from './ui/Modal';
import Toast from './ui/Toast';

const DocumentManager = ({ propertyId = null, tenantId = null, category = null }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingMultiple, setUploadingMultiple] = useState(false);
  const [filter, setFilter] = useState({
    category: category || 'all',
    search: ''
  });
  const [storageStats, setStorageStats] = useState(null);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [showArchiveModal, setShowArchiveModal] = useState(false);
  const [toast, setToast] = useState(null);
  
  const fileInputRef = useRef(null);
  const multipleFileInputRef = useRef(null);

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'documents', label: 'Documents' },
    { value: 'images', label: 'Images' },
    { value: 'archives', label: 'Archives' },
    { value: 'general', label: 'General' }
  ];

  // Fetch documents
  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (propertyId) params.append('property_id', propertyId);
      if (tenantId) params.append('tenant_id', tenantId);
      if (filter.category !== 'all') params.append('category', filter.category);

      const response = await fetch(`/api/files/documents?${params}`);
      const data = await response.json();
      
      let filteredData = data;
      if (filter.search) {
        filteredData = data.filter(doc => 
          doc.name.toLowerCase().includes(filter.search.toLowerCase()) ||
          (doc.description && doc.description.toLowerCase().includes(filter.search.toLowerCase()))
        );
      }
      
      setDocuments(filteredData);
    } catch (error) {
      console.error('Error fetching documents:', error);
      showToast('Failed to fetch documents', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch storage statistics
  const fetchStorageStats = async () => {
    try {
      const response = await fetch('/api/files/storage-stats');
      const data = await response.json();
      setStorageStats(data);
    } catch (error) {
      console.error('Error fetching storage stats:', error);
    }
  };

  // Upload single file
  const uploadSingleFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    if (propertyId) formData.append('property_id', propertyId);
    if (tenantId) formData.append('tenant_id', tenantId);
    formData.append('category', filter.category === 'all' ? 'general' : filter.category);
    formData.append('description', `Uploaded on ${new Date().toLocaleDateString()}`);

    try {
      const response = await fetch('/api/files/upload', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (result.success) {
        showToast('File uploaded successfully', 'success');
        fetchDocuments();
        fetchStorageStats();
        return true;
      } else {
        showToast(result.error || 'Upload failed', 'error');
        return false;
      }
    } catch (error) {
      console.error('Upload error:', error);
      showToast('Upload failed', 'error');
      return false;
    }
  };

  // Upload multiple files
  const uploadMultipleFiles = async () => {
    if (selectedFiles.length === 0) return;

    setUploadingMultiple(true);
    setUploadProgress(0);

    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });
    
    if (propertyId) formData.append('property_id', propertyId);
    if (tenantId) formData.append('tenant_id', tenantId);
    formData.append('category', filter.category === 'all' ? 'general' : filter.category);

    try {
      const response = await fetch('/api/files/upload-multiple', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      
      const successCount = result.results?.filter(r => r.success).length || 0;
      const totalCount = selectedFiles.length;
      
      if (successCount > 0) {
        showToast(`${successCount}/${totalCount} files uploaded successfully`, 'success');
        fetchDocuments();
        fetchStorageStats();
      }
      
      if (successCount < totalCount) {
        showToast(`${totalCount - successCount} files failed to upload`, 'error');
      }

    } catch (error) {
      console.error('Multiple upload error:', error);
      showToast('Upload failed', 'error');
    } finally {
      setUploadingMultiple(false);
      setUploadProgress(0);
      setSelectedFiles([]);
      setUploadModalOpen(false);
    }
  };

  // Delete document
  const deleteDocument = async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      const response = await fetch(`/api/files/documents/${docId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        showToast('Document deleted successfully', 'success');
        fetchDocuments();
        fetchStorageStats();
      } else {
        showToast('Failed to delete document', 'error');
      }
    } catch (error) {
      console.error('Delete error:', error);
      showToast('Delete failed', 'error');
    }
  };

  // Create archive of selected documents
  const createArchive = async () => {
    if (selectedDocs.length === 0) return;

    try {
      const response = await fetch('/api/files/create-archive', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_ids: selectedDocs
        })
      });

      const result = await response.json();
      if (result.success) {
        showToast('Archive created successfully', 'success');
        window.open(result.download_url, '_blank');
      } else {
        showToast(result.error || 'Failed to create archive', 'error');
      }
    } catch (error) {
      console.error('Archive creation error:', error);
      showToast('Failed to create archive', 'error');
    } finally {
      setShowArchiveModal(false);
      setSelectedDocs([]);
    }
  };

  // Handle file input change
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
    if (files.length === 1) {
      uploadSingleFile(files[0]);
    } else {
      setUploadModalOpen(true);
    }
  };

  // Show toast notification
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Get file icon
  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const iconMap = {
      pdf: '📄', doc: '📝', docx: '📝', xls: '📊', xlsx: '📊',
      ppt: '📈', pptx: '📈', txt: '📋', jpg: '🖼️', jpeg: '🖼️',
      png: '🖼️', gif: '🖼️', zip: '📦', rar: '📦'
    };
    return iconMap[ext] || '📄';
  };

  useEffect(() => {
    fetchDocuments();
    fetchStorageStats();
  }, [propertyId, tenantId, filter.category]);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchDocuments();
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [filter.search]);

  return (
    <div className="space-y-6">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Document Manager</h2>
          <p className="text-gray-600">Upload, organize, and manage your documents</p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={() => fileInputRef.current?.click()}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Upload Files
          </Button>
          
          {selectedDocs.length > 0 && (
            <Button
              onClick={() => setShowArchiveModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              Create Archive ({selectedDocs.length})
            </Button>
          )}
        </div>
      </div>

      {/* Storage Statistics */}
      {storageStats && (
        <Card className="p-4">
          <h3 className="text-lg font-semibold mb-3">Storage Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{storageStats.total_files}</div>
              <div className="text-sm text-gray-600">Total Files</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{storageStats.total_size_mb} MB</div>
              <div className="text-sm text-gray-600">Total Size</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {storageStats.categories?.documents?.files || 0}
              </div>
              <div className="text-sm text-gray-600">Documents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {storageStats.categories?.images?.files || 0}
              </div>
              <div className="text-sm text-gray-600">Images</div>
            </div>
          </div>
        </Card>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={filter.category}
              onChange={(e) => setFilter({ ...filter, category: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {categories.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              type="text"
              placeholder="Search documents..."
              value={filter.search}
              onChange={(e) => setFilter({ ...filter, search: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </Card>

      {/* Documents List */}
      <Card className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">
            Documents ({documents.length})
          </h3>
          
          {documents.length > 0 && (
            <Button
              onClick={() => {
                if (selectedDocs.length === documents.length) {
                  setSelectedDocs([]);
                } else {
                  setSelectedDocs(documents.map(doc => doc.id));
                }
              }}
              variant="outline"
              size="sm"
            >
              {selectedDocs.length === documents.length ? 'Deselect All' : 'Select All'}
            </Button>
          )}
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-6xl mb-4">📁</div>
            <p className="text-gray-600">No documents found</p>
            <p className="text-sm text-gray-500 mt-2">Upload some files to get started</p>
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className={`flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 ${
                  selectedDocs.includes(doc.id) ? 'bg-blue-50 border-blue-200' : 'bg-white'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={selectedDocs.includes(doc.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedDocs([...selectedDocs, doc.id]);
                      } else {
                        setSelectedDocs(selectedDocs.filter(id => id !== doc.id));
                      }
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  
                  <div className="text-2xl">
                    {getFileIcon(doc.name)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {doc.name}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span className="capitalize">{doc.category}</span>
                      {doc.uploaded_by_name && <span>by {doc.uploaded_by_name}</span>}
                      <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                    </div>
                    {doc.description && (
                      <p className="text-xs text-gray-600 mt-1 truncate">
                        {doc.description}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    onClick={() => window.open(doc.download_url, '_blank')}
                    variant="outline"
                    size="sm"
                  >
                    Download
                  </Button>
                  
                  <Button
                    onClick={() => deleteDocument(doc.id)}
                    variant="outline"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileSelect}
        className="hidden"
        accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar"
      />

      {/* Upload Modal */}
      <Modal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        title="Upload Multiple Files"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            {selectedFiles.length} file(s) selected for upload
          </p>
          
          <div className="max-h-48 overflow-y-auto">
            {selectedFiles.map((file, index) => (
              <div key={index} className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded">
                <span className="text-sm truncate">{file.name}</span>
                <span className="text-xs text-gray-500">{formatFileSize(file.size)}</span>
              </div>
            ))}
          </div>

          {uploadingMultiple && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button
              onClick={() => {
                setUploadModalOpen(false);
                setSelectedFiles([]);
              }}
              variant="outline"
              disabled={uploadingMultiple}
            >
              Cancel
            </Button>
            <Button
              onClick={uploadMultipleFiles}
              disabled={uploadingMultiple}
            >
              {uploadingMultiple ? 'Uploading...' : 'Upload All'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Archive Modal */}
      <Modal
        isOpen={showArchiveModal}
        onClose={() => setShowArchiveModal(false)}
        title="Create Archive"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Create a downloadable archive containing {selectedDocs.length} selected document(s)?
          </p>
          
          <div className="flex justify-end space-x-2">
            <Button
              onClick={() => setShowArchiveModal(false)}
              variant="outline"
            >
              Cancel
            </Button>
            <Button onClick={createArchive}>
              Create Archive
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DocumentManager;