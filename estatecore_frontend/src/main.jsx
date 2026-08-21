import React,{useState} from "react";
import{createRoot}from"react-dom/client";
import"./styles.css";
const API=import.meta.env.VITE_API_URL||"";
function App(){
 const[token,setToken]=useState(localStorage.getItem("token")||"");
 const[portal,setPortal]=useState(null),[error,setError]=useState(""),[maintenance,setMaintenance]=useState("");
 async function login(e){e.preventDefault();setError("");const data=Object.fromEntries(new FormData(e.currentTarget));const r=await fetch(API+"/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});const j=await r.json();if(!r.ok){setError(j.error||"Login failed");return}localStorage.setItem("token",j.access_token);setToken(j.access_token);await load(j.access_token)}
 async function load(t=token){const r=await fetch(API+"/api/tenant/me",{headers:{Authorization:"Bearer "+t}});const j=await r.json();if(r.ok)setPortal(j);else setError(j.error||"Unable to load portal")}
 async function submitMaintenance(e){e.preventDefault();const r=await fetch(API+"/api/maintenance",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({description:maintenance,priority:"normal"})});if(r.ok){setMaintenance("");await load()}else setError("Unable to submit request")}
 if(!token)return <main className="shell"><section className="card"><h1>EstateCore</h1><p>Tenant portal</p><form onSubmit={login}><label>Email<input name="email" type="email" required/></label><label>Password<input name="password" type="password" required/></label><button>Sign in</button></form>{error&&<p className="error">{error}</p>}</section></main>;
 if(!portal)return <main className="shell"><section className="card"><h1>EstateCore</h1><button onClick={()=>load()}>Open my portal</button>{error&&<p className="error">{error}</p>}</section></main>;
 return <main className="shell"><header><div><h1>Hello, {portal.user.name}</h1><p>{portal.lease?.property||"No active lease"}</p></div><button className="ghost" onClick={()=>{localStorage.removeItem("token");setToken("");setPortal(null)}}>Sign out</button></header><div className="grid"><section className="card"><h2>Rent</h2><strong className="money">{"$"+(portal.lease?.monthly_rent?.toFixed(2)||"0.00")}</strong><p>Status: {portal.payments[0]?.status||"No charge"}</p></section><section className="card"><h2>Maintenance</h2><form onSubmit={submitMaintenance}><textarea value={maintenance} onChange={e=>setMaintenance(e.target.value)} placeholder="Describe the issue" required/><button>Submit request</button></form></section><section className="card wide"><h2>Recent requests</h2>{portal.maintenance.length?portal.maintenance.map(x=><div className="row" key={x.id}><span>{x.description}</span><b>{x.status}</b></div>):<p>No requests yet.</p>}</section></div></main>
}
createRoot(document.getElementById("root")).render(<App/>);
