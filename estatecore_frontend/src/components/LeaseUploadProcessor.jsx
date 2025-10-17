import React, { useState } from 'react';
import api from '../api';

const LeaseUploadProcessor = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      const allowedTypes = ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (allowedTypes.includes(file.type)) {
        setSelectedFile(file);
        setError('');
      } else {
        setError('Please select a PDF, TXT, DOC, or DOCX file');
        setSelectedFile(null);
      }
    }
  };

  const processLease = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError('');
    setExtractedData(null);

    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await api.upload('/api/ai/process-lease-upload', formData);
      
      if (response.success) {
        setExtractedData(response.data);
      } else {
        setError(response.error || 'Failed to process lease document');
      }
    } catch (error) {
      console.error('Error processing lease:', error);
      setError('Error processing lease document');
    } finally {
      setLoading(false);
    }
  };

  const processWithTextContent = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError('');
    setExtractedData(null);

    try {
      // Read file as text for demonstration
      const fileReader = new FileReader();
      fileReader.onload = async (e) => {
        try {
          const content = e.target.result;
          
          const result = await api.post('/api/ai/process-lease', {
            filename: selectedFile.name,
            content: content
          });
          
          if (result.success) {
            setExtractedData(result.data);
          } else {
            setError(result.error || 'Failed to process lease document');
          }
        } catch (error) {
          console.error('Error processing lease:', error);
          setError('Error processing lease document');
        }
        setLoading(false);
      };

      fileReader.onerror = () => {
        setError('Error reading file');
        setLoading(false);
      };

      fileReader.readAsText(selectedFile);
    } catch (error) {
      console.error('Error processing lease:', error);
      setError('Error processing lease document');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">AI Lease Document Processor</h2>
      
      {/* File Upload Section */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload Lease Document
        </label>
        <input
          type="file"
          accept=".pdf,.txt,.doc,.docx"
          onChange={handleFileSelect}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        {selectedFile && (
          <div className="mt-2 text-sm text-gray-600">
            Selected: {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
          </div>
        )}
      </div>

      {/* Process Buttons */}
      <div className="mb-6 flex gap-4">
        <button
          onClick={processLease}
          disabled={!selectedFile || loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : 'Process with AI (File Upload)'}
        </button>
        
        <button
          onClick={processWithTextContent}
          disabled={!selectedFile || loading}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : 'Process with AI (Text Content)'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Results Display */}
      {extractedData && (
        <div className="bg-gray-50 p-6 rounded-lg">
          <h3 className="text-xl font-semibold mb-4 text-gray-800">Extracted Information</h3>
          
          {/* AI Status Indicator */}
          <div className="mb-4">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              extractedData.ai_status === 'active' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {extractedData.ai_status === 'active' ? '🤖 AI Active' : '⚠️ Fallback Mode'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-700">Tenant Information</h4>
              <p><strong>Name:</strong> {extractedData.tenant_name}</p>
              <p><strong>Email:</strong> {extractedData.tenant_email}</p>
              <p><strong>Phone:</strong> {extractedData.tenant_phone}</p>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-700">Lease Details</h4>
              <p><strong>Start Date:</strong> {extractedData.lease_start}</p>
              <p><strong>End Date:</strong> {extractedData.lease_end}</p>
              <p><strong>Rent Amount:</strong> ${extractedData.rent_amount}</p>
              <p><strong>Security Deposit:</strong> ${extractedData.security_deposit}</p>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-700">Property Information</h4>
              <p><strong>Address:</strong> {extractedData.property_address}</p>
              <p><strong>Unit Number:</strong> {extractedData.unit_number}</p>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-700">Processing Info</h4>
              {extractedData.extracted_text_length && (
                <p><strong>Text Length:</strong> {extractedData.extracted_text_length} characters</p>
              )}
              {extractedData.document_preview && (
                <div className="mt-2">
                  <p><strong>Document Preview:</strong></p>
                  <div className="bg-white p-2 rounded border text-xs max-h-20 overflow-y-auto">
                    {extractedData.document_preview}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* AI Analysis (if available) */}
          {extractedData.ai_analysis && (
            <div className="mt-4">
              <h4 className="font-medium text-gray-700">AI Analysis</h4>
              <div className="bg-white p-3 rounded border text-sm max-h-40 overflow-y-auto">
                {extractedData.ai_analysis}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LeaseUploadProcessor;