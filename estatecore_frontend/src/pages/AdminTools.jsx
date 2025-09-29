import { useState } from "react";

export default function AdminTools() {
  const [link, setLink] = useState("");
  const [title, setTitle] = useState("");

  const handleGenerate = async () => {
    const res = await fetch("/api/invite-link", {
      method: "POST",
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });
    const data = await res.json();
    setLink(data.link);
  };

  const handleMaintenance = async (e) => {
    e.preventDefault();
    await fetch("/api/maintenance", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`
      },
      body: JSON.stringify({ title })
    });
    setTitle("");
    alert("Request submitted");
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-4 shadow rounded">
        <h2 className="text-xl font-bold">Invite Link</h2>
        <button onClick={handleGenerate} className="mt-2 px-4 py-2 bg-blue-600 text-white rounded">Generate Invite Link</button>
        {link && <p className="mt-2 text-sm text-gray-600 break-all">{link}</p>}
      </div>
      <div className="bg-white p-4 shadow rounded">
        <h2 className="text-xl font-bold">Submit Maintenance Request</h2>
        <form onSubmit={handleMaintenance} className="mt-2 space-x-2">
          <input value={title} onChange={e => setTitle(e.target.value)} className="p-2 border" placeholder="Request title" />
          <button className="bg-green-600 text-white px-4 py-2 rounded" type="submit">Submit</button>
        </form>
      </div>
    </div>
  );
}
