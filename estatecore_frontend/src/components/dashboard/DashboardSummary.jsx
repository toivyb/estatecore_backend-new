import React, { useEffect, useState } from "react";
import AccessLogWidget from "./AccessLogWidget";
import IncomeVsCostWidget from "./IncomeVsCostWidget";

const DashboardSummary = () => {
  const [data, setData] = useState({});

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch("/api/dashboard-metrics", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => res.json())
      .then(setData)
      .catch((err) => console.error("Error fetching dashboard metrics:", err));
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Dashboard Summary</h1>

      <div className="grid grid-cols-3 gap-4 my-6">
        <div className="bg-blue-100 rounded-lg p-4 shadow">
          <div className="text-xl font-bold">${data.total_paid || 0}</div>
          <div className="text-gray-700">Rent Collected</div>
        </div>
        <div className="bg-yellow-100 rounded-lg p-4 shadow">
          <div className="text-xl font-bold">${data.total_unpaid || 0}</div>
          <div className="text-gray-700">Outstanding Rent</div>
        </div>
        <div className="bg-green-100 rounded-lg p-4 shadow">
          <div className="text-xl font-bold">{data.open_maintenance || 0}</div>
          <div className="text-gray-700">Open Maintenance</div>
        </div>
      </div>

      <AccessLogWidget />
      <IncomeVsCostWidget />
    </div>
  );
};

export default DashboardSummary;
