
import React, { useState } from "react";

const RevenueLeakageDemo = () => {
  const [result, setResult] = useState(null);
  const [form, setForm] = useState({
    units: 0,
    expected_rent: 0,
    actual_collected: 0
  });

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: Number(e.target.value) });
  };

  const handleSubmit = async () => {
    const res = await fetch("/api/ai/detect-leakage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form)
    });
    const data = await res.json();
    setResult(data.leakage_status);
  };

  return (
    <div className="p-4 border rounded bg-white">
      <h2 className="text-lg font-bold mb-2">Revenue Leakage Detection</h2>
      <input name="units" type="number" placeholder="Units" onChange={handleChange} className="border p-1 m-1" />
      <input name="expected_rent" type="number" placeholder="Expected Rent" onChange={handleChange} className="border p-1 m-1" />
      <input name="actual_collected" type="number" placeholder="Actual Collected" onChange={handleChange} className="border p-1 m-1" />
      <button onClick={handleSubmit} className="bg-blue-500 text-white px-4 py-1 rounded m-1">Submit</button>
      {result && <div className="mt-2">Status: <strong>{result}</strong></div>}
    </div>
  );
};

export default RevenueLeakageDemo;
