import React, { useEffect, useState } from 'react'
import API from '../api'
export default function Rent(){
  const [items,setItems] = useState([])
  const [month,setMonth] = useState('')
  const [year,setYear] = useState('')
  const load = ()=>{
    const params = {}
    if(month) params.month = month
    if(year) params.year = year
    API.get('/rent', { params }).then(r=>setItems(r.data))
  }
  useEffect(load,[])
  const bulkUploadJSON = async ()=>{
    const payload = [
      {"tenant_id":1,"month":8,"year":2025,"amount":1500,"paid":true},
      {"tenant_id":2,"month":8,"year":2025,"amount":1800,"paid":false}
    ]
    const {data} = await API.post('/rent/bulk-upload', payload, {headers:{'Content-Type':'application/json'}})
    alert('Created: '+data.created); load()
  }
  return (
    <div style={{padding:16}}>
      <h3>Rent</h3>
      <div style={{display:'flex', gap:8, marginBottom:12}}>
        <input placeholder="Month" value={month} onChange={e=>setMonth(e.target.value)} />
        <input placeholder="Year" value={year} onChange={e=>setYear(e.target.value)} />
        <button onClick={load}>Filter</button>
        <button onClick={bulkUploadJSON}>Bulk Upload (Demo)</button>
        <a href="/api/pdf/rent-receipt?tenant=Tenant&month=8&year=2025&amount=1500" target="_blank" rel="noreferrer">Rent Receipt PDF</a>
      </div>
      <table border="1" cellPadding="6">
        <thead><tr><th>ID</th><th>Tenant</th><th>Month</th><th>Year</th><th>Amount</th><th>Paid</th></tr></thead>
        <tbody>
          {items.map(it=>(<tr key={it.id}><td>{it.id}</td><td>{it.tenant_id}</td><td>{it.month}</td><td>{it.year}</td><td>${it.amount.toFixed(2)}</td><td>{it.paid ? 'Yes':'No'}</td></tr>))}
        </tbody>
      </table>
    </div>
  )
}
