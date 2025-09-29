
import React, { useState } from "react";

const UtilityForecastDemo = () => {
  const [result, setResult] = useState(null);
  const [form, setForm] = useState({
    avg_temp: 0,
    occupants: 0,
    unit_size_sqft: 0
  });

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: Number(e.target.value) });
  };

  const handleSubmit = async () => {
    const res = await fetch("/api/ai/forecast-utility", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form)
    });
    const data = await res.json();
    setResult(data.utility_estimate);
  };

  return (
    <div className="p-4 border rounded bg-white">
      <h2 className="text-lg font-bold mb-2">Utility Forecast</h2>
      <input name="avg_temp" type="number" placeholder="Average Temp" onChange={handleChange} className="border p-1 m-1" />
      <input name="occupants" type="number" placeholder="Occupants" onChange={handleChange} className="border p-1 m-1" />
      <input name="unit_size_sqft" type="number" placeholder="Unit Size (sqft)" onChange={handleChange} className="border p-1 m-1" />
      <button onClick={handleSubmit} className="bg-blue-500 text-white px-4 py-1 rounded m-1">Submit</button>
      {result && <div className="mt-2">Forecast: <strong>{result}</strong></div>}
    </div>
  );
};

export default UtilityForecastDemo;
