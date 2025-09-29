import React from "react";

export function RentExportButton() {
  return <a href="/api/reports/rent_csv" className="bg-blue-600 text-white px-4 py-2 rounded mr-2">Export Rent CSV</a>;
}
export function PaymentsExportButton() {
  return <a href="/api/reports/payments_csv" className="bg-green-600 text-white px-4 py-2 rounded mr-2">Export Payments CSV</a>;
}
export function MaintExportButton() {
  return <a href="/api/reports/maintenance_csv" className="bg-yellow-600 text-white px-4 py-2 rounded">Export Maintenance CSV</a>;
}
