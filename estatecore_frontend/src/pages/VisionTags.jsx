import React, { useState } from 'react'
export default function VisionTags(){
  const [url, setUrl] = useState('https://example.com/issue.jpg')
  const [res, setRes] = useState(null)
  async function run(){
    const r = await fetch(`/api/ai/inspections/tag`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({image_url:url})})
    setRes(await r.json())
  }
  return (<div>
    <h2>Inspection Tagging (demo)</h2>
    <input value={url} onChange={e=>setUrl(e.target.value)} style={{width:400}}/>
    <button onClick={run} style={{marginLeft:8}}>Tag</button>
    <pre>{JSON.stringify(res,null,2)}</pre>
  </div>)
}
