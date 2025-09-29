export default function RecentTable({ rows=[] }){
  return (
    <div className="ec-card p-0 overflow-hidden">
      <div className="ec-card-header">Recent Activity</div>
      <div className="ec-card-content overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left text-slate-400">
            <tr>
              <th className="py-2 pr-4">When</th>
              <th className="py-2 pr-4">Type</th>
              <th className="py-2 pr-4">Details</th>
              <th className="py-2 pr-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r,i)=>(
              <tr key={i} className="border-t border-white/5">
                <td className="py-2 pr-4">{r.when}</td>
                <td className="py-2 pr-4">{r.type}</td>
                <td className="py-2 pr-4">{r.detail}</td>
                <td className="py-2 pr-4">
                  <span className={`badge ${r.status==='closed'?'badge-success':r.status==='overdue'?'badge-danger':''}`}>{r.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
