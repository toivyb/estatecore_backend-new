import React, { useState } from 'react'
export default function Forecasts(){
  const [units, setUnits] = useState(150)
  const [months, setMonths] = useState(6)
  const [rows, setRows] = useState([])
  async function run(){
    const r = await fetch(`/api/ai/forecast/utilities?units=${units}&months=${months}`)
    setRows(await r.json())
  }
  return (<div>
    <h2>Utility Forecast</h2>
    <input value={units} onChange={e=>setUnits(e.target.value)} /> units
    <input value={months} onChange={e=>setMonths(e.target.value)} style={{marginLeft:8}}/> months
    <button onClick={run} style={{marginLeft:8}}>Forecast</button>
    <pre>{JSON.stringify(rows,null,2)}</pre>
  </div>)
}
