import React, { useState } from 'react'
export default function Cashflow(){
  const [prop, setProp] = useState(1)
  const [months, setMonths] = useState(6)
  const [rows, setRows] = useState([])
  async function run(){
    const r = await fetch(`/api/ai/cashflow/${prop}?months=${months}`)
    setRows(await r.json())
  }
  return (<div>
    <h2>Cash Flow Projection</h2>
    <input value={prop} onChange={e=>setProp(e.target.value)} /> property id
    <input value={months} onChange={e=>setMonths(e.target.value)} style={{marginLeft:8}}/> months
    <button onClick={run} style={{marginLeft:8}}>Project</button>
    <pre>{JSON.stringify(rows,null,2)}</pre>
  </div>)
}
