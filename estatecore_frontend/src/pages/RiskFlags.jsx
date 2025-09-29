import React, { useState } from 'react'
export default function RiskFlags(){
  const [tenant, setTenant] = useState(2)
  const [res1, setRes1] = useState(null)
  const [res2, setRes2] = useState(null)
  async function run(){
    const r1 = await fetch(`/api/ai/rent-delay-risk/${tenant}`)
    const r2 = await fetch(`/api/ai/eviction-risk/${tenant}`)
    setRes1(await r1.json()); setRes2(await r2.json())
  }
  return (<div>
    <h2>Risk Flags</h2>
    <input value={tenant} onChange={e=>setTenant(e.target.value)} /> tenant id
    <button onClick={run} style={{marginLeft:8}}>Analyze</button>
    <pre>{JSON.stringify(res1,null,2)}</pre>
    <pre>{JSON.stringify(res2,null,2)}</pre>
  </div>)
}
