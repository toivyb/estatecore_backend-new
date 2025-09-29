import { useEffect, useState } from "react";

export default function AccessControl() {
  const [logs, setLogs] = useState([]);
  const [form, setForm] = useState({ time: "", user: "", door: "" });

  useEffect(() => {
    fetch("/api/access-logs", {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    })
      .then(res => res.json())
      .then(setLogs);
  }, []);

  const handleSimulate = async (e) => {
    e.preventDefault();
    await fetch("/api/access-logs/simulate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify(form),
    });
    window.location.reload();
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Access Control</h2>
      <form onSubmit={handleSimulate} className="space-x-2">
        <input value={form.time} onChange={e => setForm({ ...form, time: e.target.value })} placeholder="Time"
          className="p-2 border" />
        <input value={form.user} onChange={e => setForm({ ...form, user: e.target.value })} placeholder="User"
          className="p-2 border" />
        <input value={form.door} onChange={e => setForm({ ...form, door: e.target.value })} placeholder="Door"
          className="p-2 border" />
        <button className="bg-blue-600 text-white px-4 py-2 rounded" type="submit">Simulate Log</button>
      </form>
      <ul className="list-disc pl-5">
        {logs.map((log, i) => <li key={i}>{log.time} - {log.user} - {log.door}</li>)}
      </ul>
    </div>
  );
}
