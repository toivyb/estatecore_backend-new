import { useState, useEffect } from "react";
import FileUpload from "../FileUpload";

export default function DocumentVault({ propertyId }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (propertyId) params.append('property_id', propertyId);
      
      const res = await fetch(`/api/files/documents?${params}`);
      const data = await res.json();
      setDocs(data);
    } catch (error) {
      console.error('Error fetching documents:', error);
      setDocs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = (result) => {
    setUploadSuccess('Document uploaded successfully!');
    setUploadError(null);
    fetchDocs(); // Refresh the list
    
    // Clear success message after 3 seconds
    setTimeout(() => setUploadSuccess(null), 3000);
  };

  const handleUploadError = (error) => {
    setUploadError(error);
    setUploadSuccess(null);
    
    // Clear error message after 5 seconds
    setTimeout(() => setUploadError(null), 5000);
  };

  const deleteDocument = async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      const response = await fetch(`/api/files/documents/${docId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setUploadSuccess('Document deleted successfully!');
        fetchDocs();
        setTimeout(() => setUploadSuccess(null), 3000);
      } else {
        setUploadError('Failed to delete document');
        setTimeout(() => setUploadError(null), 5000);
      }
    } catch (error) {
      console.error('Delete error:', error);
      setUploadError('Delete failed');
      setTimeout(() => setUploadError(null), 5000);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

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
    fetchDocs(); 
  }, [propertyId]);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Document Vault</h2>
      
      {/* Success/Error Messages */}
      {uploadSuccess && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {uploadSuccess}
        </div>
      )}
      
      {uploadError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {uploadError}
        </div>
      )}

      {/* File Upload Component */}
      <div className="mb-6">
        <FileUpload
          propertyId={propertyId}
          category="documents"
          multiple={true}
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
          className="mb-4"
        />
      </div>

      {/* Documents List */}
      <div>
        <h3 className="text-lg font-semibold mb-3">
          Uploaded Documents ({docs.length})
        </h3>
        
        {loading ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading documents...</p>
          </div>
        ) : docs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📁</div>
            <p>No documents uploaded yet</p>
            <p className="text-sm mt-1">Upload some files to get started</p>
          </div>
        ) : (
          <div className="space-y-2">
            {docs.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-center space-x-3">
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
                  <button
                    onClick={() => window.open(doc.download_url, '_blank')}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Download
                  </button>
                  
                  <button
                    onClick={() => deleteDocument(doc.id)}
                    className="text-red-600 hover:text-red-800 text-sm font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}