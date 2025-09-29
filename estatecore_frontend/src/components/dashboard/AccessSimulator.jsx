import React, { useEffect, useState } from 'react';
import axios from 'axios';

function AccessSimulator() {
  const [plate, setPlate] = useState('');
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('granted');
  const [method, setMethod] = useState('manual');
  const [location, setLocation] = useState('Default');

  const token = localStorage.getItem('token');

  const fetchLogs = async () => {
    try {
      const res = await axios.get('/api/access-logs', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setLogs(res.data);
    } catch (err) {
      console.error('Failed to load logs', err);
    }
  };

  const simulateEntry = async () => {
    try {
      await axios.post(
        '/api/access-log',
        { plate, status, method, location },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setPlate('');
      fetchLogs();
    } catch (err) {
      console.error('Failed to simulate log', err);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div>
      <h2>Access Log Simulator</h2>
      <input
        type="text"
        placeholder="License Plate"
        value={plate}
        onChange={(e) => setPlate(e.target.value)}
      />
      <button onClick={simulateEntry}>Simulate Entry</button>

      <h3>Latest Access Logs</h3>
      <ul>
        {logs.map((log) => (
          <li key={log.id}>
            {log.timestamp} — {log.plate} — {log.status}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default AccessSimulator;
