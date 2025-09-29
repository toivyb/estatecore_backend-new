import React, { useRef } from 'react';
import axios from 'axios';

export default function BulkUploadRent({ onSuccess }) {
  const fileRef = useRef();

  const handleUpload = async () => {
    const file = fileRef.current.files[0];
    const formData = new FormData();
    formData.append('file', file);
    await axios.post('/api/rent/bulk_upload', formData);
    onSuccess();
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <label className="block text-lg font-semibold mb-2">Bulk Upload Rent Records</label>
      <input ref={fileRef} type="file" accept=".csv,.json" className="mb-2" />
      <button onClick={handleUpload} className="bg-blue-600 text-white px-4 py-2 rounded-lg">Upload</button>
    </div>
  );
}
