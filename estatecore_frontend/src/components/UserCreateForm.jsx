import React, { useState } from 'react';
import api from '../api';

export default function UserCreateForm({ companies, onUserCreated, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    role: 'property_manager',
    company_id: '',
    use_otp: true, // Default to OTP method
    temp_password: '',
    property_access: []
  });
  
  const [loading, setLoading] = useState(false);
  const [createdUser, setCreatedUser] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/api/users', formData);
      
      if (response.success) {
        setCreatedUser(response);
        
        // Show success message with OTP or setup method
        if (response.setup_method === 'otp') {
          alert(`User created successfully!\n\nOTP has been sent to ${formData.email}\nOTP: ${response.otp}\n\nThe user will need to use this OTP to log in and set their password.`);
        } else {
          alert(`User created successfully!\n\nPassword setup link has been sent to ${formData.email}`);
        }
        
        if (onUserCreated) {
          onUserCreated(response);
        }
      } else {
        alert(`Error creating user: ${response.error}`);
      }
    } catch (error) {
      console.error('Error creating user:', error);
      alert('Network error occurred while creating user.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const roleOptions = [
    { value: 'super_admin', label: 'Super Admin', description: 'Full system access' },
    { value: 'company_admin', label: 'Company Admin', description: 'Full access to company data' },
    { value: 'property_admin', label: 'Property Admin', description: 'Manage assigned properties' },
    { value: 'property_manager', label: 'Property Manager', description: 'Day-to-day operations' },
    { value: 'maintenance_personnel', label: 'Maintenance Personnel', description: 'Handle assigned maintenance work orders' },
    { value: 'maintenance_supervisor', label: 'Maintenance Supervisor', description: 'Supervise maintenance team and all work orders' },
    { value: 'tenant', label: 'Tenant', description: 'Tenant portal access' },
    { value: 'viewer', label: 'Viewer', description: 'Read-only access' }
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black opacity-50" onClick={onCancel}></div>
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Create New User</h3>
            <p className="text-sm text-gray-600">Add a new user to the system with secure authentication</p>
          </div>
          
          <form onSubmit={handleSubmit} className="px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Basic Information */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900 border-b pb-2">User Information</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter full name"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address *
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="user@company.com"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="(555) 123-4567"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company *
                  </label>
                  <select
                    name="company_id"
                    value={formData.company_id}
                    onChange={handleChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="">Select Company</option>
                    {companies.map(company => (
                      <option key={company.id} value={company.id}>
                        {company.name} ({company.subscription_plan})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Role and Security */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900 border-b pb-2">Role & Security</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    User Role *
                  </label>
                  <select
                    name="role"
                    value={formData.role}
                    onChange={handleChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    {roleOptions.map(role => (
                      <option key={role.value} value={role.value}>
                        {role.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {roleOptions.find(r => r.value === formData.role)?.description}
                  </p>
                </div>

                {/* Security Setup Method */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h5 className="font-medium text-blue-900 mb-3">🔐 Security Setup Method</h5>
                  
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <input
                        type="radio"
                        id="use_otp_yes"
                        name="use_otp"
                        checked={formData.use_otp === true}
                        onChange={() => setFormData(prev => ({ ...prev, use_otp: true, temp_password: '' }))}
                        className="mt-1"
                      />
                      <div>
                        <label htmlFor="use_otp_yes" className="block text-sm font-medium text-blue-900">
                          ✅ Generate OTP (Recommended)
                        </label>
                        <p className="text-xs text-blue-700">
                          Secure one-time password sent via email. User must change password on first login.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <input
                        type="radio"
                        id="use_otp_no"
                        name="use_otp"
                        checked={formData.use_otp === false}
                        onChange={() => setFormData(prev => ({ ...prev, use_otp: false }))}
                        className="mt-1"
                      />
                      <div>
                        <label htmlFor="use_otp_no" className="block text-sm font-medium text-blue-900">
                          🔗 Email Setup Link
                        </label>
                        <p className="text-xs text-blue-700">
                          Traditional email link for password setup. User clicks link to set password.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Temporary Password Option */}
                  {!formData.use_otp && (
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-blue-900 mb-1">
                        Temporary Password (Optional)
                      </label>
                      <input
                        type="password"
                        name="temp_password"
                        value={formData.temp_password}
                        onChange={handleChange}
                        className="w-full p-2 border border-blue-300 rounded focus:ring-1 focus:ring-blue-500"
                        placeholder="Leave empty for email-only setup"
                      />
                      <p className="text-xs text-blue-600 mt-1">
                        If provided, user can login immediately with this password
                      </p>
                    </div>
                  )}
                </div>

                {/* OTP Benefits */}
                {formData.use_otp && (
                  <div className="bg-green-50 p-3 rounded-lg">
                    <h6 className="font-medium text-green-900 mb-2">🛡️ OTP Benefits:</h6>
                    <ul className="text-xs text-green-800 space-y-1">
                      <li>• More secure than email links</li>
                      <li>• Cannot be intercepted or forwarded</li>
                      <li>• Forces strong password creation</li>
                      <li>• Immediate access after verification</li>
                      <li>• Automatically expires after use</li>
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Form Actions */}
            <div className="mt-6 pt-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !formData.name || !formData.email || !formData.company_id}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Creating...
                  </div>
                ) : (
                  `👤 Create User ${formData.use_otp ? 'with OTP' : 'with Email Link'}`
                )}
              </button>
            </div>
          </form>

          {/* Success Information */}
          {createdUser && (
            <div className="px-6 py-4 border-t border-gray-200 bg-green-50">
              <h4 className="font-medium text-green-900 mb-2">✅ User Created Successfully!</h4>
              {createdUser.setup_method === 'otp' ? (
                <div className="text-sm text-green-800">
                  <p>📧 OTP has been sent to: <strong>{formData.email}</strong></p>
                  <p>🔑 One-Time Password: <code className="bg-green-100 px-2 py-1 rounded">{createdUser.otp}</code></p>
                  <p>⚠️ User must use this OTP to log in and create their password.</p>
                </div>
              ) : (
                <div className="text-sm text-green-800">
                  <p>📧 Setup link has been sent to: <strong>{formData.email}</strong></p>
                  <p>🔗 User must click the link to set up their password.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}