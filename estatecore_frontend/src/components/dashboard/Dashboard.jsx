// src/components/dashboard/Dashboard.jsx

import React, { useState } from "react";

export default function Dashboard() {
  // ─────────── State hooks for inputs & results ───────────
  const [lease, setLease] = useState({
    rent: "",
    onTime: "",
    complaints: "",
  });
  const [leaseScore, setLeaseScore] = useState(null);

  const [delay, setDelay] = useState({
    latePayments: "",
    avgDaysLate: "",
    monthsOnTime: "",
  });
  const [delayPred, setDelayPred] = useState(null);

  const [maint, setMaint] = useState({
    age: "",
    lastService: "",
    incidents: "",
  });
  const [maintPred, setMaintPred] = useState(null);

  const [util, setUtil] = useState({
    avgTemp: "",
    occupants: "",
    unitSize: "",
  });
  const [utilPred, setUtilPred] = useState(null);

  const [leak, setLeak] = useState({
    units: "",
    expected: "",
    actual: "",
  });
  const [leakDet, setLeakDet] = useState(null);

  const [health, setHealth] = useState({
    openIssues: "",
    netProfit: "",
    vacancyRate: "",
  });
  const [healthScore, setHealthScore] = useState(null);
  // ───────────────────────────────────────────────────────────

  const fieldClass = "border border-gray-300 rounded px-3 py-2 w-full";
  const btnClass = "bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2";

  // generic helper to POST to your AI API & store the result
  const postAI = async (url, body, setter) => {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      setter(data);
    } catch (e) {
      console.error(e);
      setter({ error: "Request failed" });
    }
  };

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-bold">EstateCore AI Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Lease Scoring */}
        <div className="bg-white shadow rounded p-4">
          <h2 className="text-xl font-semibold mb-3">Lease Scoring</h2>
          <form
            className="flex space-x-2 items-end"
            onSubmit={(e) => {
              e.preventDefault();
              postAI(
                "/api/ai/score-lease",
                {
                  rent: parseFloat(lease.rent),
                  on_time_months: parseFloat(lease.onTime),
                  complaints: parseInt(lease.complaints, 10),
                },
                setLeaseScore
              );
            }}
          >
            <input
              className={fieldClass}
              placeholder="Rent"
              value={lease.rent}
              onChange={(e) =>
                setLease({ ...lease, rent: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="On-Time Months"
              value={lease.onTime}
              onChange={(e) =>
                setLease({ ...lease, onTime: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Complaints"
              value={lease.complaints}
              onChange={(e) =>
                setLease({ ...lease, complaints: e.target.value })
              }
            />
            <button type="submit" className={btnClass}>
              Submit
            </button>
          </form>
          {leaseScore && (
            <pre className="mt-3 bg-gray-100 p-2 rounded">
              {JSON.stringify(leaseScore, null, 2)}
            </pre>
          )}
        </div>

        {/* Rent Delay Prediction */}
        <div className="bg-white shadow rounded p-4">
          <h2 className="text-xl font-semibold mb-3">
            Rent Delay Prediction
          </h2>
          <form
            className="flex space-x-2 items-end"
            onSubmit={(e) => {
              e.preventDefault();
              postAI(
                "/api/ai/predict-delay",
                {
                  late_payments: parseInt(delay.latePayments, 10),
                  avg_days_late: parseFloat(delay.avgDaysLate),
                  months_paid_on_time: parseFloat(delay.monthsOnTime),
                },
                setDelayPred
              );
            }}
          >
            <input
              className={fieldClass}
              placeholder="Late Payments"
              value={delay.latePayments}
              onChange={(e) =>
                setDelay({ ...delay, latePayments: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Avg Days Late"
              value={delay.avgDaysLate}
              onChange={(e) =>
                setDelay({ ...delay, avgDaysLate: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Months Paid On-Time"
              value={delay.monthsOnTime}
              onChange={(e) =>
                setDelay({ ...delay, monthsOnTime: e.target.value })
              }
            />
            <button className={btnClass}>Submit</button>
          </form>
          {delayPred && (
            <pre className="mt-3 bg-gray-100 p-2 rounded">
              {JSON.stringify(delayPred, null, 2)}
            </pre>
          )}
        </div>

        {/* Maintenance Forecast */}
        <div className="bg-white shadow rounded p-4">
          <h2 className="text-xl font-semibold mb-3">
            Maintenance Forecast
          </h2>
          <form
            className="flex space-x-2 items-end"
            onSubmit={(e) => {
              e.preventDefault();
              postAI(
                "/api/ai/forecast-maintenance",
                {
                  age_months: parseFloat(maint.age),
                  last_service_months: parseFloat(maint.lastService),
                  incident_reports: parseInt(maint.incidents, 10),
                },
                setMaintPred
              );
            }}
          >
            <input
              className={fieldClass}
              placeholder="Age (months)"
              value={maint.age}
              onChange={(e) =>
                setMaint({ ...maint, age: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Last Service (months)"
              value={maint.lastService}
              onChange={(e) =>
                setMaint({ ...maint, lastService: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Incidents"
              value={maint.incidents}
              onChange={(e) =>
                setMaint({ ...maint, incidents: e.target.value })
              }
            />
            <button className={btnClass}>Submit</button>
          </form>
          {maintPred && (
            <pre className="mt-3 bg-gray-100 p-2 rounded">
              {JSON.stringify(maintPred, null, 2)}
            </pre>
          )}
        </div>

        {/* Utility Forecast */}
        <div className="bg-white shadow rounded p-4">
          <h2 className="text-xl font-semibold mb-3">
            Utility Forecast
          </h2>
          <form
            className="flex space-x-2 items-end"
            onSubmit={(e) => {
              e.preventDefault();
              postAI(
                "/api/ai/forecast-utility",
                {
                  average_temp: parseFloat(util.avgTemp),
                  occupants: parseInt(util.occupants, 10),
                  unit_size_sqft: parseFloat(util.unitSize),
                },
                setUtilPred
              );
            }}
          >
            <input
              className={fieldClass}
              placeholder="Avg Temperature"
              value={util.avgTemp}
              onChange={(e) =>
                setUtil({ ...util, avgTemp: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Occupants"
              value={util.occupants}
              onChange={(e) =>
                setUtil({ ...util, occupants: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Unit Size (sqft)"
              value={util.unitSize}
              onChange={(e) =>
                setUtil({ ...util, unitSize: e.target.value })
              }
            />
            <button className={btnClass}>Submit</button>
          </form>
          {utilPred && (
            <pre className="mt-3 bg-gray-100 p-2 rounded">
              {JSON.stringify(utilPred, null, 2)}
            </pre>
          )}
        </div>

        {/* Revenue Leakage Detection */}
        <div className="bg-white shadow rounded p-4">
          <h2 className="text-xl font-semibold mb-3">
            Revenue Leakage Detection
          </h2>
          <form
            className="flex space-x-2 items-end"
            onSubmit={(e) => {
              e.preventDefault();
              postAI(
                "/api/ai/detect-leakage",
                {
                  units: parseInt(leak.units, 10),
                  expected_rent: parseFloat(leak.expected),
                  actual_collected: parseFloat(leak.actual),
                },
                setLeakDet
              );
            }}
          >
            <input
              className={fieldClass}
              placeholder="Units"
              value={leak.units}
              onChange={(e) =>
                setLeak({ ...leak, units: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Expected Rent"
              value={leak.expected}
              onChange={(e) =>
                setLeak({ ...leak, expected: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Actual Collected"
              value={leak.actual}
              onChange={(e) =>
                setLeak({ ...leak, actual: e.target.value })
              }
            />
            <button className={btnClass}>Submit</button>
          </form>
          {leakDet && (
            <pre className="mt-3 bg-gray-100 p-2 rounded">
              {JSON.stringify(leakDet, null, 2)}
            </pre>
          )}
        </div>

        {/* Asset Health Score */}
        <div className="bg-white shadow rounded p-4">
          <h2 className="text-xl font-semibold mb-3">
            Asset Health Score
          </h2>
          <form
            className="flex space-x-2 items-end"
            onSubmit={(e) => {
              e.preventDefault();
              postAI(
                "/api/ai/health-score",
                {
                  open_issues: parseInt(health.openIssues, 10),
                  net_profit: parseFloat(health.netProfit),
                  vacancy_rate: parseFloat(health.vacancyRate),
                },
                setHealthScore
              );
            }}
          >
            <input
              className={fieldClass}
              placeholder="Open Issues"
              value={health.openIssues}
              onChange={(e) =>
                setHealth({ ...health, openIssues: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Net Profit"
              value={health.netProfit}
              onChange={(e) =>
                setHealth({ ...health, netProfit: e.target.value })
              }
            />
            <input
              className={fieldClass}
              placeholder="Vacancy Rate (%)"
              value={health.vacancyRate}
              onChange={(e) =>
                setHealth({ ...health, vacancyRate: e.target.value })
              }
            />
            <button className={btnClass}>Submit</button>
          </form>
          {healthScore && (
            <pre className="mt-3 bg-gray-100 p-2 rounded">
              {JSON.stringify(healthScore, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
