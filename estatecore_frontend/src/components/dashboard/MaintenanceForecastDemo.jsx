
import React, { useState } from "react";

const MaintenanceForecastDemo = () => {
  const [result, setResult] = useState(null);
  const [form, setForm] = useState({
    age_months: 0,
    last_service_months_ago: 0,
    incident_reports: 0
  });

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: Number(e.target.value) });
  };

  const handleSubmit = async () => {
    const res = await fetch("/api/ai/forecast-maintenance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form)
    });
    const data = await res.json();
    setResult(data.maintenance_risk);
  };

  return (
    <div className="p-4 border rounded bg-white">
      <h2 className="text-lg font-bold mb-2">Maintenance Forecast</h2>
      <input name="age_months" type="number" placeholder="Age (months)" onChange={handleChange} className="border p-1 m-1" />
      <input name="last_service_months_ago" type="number" placeholder="Last Service (months)" onChange={handleChange} className="border p-1 m-1" />
      <input name="incident_reports" type="number" placeholder="Incident Reports" onChange={handleChange} className="border p-1 m-1" />
      <button onClick={handleSubmit} className="bg-blue-500 text-white px-4 py-1 rounded m-1">Submit</button>
      {result && <div className="mt-2">Forecast: <strong>{result}</strong></div>}
    </div>
  );
};

export default MaintenanceForecastDemo;
