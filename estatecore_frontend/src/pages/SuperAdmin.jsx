import Sidebar from '../components/Sidebar'

export default function SuperAdmin(){
  return (
    <div>
      <Sidebar />
      <div style={{padding:16}}>
        <h1>Super Admin</h1>
        <p>Only users with role <code>super_admin</code> can view this page.</p>
      </div>
    </div>
  )
}
