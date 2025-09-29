import React, { useEffect, useState } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function RentVsPaidChart({ propertyId }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    // For demo: fetch monthly summary for the past 6 months
    const months = [];
    const now = new Date();
    for (let i = 5; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      months.push(d.toISOString().slice(0, 7));
    }
    Promise.all(
      months.map(m =>
        axios.get('/api/reports/summary', { params: { month: m, property_id: propertyId } })
          .then(res => ({
            month: m,
            paid: res.data.total_paid || 0,
            due: res.data.total_due || 0,
          }))
      )
    ).then(setData);
  }, [propertyId]);

  return (
    <div className="bg-white rounded-lg p-4 shadow">
      <h2 className="text-lg font-semibold mb-2">Rent Collected vs Due (6 Months)</h2>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <XAxis dataKey="month"/>
          <YAxis/>
          <Tooltip/>
          <Legend/>
          <Bar dataKey="due" fill="#fbbf24" name="Due"/>
          <Bar dataKey="paid" fill="#34d399" name="Paid"/>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
