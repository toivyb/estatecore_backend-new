import React, { useState } from 'react'
export default function RevenueLeakage(){
  const [prop, setProp] = useState(1)
  const [rows, setRows] = useState([])
  async function run(){
    const r = await fetch(`/api/ai/revenue-leakage/${prop}`)
    setRows(await r.json())
  }
  return (<div>
    <h2>Revenue Leakage</h2>
    <input value={prop} onChange={e=>setProp(e.target.value)} /> property id
    <button onClick={run} style={{marginLeft:8}}>Scan</button>
    <pre>{JSON.stringify(rows,null,2)}</pre>
  </div>)
}
