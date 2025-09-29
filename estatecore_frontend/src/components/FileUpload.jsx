import React, { useState, useRef } from 'react';
import Button from './ui/Button';

const FileUpload = ({ 
  onUploadSuccess, 
  onUploadError, 
  propertyId = null, 
  tenantId = null, 
  category = 'general',
  multiple = false,
  accept = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar',
  maxFileSize = 10 * 1024 * 1024, // 10MB
  className = ''
}) => {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    if (file.size > maxFileSize) {
      return `File ${file.name} is too large. Maximum size is ${formatFileSize(maxFileSize)}.`;
    }
    
    if (accept && !isFileTypeAllowed(file.name, accept)) {
      return `File type not allowed for ${file.name}.`;
    }
    
    return null;
  };

  const isFileTypeAllowed = (filename, acceptedTypes) => {
    const fileExt = '.' + filename.split('.').pop().toLowerCase();
    const allowedExts = acceptedTypes.split(',').map(ext => ext.trim());
    return allowedExts.includes(fileExt);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const uploadFiles = async (files) => {
    const fileList = Array.from(files);
    
    // Validate all files first
    for (const file of fileList) {
      const validationError = validateFile(file);
      if (validationError) {
        onUploadError?.(validationError);
        return;
      }
    }

    setUploading(true);

    try {
      if (fileList.length === 1) {
        // Single file upload
        await uploadSingleFile(fileList[0]);
      } else {
        // Multiple file upload
        await uploadMultipleFiles(fileList);
      }
    } catch (error) {
      console.error('Upload error:', error);
      onUploadError?.('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const uploadSingleFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    if (propertyId) formData.append('property_id', propertyId);
    if (tenantId) formData.append('tenant_id', tenantId);
    formData.append('category', category);
    formData.append('description', `Uploaded on ${new Date().toLocaleDateString()}`);

    const response = await fetch('/api/files/upload', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    
    if (result.success) {
      onUploadSuccess?.(result.file);
    } else {
      onUploadError?.(result.error || 'Upload failed');
    }
  };

  const uploadMultipleFiles = async (files) => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    if (propertyId) formData.append('property_id', propertyId);
    if (tenantId) formData.append('tenant_id', tenantId);
    formData.append('category', category);

    const response = await fetch('/api/files/upload-multiple', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    
    const successCount = result.results?.filter(r => r.success).length || 0;
    const totalCount = files.length;
    
    if (successCount > 0) {
      onUploadSuccess?.({
        message: `${successCount}/${totalCount} files uploaded successfully`,
        results: result.results
      });
    }
    
    if (successCount < totalCount) {
      onUploadError?.(`${totalCount - successCount} files failed to upload`);
    }
  };

  const handleFileSelect = (event) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      uploadFiles(files);
    }
    // Reset input value to allow selecting the same file again
    event.target.value = '';
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragOver(false);
    
    const files = event.dataTransfer.files;
    if (files && files.length > 0) {
      uploadFiles(files);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setDragOver(false);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          dragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <div className="space-y-3">
          <div className="text-4xl text-gray-400">
            📁
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-700">
              {uploading ? 'Uploading...' : 'Drop files here or click to upload'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {multiple ? 'You can upload multiple files at once' : 'Upload a single file'}
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Max file size: {formatFileSize(maxFileSize)}
            </p>
          </div>

          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {uploading ? 'Uploading...' : 'Choose Files'}
          </Button>
        </div>
      </div>

      {/* Progress indicator */}
      {uploading && (
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-blue-600 h-2 rounded-full animate-pulse w-1/2"></div>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple={multiple}
        accept={accept}
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
};

export default FileUpload;