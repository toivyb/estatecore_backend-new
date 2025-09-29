import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function MaintenanceTable() {
  const [requests, setRequests] = useState([]);
  const [status, setStatus] = useState('');
  const [propertyId, setPropertyId] = useState('');

  const fetchRequests = async () => {
    const params = {};
    if (status) params.status = status;
    if (propertyId) params.property_id = propertyId;
    const res = await axios.get('/api/maintenance', { params });
    setRequests(res.data.requests);
  };

  useEffect(() => {
    fetchRequests();
  }, [status, propertyId]);

  const updateStatus = async (id, newStatus) => {
    await axios.patch(`/api/maintenance/${id}`, { status: newStatus });
    fetchRequests();
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow mt-4">
      <div className="flex gap-4 mb-3">
        <input placeholder="Property ID" value={propertyId} onChange={e=>setPropertyId(e.target.value)} className="border rounded p-1"/>
        <select value={status} onChange={e=>setStatus(e.target.value)} className="border rounded p-1">
          <option value="">All</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="closed">Closed</option>
        </select>
      </div>
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th>ID</th><th>Property</th><th>Tenant</th><th>Description</th>
            <th>Status</th><th>Priority</th><th>Assigned To</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {requests.map(r => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.property_id}</td>
              <td>{r.tenant_id || '-'}</td>
              <td>{r.description}</td>
              <td>{r.status}</td>
              <td>{r.priority}</td>
              <td>{r.assigned_to || '-'}</td>
              <td>
                <button onClick={()=>updateStatus(r.id, 'in_progress')} className="bg-yellow-500 text-white px-2 py-1 rounded mr-1">In Progress</button>
                <button onClick={()=>updateStatus(r.id, 'closed')} className="bg-green-600 text-white px-2 py-1 rounded">Close</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
