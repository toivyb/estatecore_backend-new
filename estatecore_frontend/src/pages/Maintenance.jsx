import React, { useState, useEffect } from 'react'
import api from '../api'

const Maintenance = () => {
  const [requests, setRequests] = useState([])
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingRequest, setEditingRequest] = useState(null)
  const [newRequest, setNewRequest] = useState({
    property_id: '',
    title: '',
    description: '',
    priority: 'medium'
  })

  useEffect(() => {
    fetchMaintenanceRequests()
    fetchProperties()
  }, [])

  const fetchMaintenanceRequests = async () => {
    try {
      const data = await api.get('/api/maintenance/requests')
      
      // Ensure data is always an array
      if (Array.isArray(data)) {
        setRequests(data)
      } else if (data && Array.isArray(data.requests)) {
        setRequests(data.requests)
      } else {
        console.warn('Maintenance requests API returned non-array data:', data)
        setRequests([]) // Set empty array as fallback
      }
    } catch (error) {
      console.error('Error fetching maintenance requests:', error)
      setRequests([]) // Set empty array on error
    } finally {
      setLoading(false)
    }
  }

  const fetchProperties = async () => {
    try {
      const response = await api.get('/api/properties')
      
      // Check if we have a successful response with properties array
      if (response.success && Array.isArray(response.properties)) {
        setProperties(response.properties)
      } else if (Array.isArray(response)) {
        // Fallback for direct array response
        setProperties(response)
      } else {
        console.warn('Properties API returned unexpected data:', response)
        setProperties([]) // Set empty array as fallback
      }
    } catch (error) {
      console.error('Error fetching properties:', error)
      setProperties([]) // Set empty array on error
    }
  }

  const handleCreateRequest = async (e) => {
    e.preventDefault()
    try {
      const result = await api.post('/api/maintenance/requests', newRequest)
      
      if (result.success) {
        setNewRequest({ property_id: '', title: '', description: '', priority: 'medium' })
        setShowCreateForm(false)
        fetchMaintenanceRequests()
        alert('Maintenance request created successfully!')
      } else {
        console.error('Error creating request:', result.error)
        alert('Failed to create maintenance request: ' + (result.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error creating request:', error)
      alert('Failed to create maintenance request')
    }
  }

  const handleUpdateRequest = async (e) => {
    e.preventDefault()
    try {
      const result = await api.put(`/api/maintenance/requests/${editingRequest.id}`, editingRequest)
      
      if (result.success) {
        setEditingRequest(null)
        fetchMaintenanceRequests()
        alert('Maintenance request updated successfully!')
      } else {
        console.error('Error updating request:', result.error)
        alert('Failed to update maintenance request: ' + (result.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error updating request:', error)
      alert('Failed to update maintenance request')
    }
  }

  const handleDeleteRequest = async (requestId) => {
    if (confirm('Are you sure you want to delete this maintenance request?')) {
      try {
        const result = await api.delete(`/api/maintenance/requests/${requestId}`)
        
        if (result.success) {
          fetchMaintenanceRequests()
          alert('Maintenance request deleted successfully!')
        } else {
          console.error('Error deleting request:', result.error)
          alert('Failed to delete maintenance request: ' + (result.error || 'Unknown error'))
        }
      } catch (error) {
        console.error('Error deleting request:', error)
        alert('Failed to delete maintenance request')
      }
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'bg-blue-100 text-blue-800'
      case 'in_progress': return 'bg-orange-100 text-orange-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'cancelled': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Maintenance Management</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          ➕ Create Request
        </button>
      </div>

      {/* Maintenance Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Requests</h3>
          <p className="text-2xl font-bold text-gray-900">{Array.isArray(requests) ? requests.length : 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Open</h3>
          <p className="text-2xl font-bold text-blue-600">
            {Array.isArray(requests) ? requests.filter(r => r.status === 'open').length : 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">In Progress</h3>
          <p className="text-2xl font-bold text-orange-600">
            {Array.isArray(requests) ? requests.filter(r => r.status === 'in_progress').length : 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">High Priority</h3>
          <p className="text-2xl font-bold text-red-600">
            {Array.isArray(requests) ? requests.filter(r => r.priority === 'high').length : 0}
          </p>
        </div>
      </div>

      {/* Create Request Form */}
      {showCreateForm && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Create Maintenance Request</h3>
          <form onSubmit={handleCreateRequest} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Property *
              </label>
              <select
                value={newRequest.property_id}
                onChange={(e) => setNewRequest({...newRequest, property_id: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                required
              >
                <option value="">Select Property</option>
                {properties.map(property => (
                  <option key={property.id} value={property.id}>
                    {property.name} - {property.address}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority *
              </label>
              <select
                value={newRequest.priority}
                onChange={(e) => setNewRequest({...newRequest, priority: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                required
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title *
              </label>
              <input
                type="text"
                value={newRequest.title}
                onChange={(e) => setNewRequest({...newRequest, title: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="Brief description of the issue"
                required
              />
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={newRequest.description}
                onChange={(e) => setNewRequest({...newRequest, description: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                rows="3"
                placeholder="Detailed description of the maintenance issue"
              />
            </div>
            
            <div className="md:col-span-2 flex gap-2">
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                ✅ Create Request
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Requests Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">All Maintenance Requests</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Request
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Property
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Priority
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Array.isArray(requests) && requests.map((request) => (
                <tr key={request.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {request.title}
                      </div>
                      <div className="text-sm text-gray-500">
                        {request.description?.substring(0, 60)}...
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {request.property}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(request.priority)}`}>
                      {request.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(request.status)}`}>
                      {request.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(request.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setEditingRequest({...request})}
                        className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                      >
                        ✏️ Edit
                      </button>
                      <button
                        onClick={() => handleDeleteRequest(request.id)}
                        className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {(!Array.isArray(requests) || requests.length === 0) && (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                    {!Array.isArray(requests) ? 'Error loading maintenance requests' : 'No maintenance requests found'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Request Modal */}
      {editingRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Edit Maintenance Request: {editingRequest.title}
              </h3>
            </div>
            
            <form onSubmit={handleUpdateRequest} className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={editingRequest.title}
                  onChange={(e) => setEditingRequest({...editingRequest, title: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <select
                  value={editingRequest.priority}
                  onChange={(e) => setEditingRequest({...editingRequest, priority: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={editingRequest.status}
                  onChange={(e) => setEditingRequest({...editingRequest, status: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={editingRequest.description || ''}
                  onChange={(e) => setEditingRequest({...editingRequest, description: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  rows="3"
                />
              </div>
              
              <div className="md:col-span-2 flex gap-2">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  ✅ Update Request
                </button>
                <button
                  type="button"
                  onClick={() => setEditingRequest(null)}
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
  )
}

export default Maintenance
