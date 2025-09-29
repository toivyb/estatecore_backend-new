import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    const res = await axios.post('/api/login', { email, password });
    if (res.data.access_token) {
      localStorage.setItem('token', res.data.access_token);
      navigate('/dashboard');
    } else {
      alert('Login failed');
    }
  };

  return (
    <form onSubmit={handleLogin} className="p-4">
      <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" className="block mb-2 border p-1" />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" className="block mb-2 border p-1" />
      <button type="submit" className="bg-blue-600 text-white px-4 py-2">Login</button>
    </form>
);
}
