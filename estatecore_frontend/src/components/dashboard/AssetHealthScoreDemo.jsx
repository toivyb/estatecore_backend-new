
import React, { useState } from "react";

const AssetHealthScoreDemo = () => {
  const [result, setResult] = useState(null);
  const [form, setForm] = useState({
    open_issues: 0,
    net_profit: 0,
    vacancy_rate: 0
  });

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: Number(e.target.value) });
  };

  const handleSubmit = async () => {
    const res = await fetch("/api/ai/health-score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form)
    });
    const data = await res.json();
    setResult(data.asset_health);
  };

  return (
    <div className="p-4 border rounded bg-white">
      <h2 className="text-lg font-bold mb-2">Asset Health Score</h2>
      <input name="open_issues" type="number" placeholder="Open Issues" onChange={handleChange} className="border p-1 m-1" />
      <input name="net_profit" type="number" placeholder="Net Profit" onChange={handleChange} className="border p-1 m-1" />
      <input name="vacancy_rate" type="number" placeholder="Vacancy Rate" step="0.01" onChange={handleChange} className="border p-1 m-1" />
      <button onClick={handleSubmit} className="bg-blue-500 text-white px-4 py-1 rounded m-1">Submit</button>
      {result && <div className="mt-2">Health: <strong>{result}</strong></div>}
    </div>
  );
};

export default AssetHealthScoreDemo;
