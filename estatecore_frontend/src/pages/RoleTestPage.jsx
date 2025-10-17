import React, { useState, useEffect } from 'react';
import api from '../api';

const RoleTestPage = () => {
  const [userRole, setUserRole] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    setUserRole(user.role || 'unknown');
  }, []);

  const testRoleEndpoint = async () => {
    setLoading(true);
    setError('');
    setDashboardData(null);

    try {
      let endpoint = '';
      switch (userRole) {
        case 'tenant':
          endpoint = '/api/portal/tenant/dashboard';
          break;
        case 'property_manager':
          endpoint = '/api/portal/property-manager/dashboard';
          break;
        case 'maintenance_personnel':
        case 'maintenance_supervisor':
          endpoint = '/api/portal/maintenance/dashboard';
          break;
        case 'company_admin':
        case 'admin':
        case 'super_admin':
          endpoint = '/api/portal/company-admin/dashboard';
          break;
        default:
          endpoint = '/api/dashboard';
      }

      const response = await api.get(endpoint);
      if (response.success) {
        setDashboardData(response.data);
      } else {
        setError(response.error || 'Failed to fetch data');
      }
    } catch (err) {
      setError('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const testUnauthorizedAccess = async () => {
    setLoading(true);
    setError('');

    try {
      // Try to access a restricted endpoint
      const response = await api.get('/api/portal/property-manager/dashboard');
      if (response.success) {
        setError('⚠️ Security Issue: User was able to access unauthorized data!');
      } else {
        setError('✅ Security Working: ' + response.error);
      }
    } catch (err) {
      setError('✅ Security Working: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Role-Based Access Control Test</h1>
      
      {/* Current User Info */}
      <div className="bg-blue-50 p-4 rounded-lg mb-6">
        <h2 className="text-xl font-semibold mb-2">Current User</h2>
        <p><strong>Name:</strong> {user.username || 'Unknown'}</p>
        <p><strong>Email:</strong> {user.email || 'Unknown'}</p>
        <p><strong>Role:</strong> <span className="font-mono bg-blue-200 px-2 py-1 rounded">{userRole}</span></p>
      </div>

      {/* Test Buttons */}
      <div className="mb-6 space-x-4">
        <button
          onClick={testRoleEndpoint}
          disabled={loading}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
        >
          {loading ? 'Loading...' : 'Test Role-Specific Data'}
        </button>
        
        <button
          onClick={testUnauthorizedAccess}
          disabled={loading}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400"
        >
          {loading ? 'Loading...' : 'Test Unauthorized Access'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className={`p-4 rounded-lg mb-6 ${
          error.includes('✅') ? 'bg-green-50 border border-green-200 text-green-700' : 
          error.includes('⚠️') ? 'bg-red-50 border border-red-200 text-red-700' :
          'bg-yellow-50 border border-yellow-200 text-yellow-700'
        }`}>
          <p>{error}</p>
        </div>
      )}

      {/* Dashboard Data Display */}
      {dashboardData && (
        <div className="bg-gray-50 p-6 rounded-lg">
          <h3 className="text-xl font-semibold mb-4">Role-Specific Dashboard Data</h3>
          <pre className="bg-white p-4 rounded border overflow-auto max-h-96 text-sm">
            {JSON.stringify(dashboardData, null, 2)}
          </pre>
        </div>
      )}

      {/* Role-Specific Instructions */}
      <div className="mt-6 bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Expected Behavior for {userRole}:</h3>
        <div className="text-sm text-gray-700">
          {userRole === 'tenant' && (
            <ul className="list-disc list-inside space-y-1">
              <li>Should see only their own tenant data (payments, maintenance requests)</li>
              <li>Should NOT see other tenants' data</li>
              <li>Should NOT see property management data</li>
            </ul>
          )}
          {userRole === 'property_manager' && (
            <ul className="list-disc list-inside space-y-1">
              <li>Should see only properties they manage</li>
              <li>Should see tenants and units for their properties only</li>
              <li>Should NOT see properties managed by other managers</li>
            </ul>
          )}
          {(userRole === 'maintenance_personnel' || userRole === 'maintenance_supervisor') && (
            <ul className="list-disc list-inside space-y-1">
              <li>Personnel: Should see only work orders assigned to them</li>
              <li>Supervisor: Should see all work orders for their team</li>
              <li>Should NOT see admin or financial data</li>
            </ul>
          )}
          {(userRole === 'company_admin' || userRole === 'admin' || userRole === 'super_admin') && (
            <ul className="list-disc list-inside space-y-1">
              <li>Company Admin: Should see only their company's data</li>
              <li>Super Admin: Should see all companies and properties</li>
              <li>Should have access to all management functions</li>
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default RoleTestPage;