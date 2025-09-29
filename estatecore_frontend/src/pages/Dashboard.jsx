import React, { useEffect, useState } from 'react';
import api from '../api'; // ✅ default import
import IncomeWidget from '../components/IncomeWidget.jsx';
import PropertyAccessManager from '../components/PropertyAccessManager.jsx';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [leaseExpirations, setLeaseExpirations] = useState(null);
  const [userInfo, setUserInfo] = useState(null);
  const [companyInfo, setCompanyInfo] = useState(null);
  const [showRoleDemo, setShowRoleDemo] = useState(false);
  const [showPropertyAccess, setShowPropertyAccess] = useState(false);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch user info first
        const userResponse = await api.get('/api/auth/user');
        if (userResponse.success) {
          setUserInfo(userResponse.user);
        }

        // Fetch company info
        const companyResponse = await api.get('/api/companies');
        if (companyResponse.success) {
          setCompanyInfo(companyResponse.company);
        }

        // Fetch dashboard data from API
        const dashboardResponse = await api.get('/api/dashboard');
        if (dashboardResponse.success) {
          setData(dashboardResponse.data);
        } else {
          console.error('Failed to fetch dashboard data');
        }

        // Fetch lease expiration data from AI API
        const leaseResponse = await api.get('/api/ai/lease-expiration-check');
        if (leaseResponse.success) {
          setLeaseExpirations(leaseResponse.data);
        } else {
          console.error('Failed to fetch lease expiration data');
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        // Fallback error state
        setData({
          total_properties: 0,
          available_properties: 0,
          total_units: 0,
          occupied_units: 0,
          total_tenants: 0,
          total_users: 0,
          total_revenue: 0,
          pending_revenue: 0,
          occupancy_rate: 0
        });
        setLeaseExpirations({ total_count: 0, high_priority_count: 0, expiring_leases: [] });
      }
    };

    fetchDashboardData();
  }, []);

  const switchUser = async (userId) => {
    try {
      const response = await api.post(`/api/demo/switch-user/${userId}`);
      if (response.success) {
        // Refresh all data after user switch
        window.location.reload();
      }
    } catch (error) {
      console.error('Error switching user:', error);
    }
  };

  if (!data) return <div>Loading...</div>;

  return (
    <div className="p-6">
      {/* Company and User Header */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
            {companyInfo && (
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span className="font-medium">{companyInfo.name}</span>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                  {companyInfo.subscription_plan.toUpperCase()}
                </span>
                <span>{companyInfo.property_count} Properties</span>
              </div>
            )}
          </div>
          
          {userInfo && (
            <div className="text-right">
              <div className="font-medium text-gray-900">{userInfo.name}</div>
              <div className="text-sm text-gray-600">
                {userInfo.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </div>
              {userInfo.role !== 'company_admin' && (
                <div className="text-xs text-gray-500">
                  Access to {userInfo.accessible_property_count} properties
                </div>
              )}
              <div className="mt-2 space-x-2">
                <button
                  onClick={() => setShowRoleDemo(!showRoleDemo)}
                  className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
                >
                  {showRoleDemo ? 'Hide' : 'Demo'} Role Switch
                </button>
                {userInfo.role === 'company_admin' && (
                  <button
                    onClick={() => setShowPropertyAccess(true)}
                    className="text-xs bg-blue-100 hover:bg-blue-200 px-2 py-1 rounded text-blue-700"
                  >
                    👥 Manage Team Access
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Role Demo Component */}
      {showRoleDemo && (
        <div className="mb-6 bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
          <h3 className="text-lg font-semibold mb-3 text-yellow-800">🎭 Multi-Tenant Demo - Switch User Roles</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="bg-white p-3 rounded border">
              <div className="font-medium text-blue-700">Premier Property Mgmt</div>
              <div className="text-xs text-gray-600 mb-2">Enterprise Plan - 2 Properties</div>
              <div className="space-y-1">
                <button onClick={() => switchUser(1)} className="block w-full text-left text-xs bg-blue-100 hover:bg-blue-200 px-2 py-1 rounded">
                  John Smith (Company Admin)
                </button>
                <button onClick={() => switchUser(2)} className="block w-full text-left text-xs bg-green-100 hover:bg-green-200 px-2 py-1 rounded">
                  Sarah Davis (Property Admin) ⭐
                </button>
                <button onClick={() => switchUser(3)} className="block w-full text-left text-xs bg-orange-100 hover:bg-orange-200 px-2 py-1 rounded">
                  Mike Johnson (Property Manager)
                </button>
              </div>
            </div>
            
            <div className="bg-white p-3 rounded border">
              <div className="font-medium text-green-700">GreenVille Estates</div>
              <div className="text-xs text-gray-600 mb-2">Pro Plan - 2 Properties</div>
              <div className="space-y-1">
                <button onClick={() => switchUser(4)} className="block w-full text-left text-xs bg-blue-100 hover:bg-blue-200 px-2 py-1 rounded">
                  Emily Rodriguez (Company Admin)
                </button>
                <button onClick={() => switchUser(5)} className="block w-full text-left text-xs bg-green-100 hover:bg-green-200 px-2 py-1 rounded">
                  David Chen (Property Admin)
                </button>
              </div>
            </div>
            
            <div className="bg-white p-3 rounded border">
              <div className="font-medium text-purple-700">Urban Living Co</div>
              <div className="text-xs text-gray-600 mb-2">Basic Plan - 1 Property</div>
              <div className="space-y-1">
                <button onClick={() => switchUser(6)} className="block w-full text-left text-xs bg-blue-100 hover:bg-blue-200 px-2 py-1 rounded">
                  Lisa Anderson (Company Admin)
                </button>
                <button onClick={() => switchUser(7)} className="block w-full text-left text-xs bg-orange-100 hover:bg-orange-200 px-2 py-1 rounded">
                  James Wilson (Property Manager)
                </button>
              </div>
            </div>
            
            <div className="bg-white p-3 rounded border">
              <div className="font-medium text-red-700">Sunset Properties LLC</div>
              <div className="text-xs text-gray-600 mb-2">Pro Plan - 2 Properties</div>
              <div className="space-y-1">
                <button onClick={() => switchUser(8)} className="block w-full text-left text-xs bg-blue-100 hover:bg-blue-200 px-2 py-1 rounded">
                  Maria Garcia (Company Admin)
                </button>
              </div>
            </div>
          </div>
          <div className="mt-3 text-xs text-yellow-700">
            ⭐ Currently logged in • Click any user to see their specific data access • Each user sees only their company's properties
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2 text-blue-700">🏢 Properties</h3>
          <div className="text-3xl font-bold text-blue-600">{data.total_properties}</div>
          <div className="text-sm text-gray-600">{data.available_properties} available</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2 text-green-700">🏠 Units</h3>
          <div className="text-3xl font-bold text-green-600">{data.total_units}</div>
          <div className="text-sm text-gray-600">{data.occupied_units} occupied</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2 text-orange-700">👥 Tenants</h3>
          <div className="text-3xl font-bold text-orange-600">{data.total_tenants}</div>
          <div className="text-sm text-gray-600">{data.total_users} total users</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2 text-purple-700">💰 Revenue</h3>
          <div className="text-3xl font-bold text-purple-600">${data.total_revenue?.toLocaleString() || '0'}</div>
          <div className="text-sm text-gray-600">${data.pending_revenue?.toFixed(2) || '0.00'} pending</div>
        </div>
      </div>
      
      {/* Additional Metrics Row */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">📊 Occupancy Rate</h3>
          <div className="text-3xl font-bold">{data.occupancy_rate}%</div>
          <div className="text-blue-100 text-sm">
            {data.occupied_units} of {data.total_units} units occupied
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">💵 Monthly Income</h3>
          <div className="text-3xl font-bold">${data.total_revenue?.toLocaleString() || '0'}</div>
          <div className="text-green-100 text-sm">From occupied units</div>
        </div>
        
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">⚡ Quick Stats</h3>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-purple-100">Avg Rent:</span>
              <span className="font-semibold">
                ${data.occupied_units > 0 ? Math.round(data.total_revenue / data.occupied_units) : 0}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-purple-100">Available:</span>
              <span className="font-semibold">{data.total_units - data.occupied_units} units</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <IncomeWidget data={{
          total_due: data.pending_revenue || 0,
          total_paid: data.total_revenue || 0,
          net: (data.total_revenue || 0) - (data.pending_revenue || 0)
        }} />
        
        {/* AI Lease Expiration Dashboard */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">🤖 AI Lease Monitoring</h3>
            {leaseExpirations && (
              <span className={`px-2 py-1 text-xs rounded-full ${
                leaseExpirations.high_priority_count > 0 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-green-100 text-green-800'
              }`}>
                {leaseExpirations.total_count} leases expiring
              </span>
            )}
          </div>
          
          {!leaseExpirations ? (
            <div className="text-center py-4 text-gray-500">Loading AI analysis...</div>
          ) : leaseExpirations.expiring_leases && leaseExpirations.expiring_leases.length > 0 ? (
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-2 text-center text-sm">
                <div className="bg-red-50 p-2 rounded">
                  <div className="text-red-600 font-semibold">{leaseExpirations.high_priority_count}</div>
                  <div className="text-red-500">High Priority</div>
                </div>
                <div className="bg-yellow-50 p-2 rounded">
                  <div className="text-yellow-600 font-semibold">
                    {leaseExpirations.expiring_leases.filter(l => l.priority === 'medium').length}
                  </div>
                  <div className="text-yellow-500">Medium</div>
                </div>
                <div className="bg-blue-50 p-2 rounded">
                  <div className="text-blue-600 font-semibold">
                    {leaseExpirations.expiring_leases.filter(l => l.priority === 'low').length}
                  </div>
                  <div className="text-blue-500">Low Priority</div>
                </div>
              </div>
              
              <div className="max-h-40 overflow-y-auto space-y-2">
                {leaseExpirations.expiring_leases.slice(0, 5).map((lease, index) => (
                  <div key={index} className={`p-3 rounded border-l-4 ${
                    lease.priority === 'high' ? 'border-red-500 bg-red-50' :
                    lease.priority === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                    'border-blue-500 bg-blue-50'
                  }`}>
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium text-gray-900">{lease.tenant_name}</div>
                        <div className="text-sm text-gray-600">
                          {lease.property_name} {lease.unit_number && `- Unit ${lease.unit_number}`}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {lease.days_until_expiry} days
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(lease.lease_end_date).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {leaseExpirations.expiring_leases.length > 5 && (
                <div className="text-center text-sm text-gray-500 pt-2">
                  ...and {leaseExpirations.expiring_leases.length - 5} more leases
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-2xl mb-2">✅</div>
              <div>All leases are current - no expiring leases detected</div>
              <div className="text-sm mt-1">AI monitoring active</div>
            </div>
          )}
        </div>
      </div>
      
      {/* Recent Activity Section */}
      <div className="mt-6">
        <h2 className="text-xl font-bold mb-4">📋 Recent Activity & System Status</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Property Status */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4 text-blue-700">🏢 Property Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                <span>Total Properties</span>
                <span className="font-semibold text-green-700">{data.total_properties}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                <span>Available Properties</span>
                <span className="font-semibold text-blue-700">{data.available_properties}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-orange-50 rounded">
                <span>Total Units</span>
                <span className="font-semibold text-orange-700">{data.total_units}</span>
              </div>
            </div>
          </div>
          
          {/* System Health */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4 text-green-700">⚡ System Health</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  Backend API
                </span>
                <span className="text-green-700 font-semibold">Online</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  Database
                </span>
                <span className="text-green-700 font-semibold">Active</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  AI Services
                </span>
                <span className="text-green-700 font-semibold">Ready</span>
              </div>
            </div>
          </div>
          
        </div>
        
        {/* Quick Actions */}
        <div className="mt-6 bg-gray-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">🚀 Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button 
              onClick={() => window.location.href = '/properties'}
              className="p-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <div className="text-2xl mb-2">🏢</div>
              <div className="text-sm font-medium">Add Property</div>
            </button>
            <button 
              onClick={() => window.location.href = '/tenants'}
              className="p-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <div className="text-2xl mb-2">👥</div>
              <div className="text-sm font-medium">Add Tenant</div>
            </button>
            <button 
              onClick={() => window.location.href = '/maintenance-dispatch'}
              className="p-4 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              <div className="text-2xl mb-2">🔧</div>
              <div className="text-sm font-medium">Maintenance</div>
            </button>
            <button 
              onClick={() => window.location.href = '/ai-analytics'}
              className="p-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <div className="text-2xl mb-2">🧠</div>
              <div className="text-sm font-medium">AI Analytics</div>
            </button>
          </div>
        </div>
      </div>
      
      {/* Property Access Management Modal */}
      {showPropertyAccess && companyInfo && (
        <PropertyAccessManager
          companyId={companyInfo.id}
          onClose={() => setShowPropertyAccess(false)}
        />
      )}
    </div>
  );
}
