import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.jsx'

export default function Login(){
  const nav = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')

  async function submit(e){
    e.preventDefault()
    setErr('')
    try{
      const u = await login(email, password)
      if(u.role === 'super_admin') nav('/super-admin')
      else nav('/')
    }catch(e){
      setErr(e.message || 'Login failed')
    }
  }

  return (
    <div className="wrap">
      <div className="card">
        <h2>Login</h2>
        <form onSubmit={submit}>
          <input placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
          <input placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          {err && <div style={{color:'crimson'}}>{err}</div>}
          <button type="submit">Login</button>
        </form>
      </div>
    </div>
  )
}