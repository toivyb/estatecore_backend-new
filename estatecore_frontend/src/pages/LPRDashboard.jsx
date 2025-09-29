import React, { useState, useEffect } from 'react';

const LPRDashboard = () => {
  const [events, setEvents] = useState([]);
  const [blacklist, setBlacklist] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newBlacklistPlate, setNewBlacklistPlate] = useState('');
  const [newBlacklistReason, setNewBlacklistReason] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [recognitionResult, setRecognitionResult] = useState(null);
  
  // AI Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [useAIRecognition, setUseAIRecognition] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [eventsRes, blacklistRes] = await Promise.all([
        fetch(`${import.meta.env.VITE_API_BASE_URL}/api/lpr/events`),
        fetch(`${import.meta.env.VITE_API_BASE_URL}/api/lpr/blacklist`)
      ]);

      if (eventsRes.ok) {
        const eventsData = await eventsRes.json();
        setEvents(Array.isArray(eventsData) ? eventsData : []);
      }

      if (blacklistRes.ok) {
        const blacklistData = await blacklistRes.json();
        setBlacklist(Array.isArray(blacklistData) ? blacklistData : []);
      }
    } catch (error) {
      console.error('Error fetching LPR data:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToBlacklist = async (e) => {
    e.preventDefault();
    if (!newBlacklistPlate.trim()) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/lpr/blacklist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plate: newBlacklistPlate.toUpperCase(),
          reason: newBlacklistReason
        }),
      });

      if (response.ok) {
        setNewBlacklistPlate('');
        setNewBlacklistReason('');
        fetchData(); // Refresh data
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error adding to blacklist:', error);
      alert('Failed to add to blacklist');
    }
  };

  const removeFromBlacklist = async (plate) => {
    if (!confirm(`Remove ${plate} from blacklist?`)) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/lpr/blacklist?plate=${plate}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchData(); // Refresh data
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error removing from blacklist:', error);
      alert('Failed to remove from blacklist');
    }
  };

  const recognizeImage = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('image', selectedFile);

    // Choose endpoint based on AI toggle
    const endpoint = useAIRecognition ? '/api/lpr/ai-recognize' : '/api/lpr/recognize';

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setRecognitionResult(result);
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error recognizing image:', error);
      alert('Failed to recognize image');
    }
  };

  const analyzeImage = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/lpr/analyze-image`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setAnalysisResult(result);
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error analyzing image:', error);
      alert('Failed to analyze image');
    }
  };

  const searchPlates = async (query = searchQuery) => {
    if (!query.trim()) return;

    setSearching(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/lpr/search?q=${encodeURIComponent(query)}&min_similarity=0.3&limit=20`
      );

      if (response.ok) {
        const result = await response.json();
        setSearchResults(result.results);
      } else {
        console.error('Search failed');
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const getSuggestions = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/lpr/suggest?q=${encodeURIComponent(query)}&limit=5`
      );

      if (response.ok) {
        const result = await response.json();
        setSuggestions(result.suggestions);
      }
    } catch (error) {
      console.error('Suggestions error:', error);
      setSuggestions([]);
    }
  };

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    getSuggestions(value);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl">Loading LPR Dashboard...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">License Plate Recognition Dashboard</h1>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Total Events</h3>
          <p className="text-3xl font-bold text-blue-600">{Array.isArray(events) ? events.length : 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Blacklisted Plates</h3>
          <p className="text-3xl font-bold text-red-600">{Array.isArray(blacklist) ? blacklist.length : 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Today's Detections</h3>
          <p className="text-3xl font-bold text-green-600">
            {Array.isArray(events) ? events.filter(e => {
              const today = new Date().toDateString();
              const eventDate = new Date(e.created_at).toDateString();
              return today === eventDate;
            }).length : 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-700">Alerts Today</h3>
          <p className="text-3xl font-bold text-orange-600">
            {Array.isArray(events) ? events.filter(e => {
              const today = new Date().toDateString();
              const eventDate = new Date(e.created_at).toDateString();
              return today === eventDate && e.is_blacklisted;
            }).length : 0}
          </p>
        </div>
      </div>

      {/* AI Plate Search */}
      <div className="mb-8 bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">🤖 AI Plate Search</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Search plates (e.g., 'ABC', 'AB*123', 'A?C123')..."
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {suggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
                  {suggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      onClick={() => {
                        setSearchQuery(suggestion);
                        setSuggestions([]);
                        searchPlates(suggestion);
                      }}
                      className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                    >
                      {suggestion}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="mt-2 text-sm text-gray-600">
              <strong>Search tips:</strong> Use * for multiple chars, ? for single char, or partial plates like "ABC" or "12"
            </div>
          </div>
          <div>
            <button
              onClick={() => searchPlates()}
              disabled={searching || !searchQuery.trim()}
              className="w-full bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:bg-gray-300"
            >
              {searching ? 'Searching...' : 'Smart Search'}
            </button>
          </div>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-3">Search Results ({searchResults.length})</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="border p-2 text-left">Plate</th>
                    <th className="border p-2 text-left">Similarity</th>
                    <th className="border p-2 text-left">Match Type</th>
                    <th className="border p-2 text-left">Status</th>
                    <th className="border p-2 text-left">Last Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {searchResults.map((result, index) => (
                    <tr key={index} className={result.is_blacklisted ? 'bg-red-50' : 'hover:bg-gray-50'}>
                      <td className="border p-2 font-mono font-bold">{result.plate}</td>
                      <td className="border p-2">
                        <div className="flex items-center">
                          <div className="w-full bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{width: `${result.similarity * 100}%`}}
                            ></div>
                          </div>
                          <span className="text-sm">{(result.similarity * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="border p-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          result.match_type === 'exact' ? 'bg-green-100 text-green-800' :
                          result.match_type === 'substring' ? 'bg-blue-100 text-blue-800' :
                          result.match_type === 'fuzzy_high' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {result.match_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="border p-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          result.is_blacklisted ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                        }`}>
                          {result.is_blacklisted ? 'BLACKLISTED' : 'Clear'}
                        </span>
                        {result.blacklist_reason && (
                          <div className="text-xs text-gray-600 mt-1">{result.blacklist_reason}</div>
                        )}
                      </td>
                      <td className="border p-2 text-sm">
                        {result.last_seen ? new Date(result.last_seen).toLocaleString() : 'Never'}
                        {result.last_camera && (
                          <div className="text-xs text-gray-600">{result.last_camera}</div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Advanced Image Recognition */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">🔍 AI Image Recognition</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Image
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setSelectedFile(e.target.files[0])}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={useAIRecognition}
                  onChange={(e) => setUseAIRecognition(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm">Use AI Multi-OCR (OpenALPR + Azure + Tesseract)</span>
              </label>
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={recognizeImage}
                disabled={!selectedFile}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-300"
              >
                Recognize Plate
              </button>
              <button
                onClick={analyzeImage}
                disabled={!selectedFile}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-300"
              >
                Deep Analysis
              </button>
            </div>
            
            {/* Recognition Results */}
            {recognitionResult && (
              <div className="mt-4 p-4 border rounded-md">
                <h3 className="font-semibold mb-2">Recognition Result:</h3>
                {recognitionResult.success ? (
                  <div>
                    {recognitionResult.results ? (
                      // AI Multi-OCR results
                      <div className="space-y-2">
                        {recognitionResult.results.map((result, index) => (
                          <div key={index} className="border-l-4 border-blue-500 pl-3">
                            <div className="flex justify-between items-center">
                              <span className="font-mono font-bold">{result.plate}</span>
                              <span className="text-sm text-gray-600">{result.confidence?.toFixed(1)}% ({result.source})</span>
                            </div>
                            <span className={`inline-block px-2 py-1 rounded text-xs ${
                              result.is_blacklisted ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                            }`}>
                              {result.is_blacklisted ? 'BLACKLISTED' : 'Clear'}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      // Standard recognition result
                      <div>
                        <p><strong>Plate:</strong> {recognitionResult.plate}</p>
                        <p><strong>Confidence:</strong> {recognitionResult.confidence?.toFixed(1)}%</p>
                        <p>
                          <strong>Status:</strong> 
                          <span className={`ml-2 px-2 py-1 rounded text-sm ${
                            recognitionResult.is_blacklisted 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {recognitionResult.is_blacklisted ? 'BLACKLISTED' : 'Clear'}
                          </span>
                        </p>
                        {recognitionResult.blacklist_reason && (
                          <p><strong>Reason:</strong> {recognitionResult.blacklist_reason}</p>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-red-600">No plate detected or recognition failed</p>
                )}
              </div>
            )}

            {/* Deep Analysis Results */}
            {analysisResult && (
              <div className="mt-4 p-4 border rounded-md bg-gray-50">
                <h3 className="font-semibold mb-2">🧠 Deep Analysis Results:</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Processed {analysisResult.image_analysis.preprocessed_versions} image versions, 
                  found {analysisResult.image_analysis.total_candidates} candidates
                </p>
                
                {analysisResult.candidates.map((candidate, index) => (
                  <div key={index} className="mb-3 p-3 border rounded bg-white">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="font-mono font-bold text-lg">#{candidate.rank} {candidate.plate}</span>
                        <span className={`ml-2 px-2 py-1 rounded text-xs ${
                          candidate.is_valid_format ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {candidate.is_valid_format ? 'Valid Format' : 'Invalid Format'}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-600">{candidate.confidence.toFixed(1)}%</div>
                        <div className="text-xs text-gray-500">{candidate.source}</div>
                      </div>
                    </div>
                    
                    <div className="mt-2 text-sm">
                      <span className="text-gray-600">Database: </span>
                      <span className={`px-1 py-0.5 rounded text-xs ${
                        candidate.database_matches.is_blacklisted ? 'bg-red-100 text-red-800' : 
                        candidate.database_matches.event_count > 0 ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {candidate.database_matches.is_blacklisted ? 'Blacklisted' :
                         candidate.database_matches.event_count > 0 ? `${candidate.database_matches.event_count} events` : 'New plate'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Add to Blacklist */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Add to Blacklist</h2>
          <form onSubmit={addToBlacklist} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                License Plate
              </label>
              <input
                type="text"
                value={newBlacklistPlate}
                onChange={(e) => setNewBlacklistPlate(e.target.value.toUpperCase())}
                placeholder="ABC123"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reason
              </label>
              <input
                type="text"
                value={newBlacklistReason}
                onChange={(e) => setNewBlacklistReason(e.target.value)}
                placeholder="Security concern, stolen vehicle, etc."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
            >
              Add to Blacklist
            </button>
          </form>
        </div>
      </div>

      {/* Recent Events */}
      <div className="mt-8 bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">Recent Detections</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Plate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Camera
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {events.slice(0, 20).map((event, index) => (
                <tr key={index} className={event.is_blacklisted ? 'bg-red-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {event.plate}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {event.confidence?.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {event.camera_id || 'Unknown'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      event.is_blacklisted 
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {event.is_blacklisted ? 'BLACKLISTED' : 'Clear'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {event.created_at ? new Date(event.created_at).toLocaleString() : 'Unknown'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Blacklist Management */}
      <div className="mt-8 bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">Blacklist Management</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Plate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reason
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Added
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Array.isArray(blacklist) ? blacklist.map((entry, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {entry.plate}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {entry.reason || 'No reason provided'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {entry.created_at ? new Date(entry.created_at).toLocaleDateString() : 'Unknown'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => removeFromBlacklist(entry.plate)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              )) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LPRDashboard;