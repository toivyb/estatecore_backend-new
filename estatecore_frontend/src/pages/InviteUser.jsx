import React, { useState, useEffect } from 'react';
import { ROLES, LPR_PERMISSIONS, ACCESS_TYPES } from '../utils/roles';
import api from '../api';

export default function InviteUser() {
  const [formData, setFormData] = useState({
    email: '',
    accessType: '',
    propertyRole: '',
    lprRole: '',
    lprCompanyId: '',
    lprPermissions: '',
  });

  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  useEffect(() => {
    fetchLPRCompanies();
  }, []);

  const fetchLPRCompanies = async () => {
    try {
      const response = await fetch(`${api.BASE}/api/lpr/companies`);
      if (response.ok) {
        const data = await response.json();
        setCompanies(Array.isArray(data) ? data : []);
      } else {
        setCompanies([]);
      }
    } catch (error) {
      console.error('Error fetching companies:', error);
      setCompanies([]);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Reset dependent fields when access type changes
    if (name === 'accessType') {
      setFormData(prev => ({
        ...prev,
        propertyRole: '',
        lprRole: '',
        lprCompanyId: '',
        lprPermissions: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      // Validate required fields
      if (!formData.email || !formData.accessType) {
        setMessage('Email and access type are required');
        setMessageType('error');
        return;
      }

      if (formData.accessType === ACCESS_TYPES.PROPERTY_MANAGEMENT && !formData.propertyRole) {
        setMessage('Property role is required for property management access');
        setMessageType('error');
        return;
      }

      if (formData.accessType === ACCESS_TYPES.LPR_MANAGEMENT && (!formData.lprRole || !formData.lprCompanyId || !formData.lprPermissions)) {
        setMessage('LPR role, company, and permissions are required for LPR management access');
        setMessageType('error');
        return;
      }

      if (formData.accessType === ACCESS_TYPES.BOTH && (!formData.propertyRole || !formData.lprRole || !formData.lprCompanyId || !formData.lprPermissions)) {
        setMessage('All fields are required for combined access');
        setMessageType('error');
        return;
      }

      // Prepare invite data
      const inviteData = {
        email: formData.email,
        access_type: formData.accessType,
        property_management_access: formData.accessType === ACCESS_TYPES.PROPERTY_MANAGEMENT || formData.accessType === ACCESS_TYPES.BOTH,
        lpr_management_access: formData.accessType === ACCESS_TYPES.LPR_MANAGEMENT || formData.accessType === ACCESS_TYPES.BOTH,
        property_role: formData.propertyRole,
        lpr_role: formData.lprRole,
        lpr_company_id: formData.lprCompanyId ? parseInt(formData.lprCompanyId) : null,
        lpr_permissions: formData.lprPermissions,
      };

      const response = await fetch(`${api.BASE}/api/invites/send-enhanced`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(inviteData),
      });

      const result = await response.json();

      if (response.ok) {
        setMessage(`Invitation sent successfully to ${formData.email}`);
        setMessageType('success');
        // Reset form
        setFormData({
          email: '',
          accessType: '',
          propertyRole: '',
          lprRole: '',
          lprCompanyId: '',
          lprPermissions: '',
        });
      } else {
        setMessage(result.error || 'Failed to send invitation');
        setMessageType('error');
      }
    } catch (error) {
      setMessage('Network error occurred');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-8 p-6 bg-white shadow-lg rounded-lg">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Invite New User</h2>
      
      {message && (
        <div className={`mb-4 p-4 rounded-md ${
          messageType === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Email */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
            Email Address *
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="user@example.com"
          />
        </div>

        {/* Access Type */}
        <div>
          <label htmlFor="accessType" className="block text-sm font-medium text-gray-700 mb-2">
            Access Type *
          </label>
          <select
            id="accessType"
            name="accessType"
            value={formData.accessType}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select access type...</option>
            <option value={ACCESS_TYPES.PROPERTY_MANAGEMENT}>Property Management Only</option>
            <option value={ACCESS_TYPES.LPR_MANAGEMENT}>LPR Management Only</option>
            <option value={ACCESS_TYPES.BOTH}>Both Property and LPR Management</option>
          </select>
        </div>

        {/* Property Management Role */}
        {(formData.accessType === ACCESS_TYPES.PROPERTY_MANAGEMENT || formData.accessType === ACCESS_TYPES.BOTH) && (
          <div className="bg-blue-50 p-4 rounded-md">
            <h3 className="text-lg font-medium text-blue-900 mb-3">Property Management Settings</h3>
            <div>
              <label htmlFor="propertyRole" className="block text-sm font-medium text-gray-700 mb-2">
                Property Role *
              </label>
              <select
                id="propertyRole"
                name="propertyRole"
                value={formData.propertyRole}
                onChange={handleInputChange}
                required={formData.accessType === ACCESS_TYPES.PROPERTY_MANAGEMENT || formData.accessType === ACCESS_TYPES.BOTH}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select property role...</option>
                <option value={ROLES.MANAGER}>Property Manager</option>
                <option value={ROLES.ADMIN}>Property Admin</option>
                <option value={ROLES.USER}>Property User</option>
              </select>
            </div>
          </div>
        )}

        {/* LPR Management Settings */}
        {(formData.accessType === ACCESS_TYPES.LPR_MANAGEMENT || formData.accessType === ACCESS_TYPES.BOTH) && (
          <div className="bg-green-50 p-4 rounded-md">
            <h3 className="text-lg font-medium text-green-900 mb-3">LPR Management Settings</h3>
            
            {/* LPR Company */}
            <div className="mb-4">
              <label htmlFor="lprCompanyId" className="block text-sm font-medium text-gray-700 mb-2">
                LPR Company *
              </label>
              <select
                id="lprCompanyId"
                name="lprCompanyId"
                value={formData.lprCompanyId}
                onChange={handleInputChange}
                required={formData.accessType === ACCESS_TYPES.LPR_MANAGEMENT || formData.accessType === ACCESS_TYPES.BOTH}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select company...</option>
                {companies.map(company => (
                  <option key={company.id} value={company.id}>
                    {company.name} ({company.user_count || 0} users)
                  </option>
                ))}
              </select>
            </div>

            {/* LPR Role */}
            <div className="mb-4">
              <label htmlFor="lprRole" className="block text-sm font-medium text-gray-700 mb-2">
                LPR Role *
              </label>
              <select
                id="lprRole"
                name="lprRole"
                value={formData.lprRole}
                onChange={handleInputChange}
                required={formData.accessType === ACCESS_TYPES.LPR_MANAGEMENT || formData.accessType === ACCESS_TYPES.BOTH}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select LPR role...</option>
                <option value={ROLES.LPR_ADMIN}>LPR Administrator</option>
                <option value={ROLES.LPR_MANAGER}>LPR Manager</option>
                <option value={ROLES.LPR_VIEWER}>LPR Viewer</option>
              </select>
            </div>

            {/* LPR Permissions */}
            <div>
              <label htmlFor="lprPermissions" className="block text-sm font-medium text-gray-700 mb-2">
                LPR Permissions *
              </label>
              <select
                id="lprPermissions"
                name="lprPermissions"
                value={formData.lprPermissions}
                onChange={handleInputChange}
                required={formData.accessType === ACCESS_TYPES.LPR_MANAGEMENT || formData.accessType === ACCESS_TYPES.BOTH}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select permissions...</option>
                <option value={LPR_PERMISSIONS.VIEW_ONLY}>View Only - Can only view LPR data</option>
                <option value={LPR_PERMISSIONS.MANAGE_ALERTS}>Manage Alerts - Can view and create/edit alerts</option>
                <option value={LPR_PERMISSIONS.FULL_ACCESS}>Full Access - Complete LPR management</option>
              </select>
            </div>

            <div className="mt-3 text-sm text-gray-600">
              <p><strong>Permission Details:</strong></p>
              <ul className="list-disc list-inside mt-1">
                <li><strong>View Only:</strong> Access to dashboards and reports, cannot modify anything</li>
                <li><strong>Manage Alerts:</strong> Can add/remove plates from blacklists and configure alerts</li>
                <li><strong>Full Access:</strong> Complete system access including user management and settings</li>
              </ul>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => window.history.back()}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Sending...' : 'Send Invitation'}
          </button>
        </div>
      </form>
    </div>
  );
}