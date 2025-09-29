import React, { useEffect, useState } from "react";

const AccessLogWidget = () => {
  const [logs, setLogs] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchLogs = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/access-logs", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await res.json();
      setLogs(data);
    } catch (err) {
      console.error("Error fetching logs:", err);
    }
  };

  const filteredLogs = logs.filter(
    (log) =>
      log.user.toLowerCase().includes(search.toLowerCase()) ||
      log.door.toLowerCase().includes(search.toLowerCase()) ||
      log.status.toLowerCase().includes(search.toLowerCase())
  );

  const downloadCSV = () => {
    const headers = "Time,User,Door,Status\n";
    const rows = logs.map((l) =>
      [l.time, l.user, l.door, l.status].join(",")
    );
    const blob = new Blob([headers + rows.join("\n")], {
      type: "text/csv;charset=utf-8;",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.setAttribute("download", "access_logs.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const triggerUnlock = async () => {
    try {
      const token = localStorage.getItem("token");
      await fetch("/api/relay/unlock", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      alert("Manual unlock triggered.");
    } catch (err) {
      alert("Error triggering unlock.");
    }
  };

  return (
    <div className="p-4 bg-white rounded-xl shadow mt-8 w-full">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-bold">Access Log</h2>
        <div className="flex items-center gap-2">
          <input
            type="text"
            className="border rounded px-2 py-1 text-sm"
            placeholder="Filter logs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button
            onClick={downloadCSV}
            className="bg-blue-500 text-white px-3 py-1 rounded text-sm"
          >
            Export CSV
          </button>
          <button
            onClick={triggerUnlock}
            className="bg-green-600 text-white px-3 py-1 rounded text-sm"
          >
            Trigger Unlock
          </button>
        </div>
      </div>

      <div className="overflow-y-auto max-h-96">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b">
              <th className="py-1">Time</th>
              <th className="py-1">User</th>
              <th className="py-1">Door</th>
              <th className="py-1">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.map((log, idx) => (
              <tr key={idx} className="border-b last:border-none">
                <td className="py-1">{log.time}</td>
                <td className="py-1">{log.user}</td>
                <td className="py-1">{log.door}</td>
                <td className="py-1">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                      log.status.includes("granted")
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {log.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AccessLogWidget;
