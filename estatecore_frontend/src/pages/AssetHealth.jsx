import React, { useState } from 'react'
export default function AssetHealth(){
  const [prop, setProp] = useState(1)
  const [res, setRes] = useState(null)
  async function run(){
    const r = await fetch(`/api/ai/asset-health/${prop}`)
    setRes(await r.json())
  }
  return (<div>
    <h2>Asset Health</h2>
    <input value={prop} onChange={e=>setProp(e.target.value)} /> property id
    <button onClick={run} style={{marginLeft:8}}>Score</button>
    <pre>{JSON.stringify(res,null,2)}</pre>
  </div>)
}
