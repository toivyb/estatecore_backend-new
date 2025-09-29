import React, { useEffect, useState } from "react";
import axios from "axios";

export default function AdminPaymentsTable({ rentId }) {
  const [payments, setPayments] = useState([]);

  useEffect(() => {
    const fetch = async () => {
      const res = await axios.get("/api/payments", { params: rentId ? { rent_id: rentId } : {} });
      setPayments(res.data.payments);
    };
    fetch();
  }, [rentId]);

  const markPaid = async (id) => {
    await axios.post(`/api/payments/mark_paid/${id}`);
    window.location.reload();
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow mt-4">
      <h2 className="text-lg font-bold mb-2">All Payments</h2>
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th>ID</th><th>Tenant</th><th>Rent</th><th>Amount</th><th>Status</th><th>Date</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          {payments.map(p => (
            <tr key={p.id}>
              <td>{p.id}</td>
              <td>{p.tenant_id}</td>
              <td>{p.rent_id}</td>
              <td>${p.amount}</td>
              <td>{p.status}</td>
              <td>{p.timestamp.replace("T", " ").slice(0, 16)}</td>
              <td>
                {p.status !== "success" && (
                  <button onClick={() => markPaid(p.id)} className="bg-green-600 text-white px-2 py-1 rounded">
                    Mark Paid
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
