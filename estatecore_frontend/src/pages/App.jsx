
import React from 'react'
import RequireRole from '../components/RequireRole'
import { ROLES } from '../utils/roles'
import AdminPanel from './AdminPanel'
import TenantPortal from './TenantPortal'

export default function App(){
  return (
    <div style={{padding:16}}>
      <h1>EstateCore</h1>
      <div style={{display:'flex', gap:8}}>
        <RequireRole roles={[ROLES.SUPER, ROLES.MANAGER]}><a href="#/admin">Admin</a></RequireRole>
        <RequireRole roles={[ROLES.USER, ROLES.ADMIN, ROLES.MANAGER, ROLES.SUPER]}><a href="#/portal">My Portal</a></RequireRole>
      </div>
      <div style={{marginTop:16}}>
        {location.hash==="#/admin" && (<RequireRole roles={[ROLES.SUPER, ROLES.MANAGER]}><AdminPanel/></RequireRole>)}
        {location.hash==="#/portal" && (<RequireRole roles={[ROLES.USER, ROLES.ADMIN, ROLES.MANAGER, ROLES.SUPER]}><TenantPortal/></RequireRole>)}
      </div>
    </div>
  )
}
