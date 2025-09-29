import React, { useEffect, useState } from 'react'
import API from '../api'
export default function AccessLogs(){
  const [items,setItems] = useState([])
  useEffect(()=>{ API.get('/access/logs').then(r=>setItems(r.data)) },[])
  return (
    <div style={{padding:16}}>
      <h3>Access Logs</h3>
      <table border="1" cellPadding="6">
        <thead><tr><th>User</th><th>Door</th><th>Status</th><th>Time</th></tr></thead>
        <tbody>{items.map((a,i)=>(<tr key={i}><td>{a.user_email}</td><td>{a.door}</td><td>{a.status}</td><td>{a.ts}</td></tr>))}</tbody>
      </table>
    </div>
  )
}
