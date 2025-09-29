import { useEffect, useState } from "react";

export default function RentManagement() {
  const [data, setData] = useState([]);
  const [form, setForm] = useState({ name: "", unit: "", amount: "", status: "Paid" });
  const [editId, setEditId] = useState(null);

  const fetchData = () => {
    fetch("/api/rent", { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } })
      .then(res => res.json()).then(setData);
  };

  useEffect(fetchData, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const method = editId ? "PUT" : "POST";
    const url = editId ? `/api/rent/${editId}` : "/api/rent";
    await fetch(url, {
      method,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("token")}` },
      body: JSON.stringify(form),
    });
    setForm({ name: "", unit: "", amount: "", status: "Paid" });
    setEditId(null);
    fetchData();
  };

  const handleDelete = async (id) => {
    await fetch(`/api/rent/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });
    fetchData();
  };

  const handlePDF = (id) => {
    window.open(`/api/rent/${id}/pdf`, "_blank");
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Rent Management</h2>
      <form onSubmit={handleSubmit} className="space-x-2">
        <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Name"
          className="p-2 border" />
        <input value={form.unit} onChange={e => setForm({ ...form, unit: e.target.value })} placeholder="Unit"
          className="p-2 border" />
        <input value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} placeholder="Amount"
          className="p-2 border" type="number" />
        <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="p-2 border">
          <option value="Paid">Paid</option>
          <option value="Unpaid">Unpaid</option>
        </select>
        <button className="bg-blue-600 text-white px-4 py-2 rounded" type="submit">
          {editId ? "Update" : "Add"}
        </button>
      </form>
      <table className="w-full table-auto bg-white shadow rounded">
        <thead>
          <tr className="bg-gray-200">
            <th className="p-2">Name</th>
            <th>Unit</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.map((r) => (
            <tr key={r.id}>
              <td className="p-2">{r.name}</td>
              <td>{r.unit}</td>
              <td>${r.amount}</td>
              <td>{r.status}</td>
              <td>
                <button className="text-blue-600" onClick={() => { setForm(r); setEditId(r.id); }}>Edit</button>
                <button className="text-red-600 ml-2" onClick={() => handleDelete(r.id)}>Delete</button>
                <button className="text-green-600 ml-2" onClick={() => handlePDF(r.id)}>PDF</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
