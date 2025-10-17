import React, { useState, useEffect } from 'react';
import api from '../api';

const PropertiesAdminDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    fetchProperties();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const data = await api.get('/api/dashboard');
      setDashboardData(data.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchProperties = async () => {
    try {
      const data = await api.get('/api/properties');
      setProperties(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching properties:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount || 0);
  };

  const getPropertyStatus = (property) => {
    // Mock property status calculation
    const occupancyRate = Math.floor(Math.random() * 30) + 70; // 70-100%
    if (occupancyRate >= 90) return { status: 'excellent', color: 'green' };
    if (occupancyRate >= 75) return { status: 'good', color: 'blue' };
    if (occupancyRate >= 60) return { status: 'fair', color: 'yellow' };
    return { status: 'needs attention', color: 'red' };
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading properties dashboard...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">Properties Administrator Dashboard</h1>
            <p className="text-gray-600">Manage and oversee all property operations</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics */}
        {dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
              <h3 className="text-sm font-medium text-gray-500">Total Properties</h3>
              <p className="text-3xl font-bold text-blue-600">{dashboardData.total_properties}</p>
              <p className="text-sm text-gray-600">Under management</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
              <h3 className="text-sm font-medium text-gray-500">Total Units</h3>
              <p className="text-3xl font-bold text-green-600">{dashboardData.total_units}</p>
              <p className="text-sm text-gray-600">{dashboardData.occupied_units} occupied</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
              <h3 className="text-sm font-medium text-gray-500">Occupancy Rate</h3>
              <p className="text-3xl font-bold text-purple-600">{dashboardData.occupancy_rate}%</p>
              <p className="text-sm text-gray-600">Portfolio average</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
              <h3 className="text-sm font-medium text-gray-500">Monthly Revenue</h3>
              <p className="text-3xl font-bold text-orange-600">{formatCurrency(dashboardData.total_revenue)}</p>
              <p className="text-sm text-gray-600">Current month</p>
            </div>
          </div>
        )}

        {/* Properties Overview */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Properties Portfolio</h3>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                + Add New Property
              </button>
            </div>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {properties.map((property) => {
                const status = getPropertyStatus(property);
                return (
                  <div key={property.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-900">{property.name}</h4>
                        <p className="text-sm text-gray-600">{property.address}</p>
                        <p className="text-xs text-gray-500">{property.city}, {property.state} {property.zip_code}</p>
                      </div>
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full bg-${status.color}-100 text-${status.color}-800`}>
                        {status.status}
                      </span>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Type:</span>
                        <span className="font-medium">{property.property_type || 'Residential'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Units:</span>
                        <span className="font-medium">12 total, 10 occupied</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Revenue:</span>
                        <span className="font-medium text-green-600">{formatCurrency(15000)}/month</span>
                      </div>
                    </div>
                    
                    <div className="mt-4 flex space-x-2">
                      <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-3 rounded text-sm hover:bg-gray-200">
                        View Details
                      </button>
                      <button className="flex-1 bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700">
                        Manage
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Property Management Tools */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Property Management Tools</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4">
                <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
                  <div className="text-2xl mb-2">🏠</div>
                  <div className="text-sm font-medium">Unit Management</div>
                </button>
                <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
                  <div className="text-2xl mb-2">👥</div>
                  <div className="text-sm font-medium">Tenant Management</div>
                </button>
                <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
                  <div className="text-2xl mb-2">💰</div>
                  <div className="text-sm font-medium">Rent Collection</div>
                </button>
                <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center">
                  <div className="text-2xl mb-2">🔧</div>
                  <div className="text-sm font-medium">Maintenance</div>
                </button>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">New tenant moved in</p>
                    <p className="text-xs text-gray-500">Unit 3B, Sunset Apartments - 2 hours ago</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Maintenance request completed</p>
                    <p className="text-xs text-gray-500">HVAC repair, Unit 7A - 5 hours ago</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Lease renewal pending</p>
                    <p className="text-xs text-gray-500">Unit 5C expires in 30 days - 1 day ago</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Property inspection scheduled</p>
                    <p className="text-xs text-gray-500">Oak Ridge Complex - 2 days ago</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Analytics */}
        <div className="mt-8 bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Performance Analytics</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">98.5%</div>
                <div className="text-sm text-gray-600">Average Occupancy</div>
                <div className="text-xs text-gray-500">+2.3% from last month</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">4.2</div>
                <div className="text-sm text-gray-600">Days Average Vacancy</div>
                <div className="text-xs text-gray-500">-1.8 days from last month</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">4.8/5</div>
                <div className="text-sm text-gray-600">Tenant Satisfaction</div>
                <div className="text-xs text-gray-500">Based on 47 reviews</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertiesAdminDashboard;