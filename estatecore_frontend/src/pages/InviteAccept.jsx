import React, { useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function InviteAccept(){
  const [params] = useSearchParams()
  const nav = useNavigate()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  async function submit(e){
    e.preventDefault()
    setErr(''); setMsg('')
    try {
      await api('/api/invites/accept', {
        method:'POST',
        body: JSON.stringify({ token, password })
      })
      setMsg('Invite accepted. You can now login.')
      setTimeout(()=> nav('/login'), 1000)
    } catch(e) {
      setErr('Invite failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50">
      <div className="card max-w-lg w-full">
        <h2 className="text-xl font-semibold mb-2">Accept Invite</h2>
        <div className="text-sm text-gray-600 mb-4">Token: {token ? token.slice(0,6)+'…' : '(none)'}</div>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="block mb-1 text-sm">Set Password</label>
            <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          </div>
          <button className="btn w-full" type="submit">Create Account</button>
        </form>
        {msg && <div className="text-green-700 mt-3">{msg}</div>}
        {err && <div className="text-red-600 mt-3">{err}</div>}
      </div>
    </div>
  )
}
