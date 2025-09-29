import React, { useEffect, useState } from "react";

const IncomeVsCostWidget = () => {
  const [metrics, setMetrics] = useState({ total_rent: 0, total_costs: 0, net_profit: 0 });

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch("/api/dashboard-metrics", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(res => res.json())
      .then(data => setMetrics(data));
  }, []);

  return (
    <div className="bg-white shadow rounded p-4 w-full">
      <h2 className="text-lg font-bold mb-2">Income vs Cost</h2>
      <div>Total Rent: ${metrics.total_rent}</div>
      <div>Total Costs: ${metrics.total_costs}</div>
      <div className="font-semibold">Net Profit: ${metrics.net_profit}</div>
    </div>
  );
};

export default IncomeVsCostWidget;
