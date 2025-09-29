
import React, { useState } from "react";

const RentDelayDemo = () => {
  const [result, setResult] = useState(null);
  const [form, setForm] = useState({
    late_payments: 0,
    average_days_late: 0,
    months_paid_on_time: 0
  });

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: Number(e.target.value) });
  };

  const handleSubmit = async () => {
    const res = await fetch("/api/ai/predict-delay", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form)
    });
    const data = await res.json();
    setResult(data.delay_prediction);
  };

  return (
    <div className="p-4 border rounded bg-white">
      <h2 className="text-lg font-bold mb-2">Rent Delay Prediction</h2>
      <input name="late_payments" type="number" placeholder="Late Payments" onChange={handleChange} className="border p-1 m-1" />
      <input name="average_days_late" type="number" placeholder="Avg Days Late" onChange={handleChange} className="border p-1 m-1" />
      <input name="months_paid_on_time" type="number" placeholder="Months Paid On Time" onChange={handleChange} className="border p-1 m-1" />
      <button onClick={handleSubmit} className="bg-blue-500 text-white px-4 py-1 rounded m-1">Submit</button>
      {result && <div className="mt-2">Prediction: <strong>{result}</strong></div>}
    </div>
  );
};

export default RentDelayDemo;
