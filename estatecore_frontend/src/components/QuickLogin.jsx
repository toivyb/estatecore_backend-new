import React from 'react';
import { useNavigate } from 'react-router-dom';

const QuickLogin = () => {
  const navigate = useNavigate();

  const handleQuickLogin = (userType) => {
    let userData;
    
    switch(userType) {
      case 'admin':
        userData = {
          id: 1,
          email: 'toivybraun@gmail.com',
          username: 'Toivy Braun',
          role: 'super_admin',
          isAdmin: true
        };
        break;
      case 'demo':
        userData = {
          id: 2,
          email: 'demo@estatecore.com',
          username: 'Demo User',
          role: 'admin',
          isAdmin: true
        };
        break;
      case 'tenant':
        userData = {
          id: 100,
          email: 'tenant@test.com',
          username: 'Test Tenant',
          role: 'tenant',
          isAdmin: false
        };
        break;
      case 'property_manager':
        userData = {
          id: 101,
          email: 'manager@test.com',
          username: 'Test Manager',
          role: 'property_manager',
          isAdmin: false
        };
        break;
      case 'maintenance':
        userData = {
          id: 102,
          email: 'maintenance@test.com',
          username: 'Test Maintenance',
          role: 'maintenance_personnel',
          isAdmin: false
        };
        break;
      case 'supervisor':
        userData = {
          id: 103,
          email: 'supervisor@test.com',
          username: 'Test Supervisor',
          role: 'maintenance_supervisor',
          isAdmin: false
        };
        break;
      default:
        return;
    }
    
    localStorage.setItem('token', `${userType}-token`);
    localStorage.setItem('user', JSON.stringify(userData));
    
    // Trigger custom event to notify App component
    window.dispatchEvent(new Event('loginStateChange'));
    navigate('/');
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-lg">
      <h3 className="text-lg font-semibold mb-4 text-center">Quick Access</h3>
      <div className="space-y-3">
        <button
          onClick={() => handleQuickLogin('admin')}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Login as Super Admin
        </button>
        <button
          onClick={() => handleQuickLogin('demo')}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          Login as Demo User
        </button>
        <button
          onClick={() => handleQuickLogin('tenant')}
          className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          Login as Tenant
        </button>
        <button
          onClick={() => handleQuickLogin('property_manager')}
          className="w-full px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
        >
          Login as Property Manager
        </button>
        <button
          onClick={() => handleQuickLogin('maintenance')}
          className="w-full px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
        >
          Login as Maintenance Personnel
        </button>
        <button
          onClick={() => handleQuickLogin('supervisor')}
          className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Login as Maintenance Supervisor
        </button>
      </div>
      <div className="mt-4 text-sm text-gray-600 text-center">
        <p>Or use the regular login form above</p>
      </div>
    </div>
  );
};

export default QuickLogin;