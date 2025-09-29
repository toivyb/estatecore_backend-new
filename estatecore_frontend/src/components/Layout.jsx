// src/components/Layout.jsx
import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import PermissionGuard, { PermissionStatus, usePermissions } from "./PermissionGuard";

export default function Layout() {
  const authData = useAuth();
  const permissionsData = usePermissions();
  
  // Handle null auth data safely
  const user = authData?.user || null;
  const logout = authData?.logout || (() => {});
  const hasPermission = permissionsData?.hasPermission || (() => false);
  const hasRole = permissionsData?.hasRole || (() => false);

  return (
    <>
      <header className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo/Brand */}
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-gray-900">EstateCore</h1>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex space-x-6">
              <NavLink 
                to="/dashboard" 
                className={({ isActive }) => 
                  `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive 
                      ? "bg-blue-100 text-blue-700" 
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  }`
                }
              >
                Dashboard
              </NavLink>
              
              <PermissionGuard permission="read_property">
                <NavLink 
                  to="/properties" 
                  className={({ isActive }) => 
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive 
                        ? "bg-blue-100 text-blue-700" 
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`
                  }
                >
                  Properties
                </NavLink>
              </PermissionGuard>

              <PermissionGuard permission="read_tenant">
                <NavLink 
                  to="/tenants" 
                  className={({ isActive }) => 
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive 
                        ? "bg-blue-100 text-blue-700" 
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`
                  }
                >
                  Tenants
                </NavLink>
              </PermissionGuard>

              <PermissionGuard permission="read_maintenance">
                <NavLink 
                  to="/maintenance" 
                  className={({ isActive }) => 
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive 
                        ? "bg-blue-100 text-blue-700" 
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`
                  }
                >
                  Maintenance
                </NavLink>
              </PermissionGuard>

              <PermissionGuard permission="read_payment">
                <NavLink 
                  to="/payments" 
                  className={({ isActive }) => 
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive 
                        ? "bg-blue-100 text-blue-700" 
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`
                  }
                >
                  Payments
                </NavLink>
              </PermissionGuard>

              <PermissionGuard permission="read_document">
                <NavLink 
                  to="/documents" 
                  className={({ isActive }) => 
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive 
                        ? "bg-blue-100 text-blue-700" 
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`
                  }
                >
                  Documents
                </NavLink>
              </PermissionGuard>

              <PermissionGuard permission="view_reports">
                <NavLink 
                  to="/reports" 
                  className={({ isActive }) => 
                    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive 
                        ? "bg-blue-100 text-blue-700" 
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                    }`
                  }
                >
                  Reports
                </NavLink>
              </PermissionGuard>

              {/* Admin Section */}
              <PermissionGuard 
                permissions={["manage_roles", "system_config", "view_audit_logs"]}
                requireAll={false}
              >
                <div className="relative group">
                  <button className="px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 flex items-center">
                    Admin
                    <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10 hidden group-hover:block">
                    <PermissionGuard permission="manage_roles">
                      <NavLink 
                        to="/admin/roles" 
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        Roles & Permissions
                      </NavLink>
                    </PermissionGuard>
                    
                    <PermissionGuard permission="read_user">
                      <NavLink 
                        to="/admin/users" 
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        User Management
                      </NavLink>
                    </PermissionGuard>
                    
                    <PermissionGuard permission="system_config">
                      <NavLink 
                        to="/admin/settings" 
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        System Settings
                      </NavLink>
                    </PermissionGuard>
                  </div>
                </div>
              </PermissionGuard>
            </nav>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <PermissionStatus />
              
              {user ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-700">
                    {user.first_name} {user.last_name}
                  </span>
                  <button 
                    onClick={logout} 
                    className="text-sm text-red-600 hover:text-red-800 font-medium"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <NavLink 
                  to="/login"
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Login
                </NavLink>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="min-h-screen bg-gray-50">
        {/* This is where nested routes will render */}
        <Outlet />
      </main>
    </>
  );
}
