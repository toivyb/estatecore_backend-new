
import React, { useState, useEffect } from 'react'
import api from '../api'

const Properties = () => {
  const [properties, setProperties] = useState([])
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingProperty, setEditingProperty] = useState(null)
  const [newProperty, setNewProperty] = useState({
    name: '',
    address: '',
    type: '',
    bedrooms: '',
    bathrooms: '',
    rent: '',
    units: '',
    description: '',
    company_id: ''
  })
  const [unitsList, setUnitsList] = useState([])
  const [showUnitForm, setShowUnitForm] = useState(false)
  const [newUnit, setNewUnit] = useState({
    unit_number: '',
    bedrooms: '',
    bathrooms: '',
    rent: '',
    square_feet: ''
  })
  const [currentPropertyId, setCurrentPropertyId] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      // Fetch both properties and companies using api client
      const [propertiesData, companiesData] = await Promise.all([
        api.get('/api/properties'),
        api.get('/api/companies')
      ])
      
      setProperties(Array.isArray(propertiesData) ? propertiesData : propertiesData.properties || [])
      setCompanies(Array.isArray(companiesData) ? companiesData : companiesData.companies || [])
    } catch (error) {
      console.error('Error fetching data:', error)
      setProperties([])
      setCompanies([])
    } finally {
      setLoading(false)
    }
  }

  const fetchProperties = async () => {
    try {
      const data = await api.get('/api/properties')
      setProperties(Array.isArray(data) ? data : data.properties || [])
    } catch (error) {
      console.error('Error fetching properties:', error)
      setProperties([])
    }
  }

  const handleCreateProperty = async (e) => {
    e.preventDefault()
    try {
      // Validate required fields
      if (!newProperty.name.trim()) {
        alert('Property name is required')
        return
      }
      if (!newProperty.address.trim()) {
        alert('Property address is required')
        return
      }
      if (!newProperty.company_id) {
        alert('Please select a company')
        return
      }

      // Map frontend field names to backend field names
      const propertyData = {
        name: newProperty.name.trim(),
        address: newProperty.address.trim(),
        type: newProperty.type || 'apartment',
        description: newProperty.description.trim() || null,
        rent_amount: newProperty.rent ? parseFloat(newProperty.rent) : null,
        units: parseInt(newProperty.units) || 1,
        bedrooms: newProperty.bedrooms ? parseInt(newProperty.bedrooms) : null,
        bathrooms: newProperty.bathrooms ? parseInt(newProperty.bathrooms) : null,
        company_id: parseInt(newProperty.company_id)
      }
      
      console.log('Sending property data:', propertyData) // Debug log
      const data = await api.post('/api/properties', propertyData)
      
      if (data.success) {
        setNewProperty({
          name: '', address: '', type: '', bedrooms: '', bathrooms: '', 
          rent: '', units: '', description: '', company_id: ''
        })
        setShowCreateForm(false)
        fetchProperties()
        
        // Show success message with company status update info
        let message = 'Property created successfully!'
        if (data.company_status_update) {
          const update = data.company_status_update
          message += `\n\nCompany Update:\n• Units added: ${update.units_added}\n• Total units: ${update.total_units_after}\n• Monthly fee: $${update.monthly_fee_before} → $${update.monthly_fee_after}`
        }
        alert(message)
      } else {
        alert(`Failed to create property: ${data.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error creating property:', error)
      alert('Network error occurred while creating property. Please try again.')
    }
  }

  const handleUpdateProperty = async (e) => {
    e.preventDefault()
    try {
      const data = await api.put(`/api/properties/${editingProperty.id}`, editingProperty)
      
      if (data.success) {
        setEditingProperty(null)
        fetchProperties()
        alert('Property updated successfully!')
      } else {
        alert(`Failed to update property: ${data.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error updating property:', error)
      alert('Network error occurred while updating property. Please try again.')
    }
  }

  const handleDeleteProperty = async (propertyId) => {
    if (confirm('Are you sure you want to delete this property? This will also delete all related units and inactive tenants.')) {
      try {
        const data = await api.delete(`/api/properties/${propertyId}`)
        
        if (data.success) {
          fetchProperties()
          alert('Property deleted successfully!')
        } else {
          // Show the specific error message from the backend
          alert(`Failed to delete property: ${data.error || 'Unknown error'}`)
        }
      } catch (error) {
        console.error('Error deleting property:', error)
        alert('Network error occurred while deleting property. Please try again.')
      }
    }
  }

  const fetchUnits = async (propertyId) => {
    try {
      const data = await api.get(`/api/units?property_id=${propertyId}`)
      
      // Validate that data is an array before setting it
      if (Array.isArray(data)) {
        setUnitsList(data)
      } else {
        console.error('API returned non-array data:', data)
        setUnitsList([]) // Set to empty array as fallback
      }
    } catch (error) {
      console.error('Error fetching units:', error)
      setUnitsList([]) // Set to empty array on error
    }
  }

  const handleCreateUnit = async (e) => {
    e.preventDefault()
    try {
      const data = await api.post('/api/units', {
        ...newUnit,
        property_id: currentPropertyId
      })
      
      if (data.success) {
        setNewUnit({
          unit_number: '', bedrooms: '', bathrooms: '', rent: '', square_feet: ''
        })
        fetchUnits(currentPropertyId)
        alert('Unit created successfully!')
      }
    } catch (error) {
      console.error('Error creating unit:', error)
    }
  }

  const showUnitsModal = (propertyId) => {
    setCurrentPropertyId(propertyId)
    fetchUnits(propertyId)
    setShowUnitForm(true)
  }

  const startEdit = (property) => {
    setEditingProperty({...property})
  }

  const cancelEdit = () => {
    setEditingProperty(null)
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
        <h1 className="text-2xl font-bold text-gray-900">Properties Management</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          ➕ Add Property
        </button>
      </div>

      {/* Property Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Properties</h3>
          <p className="text-2xl font-bold text-gray-900">{properties.length}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Available</h3>
          <p className="text-2xl font-bold text-green-600">
            {properties.filter(p => p.is_available).length}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Occupied</h3>
          <p className="text-2xl font-bold text-red-600">
            {properties.filter(p => !p.is_available).length}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Revenue</h3>
          <p className="text-2xl font-bold text-purple-600">
            ${properties.reduce((sum, p) => sum + (p.rent || 0), 0).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Create Property Form */}
      {showCreateForm && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Add New Property</h3>
          <form onSubmit={handleCreateProperty} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Property Name *
              </label>
              <input
                type="text"
                value={newProperty.name}
                onChange={(e) => setNewProperty({...newProperty, name: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="e.g., Maple Grove Apartments"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Address *
              </label>
              <input
                type="text"
                value={newProperty.address}
                onChange={(e) => setNewProperty({...newProperty, address: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="e.g., 123 Main St, City, State"
                required
              />
            </div>
            
            {/* Company selection - only show for super admin */}
            {companies.length > 1 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company {companies.length > 1 ? '*' : ''}
                </label>
                <select
                  value={newProperty.company_id}
                  onChange={(e) => setNewProperty({...newProperty, company_id: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required={companies.length > 1}
                >
                  <option value="">Select Company</option>
                  {companies.map(company => (
                    <option key={company.id} value={company.id}>
                      {company.name} ({company.subscription_plan})
                    </option>
                  ))}
                </select>
                <p className="text-sm text-gray-500 mt-1">
                  The property will be affiliated with this company and update their monthly billing.
                </p>
              </div>
            )}
            
            {/* Show company info for company admin */}
            {companies.length === 1 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company
                </label>
                <div className="w-full p-2 border border-gray-300 rounded-md bg-gray-50">
                  {companies[0]?.name} ({companies[0]?.subscription_plan})
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Property will be automatically affiliated with your company.
                </p>
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Property Type *
              </label>
              <select
                value={newProperty.type}
                onChange={(e) => setNewProperty({...newProperty, type: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                required
              >
                <option value="">Select Type</option>
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="condo">Condo</option>
                <option value="townhouse">Townhouse</option>
                <option value="commercial">Commercial</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {newProperty.type === 'apartment' ? 'Base/Average Rent *' : 'Monthly Rent *'}
              </label>
              <input
                type="number"
                value={newProperty.rent}
                onChange={(e) => setNewProperty({...newProperty, rent: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder={newProperty.type === 'apartment' ? 'Average unit rent' : '1200.00'}
                step="0.01"
                required
              />
              {newProperty.type === 'apartment' && (
                <p className="text-sm text-gray-500 mt-1">
                  This is for reference only. Individual unit rents will be set when adding units.
                </p>
              )}
            </div>
            
            {/* Hide bedrooms/bathrooms for apartment buildings since they have multiple units */}
            {newProperty.type !== 'apartment' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bedrooms
                  </label>
                  <input
                    type="number"
                    value={newProperty.bedrooms}
                    onChange={(e) => setNewProperty({...newProperty, bedrooms: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    placeholder="2"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bathrooms
                  </label>
                  <input
                    type="number"
                    value={newProperty.bathrooms}
                    onChange={(e) => setNewProperty({...newProperty, bathrooms: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    placeholder="1.5"
                    step="0.5"
                  />
                </div>
              </>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {newProperty.type === 'apartment' ? 'Total Units (Estimate)' : 'Units'}
              </label>
              <input
                type="number"
                value={newProperty.units}
                onChange={(e) => setNewProperty({...newProperty, units: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder={newProperty.type === 'apartment' ? 'Total units in building' : '1'}
              />
              {newProperty.type === 'apartment' && (
                <p className="text-sm text-blue-600 mt-1">
                  💡 After creating, use the "Units" button to add individual unit details.
                </p>
              )}
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={newProperty.description}
                onChange={(e) => setNewProperty({...newProperty, description: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                rows="3"
                placeholder="Property description..."
              />
            </div>
            
            <div className="md:col-span-2 flex gap-2">
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                ✅ Create Property
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

      {/* Properties Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">All Properties</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Property
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bed/Bath
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
              {properties.map((property) => (
                <tr key={property.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {property.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {property.address}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {property.type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${property.rent?.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {property.bedrooms}br/{property.bathrooms}ba
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      property.is_available 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {property.is_available ? 'Available' : 'Occupied'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex gap-2">
                      <button
                        onClick={() => showUnitsModal(property.id)}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        🏢 Units
                      </button>
                      <button
                        onClick={() => startEdit(property)}
                        className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                      >
                        ✏️ Edit
                      </button>
                      <button
                        onClick={() => handleDeleteProperty(property.id)}
                        className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Property Modal */}
      {editingProperty && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Edit Property: {editingProperty.name}
              </h3>
            </div>
            
            <form onSubmit={handleUpdateProperty} className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Property Name *
                </label>
                <input
                  type="text"
                  value={editingProperty.name}
                  onChange={(e) => setEditingProperty({...editingProperty, name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Address *
                </label>
                <input
                  type="text"
                  value={editingProperty.address}
                  onChange={(e) => setEditingProperty({...editingProperty, address: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Property Type *
                </label>
                <select
                  value={editingProperty.type}
                  onChange={(e) => setEditingProperty({...editingProperty, type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                >
                  <option value="apartment">Apartment</option>
                  <option value="house">House</option>
                  <option value="condo">Condo</option>
                  <option value="townhouse">Townhouse</option>
                  <option value="commercial">Commercial</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {editingProperty.type === 'apartment' ? 'Base/Average Rent *' : 'Monthly Rent *'}
                </label>
                <input
                  type="number"
                  value={editingProperty.rent}
                  onChange={(e) => setEditingProperty({...editingProperty, rent: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  step="0.01"
                  required
                />
                {editingProperty.type === 'apartment' && (
                  <p className="text-sm text-gray-500 mt-1">
                    This is for reference only. Individual unit rents are set per unit.
                  </p>
                )}
              </div>
              
              {/* Hide bedrooms/bathrooms for apartment buildings since they have multiple units */}
              {editingProperty.type !== 'apartment' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Bedrooms
                    </label>
                    <input
                      type="number"
                      value={editingProperty.bedrooms}
                      onChange={(e) => setEditingProperty({...editingProperty, bedrooms: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Bathrooms
                    </label>
                    <input
                      type="number"
                      value={editingProperty.bathrooms}
                      onChange={(e) => setEditingProperty({...editingProperty, bathrooms: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      step="0.5"
                    />
                  </div>
                </>
              )}
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={editingProperty.description || ''}
                  onChange={(e) => setEditingProperty({...editingProperty, description: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  rows="3"
                />
              </div>
              
              <div className="md:col-span-2 flex gap-2">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  ✅ Update Property
                </button>
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Units Management Modal */}
      {showUnitForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-4xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Manage Units
              </h3>
            </div>
            
            <div className="p-6">
              {/* Add New Unit Form */}
              <div className="mb-6 bg-gray-50 p-4 rounded-lg">
                <h4 className="text-md font-medium mb-3">Add New Unit</h4>
                <form onSubmit={handleCreateUnit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Unit Number *
                    </label>
                    <input
                      type="text"
                      value={newUnit.unit_number}
                      onChange={(e) => setNewUnit({...newUnit, unit_number: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="e.g., 1A, 101, A1"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Bedrooms
                    </label>
                    <input
                      type="number"
                      value={newUnit.bedrooms}
                      onChange={(e) => setNewUnit({...newUnit, bedrooms: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="2"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Bathrooms
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      value={newUnit.bathrooms}
                      onChange={(e) => setNewUnit({...newUnit, bathrooms: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="1.5"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Monthly Rent *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={newUnit.rent}
                      onChange={(e) => setNewUnit({...newUnit, rent: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="1200.00"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Square Feet
                    </label>
                    <input
                      type="number"
                      value={newUnit.square_feet}
                      onChange={(e) => setNewUnit({...newUnit, square_feet: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="850"
                    />
                  </div>
                  
                  <div className="flex items-end">
                    <button
                      type="submit"
                      className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                    >
                      ➕ Add Unit
                    </button>
                  </div>
                </form>
              </div>

              {/* Units List */}
              <div>
                <h4 className="text-md font-medium mb-3">Existing Units ({unitsList.length})</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {unitsList.map((unit) => (
                    <div key={unit.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h5 className="font-medium text-gray-900">Unit {unit.unit_number}</h5>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          unit.is_available 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {unit.is_available ? 'Available' : 'Occupied'}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>{unit.bedrooms}br / {unit.bathrooms}ba</div>
                        <div className="font-semibold text-gray-900">${unit.rent?.toLocaleString()}/month</div>
                        {unit.square_feet && <div>{unit.square_feet} sq ft</div>}
                      </div>
                    </div>
                  ))}
                </div>
                
                {unitsList.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No units added yet. Add your first unit above.
                  </div>
                )}
              </div>
            </div>
            
            <div className="p-6 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => {
                  setShowUnitForm(false)
                  setCurrentPropertyId(null)
                  setUnitsList([])
                }}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Properties
