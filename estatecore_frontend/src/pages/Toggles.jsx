import React, { useEffect, useState } from 'react'
const defaultKeys = [
  'ai_lease_scoring','ai_forecast_util','ai_rent_delay','ai_maint_pred',
  'ai_rev_leak','ai_asset_health','ai_cashflow','ai_eviction_risk',
  'ai_vision_tag','ai_sentiment','ai_assistant'
]
export default function Toggles(){
  const [toggles, setToggles] = useState([])
  const [key, setKey] = useState('ai_lease_scoring')
  const [enabled, setEnabled] = useState(true)

  async function load(){
    const r = await fetch(`/api/toggles`)
    setToggles(await r.json())
  }
  useEffect(()=>{ load() }, [])

  async function save(){
    await fetch(`/api/toggles`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({key, enabled})})
    setKey('ai_lease_scoring'); setEnabled(true); load()
  }

  return (<div>
    <h2>Feature Toggles</h2>
    <div style={{display:'flex', gap:8, alignItems:'center'}}>
      <select value={key} onChange={e=>setKey(e.target.value)}>
        {defaultKeys.map(k=><option key={k} value={k}>{k}</option>)}
      </select>
      <label><input type="checkbox" checked={enabled} onChange={e=>setEnabled(e.target.checked)}/> enabled</label>
      <button onClick={save}>Save</button>
    </div>
    <pre>{JSON.stringify(toggles,null,2)}</pre>
  </div>)
}
