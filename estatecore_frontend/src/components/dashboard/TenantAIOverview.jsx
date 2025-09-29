
import React, { useState } from "react";

const TenantAIOverview = ({ onSave }) => {
  const [visible, setVisible] = useState(false);
  const [result, setResult] = useState(null);
  const [form, setForm] = useState({
    late_payments: 0,
    on_time_months: 0,
    complaints: 0,
    average_days_late: 0,
    age_months: 0,
    last_service_months_ago: 0,
    incident_reports: 0,
    avg_temp: 0,
    occupants: 0,
    unit_size_sqft: 0,
    units: 0,
    expected_rent: 0,
    actual_collected: 0,
    net_profit: 0,
    open_issues: 0,
    vacancy_rate: 0,
  });

  const handleChange = e => {
    const value = e.target.type === "number" ? Number(e.target.value) : e.target.value;
    setForm({ ...form, [e.target.name]: value });
  };

  const handleSubmit = async () => {
    const [lease, delay, maintenance, utility, leakage, health] = await Promise.all([
      fetch("/api/ai/score-lease", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form)
      }).then(res => res.json()),
      fetch("/api/ai/predict-delay", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form)
      }).then(res => res.json()),
      fetch("/api/ai/forecast-maintenance", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form)
      }).then(res => res.json()),
      fetch("/api/ai/forecast-utility", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form)
      }).then(res => res.json()),
      fetch("/api/ai/detect-leakage", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form)
      }).then(res => res.json()),
      fetch("/api/ai/health-score", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form)
      }).then(res => res.json())
    ]);

    const combined = {
      lease_risk: lease.risk,
      delay_prediction: delay.delay_prediction,
      maintenance_risk: maintenance.maintenance_risk,
      utility_estimate: utility.utility_estimate,
      leakage_status: leakage.leakage_status,
      asset_health: health.asset_health
    };

    setResult(combined);

    if (onSave) {
      onSave({ input: form, output: combined });
    }
  };

  return (
    <div>
      <button onClick={() => setVisible(true)} className="bg-indigo-600 text-white px-4 py-2 rounded">
        Open Tenant AI Overview
      </button>

      {visible && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-start overflow-auto z-50 pt-10">
          <div className="bg-white p-6 rounded-lg w-full max-w-4xl relative shadow-xl">
            <button onClick={() => setVisible(false)} className="absolute top-2 right-2 text-gray-500 hover:text-black">&times;</button>
            <h2 className="text-2xl font-bold mb-4">Tenant AI Analysis</h2>
            
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(form).map(([key, value]) => (
                <input
                  key={key}
                  name={key}
                  type="number"
                  placeholder={key.replace(/_/g, ' ')}
                  value={value}
                  onChange={handleChange}
                  className="border p-1 text-sm"
                />
              ))}
            </div>

            <button onClick={handleSubmit} className="mt-4 bg-green-600 text-white px-4 py-2 rounded">Analyze</button>

            {result && (
              <div className="mt-6 bg-gray-50 p-4 rounded text-sm border">
                <h3 className="font-semibold mb-2">Results:</h3>
                <ul className="list-disc list-inside space-y-1">
                  <li><strong>Lease Risk:</strong> {result.lease_risk}</li>
                  <li><strong>Delay Prediction:</strong> {result.delay_prediction}</li>
                  <li><strong>Maintenance Risk:</strong> {result.maintenance_risk}</li>
                  <li><strong>Utility Estimate:</strong> {result.utility_estimate}</li>
                  <li><strong>Leakage Status:</strong> {result.leakage_status}</li>
                  <li><strong>Asset Health:</strong> {result.asset_health}</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TenantAIOverview;
