import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

const ComputerVisionDashboard = () => {
  const [activeTab, setActiveTab] = useState('analyze');
  const [loading, setLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [analysisResults, setAnalysisResults] = useState([]);
  const [damageAssessment, setDamageAssessment] = useState(null);
  const [propertyId, setPropertyId] = useState('1');

  const tabs = [
    { id: 'analyze', label: 'Property Analysis', icon: '🏠' },
    { id: 'damage', label: 'Damage Detection', icon: '🔍' },
    { id: 'enhance', label: 'Image Enhancement', icon: '✨' },
    { id: 'history', label: 'Analysis History', icon: '📊' }
  ];

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
  };

  const analyzeProperty = async () => {
    if (!selectedFiles.length) {
      alert('Please select images to analyze');
      return;
    }

    setLoading(true);
    const results = [];

    try {
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('property_id', propertyId);
        formData.append('metadata', JSON.stringify({
          filename: file.name,
          upload_timestamp: new Date().toISOString()
        }));

        const response = await fetch('/api/ai/analyze-property', {
          method: 'POST',
          body: formData
        });

        const result = await response.json();
        if (result.success) {
          results.push({
            filename: file.name,
            analysis: result.analysis
          });
        }
      }

      setAnalysisResults(results);
    } catch (error) {
      console.error('Error analyzing property:', error);
      alert('Error analyzing property images');
    } finally {
      setLoading(false);
    }
  };

  const assessDamage = async () => {
    if (!selectedFiles.length) {
      alert('Please select images to analyze');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('image', selectedFiles[0]);
      formData.append('property_id', propertyId);
      formData.append('inspection_notes', 'Frontend damage assessment');

      const response = await fetch('/api/ai/assess-damage', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (result.success) {
        setDamageAssessment(result.assessment);
      }
    } catch (error) {
      console.error('Error assessing damage:', error);
      alert('Error assessing damage');
    } finally {
      setLoading(false);
    }
  };

  const enhanceImages = async () => {
    if (!selectedFiles.length) {
      alert('Please select images to enhance');
      return;
    }

    setLoading(true);

    try {
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('image', file);

        const response = await fetch('/api/ai/enhance-image', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          // Handle enhanced image download
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `enhanced_${file.name}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        }
      }
    } catch (error) {
      console.error('Error enhancing images:', error);
      alert('Error enhancing images');
    } finally {
      setLoading(false);
    }
  };

  const renderAnalysisTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Property Image Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Property ID</label>
              <input
                type="text"
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter property ID"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Select Images</label>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileSelect}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={analyzeProperty}
              disabled={loading || !selectedFiles.length}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Analyzing...' : 'Analyze Property Images'}
            </button>
          </div>
        </CardContent>
      </Card>

      {analysisResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analysisResults.map((result, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium mb-2">{result.filename}</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="font-medium">Confidence Score</div>
                      <div>{(result.analysis.confidence_score * 100).toFixed(1)}%</div>
                    </div>
                    <div>
                      <div className="font-medium">Property Condition</div>
                      <div className="capitalize">{result.analysis.property_condition || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="font-medium">Features Detected</div>
                      <div>{result.analysis.features_detected || 0}</div>
                    </div>
                    <div>
                      <div className="font-medium">Analysis Time</div>
                      <div>{result.analysis.analysis_time?.toFixed(2)}s</div>
                    </div>
                  </div>
                  
                  {result.analysis.recommendations && (
                    <div className="mt-3">
                      <div className="font-medium mb-1">Recommendations:</div>
                      <ul className="list-disc list-inside text-sm text-gray-600">
                        {result.analysis.recommendations.map((rec, i) => (
                          <li key={i}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderDamageTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Damage Detection & Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Property ID</label>
              <input
                type="text"
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter property ID"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Select Image</label>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={assessDamage}
              disabled={loading || !selectedFiles.length}
              className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Assessing...' : 'Assess Damage'}
            </button>
          </div>
        </CardContent>
      </Card>

      {damageAssessment && (
        <Card>
          <CardHeader>
            <CardTitle>Damage Assessment Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {damageAssessment.damage_score?.toFixed(1) || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Damage Score</div>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-lg font-bold text-orange-600 capitalize">
                    {damageAssessment.urgency_level || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Urgency Level</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-lg font-bold text-green-600">
                    ${damageAssessment.estimated_cost?.toFixed(0) || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Repair Cost</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-lg font-bold text-blue-600">
                    {damageAssessment.repair_timeframe || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Timeframe</div>
                </div>
              </div>

              {damageAssessment.damage_categories && damageAssessment.damage_categories.length > 0 && (
                <div>
                  <h3 className="font-medium mb-2">Damage Categories</h3>
                  <div className="space-y-2">
                    {damageAssessment.damage_categories.map((category, index) => (
                      <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span className="capitalize">{category.category || category}</span>
                        <span className="text-sm text-gray-600">
                          {typeof category === 'object' ? `${category.severity} severity` : ''}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {damageAssessment.recommendations && (
                <div>
                  <h3 className="font-medium mb-2">Recommendations</h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                    {damageAssessment.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderEnhanceTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Image Enhancement</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Select Images to Enhance</label>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileSelect}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Enhanced images will be automatically downloaded
              </p>
            </div>

            <button
              onClick={enhanceImages}
              disabled={loading || !selectedFiles.length}
              className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Enhancing...' : 'Enhance Images'}
            </button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Enhancement Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h3 className="font-medium">Automatic Enhancements</h3>
              <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                <li>Brightness and contrast optimization</li>
                <li>Noise reduction</li>
                <li>Sharpness enhancement</li>
                <li>Color correction</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h3 className="font-medium">Quality Improvements</h3>
              <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                <li>Improved clarity for analysis</li>
                <li>Better feature detection</li>
                <li>Enhanced damage visibility</li>
                <li>Optimal lighting conditions</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderHistoryTab = () => (
    <Card>
      <CardHeader>
        <CardTitle>Analysis History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-4">📊</div>
          <p>Analysis history will appear here</p>
          <p className="text-sm">Recent property analyses and damage assessments</p>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Computer Vision Dashboard</h1>
        <p className="text-gray-600">AI-powered property analysis and damage detection</p>
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
        {activeTab === 'analyze' && renderAnalysisTab()}
        {activeTab === 'damage' && renderDamageTab()}
        {activeTab === 'enhance' && renderEnhanceTab()}
        {activeTab === 'history' && renderHistoryTab()}
      </div>
    </div>
  );
};

export default ComputerVisionDashboard;