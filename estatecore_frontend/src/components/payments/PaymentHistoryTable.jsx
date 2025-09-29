import React, { useEffect, useState } from "react";
import axios from "axios";

export default function PaymentHistoryTable({ tenantId }) {
  const [payments, setPayments] = useState([]);

  useEffect(() => {
    const fetch = async () => {
      const res = await axios.get("/api/payments", { params: { tenant_id: tenantId } });
      setPayments(res.data.payments);
    };
    fetch();
  }, [tenantId]);

  return (
    <div className="bg-white p-4 rounded-lg shadow mt-4">
      <h2 className="text-lg font-bold mb-2">Payment History</h2>
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th>ID</th><th>Rent</th><th>Amount</th><th>Status</th><th>Date</th><th>Receipt</th>
          </tr>
        </thead>
        <tbody>
          {payments.map(p => (
            <tr key={p.id}>
              <td>{p.id}</td>
              <td>{p.rent_id}</td>
              <td>${p.amount}</td>
              <td>{p.status}</td>
              <td>{p.timestamp.replace("T", " ").slice(0, 16)}</td>
              <td>
                <a href={`/api/payments/receipt/${p.id}`} target="_blank" rel="noopener noreferrer" className="underline">
                  PDF
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
