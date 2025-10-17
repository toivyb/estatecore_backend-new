import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'; // ✅ default import
import QuickLogin from '../components/QuickLogin';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    // For development: bypass authentication
    if (email === 'toivybraun@gmail.com' && password === 'Unique3315!') {
      localStorage.setItem('token', 'super-admin-token');
      localStorage.setItem('user', JSON.stringify({
        id: 1,
        email: 'toivybraun@gmail.com',
        username: 'Toivy Braun',
        role: 'super_admin',
        isAdmin: true
      }));
      // Trigger custom event to notify App component
      window.dispatchEvent(new Event('loginStateChange'));
      navigate('/');
      return;
    }
    
    if (email === 'demo@estatecore.com' && password === 'demo123') {
      localStorage.setItem('token', 'demo-token');
      localStorage.setItem('user', JSON.stringify({
        id: 2,
        email: 'demo@estatecore.com',
        username: 'Demo User',
        role: 'admin',
        isAdmin: true
      }));
      // Trigger custom event to notify App component
      window.dispatchEvent(new Event('loginStateChange'));
      navigate('/');
      return;
    }

    try {
      const res = await fetch(`${api.BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || 'Login failed');
      }

      const data = await res.json();
      if (data.token) {
        localStorage.setItem('token', data.token);
      }
      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }

      // Trigger custom event to notify App component
      window.dispatchEvent(new Event('loginStateChange'));
      navigate('/');
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Something went wrong. Try demo@estatecore.com / demo123');
    }
  };

  return (
    <div className="flex justify-center items-center h-screen bg-gray-100">
      <form
        onSubmit={handleLogin}
        className="bg-white p-6 rounded shadow-md w-80"
      >
        <h2 className="text-2xl font-bold mb-4 text-center">Login</h2>
        
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-sm">
          <strong>Super Admin:</strong><br/>
          Email: toivybraun@gmail.com<br/>
          Password: Unique3315!
        </div>
        
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm">
          <strong>Demo Login:</strong><br/>
          Email: demo@estatecore.com<br/>
          Password: demo123
        </div>
        
        <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded text-sm">
          <strong>Backend Admin:</strong><br/>
          Email: admin@estatecore.com<br/>
          Password: admin
        </div>

        {error && <p className="text-red-500 mb-3">{error}</p>}

        <input
          type="email"
          placeholder="Email"
          className="border p-2 w-full mb-3 rounded"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="username"
          required
        />

        <input
          type="password"
          placeholder="Password"
          className="border p-2 w-full mb-4 rounded"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        <button
          type="submit"
          className="bg-blue-500 text-white py-2 rounded w-full hover:bg-blue-600 transition"
        >
          Login
        </button>
      </form>
      
      <QuickLogin />
    </div>
  );
}
