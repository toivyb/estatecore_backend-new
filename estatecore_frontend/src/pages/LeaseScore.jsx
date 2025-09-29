import React, { useState } from 'react'
export default function LeaseScore(){
  const [income, setIncome] = useState(5000)
  const [rent, setRent] = useState(1500)
  const [out, setOut] = useState(null)
  async function run(){
    const r = await fetch(`/api/ai/lease-score`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({monthly_income:income, monthly_rent:rent})})
    setOut(await r.json())
  }
  return (<div>
    <h2>Lease Score</h2>
    <input type="number" value={income} onChange={e=>setIncome(e.target.value)} /> income
    <input type="number" value={rent} onChange={e=>setRent(e.target.value)} style={{marginLeft:8}}/> rent
    <button onClick={run} style={{marginLeft:8}}>Score</button>
    {out && <pre>{JSON.stringify(out,null,2)}</pre>}
  </div>)
}
