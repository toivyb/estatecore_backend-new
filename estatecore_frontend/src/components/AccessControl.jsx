import React, { useState } from "react";

const AccessControl = () => {
  const [licensePlate, setLicensePlate] = useState("");
  const [locationId, setLocationId] = useState("");
  const [result, setResult] = useState("");

  const checkAccess = async () => {
    setResult("Checking...");

    try {
      const response = await fetch("http://localhost:5000/access/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          license_plate: licensePlate,
          location_id: locationId,
        }),
      });

      const contentType = response.headers.get("content-type");

      if (contentType && contentType.includes("application/json")) {
        const data = await response.json();
        setResult(JSON.stringify(data));
      } else {
        const text = await response.text();
        setResult(`Unexpected response:\n${text}`);
      }
    } catch (error) {
      setResult(`Error: ${error.message}`);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl mb-2 font-bold">Access Control Check</h2>
      <input
        type="text"
        placeholder="License Plate"
        value={licensePlate}
        onChange={(e) => setLicensePlate(e.target.value)}
        className="border p-2 mr-2"
      />
      <input
        type="text"
        placeholder="Location ID"
        value={locationId}
        onChange={(e) => setLocationId(e.target.value)}
        className="border p-2 mr-2"
      />
      <button onClick={checkAccess} className="bg-blue-500 text-white px-4 py-2 rounded">
        Check Access
      </button>
      <pre className="mt-4 bg-gray-100 p-2 rounded">{result}</pre>
    </div>
  );
};

export default AccessControl;