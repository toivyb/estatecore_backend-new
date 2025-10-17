import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import LeaseUploadProcessor from '../components/LeaseUploadProcessor';

const DocumentProcessingDashboard = () => {
  const [activeTab, setActiveTab] = useState('single');
  const [documentText, setDocumentText] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [extractionResult, setExtractionResult] = useState(null);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [batchDocuments, setBatchDocuments] = useState([]);
  const [batchResults, setBatchResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const tabs = [
    { id: 'single', label: 'Document Analysis', icon: '📄' },
    { id: 'lease', label: 'Lease Analysis', icon: '📋' },
    { id: 'ai-lease', label: 'AI Lease Processor', icon: '🤖' },
    { id: 'extract', label: 'Entity Extraction', icon: '🔍' },
    { id: 'risk', label: 'Risk Assessment', icon: '⚠️' },
    { id: 'batch', label: 'Batch Processing', icon: '📚' }
  ];

  const processDocument = async () => {
    if (!documentText.trim()) {
      alert('Please enter document text to analyze');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/document/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: documentText,
          document_id: `doc_${Date.now()}`
        })
      });

      const result = await response.json();
      if (result.success) {
        setAnalysisResult(result.analysis);
      } else {
        alert(result.error || 'Failed to process document');
      }
    } catch (error) {
      console.error('Error processing document:', error);
      alert('Error processing document');
    } finally {
      setLoading(false);
    }
  };

  const analyzeLease = async () => {
    if (!documentText.trim()) {
      alert('Please enter lease document text to analyze');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/document/analyze-lease', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: documentText,
          property_id: 1,
          tenant_id: 1
        })
      });

      const result = await response.json();
      if (result.success) {
        setAnalysisResult(result.lease_analysis);
      } else {
        alert(result.error || 'Failed to analyze lease');
      }
    } catch (error) {
      console.error('Error analyzing lease:', error);
      alert('Error analyzing lease');
    } finally {
      setLoading(false);
    }
  };

  const extractEntities = async () => {
    if (!documentText.trim()) {
      alert('Please enter document text to extract entities');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/document/extract-entities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: documentText
        })
      });

      const result = await response.json();
      if (result.success) {
        setExtractionResult(result.extraction_results);
      } else {
        alert(result.error || 'Failed to extract entities');
      }
    } catch (error) {
      console.error('Error extracting entities:', error);
      alert('Error extracting entities');
    } finally {
      setLoading(false);
    }
  };

  const assessRisk = async () => {
    if (!documentText.trim()) {
      alert('Please enter document text to assess risk');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/document/assess-risk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: documentText
        })
      });

      const result = await response.json();
      if (result.success) {
        setRiskAssessment(result.risk_assessment);
      } else {
        alert(result.error || 'Failed to assess risk');
      }
    } catch (error) {
      console.error('Error assessing risk:', error);
      alert('Error assessing risk');
    } finally {
      setLoading(false);
    }
  };

  const processBatch = async () => {
    if (batchDocuments.length === 0) {
      alert('Please add documents to process in batch');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/document/batch-process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          documents: batchDocuments
        })
      });

      const result = await response.json();
      if (result.success) {
        setBatchResults(result);
      } else {
        alert(result.error || 'Failed to process batch');
      }
    } catch (error) {
      console.error('Error processing batch:', error);
      alert('Error processing batch');
    } finally {
      setLoading(false);
    }
  };

  const addBatchDocument = () => {
    if (!documentText.trim()) {
      alert('Please enter document text');
      return;
    }

    const newDoc = {
      document_id: `batch_doc_${batchDocuments.length + 1}`,
      text: documentText
    };

    setBatchDocuments([...batchDocuments, newDoc]);
    setDocumentText('');
  };

  const removeBatchDocument = (index) => {
    setBatchDocuments(batchDocuments.filter((_, i) => i !== index));
  };

  const getRiskLevelColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const renderSingleTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Document Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Document Text</label>
              <textarea
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                className="w-full h-40 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Paste your document text here..."
              />
            </div>

            <button
              onClick={processDocument}
              disabled={loading || !documentText.trim()}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Analyzing...' : 'Analyze Document'}
            </button>
          </div>
        </CardContent>
      </Card>

      {analysisResult && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-lg font-bold text-blue-600 capitalize">
                    {analysisResult.document_type?.replace('_', ' ') || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Document Type</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-lg font-bold text-green-600 capitalize">
                    {analysisResult.confidence || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Confidence</div>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-lg font-bold text-purple-600">
                    {analysisResult.legal_risk_score?.toFixed(1) || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Risk Score</div>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-lg font-bold text-orange-600">
                    {analysisResult.readability_score?.toFixed(1) || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Readability</div>
                </div>
              </div>

              {analysisResult.summary && (
                <div>
                  <h3 className="font-medium mb-2">Summary</h3>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded">{analysisResult.summary}</p>
                </div>
              )}

              {analysisResult.entities && analysisResult.entities.length > 0 && (
                <div>
                  <h3 className="font-medium mb-2">Extracted Entities ({analysisResult.entities.length})</h3>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.entities.slice(0, 10).map((entity, index) => (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                        {entity.text} ({entity.type})
                      </span>
                    ))}
                    {analysisResult.entities.length > 10 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-sm">
                        +{analysisResult.entities.length - 10} more
                      </span>
                    )}
                  </div>
                </div>
              )}

              {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
                <div>
                  <h3 className="font-medium mb-2">Recommendations</h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                    {analysisResult.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {analysisResult.warnings && analysisResult.warnings.length > 0 && (
                <div>
                  <h3 className="font-medium mb-2">Warnings</h3>
                  <div className="space-y-1">
                    {analysisResult.warnings.map((warning, index) => (
                      <div key={index} className="flex items-center text-sm text-red-600 bg-red-50 p-2 rounded">
                        <span className="mr-2">⚠️</span>
                        {warning}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderLeaseTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Lease Agreement Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Lease Agreement Text</label>
              <textarea
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                className="w-full h-40 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Paste your lease agreement text here..."
              />
            </div>

            <button
              onClick={analyzeLease}
              disabled={loading || !documentText.trim()}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Analyzing Lease...' : 'Analyze Lease Agreement'}
            </button>
          </div>
        </CardContent>
      </Card>

      {analysisResult && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Lease Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="font-medium">Tenant:</span>
                  <span>{analysisResult.tenant_name || 'Not specified'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Landlord:</span>
                  <span>{analysisResult.landlord_name || 'Not specified'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Property:</span>
                  <span>{analysisResult.property_address || 'Not specified'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Monthly Rent:</span>
                  <span>${analysisResult.monthly_rent || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Security Deposit:</span>
                  <span>${analysisResult.security_deposit || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Start Date:</span>
                  <span>{analysisResult.lease_start_date || 'Not specified'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">End Date:</span>
                  <span>{analysisResult.lease_end_date || 'Not specified'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Term (Months):</span>
                  <span>{analysisResult.lease_term_months || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Analysis Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analysisResult.analysis_summary && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-blue-50 rounded">
                      <div className="font-bold text-blue-600">
                        {analysisResult.analysis_summary.legal_risk_score?.toFixed(1) || 'N/A'}
                      </div>
                      <div className="text-xs text-gray-600">Risk Score</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded">
                      <div className="font-bold text-green-600">
                        {analysisResult.analysis_summary.high_risk_clauses || 0}
                      </div>
                      <div className="text-xs text-gray-600">High Risk Clauses</div>
                    </div>
                  </div>
                )}

                {analysisResult.summary && (
                  <div>
                    <h4 className="font-medium mb-2">Summary</h4>
                    <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">{analysisResult.summary}</p>
                  </div>
                )}

                {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Recommendations</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                      {analysisResult.recommendations.map((rec, index) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );

  const renderExtractTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Entity Extraction</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Document Text</label>
              <textarea
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                className="w-full h-40 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Paste text to extract entities from..."
              />
            </div>

            <button
              onClick={extractEntities}
              disabled={loading || !documentText.trim()}
              className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Extracting...' : 'Extract Entities'}
            </button>
          </div>
        </CardContent>
      </Card>

      {extractionResult && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>People & Organizations ({extractionResult.entities?.length || 0})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {extractionResult.entities?.map((entity, index) => (
                  <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded text-sm">
                    <span>{entity.text}</span>
                    <span className="text-xs text-gray-500 capitalize">{entity.type}</span>
                  </div>
                )) || <p className="text-gray-500 text-sm">No entities found</p>}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Dates ({extractionResult.dates?.length || 0})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {extractionResult.dates?.map((date, index) => (
                  <div key={index} className="p-2 bg-gray-50 rounded text-sm">
                    <div className="font-medium">{date.text}</div>
                    <div className="text-xs text-gray-500">{date.date_type} - {new Date(date.parsed_date).toLocaleDateString()}</div>
                  </div>
                )) || <p className="text-gray-500 text-sm">No dates found</p>}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Amounts ({extractionResult.amounts?.length || 0})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {extractionResult.amounts?.map((amount, index) => (
                  <div key={index} className="p-2 bg-gray-50 rounded text-sm">
                    <div className="font-medium">{amount.text}</div>
                    <div className="text-xs text-gray-500">{amount.amount_type} - ${amount.amount}</div>
                  </div>
                )) || <p className="text-gray-500 text-sm">No amounts found</p>}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {extractionResult?.summary && (
        <Card>
          <CardHeader>
            <CardTitle>Extraction Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded">
                <div className="text-2xl font-bold text-blue-600">{extractionResult.summary.total_entities}</div>
                <div className="text-sm text-gray-600">Total Entities</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded">
                <div className="text-2xl font-bold text-green-600">{extractionResult.summary.total_dates}</div>
                <div className="text-sm text-gray-600">Dates Found</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded">
                <div className="text-2xl font-bold text-purple-600">{extractionResult.summary.total_amounts}</div>
                <div className="text-sm text-gray-600">Amounts Found</div>
              </div>
              <div className="text-center p-3 bg-orange-50 rounded">
                <div className="text-2xl font-bold text-orange-600">${extractionResult.summary.total_amount_value?.toFixed(0) || 0}</div>
                <div className="text-sm text-gray-600">Total Value</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderRiskTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Risk Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Document Text</label>
              <textarea
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                className="w-full h-40 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Paste document text to assess risk..."
              />
            </div>

            <button
              onClick={assessRisk}
              disabled={loading || !documentText.trim()}
              className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Assessing Risk...' : 'Assess Risk'}
            </button>
          </div>
        </CardContent>
      </Card>

      {riskAssessment && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Risk Assessment Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className={`text-center p-4 rounded-lg ${getRiskLevelColor(riskAssessment.risk_level)}`}>
                  <div className="text-2xl font-bold">{riskAssessment.risk_level || 'N/A'}</div>
                  <div className="text-sm">Overall Risk</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{riskAssessment.legal_risk_score?.toFixed(1) || 'N/A'}</div>
                  <div className="text-sm text-gray-600">Legal Risk Score</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">{riskAssessment.complexity_score?.toFixed(1) || 'N/A'}</div>
                  <div className="text-sm text-gray-600">Complexity Score</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">{riskAssessment.sentiment_score?.toFixed(2) || 'N/A'}</div>
                  <div className="text-sm text-gray-600">Sentiment Score</div>
                </div>
              </div>

              {riskAssessment.risk_breakdown && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-red-50 rounded">
                    <div className="font-bold text-red-600">{riskAssessment.risk_breakdown.high_risk_clauses || 0}</div>
                    <div className="text-xs text-gray-600">High Risk Clauses</div>
                  </div>
                  <div className="text-center p-3 bg-yellow-50 rounded">
                    <div className="font-bold text-yellow-600">{riskAssessment.risk_breakdown.medium_risk_clauses || 0}</div>
                    <div className="text-xs text-gray-600">Medium Risk Clauses</div>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded">
                    <div className="font-bold text-orange-600">{riskAssessment.risk_breakdown.critical_clauses || 0}</div>
                    <div className="text-xs text-gray-600">Critical Clauses</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded">
                    <div className="font-bold text-gray-600">{riskAssessment.risk_breakdown.total_clauses || 0}</div>
                    <div className="text-xs text-gray-600">Total Clauses</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {riskAssessment.clauses && riskAssessment.clauses.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>High-Risk Clauses</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {riskAssessment.clauses.map((clause, index) => (
                    <div key={index} className="border border-red-200 rounded-lg p-3 bg-red-50">
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-medium text-red-800 capitalize">{clause.type}</span>
                        <div className="flex space-x-2">
                          <span className={`px-2 py-1 rounded text-xs ${getRiskLevelColor(clause.risk_level)}`}>
                            {clause.risk_level}
                          </span>
                          <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs capitalize">
                            {clause.importance}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-red-700">{clause.summary}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {riskAssessment.recommendations && riskAssessment.recommendations.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc list-inside space-y-2 text-sm text-gray-700">
                    {riskAssessment.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {riskAssessment.warnings && riskAssessment.warnings.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Warnings</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {riskAssessment.warnings.map((warning, index) => (
                      <div key={index} className="flex items-start text-sm text-red-600 bg-red-50 p-3 rounded">
                        <span className="mr-2 mt-0.5">⚠️</span>
                        <span>{warning}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderBatchTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Batch Document Processing</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Document Text</label>
              <textarea
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter document text to add to batch..."
              />
            </div>

            <div className="flex space-x-2">
              <button
                onClick={addBatchDocument}
                disabled={!documentText.trim()}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Add to Batch ({batchDocuments.length}/10)
              </button>
              
              <button
                onClick={processBatch}
                disabled={loading || batchDocuments.length === 0}
                className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Processing...' : 'Process Batch'}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {batchDocuments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Batch Queue ({batchDocuments.length} documents)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {batchDocuments.map((doc, index) => (
                <div key={index} className="flex justify-between items-start p-3 border border-gray-200 rounded">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{doc.document_id}</div>
                    <div className="text-xs text-gray-600 mt-1">
                      {doc.text.substring(0, 100)}...
                    </div>
                  </div>
                  <button
                    onClick={() => removeBatchDocument(index)}
                    className="ml-2 text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {batchResults && (
        <Card>
          <CardHeader>
            <CardTitle>Batch Processing Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {batchResults.summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded">
                    <div className="text-2xl font-bold text-blue-600">{batchResults.summary.total_documents}</div>
                    <div className="text-sm text-gray-600">Total Documents</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded">
                    <div className="text-2xl font-bold text-green-600">{batchResults.summary.successful_analyses}</div>
                    <div className="text-sm text-gray-600">Successful</div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded">
                    <div className="text-2xl font-bold text-red-600">{batchResults.summary.failed_analyses}</div>
                    <div className="text-sm text-gray-600">Failed</div>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded">
                    <div className="text-2xl font-bold text-purple-600">{batchResults.summary.average_risk_score?.toFixed(1) || 'N/A'}</div>
                    <div className="text-sm text-gray-600">Avg Risk Score</div>
                  </div>
                </div>
              )}

              <div className="space-y-3">
                {batchResults.results?.map((result, index) => (
                  <div key={index} className={`border rounded-lg p-4 ${result.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium">{result.document_id}</span>
                      <span className={`px-2 py-1 rounded text-xs ${result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {result.success ? 'Success' : 'Failed'}
                      </span>
                    </div>
                    
                    {result.success && result.summary && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div>
                          <span className="font-medium">Type:</span>
                          <span className="ml-1 capitalize">{result.summary.document_type?.replace('_', ' ')}</span>
                        </div>
                        <div>
                          <span className="font-medium">Risk Score:</span>
                          <span className="ml-1">{result.summary.legal_risk_score?.toFixed(1)}</span>
                        </div>
                        <div>
                          <span className="font-medium">Entities:</span>
                          <span className="ml-1">{result.summary.entities_found}</span>
                        </div>
                        <div>
                          <span className="font-medium">Processing:</span>
                          <span className="ml-1">{result.summary.processing_time?.toFixed(2)}s</span>
                        </div>
                      </div>
                    )}
                    
                    {!result.success && (
                      <p className="text-sm text-red-700">{result.error}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Document Processing Dashboard</h1>
        <p className="text-gray-600">AI-powered natural language processing for legal documents</p>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'single' && renderSingleTab()}
        {activeTab === 'lease' && renderLeaseTab()}
        {activeTab === 'ai-lease' && <LeaseUploadProcessor />}
        {activeTab === 'extract' && renderExtractTab()}
        {activeTab === 'risk' && renderRiskTab()}
        {activeTab === 'batch' && renderBatchTab()}
      </div>
    </div>
  );
};

export default DocumentProcessingDashboard;