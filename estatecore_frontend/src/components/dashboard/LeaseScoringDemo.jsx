import React, { useState } from "react";

const LeaseScoringDemo = () => {
  const [result, setResult] = useState(null);
  const [form, setForm] = useState({ late_payments: 0, on_time_months: 0, complaints: 0 });

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: Number(e.target.value) });
  };

  const handleSubmit = async () => {
    const res = await fetch("/api/ai/score-lease", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form)
    });
    const data = await res.json();
    setResult(data.risk);
  };

  return (
    <div className="p-4 border rounded bg-white">
      <h2 className="text-lg font-bold mb-2">Lease Scoring</h2>
      <input name="late_payments" type="number" placeholder="Late Payments" onChange={handleChange} className="border p-1 m-1" />
      <input name="on_time_months" type="number" placeholder="On Time Months" onChange={handleChange} className="border p-1 m-1" />
      <input name="complaints" type="number" placeholder="Complaints" onChange={handleChange} className="border p-1 m-1" />
      <button onClick={handleSubmit} className="bg-blue-500 text-white px-4 py-1 rounded m-1">Submit</button>
      {result && <div className="mt-2">Prediction: <strong>{result}</strong></div>}
    </div>
  );
};

export default LeaseScoringDemo;
