import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function RentTable() {
  const [rents, setRents] = useState([]);
  const [month, setMonth] = useState('');

  const fetchRents = async () => {
    const params = month ? { month } : {};
    const res = await axios.get('/api/rent', { params });
    setRents(res.data.rents);
  };

  useEffect(() => {
    fetchRents();
  }, [month]);

  const markPaid = async (id) => {
    await axios.post(`/api/rent/mark_paid/${id}`);
    fetchRents();
  };

  const markUnpaid = async (id) => {
    await axios.post(`/api/rent/mark_unpaid/${id}`);
    fetchRents();
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow mt-4">
      <div className="flex gap-4 items-center mb-3">
        <label className="font-semibold">Month:</label>
        <input type="month" value={month} onChange={e => setMonth(e.target.value)} className="border rounded p-1" />
      </div>
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th>ID</th><th>Tenant</th><th>Amount</th><th>Due</th><th>Status</th><th>Paid On</th><th>Late Fee</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rents.map(r => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.tenant_id}</td>
              <td>${r.amount}</td>
              <td>{r.due_date}</td>
              <td>{r.status}</td>
              <td>{r.paid_on ? r.paid_on.split('T')[0] : ''}</td>
              <td>${r.late_fee}</td>
              <td>
                {r.status === 'unpaid' ?
                  <button onClick={() => markPaid(r.id)} className="bg-green-600 text-white px-2 py-1 rounded mr-2">Mark Paid</button>
                  :
                  <button onClick={() => markUnpaid(r.id)} className="bg-yellow-600 text-white px-2 py-1 rounded">Mark Unpaid</button>
                }
                <a href={`/api/rent/pdf/${r.id}`} target="_blank" rel="noopener noreferrer" className="ml-2 underline">PDF</a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
