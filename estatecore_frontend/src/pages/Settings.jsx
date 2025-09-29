import React, { useEffect, useState } from 'react'
const API = import.meta.env.VITE_API_BASE || ''

export default function Settings(){
  const [toggles, setToggles] = useState([])
  const [key, setKey] = useState('')
  const [enabled, setEnabled] = useState(true)

  async function load(){
    const r = await fetch(`${API}/api/toggles`, {headers:{'X-Role':'super_admin'}})
    if(r.ok) setToggles(await r.json())
  }
  useEffect(()=>{ load() }, [])

  async function save(){
    await fetch(`${API}/api/toggles`, {
      method:'POST',
      headers:{'Content-Type':'application/json', 'X-Role':'super_admin'},
      body: JSON.stringify({ key, enabled })
    })
    setKey(''); setEnabled(true); load()
  }

  async function seed(){
    await fetch(`${API}/api/demo/seed`, {method:'POST'}); load()
  }
  async function reset(){
    await fetch(`${API}/api/demo/reset`, {method:'POST'}); load()
  }

  return (
    <div style={{display:'grid', gap:8}}>
      <h2>Settings (Super Admin)</h2>
      <div>
        <button onClick={seed}>Seed Demo</button>
        <button onClick={reset} style={{marginLeft:8}}>Reset Demo</button>
      </div>
      <div style={{display:'flex', gap:8, marginTop:8}}>
        <input value={key} onChange={e=>setKey(e.target.value)} placeholder="feature key (e.g., visitor_pass)" />
        <label><input type="checkbox" checked={enabled} onChange={e=>setEnabled(e.target.checked)} /> enabled</label>
        <button onClick={save}>Save Toggle</button>
      </div>
      <ul>
        {toggles.map(t=>(<li key={t.id}>{t.key}: {t.enabled? 'on':'off'}</li>))}
      </ul>
    </div>
  )
}
