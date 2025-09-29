export default function StatCard({ label, value, delta, hint }){
  return (
    <div className="ec-card p-4">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
      {delta && <div className={`mt-1 text-xs ${delta.startsWith('+') ? 'text-emerald-400' : 'text-rose-400'}`}>{delta}</div>}
      {hint && <div className="mt-2 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}
