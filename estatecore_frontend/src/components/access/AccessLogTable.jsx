import React, { useEffect, useState } from "react";
import axios from "axios";

export default function AccessLogTable() {
  const [logs, setLogs] = useState([]);
  const [filters, setFilters] = useState({ user_id: '', event_type: '', door_id: '' });

  const fetchLogs = async () => {
    const res = await axios.get('/api/access/logs', { params: filters });
    setLogs(res.data.logs);
  };

  useEffect(() => { fetchLogs(); }, [filters]);

  return (
    <div className="bg-white p-4 rounded-lg shadow mt-4">
      <div className="flex gap-2 mb-2">
        <input placeholder="User ID" className="border p-1" value={filters.user_id} onChange={e => setFilters({ ...filters, user_id: e.target.value })}/>
        <input placeholder="Door ID" className="border p-1" value={filters.door_id} onChange={e => setFilters({ ...filters, door_id: e.target.value })}/>
        <select className="border p-1" value={filters.event_type} onChange={e => setFilters({ ...filters, event_type: e.target.value })}>
          <option value="">All Events</option>
          <option value="entry">Entry</option>
          <option value="exit">Exit</option>
          <option value="denied">Denied</option>
          <option value="visitor_entry">Visitor Entry</option>
        </select>
        <button className="bg-blue-600 text-white px-4 rounded" onClick={fetchLogs}>Filter</button>
      </div>
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th>ID</th><th>User</th><th>Door</th><th>Event</th><th>Reason</th><th>Time</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{log.id}</td>
              <td>{log.user_id}</td>
              <td>{log.door_id}</td>
              <td>{log.event_type}</td>
              <td>{log.reason || ''}</td>
              <td>{log.timestamp.replace('T', ' ').slice(0, 16)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
