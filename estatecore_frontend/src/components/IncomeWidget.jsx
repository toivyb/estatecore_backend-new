import React from 'react'

export default function IncomeWidget({ data = {} }) {
  const totalDue = data.total_due || 0;
  const totalPaid = data.total_paid || 0;
  const net = data.net || 0;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-2">Income vs Cost</h3>
      <div>Total Due: ${totalDue.toFixed(2)}</div>
      <div>Total Paid: ${totalPaid.toFixed(2)}</div>
      <div className="font-bold mt-2">Net: ${net.toFixed(2)}</div>
    </div>
  )
}
