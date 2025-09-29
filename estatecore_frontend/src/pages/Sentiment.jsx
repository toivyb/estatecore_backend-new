import React, { useState } from 'react'
export default function Sentiment(){
  const [text, setText] = useState('The AC is terrible, I am angry.')
  const [res, setRes] = useState(null)
  async function run(){
    const r = await fetch(`/api/ai/sentiment`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text})})
    setRes(await r.json())
  }
  return (<div>
    <h2>Sentiment</h2>
    <textarea value={text} onChange={e=>setText(e.target.value)} rows={4} cols={60}/>
    <div><button onClick={run}>Analyze</button></div>
    <pre>{JSON.stringify(res,null,2)}</pre>
  </div>)
}
