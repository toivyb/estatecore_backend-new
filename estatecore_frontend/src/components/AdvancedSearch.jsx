import React, { useState, useEffect, useRef } from 'react'

const AdvancedSearch = ({ onSearch, entityType = 'all', placeholder = 'Search...' }) => {
  const [query, setQuery] = useState('')
  const [isAdvanced, setIsAdvanced] = useState(false)
  const [filters, setFilters] = useState({})
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [savedSearches, setSavedSearches] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const inputRef = useRef(null)
  const debounceRef = useRef(null)

  useEffect(() => {
    loadSavedSearches()
  }, [])

  useEffect(() => {
    // Debounced search
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }
    
    debounceRef.current = setTimeout(() => {
      if (query.length > 2) {
        fetchSuggestions(query)
        performSearch()
      } else {
        setSuggestions([])
        setShowSuggestions(false)
      }
    }, 300)

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [query, filters])

  const fetchSuggestions = async (searchQuery) => {
    try {
      const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(searchQuery)}&type=${entityType}`)
      const data = await response.json()
      setSuggestions(data)
      setShowSuggestions(true)
    } catch (error) {
      console.error('Error fetching suggestions:', error)
    }
  }

  const performSearch = async () => {
    setIsLoading(true)
    try {
      const searchParams = {
        query,
        filters,
        entityType
      }
      
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(searchParams)
      })
      
      const results = await response.json()
      onSearch(results)
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadSavedSearches = async () => {
    try {
      const response = await fetch('/api/search/saved')
      const data = await response.json()
      setSavedSearches(data)
    } catch (error) {
      console.error('Error loading saved searches:', error)
    }
  }

  const saveSearch = async () => {
    if (!query) return
    
    const searchName = prompt('Enter a name for this search:')
    if (!searchName) return

    try {
      const response = await fetch('/api/search/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: searchName,
          query,
          filters,
          entityType
        })
      })
      
      if (response.ok) {
        loadSavedSearches()
        alert('Search saved successfully!')
      }
    } catch (error) {
      console.error('Error saving search:', error)
    }
  }

  const loadSavedSearch = (savedSearch) => {
    setQuery(savedSearch.query)
    setFilters(savedSearch.filters)
    setShowSuggestions(false)
  }

  const clearSearch = () => {
    setQuery('')
    setFilters({})
    setSuggestions([])
    setShowSuggestions(false)
    onSearch([])
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const removeFilter = (key) => {
    setFilters(prev => {
      const newFilters = { ...prev }
      delete newFilters[key]
      return newFilters
    })
  }

  const getFilterOptions = () => {
    const commonFilters = {
      dateRange: {
        label: 'Date Range',
        type: 'select',
        options: [
          { value: 'today', label: 'Today' },
          { value: 'week', label: 'This Week' },
          { value: 'month', label: 'This Month' },
          { value: 'quarter', label: 'This Quarter' },
          { value: 'year', label: 'This Year' }
        ]
      },
      status: {
        label: 'Status',
        type: 'select',
        options: [
          { value: 'active', label: 'Active' },
          { value: 'inactive', label: 'Inactive' },
          { value: 'pending', label: 'Pending' }
        ]
      }
    }

    const entitySpecificFilters = {
      properties: {
        propertyType: {
          label: 'Property Type',
          type: 'select',
          options: [
            { value: 'apartment', label: 'Apartment' },
            { value: 'house', label: 'House' },
            { value: 'condo', label: 'Condo' },
            { value: 'commercial', label: 'Commercial' }
          ]
        },
        rentRange: {
          label: 'Rent Range',
          type: 'range',
          min: 0,
          max: 5000,
          step: 100
        }
      },
      tenants: {
        leaseStatus: {
          label: 'Lease Status',
          type: 'select',
          options: [
            { value: 'current', label: 'Current' },
            { value: 'expired', label: 'Expired' },
            { value: 'future', label: 'Future' }
          ]
        }
      },
      maintenance: {
        priority: {
          label: 'Priority',
          type: 'select',
          options: [
            { value: 'high', label: 'High' },
            { value: 'medium', label: 'Medium' },
            { value: 'low', label: 'Low' }
          ]
        },
        category: {
          label: 'Category',
          type: 'select',
          options: [
            { value: 'plumbing', label: 'Plumbing' },
            { value: 'electrical', label: 'Electrical' },
            { value: 'hvac', label: 'HVAC' },
            { value: 'appliances', label: 'Appliances' }
          ]
        }
      }
    }

    return {
      ...commonFilters,
      ...(entitySpecificFilters[entityType] || {})
    }
  }

  const renderFilterInput = (key, filterConfig) => {
    const value = filters[key] || ''

    switch (filterConfig.type) {
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleFilterChange(key, e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="">All {filterConfig.label}</option>
            {filterConfig.options.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        )
      
      case 'range':
        return (
          <div className="space-y-2">
            <input
              type="range"
              min={filterConfig.min}
              max={filterConfig.max}
              step={filterConfig.step}
              value={value || filterConfig.min}
              onChange={(e) => handleFilterChange(key, e.target.value)}
              className="w-full"
            />
            <div className="text-xs text-gray-600 text-center">
              ${value || filterConfig.min} - ${filterConfig.max}
            </div>
          </div>
        )
      
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFilterChange(key, e.target.value)}
            placeholder={filterConfig.label}
            className="w-full p-2 border border-gray-300 rounded-md text-sm"
          />
        )
    }
  }

  return (
    <div className="relative">
      {/* Main Search Bar */}
      <div className="relative">
        <div className="flex items-center bg-white border border-gray-300 rounded-lg shadow-sm">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={placeholder}
              className="w-full p-3 pl-10 pr-4 border-0 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onFocus={() => setShowSuggestions(suggestions.length > 0)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            />
            <svg className="absolute left-3 top-3.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {isLoading && (
              <div className="absolute right-3 top-3.5">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2 px-3">
            <button
              onClick={() => setIsAdvanced(!isAdvanced)}
              className={`p-2 rounded-md ${isAdvanced ? 'bg-blue-100 text-blue-700' : 'text-gray-500 hover:text-gray-700'}`}
              title="Advanced Search"
            >
              🔧
            </button>
            <button
              onClick={saveSearch}
              className="p-2 text-gray-500 hover:text-gray-700"
              title="Save Search"
            >
              💾
            </button>
            <button
              onClick={clearSearch}
              className="p-2 text-gray-500 hover:text-gray-700"
              title="Clear Search"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Search Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => {
                  setQuery(suggestion.text)
                  setShowSuggestions(false)
                }}
                className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2"
              >
                <span className="text-gray-400">{suggestion.icon}</span>
                <span>{suggestion.text}</span>
                <span className="text-xs text-gray-500 ml-auto">{suggestion.type}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Active Filters */}
      {Object.keys(filters).length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {Object.entries(filters).map(([key, value]) => (
            value && (
              <span
                key={key}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {key}: {value}
                <button
                  onClick={() => removeFilter(key)}
                  className="ml-2 text-blue-600 hover:text-blue-800"
                >
                  ✕
                </button>
              </span>
            )
          ))}
        </div>
      )}

      {/* Advanced Search Panel */}
      {isAdvanced && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Advanced Filters</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(getFilterOptions()).map(([key, filterConfig]) => (
              <div key={key}>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  {filterConfig.label}
                </label>
                {renderFilterInput(key, filterConfig)}
              </div>
            ))}
          </div>

          {/* Saved Searches */}
          {savedSearches.length > 0 && (
            <div className="mt-4">
              <h4 className="text-xs font-medium text-gray-700 mb-2">Saved Searches</h4>
              <div className="flex flex-wrap gap-2">
                {savedSearches.map((savedSearch) => (
                  <button
                    key={savedSearch.id}
                    onClick={() => loadSavedSearch(savedSearch)}
                    className="px-3 py-1 text-xs bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    {savedSearch.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AdvancedSearch