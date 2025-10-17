import React, { useState, useEffect } from 'react'
import api from '../api'

const Tenants = () => {
  const [tenants, setTenants] = useState([])
  const [properties, setProperties] = useState([])
  const [availableUnits, setAvailableUnits] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingTenant, setEditingTenant] = useState(null)
  const [leaseFile, setLeaseFile] = useState(null)
  const [isProcessingLease, setIsProcessingLease] = useState(false)
  const [aiExtracted, setAiExtracted] = useState(false)
  const [newTenant, setNewTenant] = useState({
    user: {
      email: '',
      username: '',
      password: ''
    },
    property_id: '',
    unit_id: '',
    lease_start: '',
    lease_end: '',
    rent_amount: '',
    deposit: '',
    lease_document_name: ''
  })

  useEffect(() => {
    fetchTenants()
    fetchProperties()
  }, [])

  const fetchTenants = async () => {
    try {
      const data = await api.get('/api/tenants')
      
      // Check if data is an array
      if (Array.isArray(data)) {
        setTenants(data)
        setError(null)
        console.log('Tenants loaded:', data.length)
      } else if (data.error) {
        console.error('API Error:', data.error)
        setTenants([])
        setError(data.error)
      } else {
        console.error('Unexpected response format:', data)
        setTenants([])
        setError('Unexpected response format')
      }
    } catch (error) {
      console.error('Error fetching tenants:', error)
      setTenants([])
      setError('Failed to load tenants')
    } finally {
      setLoading(false)
    }
  }

  const fetchProperties = async () => {
    try {
      const data = await api.get('/api/properties')
      
      // Check if response is successful and has properties array
      if (data.success && Array.isArray(data.properties)) {
        setProperties(data.properties)
      } else if (Array.isArray(data)) {
        // Fallback for old API format
        setProperties(data)
      } else if (data.properties && Array.isArray(data.properties)) {
        // Handle case where success might not be present but properties array exists
        setProperties(data.properties)
      } else {
        console.error('Properties API Error:', data)
        setProperties([]) // Set empty array as fallback
      }
    } catch (error) {
      console.error('Error fetching properties:', error)
      setProperties([]) // Set empty array as fallback
    }
  }

  const fetchAvailableUnits = async (propertyId) => {
    if (!propertyId) {
      setAvailableUnits([])
      return
    }
    try {
      const response = await fetch(`${api.BASE}/api/units?property_id=${propertyId}`)
      const data = await response.json()
      
      // Check if response is successful and data is an array
      if (response.ok && Array.isArray(data)) {
        setAvailableUnits(data.filter(unit => unit.is_available))
      } else {
        console.error('Units API Error:', data)
        setAvailableUnits([])
      }
    } catch (error) {
      console.error('Error fetching units:', error)
      setAvailableUnits([])
    }
  }

  const handleLeaseFileUpload = async (file) => {
    if (!file) return null
    
    setIsProcessingLease(true)
    
    // Simulate file upload and AI processing
    const reader = new FileReader()
    return new Promise((resolve) => {
      reader.onload = async (e) => {
        const content = e.target.result
        
        // Simulate AI processing of lease document
        try {
          const response = await fetch(`${api.BASE}/api/ai/process-lease`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              lease_content: content,
              filename: file.name
            })
          })
          
          const result = await response.json()
          resolve({
            filename: file.name,
            processed_data: result.data,
            upload_path: `/uploads/leases/${file.name}` // Mock path
          })
        } catch (error) {
          console.error('Error processing lease:', error)
          resolve({
            filename: file.name,
            processed_data: null,
            upload_path: `/uploads/leases/${file.name}`
          })
        }
      }
      reader.readAsText(file)
    })
  }

  const handleLeaseFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    setLeaseFile(file)
    setIsProcessingLease(true)
    
    try {
      // Process the lease with AI to extract information
      const leaseData = await handleLeaseFileUpload(file)
      
      if (leaseData.processed_data) {
        const extracted = leaseData.processed_data
        
        // Auto-fill form with extracted data
        setNewTenant(prev => ({
          ...prev,
          user: {
            ...prev.user,
            username: extracted.tenant_name || prev.user.username,
            email: extracted.tenant_email || prev.user.email,
            phone: extracted.tenant_phone || prev.user.phone
          },
          lease_start: extracted.lease_start || prev.lease_start,
          lease_end: extracted.lease_end || prev.lease_end,
          rent_amount: extracted.rent_amount || prev.rent_amount,
          deposit: extracted.security_deposit || prev.deposit
        }))
        
        // Try to find and auto-select property/unit based on extracted address
        if (extracted.property_address) {
          const matchingProperty = properties.find(prop => 
            prop.address.toLowerCase().includes(extracted.property_address.toLowerCase()) ||
            extracted.property_address.toLowerCase().includes(prop.address.toLowerCase())
          )
          
          if (matchingProperty) {
            setNewTenant(prev => ({...prev, property_id: matchingProperty.id.toString()}))
            fetchAvailableUnits(matchingProperty.id)
            
            // If unit number is extracted, try to match it
            if (extracted.unit_number) {
              setTimeout(() => {
                // Wait for units to load, then try to match
                const matchingUnit = availableUnits.find(unit => 
                  unit.unit_number.toString() === extracted.unit_number.toString()
                )
                if (matchingUnit) {
                  setNewTenant(prev => ({
                    ...prev, 
                    unit_id: matchingUnit.id.toString(),
                    rent_amount: matchingUnit.rent
                  }))
                }
              }, 1000)
            }
          }
        }
        
        setAiExtracted(true)
        alert('✅ Lease processed successfully! Form has been auto-filled with extracted information. Please review and adjust as needed.')
      }
    } catch (error) {
      console.error('Error processing lease:', error)
      alert('Failed to process lease document. Please fill the form manually.')
    } finally {
      setIsProcessingLease(false)
    }
  }

  const handleCreateTenant = async (e) => {
    e.preventDefault()
    
    try {
      // Process lease document with AI if file is provided
      let leaseData = null
      if (leaseFile) {
        leaseData = await handleLeaseFileUpload(leaseFile)
      }
      
      // Validate required fields before sending
      if (!newTenant.user.username || !newTenant.user.email) {
        alert('Please fill in all required fields (Name and Email)')
        return
      }

      console.log('Creating tenant with data:', {
        name: newTenant.user.username,
        email: newTenant.user.email,
        phone: newTenant.user.phone || '',
        company_id: 1,
        unit_id: newTenant.unit_id
      })

      // Create the tenant (which creates a user with role 'tenant')
      const tenant = await api.post('/api/tenants', {
        name: newTenant.user.username,
        email: newTenant.user.email,
        phone: newTenant.user.phone || '',
        password: newTenant.user.password,
        company_id: 1,  // Default company
        unit_id: newTenant.unit_id || null  // Include unit assignment
        // Note: Additional lease data would be stored in a separate lease table in a full implementation
      })
      
      console.log('Tenant creation response:', tenant)
      
      // Check if tenant creation was successful
      if (!tenant.success || tenant.error) {
        throw new Error(tenant.error || 'Failed to create tenant')
      }
      
      // Unit assignment is now handled automatically by the backend
      if (newTenant.unit_id) {
        const selectedUnit = availableUnits.find(unit => unit.id.toString() === newTenant.unit_id)
        const unitDisplayName = selectedUnit ? `Unit ${selectedUnit.unit_number}` : `Unit ID ${newTenant.unit_id}`
        alert(`✅ Tenant created successfully! ${unitDisplayName} has been assigned and marked as occupied.`)
      } else {
        alert('✅ Tenant created successfully!')
      }
      
      // Send AI processing request for this tenant if lease data exists
      if (leaseData && leaseData.processed_data) {
        try {
          await api.post('/api/ai/process-lease', {
            lease_content: leaseFile.name,
            tenant_id: tenant.tenant_id || tenant.user_id
          })
        } catch (error) {
          console.error('AI processing error:', error)
        }
      }
      
      // Reset form on success
      setNewTenant({
        user: { email: '', username: '', password: '' },
        property_id: '', unit_id: '', lease_start: '', lease_end: '',
        rent_amount: '', deposit: '', lease_document_name: ''
      })
      setLeaseFile(null)
      setAvailableUnits([])
      setAiExtracted(false)
      setShowCreateForm(false)
      fetchTenants()
      alert('Tenant created successfully!')
      
    } catch (error) {
      console.error('Error creating tenant:', error)
      
      // Show specific error messages for common issues
      let errorMessage = 'Failed to create tenant'
      
      // Check if it's a specific API error response
      if (error.message && error.message.includes('A user with this email address already exists')) {
        errorMessage = 'This email is already registered. Please use a different email address.'
      } else if (error.message && error.message.includes('UNIQUE constraint failed')) {
        if (error.message.includes('email')) {
          errorMessage = 'This email is already registered. Please use a different email address.'
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      
      alert(errorMessage)
    }
  }

  const handleUpdateTenant = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch(`${api.BASE}/api/tenants/${editingTenant.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editingTenant)
      })
      
      if (response.ok) {
        setEditingTenant(null)
        fetchTenants()
        alert('Tenant updated successfully!')
      }
    } catch (error) {
      console.error('Error updating tenant:', error)
    }
  }

  const handleDeleteTenant = async (tenantId) => {
    if (confirm('Are you sure you want to delete this tenant? This will also mark their unit as available.')) {
      try {
        // Delete the tenant - backend will automatically handle unit availability
        const response = await fetch(`${api.BASE}/api/tenants/${tenantId}`, {
          method: 'DELETE'
        })
        
        if (response.ok) {
          const responseData = await response.json()
          
          // Show success message with unit information if available
          if (responseData.units_updated && responseData.units_updated.length > 0) {
            alert(`✅ Tenant deleted successfully! Units ${responseData.units_updated.join(', ')} have been marked as available.`)
          } else {
            alert('✅ Tenant deleted successfully!')
          }
          
          fetchTenants()
        } else {
          const errorData = await response.json()
          alert(`Failed to delete tenant: ${errorData.error || 'Unknown error'}`)
        }
      } catch (error) {
        console.error('Error deleting tenant:', error)
        alert('Network error occurred while deleting tenant. Please try again.')
      }
    }
  }

  const startEdit = (tenant) => {
    setEditingTenant({...tenant})
  }

  const cancelEdit = () => {
    setEditingTenant(null)
  }

  const getLeaseStatus = (startDate, endDate) => {
    const now = new Date()
    const start = new Date(startDate)
    const end = new Date(endDate)
    
    if (now < start) return { status: 'Upcoming', color: 'bg-blue-100 text-blue-800' }
    if (now > end) return { status: 'Expired', color: 'bg-red-100 text-red-800' }
    return { status: 'Active', color: 'bg-green-100 text-green-800' }
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
        <h1 className="text-2xl font-bold text-gray-900">Tenants Management</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          ➕ Add Tenant
        </button>
      </div>

      {/* Tenant Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Tenants</h3>
          <p className="text-2xl font-bold text-gray-900">{Array.isArray(tenants) ? tenants.length : 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Active Leases</h3>
          <p className="text-2xl font-bold text-green-600">
            {Array.isArray(tenants) ? tenants.filter(t => t.status === 'active').length : 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Upcoming Leases</h3>
          <p className="text-2xl font-bold text-blue-600">
            {Array.isArray(tenants) ? tenants.filter(t => 
              t.lease_start && new Date(t.lease_start) > new Date()
            ).length : 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Rent</h3>
          <p className="text-2xl font-bold text-purple-600">
            ${Array.isArray(tenants) ? tenants.reduce((sum, t) => sum + (t.rent_amount || 0), 0).toLocaleString() : '0'}
          </p>
        </div>
      </div>

      {/* Create Tenant Form */}
      {showCreateForm && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Add New Tenant</h3>
          
          {/* AI Instructions */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="text-sm font-semibold text-blue-800 mb-2">🤖 AI-Powered Form Filling</h4>
            <p className="text-sm text-blue-700 mb-2">
              <strong>Option 1:</strong> Upload a signed lease document first, and AI will automatically extract and fill all the information for you.
            </p>
            <p className="text-sm text-blue-700">
              <strong>Option 2:</strong> Fill out the form manually if you prefer.
            </p>
          </div>
          
          <form onSubmit={handleCreateTenant} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* Lease Document Upload - Moved to top */}
            <div className="md:col-span-2 mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📋 Step 1: Upload Signed Lease Document (Optional)
                {aiExtracted && <span className="text-green-600 ml-2">✅ AI Extracted</span>}
              </label>
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleLeaseFileChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                disabled={isProcessingLease}
              />
              <p className="text-sm text-gray-500 mt-1">
                Upload the signed lease agreement for AI auto-fill, or fill the form manually below.
              </p>
              {isProcessingLease && (
                <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                    <p className="text-sm text-blue-700">
                      🤖 AI is processing your lease document and extracting information...
                    </p>
                  </div>
                </div>
              )}
              {leaseFile && !isProcessingLease && (
                <div className={`mt-2 p-2 border rounded-md ${aiExtracted ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                  <p className={`text-sm ${aiExtracted ? 'text-green-700' : 'text-yellow-700'}`}>
                    📄 {leaseFile.name} {aiExtracted ? '- AI processing complete! Form auto-filled.' : 'selected'}
                  </p>
                  {aiExtracted && (
                    <p className="text-xs text-green-600 mt-1">
                      Please review the auto-filled information below and make any necessary adjustments.
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Form fields section header */}
            <div className="md:col-span-2 mb-2">
              <h4 className="text-md font-medium text-gray-800 border-b border-gray-200 pb-2">
                📝 Step 2: Review & Complete Tenant Information {aiExtracted ? '(Auto-filled by AI)' : ''}
              </h4>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name *
              </label>
              <input
                type="text"
                value={newTenant.user.username}
                onChange={(e) => setNewTenant({
                  ...newTenant, 
                  user: {...newTenant.user, username: e.target.value}
                })}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="e.g., John Doe"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email *
              </label>
              <input
                type="email"
                value={newTenant.user.email}
                onChange={(e) => setNewTenant({
                  ...newTenant, 
                  user: {...newTenant.user, email: e.target.value}
                })}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="john@email.com"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password *
              </label>
              <input
                type="password"
                value={newTenant.user.password}
                onChange={(e) => setNewTenant({
                  ...newTenant, 
                  user: {...newTenant.user, password: e.target.value}
                })}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="Temporary password"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Property *
              </label>
              <select
                value={newTenant.property_id}
                onChange={(e) => {
                  const propertyId = e.target.value
                  setNewTenant({...newTenant, property_id: propertyId, unit_id: '', rent_amount: ''})
                  fetchAvailableUnits(propertyId)
                }}
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
                Unit *
              </label>
              <select
                value={newTenant.unit_id}
                onChange={(e) => {
                  const selectedUnitId = e.target.value;
                  const selectedUnit = availableUnits.find(unit => unit.id.toString() === selectedUnitId);
                  setNewTenant({
                    ...newTenant, 
                    unit_id: selectedUnitId,
                    rent_amount: selectedUnit ? selectedUnit.rent : ''
                  });
                }}
                className="w-full p-2 border border-gray-300 rounded-md"
                required
                disabled={!newTenant.property_id}
              >
                <option value="">Select Unit</option>
                {availableUnits.map(unit => (
                  <option key={unit.id} value={unit.id}>
                    Unit {unit.unit_number} - {unit.bedrooms}br/{unit.bathrooms}ba - ${unit.rent}/month
                  </option>
                ))}
              </select>
              {newTenant.property_id && availableUnits.length === 0 && (
                <p className="text-sm text-red-600 mt-1">
                  No available units in this property. Please add units first.
                </p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lease Start Date *
              </label>
              <input
                type="date"
                value={newTenant.lease_start}
                onChange={(e) => setNewTenant({...newTenant, lease_start: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lease End Date *
              </label>
              <input
                type="date"
                value={newTenant.lease_end}
                onChange={(e) => setNewTenant({...newTenant, lease_end: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Monthly Rent (from selected unit)
              </label>
              <input
                type="number"
                value={newTenant.rent_amount}
                className="w-full p-2 border border-gray-300 rounded-md bg-gray-50"
                placeholder="Select a unit to auto-fill rent"
                step="0.01"
                readOnly
              />
              <p className="text-xs text-gray-500 mt-1">
                Rent amount is automatically filled when you select a unit
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Security Deposit
              </label>
              <input
                type="number"
                value={newTenant.deposit}
                onChange={(e) => setNewTenant({...newTenant, deposit: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="0.00"
                step="0.01"
              />
            </div>
            
            <div className="md:col-span-2 flex gap-2">
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                ✅ Create Tenant
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

      {/* Tenants Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">All Tenants</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tenant
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Property
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lease Period
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Array.isArray(tenants) && tenants.map((tenant) => {
                const leaseStatus = getLeaseStatus(tenant.lease_start, tenant.lease_end)
                return (
                  <tr key={tenant.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {tenant.name || 'N/A'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {tenant.email || 'N/A'}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {tenant.property?.name || 'N/A'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {tenant.property?.address || 'N/A'}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div>{tenant.lease_start ? new Date(tenant.lease_start).toLocaleDateString() : 'N/A'}</div>
                        <div className="text-gray-500">to {tenant.lease_end ? new Date(tenant.lease_end).toLocaleDateString() : 'N/A'}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      ${tenant.rent_amount?.toLocaleString() || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${leaseStatus.color}`}>
                        {leaseStatus.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex gap-2">
                        <button
                          onClick={() => startEdit(tenant)}
                          className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDeleteTenant(tenant.id)}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
              {(!Array.isArray(tenants) || tenants.length === 0) && (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                    {!Array.isArray(tenants) ? 'Error loading tenants' : 'No tenants found'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Tenant Modal */}
      {editingTenant && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Edit Tenant: {editingTenant.name}
              </h3>
            </div>
            
            <form onSubmit={handleUpdateTenant} className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={editingTenant.name || ''}
                  onChange={(e) => setEditingTenant({
                    ...editingTenant, 
                    name: e.target.value
                  })}
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={editingTenant.email || ''}
                  onChange={(e) => setEditingTenant({
                    ...editingTenant, 
                    email: e.target.value
                  })}
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lease Start Date *
                </label>
                <input
                  type="date"
                  value={editingTenant.lease_start || ''}
                  onChange={(e) => setEditingTenant({...editingTenant, lease_start: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lease End Date *
                </label>
                <input
                  type="date"
                  value={editingTenant.lease_end || ''}
                  onChange={(e) => setEditingTenant({...editingTenant, lease_end: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Monthly Rent *
                </label>
                <input
                  type="number"
                  value={editingTenant.rent_amount || ''}
                  onChange={(e) => setEditingTenant({...editingTenant, rent_amount: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  step="0.01"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Security Deposit
                </label>
                <input
                  type="number"
                  value={editingTenant.deposit || ''}
                  onChange={(e) => setEditingTenant({...editingTenant, deposit: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  step="0.01"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={editingTenant.status || 'active'}
                  onChange={(e) => setEditingTenant({...editingTenant, status: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="terminated">Terminated</option>
                </select>
              </div>
              
              <div className="md:col-span-2 flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="bg-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 font-medium"
                >
                  💾 Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Tenants
