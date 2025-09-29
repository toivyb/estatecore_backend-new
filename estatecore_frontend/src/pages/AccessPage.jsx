import React, { useState } from "react";
import { checkAccess } from "../api";

export default function AccessPage() {
  const [userId, setUserId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [response, setResponse] = useState(null);

  const handleCheck = async () => {
    const data = await checkAccess(userId, locationId);
    setResponse(data);
  };

  return (
    <div className="p-4">
      <h2 className="text-xl mb-2">Access Control</h2>
      <input
        type="text"
        placeholder="User ID"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
        className="border p-1 mr-2"
      />
      <input
        type="text"
        placeholder="Location ID"
        value={locationId}
        onChange={(e) => setLocationId(e.target.value)}
        className="border p-1 mr-2"
      />
      <button onClick={handleCheck} className="bg-blue-500 text-white px-3 py-1 rounded">
        Check Access
      </button>
      {response && (
        <div className="mt-4">
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
