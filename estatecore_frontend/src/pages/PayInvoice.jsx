import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { api } from '../utils/api'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY)

function CheckoutInner({ invoiceId }){
  const stripe = useStripe()
  const elements = useElements()
  const [clientSecret, setClientSecret] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  useEffect(()=>{
    api('POST','/payments/create', { invoice_id: Number(invoiceId) })
      .then(r => { setClientSecret(r.client_secret); setLoading(false) })
      .catch(e => { setMessage(e.message); setLoading(false) })
  }, [invoiceId])

  async function onSubmit(e){
    e.preventDefault()
    if(!stripe || !elements) return
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: (import.meta.env.VITE_PUBLIC_BASE_URL || location.origin) + '/#/invoices' }
    })
    if(error) setMessage(error.message || 'Payment failed')
  }

  if(loading) return <div>Loading...</div>
  if(!clientSecret) return <div>Error: {message || 'Missing client secret'}</div>

  return (
    <form onSubmit={onSubmit}>
      <PaymentElement />
      <button disabled={!stripe} style={{marginTop:12}}>Pay</button>
      {message && <div style={{color:'red'}}>{message}</div>}
    </form>
  )
}

export default function PayInvoice(){
  const { invoiceId } = useParams()
  if(!stripePromise) return <div>Missing VITE_STRIPE_PUBLISHABLE_KEY</div>
  return (
    <Elements stripe={stripePromise} options={{appearance:{theme:'stripe'}}}>
      <CheckoutInner invoiceId={invoiceId} />
    </Elements>
  )
}
