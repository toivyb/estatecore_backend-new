import React, { useState } from "react";

export default function QuickBooksExportPanel() {
  const [year, setYear] = useState(new Date().getFullYear());

  return (
    <div className="bg-white p-4 rounded-lg shadow mt-6">
      <h2 className="text-lg font-bold mb-4">QuickBooks & Tax Export</h2>
      <div className="flex flex-wrap gap-3 mb-4">
        <a href="/api/accounting/quickbooks_csv?type=rent" className="bg-blue-600 text-white px-4 py-2 rounded">Export Rent CSV</a>
        <a href="/api/accounting/quickbooks_csv?type=payment" className="bg-green-600 text-white px-4 py-2 rounded">Export Payments CSV</a>
        <a href="/api/accounting/quickbooks_csv?type=expense" className="bg-yellow-600 text-white px-4 py-2 rounded">Export Expenses CSV</a>
      </div>
      <div className="flex gap-3 items-center">
        <input
          type="number"
          min="2000"
          value={year}
          onChange={e => setYear(e.target.value)}
          className="border rounded p-1 w-24"
        />
        <a href={`/api/accounting/tax_summary_pdf?year=${year}`} className="bg-purple-600 text-white px-4 py-2 rounded">
          Download Tax Summary PDF
        </a>
      </div>
    </div>
  );
}
