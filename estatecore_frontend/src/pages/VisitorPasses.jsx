import React, { useEffect, useState } from 'react'
const API = import.meta.env.VITE_API_BASE || ''
export default function VisitorPasses(){
  const [rows, setRows] = useState([])
  const [hours, setHours] = useState(6)
  const [notes, setNotes] = useState('')

  async function load(){
    const r = await fetch(`${API}/api/visitor`, {headers:{'X-Role':'super_admin'}})
    if(r.ok) setRows(await r.json())
  }
  useEffect(()=>{ load() }, [])

  async function create(){
    const r = await fetch(`${API}/api/visitor/create`, {
      method:'POST',
      headers:{'Content-Type':'application/json','X-Role':'super_admin'},
      body: JSON.stringify({ hours, notes, created_by:1 })
    })
    if(r.ok){ await load() }
  }

  return (
    <div>
      <h2>Visitor Passes</h2>
      <div style={{display:'flex', gap:8}}>
        <input type="number" value={hours} onChange={e=>setHours(e.target.value)} />
        <input value={notes} onChange={e=>setNotes(e.target.value)} placeholder="notes" />
        <button onClick={create}>Create Pass</button>
      </div>
      <ul>
        {rows.map(v=>(<li key={v.id}><b>{v.code}</b> — expires {v.expires_at} — {v.notes||''}</li>))}
      </ul>
    </div>
  )
}
