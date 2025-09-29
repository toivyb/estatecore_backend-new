import React, { useState } from 'react';
import axios from 'axios';

export default function CreateMaintenanceForm({ onSuccess }) {
  const [propertyId, setPropertyId] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('normal');

  const submit = async () => {
    await axios.post('/api/maintenance', { property_id: propertyId, description, priority });
    setPropertyId(''); setDescription(''); setPriority('normal');
    onSuccess();
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="text-lg font-bold mb-2">New Maintenance Request</h2>
      <input placeholder="Property ID" value={propertyId} onChange={e=>setPropertyId(e.target.value)} className="border mb-2 p-1 block w-full"/>
      <textarea placeholder="Description" value={description} onChange={e=>setDescription(e.target.value)} className="border mb-2 p-1 block w-full"/>
      <select value={priority} onChange={e=>setPriority(e.target.value)} className="border mb-2 p-1 block w-full">
        <option value="normal">Normal</option>
        <option value="urgent">Urgent</option>
      </select>
      <button onClick={submit} className="bg-blue-600 text-white px-4 py-2 rounded-lg">Create</button>
    </div>
  );
}
