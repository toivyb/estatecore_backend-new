
import React, { useState } from "react";
import axios from "axios";

const models = [
  { name: "Lease Model", endpoint: "train-lease" },
  { name: "Rent Delay Model", endpoint: "train-rent-delay" },
  { name: "Maintenance Model", endpoint: "train-maintenance" },
  { name: "Utility Model", endpoint: "train-utility" },
  { name: "Revenue Model", endpoint: "train-revenue" },
  { name: "Asset Health Model", endpoint: "train-asset-health" }
];

export default function ModelTrainingPanel() {
  const [status, setStatus] = useState("");

  const handleTrain = async (endpoint) => {
    try {
      setStatus("Training...");
      const res = await axios.post(`/api/train/${endpoint}`);
      setStatus(res.data.message);
    } catch (err) {
      setStatus("Error training model.");
    }
  };

  return (
    <div className="p-4 border rounded shadow bg-white">
      <h2 className="text-lg font-bold mb-2">AI Model Training</h2>
      {models.map((m) => (
        <div key={m.endpoint} className="flex items-center justify-between mb-2">
          <span>{m.name}</span>
          <button
            className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
            onClick={() => handleTrain(m.endpoint)}
          >
            Train
          </button>
        </div>
      ))}
      {status && <p className="mt-2 text-sm text-gray-600">{status}</p>}
    </div>
  );
}
