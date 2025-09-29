import React from 'react';
import Layout from '../components/Layout';
import RoleManager from '../components/RoleManager';
import PermissionGuard from '../components/PermissionGuard';

const RolesPermissions = () => {
  return (
    <Layout>
      <PermissionGuard
        permission="manage_roles"
        fallback={
          <div className="container mx-auto px-4 py-8">
            <div className="text-center">
              <div className="text-6xl mb-4">🔒</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
              <p className="text-gray-600">
                You don't have permission to manage roles and permissions.
              </p>
            </div>
          </div>
        }
      >
        <div className="container mx-auto px-4 py-8">
          <RoleManager />
        </div>
      </PermissionGuard>
    </Layout>
  );
};

export default RolesPermissions;