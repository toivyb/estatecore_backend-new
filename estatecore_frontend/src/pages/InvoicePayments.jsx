import React, { useEffect, useState } from 'react'
import { api } from '../utils/api'

export default function InvoicePayments({ invoiceId }){
  const [inv, setInv] = useState(null)
  useEffect(()=>{ api('GET', `/payments/invoice/${invoiceId}`).then(setInv).catch(console.error) },[invoiceId])
  if(!inv) return <div>Loading...</div>
  return (
    <div>
      <h3>Invoice #{inv.id}</h3>
      <p>Status: {inv.status}</p>
      <ul>
        {inv.payments.map(p => <li key={p.id}>${'{'}(p.amount_cents/100).toFixed(2){'}'} - {p.status} ({p.method})</li>)}
      </ul>
    </div>
  )
}
