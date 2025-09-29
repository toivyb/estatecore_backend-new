import React, { useEffect, useState } from 'react';
import axios from 'axios';

const MaintenanceRequests = () => {
  const [requests, setRequests] = useState([]);
  const [form, setForm] = useState({ title: '', description: '' });
  const [loading, setLoading] = useState(false);

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    try {
      const res = await axios.get('/api/maintenance-requests', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRequests(res.data);
    } catch (err) {
      console.error('Error fetching requests', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title || !form.description) return;

    setLoading(true);
    try {
      await axios.post('/api/maintenance-request', form, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setForm({ title: '', description: '' });
      fetchRequests();
    } catch (err) {
      console.error('Submission failed', err);
    }
    setLoading(false);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4">Submit Maintenance Request</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          placeholder="Title"
          className="w-full border px-3 py-2"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
        />
        <textarea
          placeholder="Description"
          className="w-full border px-3 py-2"
          rows={4}
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2"
          disabled={loading}
        >
          {loading ? 'Submitting...' : 'Submit'}
        </button>
      </form>

      <hr className="my-6" />

      <h3 className="text-xl font-semibold mb-2">My Requests</h3>
      <ul className="space-y-2">
        {requests.map((req) => (
          <li key={req.id} className="border p-3 rounded">
            <div className="font-bold">{req.title}</div>
            <div className="text-sm text-gray-600">{req.description}</div>
            <div className="text-xs text-gray-400">Status: {req.status}</div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default MaintenanceRequests;
