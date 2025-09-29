import React, { useState, useEffect, useRef } from 'react'
import ResponsiveTable from '../components/ResponsiveTable'
import { ResponsiveModal } from '../components/ResponsiveDashboard'

const DocumentManager = () => {
  const [documents, setDocuments] = useState([])
  const [folders, setFolders] = useState([])
  const [currentFolder, setCurrentFolder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showCreateFolderModal, setShowCreateFolderModal] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])
  const [uploadProgress, setUploadProgress] = useState({})
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [viewMode, setViewMode] = useState('list') // 'list' or 'grid'
  const [selectedDocuments, setSelectedDocuments] = useState([])
  const fileInputRef = useRef(null)

  useEffect(() => {
    fetchDocuments()
    fetchFolders()
  }, [currentFolder])

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`/api/documents${currentFolder ? `?folder=${currentFolder}` : ''}`)
      const data = await response.json()
      setDocuments(data)
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchFolders = async () => {
    try {
      const response = await fetch('/api/documents/folders')
      const data = await response.json()
      setFolders(data)
    } catch (error) {
      console.error('Error fetching folders:', error)
    }
  }

  const handleFileUpload = async (files) => {
    const formData = new FormData()
    
    Array.from(files).forEach((file, index) => {
      formData.append(`files`, file)
      setUploadProgress(prev => ({ ...prev, [file.name]: 0 }))
    })
    
    if (currentFolder) {
      formData.append('folder_id', currentFolder)
    }

    try {
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          // Update progress for all files (simplified)
          setUploadProgress(prev => {
            const updated = { ...prev }
            Object.keys(updated).forEach(key => {
              updated[key] = progress
            })
            return updated
          })
        }
      })

      if (response.ok) {
        setShowUploadModal(false)
        setSelectedFiles([])
        setUploadProgress({})
        fetchDocuments()
        alert('Files uploaded successfully!')
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed')
    }
  }

  const createFolder = async (folderName) => {
    try {
      const response = await fetch('/api/documents/folders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: folderName, 
          parent_id: currentFolder 
        })
      })

      if (response.ok) {
        setShowCreateFolderModal(false)
        fetchFolders()
        fetchDocuments()
      }
    } catch (error) {
      console.error('Error creating folder:', error)
    }
  }

  const deleteDocument = async (documentId) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      const response = await fetch(`/api/documents/${documentId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        fetchDocuments()
      }
    } catch (error) {
      console.error('Error deleting document:', error)
    }
  }

  const downloadDocument = async (document) => {
    try {
      const response = await fetch(`/api/documents/${document.id}/download`)
      const blob = await response.blob()
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = document.name
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download error:', error)
    }
  }

  const shareDocument = async (document) => {
    try {
      const response = await fetch(`/api/documents/${document.id}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          expires_in: 7 * 24 * 60 * 60, // 7 days
          permissions: ['view', 'download']
        })
      })

      const data = await response.json()
      
      // Copy share link to clipboard
      navigator.clipboard.writeText(data.share_url)
      alert('Share link copied to clipboard!')
    } catch (error) {
      console.error('Share error:', error)
    }
  }

  const bulkAction = async (action) => {
    if (selectedDocuments.length === 0) return

    const confirmMessage = action === 'delete' 
      ? 'Are you sure you want to delete the selected documents?'
      : `Are you sure you want to ${action} the selected documents?`

    if (!confirm(confirmMessage)) return

    try {
      const response = await fetch(`/api/documents/bulk/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: selectedDocuments })
      })

      if (response.ok) {
        setSelectedDocuments([])
        fetchDocuments()
      }
    } catch (error) {
      console.error(`Bulk ${action} error:`, error)
    }
  }

  const getFileIcon = (fileType) => {
    const iconMap = {
      'pdf': '📄',
      'doc': '📝',
      'docx': '📝',
      'xls': '📊',
      'xlsx': '📊',
      'ppt': '📈',
      'pptx': '📈',
      'jpg': '🖼️',
      'jpeg': '🖼️',
      'png': '🖼️',
      'gif': '🖼️',
      'txt': '📋',
      'zip': '📦',
      'folder': '📁'
    }
    return iconMap[fileType?.toLowerCase()] || '📄'
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === 'all' || doc.type === filterType
    return matchesSearch && matchesType
  })

  const documentColumns = [
    {
      key: 'name',
      label: 'Name',
      sortable: true,
      render: (value, doc) => (
        <div className="flex items-center">
          <span className="text-2xl mr-3">{getFileIcon(doc.type)}</span>
          <div>
            <div className="text-sm font-medium text-gray-900">{value}</div>
            <div className="text-sm text-gray-500">{doc.description}</div>
          </div>
        </div>
      )
    },
    {
      key: 'type',
      label: 'Type',
      sortable: true,
      render: (value) => (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          {value?.toUpperCase()}
        </span>
      )
    },
    {
      key: 'size',
      label: 'Size',
      sortable: true,
      render: (value) => formatFileSize(value)
    },
    {
      key: 'uploaded_at',
      label: 'Uploaded',
      sortable: true,
      render: (value) => new Date(value).toLocaleDateString()
    },
    {
      key: 'uploaded_by',
      label: 'Uploaded By',
      sortable: true
    }
  ]

  const documentActions = (document) => (
    <div className="flex space-x-2">
      <button
        onClick={() => downloadDocument(document)}
        className="text-blue-600 hover:text-blue-900 text-sm"
        title="Download"
      >
        ⬇️
      </button>
      <button
        onClick={() => shareDocument(document)}
        className="text-green-600 hover:text-green-900 text-sm"
        title="Share"
      >
        🔗
      </button>
      <button
        onClick={() => deleteDocument(document.id)}
        className="text-red-600 hover:text-red-900 text-sm"
        title="Delete"
      >
        🗑️
      </button>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <h1 className="text-2xl font-bold text-gray-900">Document Management</h1>
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
          <button
            onClick={() => setShowCreateFolderModal(true)}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
          >
            📁 New Folder
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            📤 Upload Files
          </button>
        </div>
      </div>

      {/* Breadcrumb and Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          {/* Breadcrumb */}
          <nav className="flex" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2">
              <li>
                <button
                  onClick={() => setCurrentFolder(null)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  🏠 Home
                </button>
              </li>
              {currentFolder && (
                <>
                  <span className="text-gray-500">/</span>
                  <li className="text-gray-900 font-medium">Current Folder</li>
                </>
              )}
            </ol>
          </nav>

          {/* Filters and View Controls */}
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="all">All Types</option>
              <option value="pdf">PDF</option>
              <option value="doc">Documents</option>
              <option value="image">Images</option>
              <option value="spreadsheet">Spreadsheets</option>
            </select>

            <div className="flex rounded-md shadow-sm">
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 text-sm font-medium rounded-l-md border ${
                  viewMode === 'list'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                📋 List
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 text-sm font-medium rounded-r-md border-t border-r border-b ${
                  viewMode === 'grid'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                ⊞ Grid
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedDocuments.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
            <span className="text-sm text-blue-800">
              {selectedDocuments.length} document(s) selected
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => bulkAction('download')}
                className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
              >
                Download
              </button>
              <button
                onClick={() => bulkAction('delete')}
                className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Documents Table/Grid */}
      {viewMode === 'list' ? (
        <ResponsiveTable
          data={filteredDocuments}
          columns={documentColumns}
          title="Documents"
          actions={documentActions}
          searchable={true}
          pagination={true}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          {filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => downloadDocument(doc)}
            >
              <div className="text-center">
                <div className="text-4xl mb-2">{getFileIcon(doc.type)}</div>
                <h3 className="text-sm font-medium text-gray-900 truncate" title={doc.name}>
                  {doc.name}
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  {formatFileSize(doc.size)}
                </p>
                <div className="mt-2 flex justify-center space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      shareDocument(doc)
                    }}
                    className="text-green-600 hover:text-green-800"
                    title="Share"
                  >
                    🔗
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteDocument(doc.id)
                    }}
                    className="text-red-600 hover:text-red-800"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <ResponsiveModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        title="Upload Documents"
        size="large"
      >
        <div className="space-y-4">
          <div
            className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
            onDrop={(e) => {
              e.preventDefault()
              const files = Array.from(e.dataTransfer.files)
              setSelectedFiles(files)
            }}
            onDragOver={(e) => e.preventDefault()}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
              accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.txt,.zip"
            />
            <div className="text-4xl mb-4">📤</div>
            <p className="text-lg font-medium text-gray-900">
              Drop files here or click to select
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Supports: PDF, DOC, XLS, PPT, Images, and more
            </p>
          </div>

          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Selected Files:</h4>
              {selectedFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm text-gray-900">{file.name}</span>
                  <span className="text-xs text-gray-500">{formatFileSize(file.size)}</span>
                </div>
              ))}
            </div>
          )}

          {Object.keys(uploadProgress).length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Upload Progress:</h4>
              {Object.entries(uploadProgress).map(([filename, progress]) => (
                <div key={filename} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{filename}</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setShowUploadModal(false)}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={() => handleFileUpload(selectedFiles)}
              disabled={selectedFiles.length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              Upload Files
            </button>
          </div>
        </div>
      </ResponsiveModal>

      {/* Create Folder Modal */}
      <ResponsiveModal
        isOpen={showCreateFolderModal}
        onClose={() => setShowCreateFolderModal(false)}
        title="Create New Folder"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault()
            const formData = new FormData(e.target)
            createFolder(formData.get('folderName'))
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Folder Name
            </label>
            <input
              name="folderName"
              type="text"
              required
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter folder name"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setShowCreateFolderModal(false)}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Create Folder
            </button>
          </div>
        </form>
      </ResponsiveModal>
    </div>
  )
}

export default DocumentManager