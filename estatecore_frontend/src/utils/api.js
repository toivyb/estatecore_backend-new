const API = import.meta.env.VITE_API_BASE || '/api'

export async function api(method, path, body, isForm=false){
  const token = JSON.parse(localStorage.getItem('estatecore.session')||'{}').token
  const headers = isForm ? (token? { Authorization:`Bearer ${token}` } : {}) : {
    'Content-Type':'application/json', ...(token? { Authorization:`Bearer ${token}` } : {})
  }
  const res = await fetch(`${API}${path}`, {
    method, headers, body: isForm? body : (body? JSON.stringify(body): undefined)
  })
  if(!res.ok){
    let msg = 'Request failed'
    try { const t = await res.json(); msg = t.msg || JSON.stringify(t) } catch {}
    throw new Error(msg)
  }
  const ctype = res.headers.get('content-type') || ''
  return ctype.includes('application/json') ? res.json() : res.blob()
}

