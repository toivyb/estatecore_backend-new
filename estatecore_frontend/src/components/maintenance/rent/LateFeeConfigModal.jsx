import React, { useState } from 'react';
import axios from 'axios';

export default function LateFeeConfigModal({ propertyId, onClose }) {
  const [fee, setFee] = useState(50);
  const [grace, setGrace] = useState(5);

  const save = async () => {
    await axios.post(`/api/property/${propertyId}/late_fee`, { late_fee_per_day: fee, late_fee_grace_days: grace });
    onClose();
  };

  return (
    <div className="fixed top-0 left-0 w-full h-full bg-black/30 flex justify-center items-center">
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <div>
          <label>Late Fee Per Day: </label>
          <input type="number" value={fee} onChange={e => setFee(e.target.value)} className="border p-1" />
        </div>
        <div>
          <label>Grace Period (days): </label>
          <input type="number" value={grace} onChange={e => setGrace(e.target.value)} className="border p-1" />
        </div>
        <div className="flex mt-4">
          <button onClick={save} className="bg-blue-600 text-white px-4 py-2 rounded-lg mr-2">Save</button>
          <button onClick={onClose} className="bg-gray-300 px-4 py-2 rounded-lg">Cancel</button>
        </div>
      </div>
    </div>
  );
}
