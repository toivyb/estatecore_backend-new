
import { useState } from 'react';

export default function InviteAccept() {
  const [token, setToken] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');

  async function submit(e){
    e.preventDefault();
    const res = await fetch('/api/invites/consume', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({token, full_name: fullName, password})
    });
    const data = await res.json();
    if(res.ok){ setMsg('Account created. You can log in.'); }
    else { setMsg(data.msg || 'Error'); }
  }

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-2xl shadow">
      <h1 className="text-xl font-bold mb-4">Accept Invite</h1>
      <form onSubmit={submit} className="space-y-3">
        <input className="w-full border p-2 rounded" placeholder="Invite Token" value={token} onChange={e=>setToken(e.target.value)} />
        <input className="w-full border p-2 rounded" placeholder="Full Name" value={fullName} onChange={e=>setFullName(e.target.value)} />
        <input className="w-full border p-2 rounded" placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <button className="w-full bg-black text-white py-2 rounded">Create Account</button>
      </form>
      {msg && <p className="mt-3 text-sm">{msg}</p>}
    </div>
  );
}
