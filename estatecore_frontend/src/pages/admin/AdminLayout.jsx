import Sidebar from "../../components/dashboard/Sidebar";
import Topbar from "../../components/dashboard/Topbar";
import { Outlet } from "react-router-dom";

function Boundary({children}) {
  try { return children; } catch (e) { return <pre style={{color:'salmon'}}>{String(e)}</pre>; }
}

export default function AdminLayout(){
  return (
    <div className="min-h-screen grid grid-rows-[auto,1fr] md:grid-rows-1 md:grid-cols-[16rem,1fr]">
      <Sidebar />
      <div className="flex flex-col">
        <Topbar title="Admin Panel" />
        <main className="p-4 md:p-6 space-y-6">
          <Boundary><Outlet /></Boundary>
        </main>
      </div>
    </div>
  );
}
