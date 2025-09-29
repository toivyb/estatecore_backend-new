import React, { useState } from 'react';
import api from '../api';

export default function OTPLogin({ onLoginSuccess, onSwitchToRegularLogin }) {
  const [step, setStep] = useState('otp'); // 'otp' or 'password_change'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [otpData, setOtpData] = useState({
    email: '',
    otp: ''
  });
  
  const [passwordData, setPasswordData] = useState({
    new_password: '',
    confirm_password: '',
    temporary_token: ''
  });

  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/auth/login', {
        email: otpData.email,
        otp: otpData.otp
      });

      if (response.success) {
        if (response.requires_password_change) {
          // Move to password change step
          setPasswordData(prev => ({
            ...prev,
            temporary_token: response.temporary_token
          }));
          setStep('password_change');
        } else {
          // Login successful
          onLoginSuccess(response);
        }
      } else {
        setError(response.error || 'Login failed');
      }
    } catch (error) {
      console.error('OTP login error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (passwordData.new_password.length < 8) {
      setError('Password must be at least 8 characters long');
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/api/auth/set-password', {
        email: otpData.email,
        temporary_token: passwordData.temporary_token,
        new_password: passwordData.new_password,
        confirm_password: passwordData.confirm_password
      });

      if (response.success) {
        onLoginSuccess(response);
      } else {
        setError(response.error || 'Password setup failed');
      }
    } catch (error) {
      console.error('Password setup error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/auth/resend-otp', {
        email: otpData.email
      });

      if (response.success) {
        alert(`New OTP sent to ${otpData.email}\nNew OTP: ${response.otp}`);
      } else {
        setError(response.error || 'Failed to resend OTP');
      }
    } catch (error) {
      console.error('Resend OTP error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (data, setData) => (e) => {
    const { name, value } = e.target;
    setData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            {step === 'otp' ? '🔐 First Time Login' : '🔑 Set Your Password'}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {step === 'otp' 
              ? 'Enter your email and the OTP sent to you'
              : 'Create a secure password for your account'
            }
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {step === 'otp' && (
          <form onSubmit={handleOTPSubmit} className="mt-8 space-y-6">
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email Address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={otpData.email}
                  onChange={handleInputChange(otpData, setOtpData)}
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="Enter your email address"
                />
              </div>

              <div>
                <label htmlFor="otp" className="block text-sm font-medium text-gray-700">
                  One-Time Password (OTP)
                </label>
                <input
                  id="otp"
                  name="otp"
                  type="text"
                  required
                  value={otpData.otp}
                  onChange={handleInputChange(otpData, setOtpData)}
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm font-mono text-center text-lg"
                  placeholder="Enter OTP from your email"
                  maxLength="8"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Check your email for the 8-character OTP code
                </p>
              </div>
            </div>

            <div className="flex flex-col space-y-3">
              <button
                type="submit"
                disabled={loading || !otpData.email || !otpData.otp}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Verifying...
                  </div>
                ) : (
                  'Verify OTP'
                )}
              </button>

              {otpData.email && (
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  📧 Resend OTP
                </button>
              )}

              <button
                type="button"
                onClick={onSwitchToRegularLogin}
                className="w-full text-center text-sm text-blue-600 hover:text-blue-500"
              >
                ← Switch to regular login
              </button>
            </div>
          </form>
        )}

        {step === 'password_change' && (
          <form onSubmit={handlePasswordChange} className="mt-8 space-y-6">
            <div className="bg-green-50 p-4 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-green-800">
                    ✅ OTP verified successfully! Now create your secure password.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label htmlFor="new_password" className="block text-sm font-medium text-gray-700">
                  New Password
                </label>
                <input
                  id="new_password"
                  name="new_password"
                  type="password"
                  required
                  value={passwordData.new_password}
                  onChange={handleInputChange(passwordData, setPasswordData)}
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="Create a secure password"
                  minLength="8"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Minimum 8 characters required
                </p>
              </div>

              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">
                  Confirm Password
                </label>
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type="password"
                  required
                  value={passwordData.confirm_password}
                  onChange={handleInputChange(passwordData, setPasswordData)}
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="Confirm your password"
                />
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-md">
              <h4 className="text-sm font-medium text-blue-900 mb-2">Password Requirements:</h4>
              <ul className="text-xs text-blue-800 space-y-1">
                <li className={passwordData.new_password.length >= 8 ? 'text-green-600' : ''}>
                  • At least 8 characters long
                </li>
                <li className={passwordData.new_password !== passwordData.confirm_password && passwordData.confirm_password ? 'text-red-600' : passwordData.new_password === passwordData.confirm_password && passwordData.confirm_password ? 'text-green-600' : ''}>
                  • Passwords must match
                </li>
                <li>• Mix of letters, numbers, and symbols recommended</li>
              </ul>
            </div>

            <button
              type="submit"
              disabled={loading || !passwordData.new_password || !passwordData.confirm_password}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Setting Password...
                </div>
              ) : (
                '🔐 Set Password & Login'
              )}
            </button>
          </form>
        )}

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Having trouble? Contact your administrator for assistance.
          </p>
        </div>
      </div>
    </div>
  );
}