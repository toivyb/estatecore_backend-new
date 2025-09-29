import { useState, useEffect } from "react";

export default function DocumentVault({ propertyId }) {
  const [docs, setDocs] = useState([]);
  const [form, setForm] = useState({ name: "", type: "", expires_on: "" });

  const fetchDocs = async () => {
    const res = await fetch(`/api/documents/${propertyId}`);
    const data = await res.json();
    setDocs(data);
  };

  const upload = async () => {
    await fetch("/api/documents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, property_id: propertyId })
    });
    setForm({ name: "", type: "", expires_on: "" });
    fetchDocs();
  };

  useEffect(() => { fetchDocs(); }, []);

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Document Vault</h2>
      <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="border p-2 mb-2 w-full" />
      <input placeholder="Type" value={form.type} onChange={e => setForm({ ...form, type: e.target.value })} className="border p-2 mb-2 w-full" />
      <input type="date" value={form.expires_on} onChange={e => setForm({ ...form, expires_on: e.target.value })} className="border p-2 mb-2 w-full" />
      <button className="bg-blue-700 text-white px-4 py-2 mb-4" onClick={upload}>Upload</button>

      <ul>
        {docs.map((d, i) => (
          <li key={i} className="border-b py-1">
            {d.name} — {d.type} — Expires: {d.expires_on}
          </li>
        ))}
      </ul>
    </div>
  );
}