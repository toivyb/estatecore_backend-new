import React, { useState } from 'react'
export default function ChatAssist(){
  const [msg, setMsg] = useState('A tenant is late')
  const [res, setRes] = useState(null)
  async function run(){
    const r = await fetch(`/api/ai/chat`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: msg})})
    setRes(await r.json())
  }
  return (<div>
    <h2>AI Assistant</h2>
    <input value={msg} onChange={e=>setMsg(e.target.value)} style={{width:400}}/>
    <button onClick={run} style={{marginLeft:8}}>Ask</button>
    <pre>{JSON.stringify(res,null,2)}</pre>
  </div>)
}
