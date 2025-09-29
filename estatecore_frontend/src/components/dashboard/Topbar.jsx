export default function Topbar({ title='Admin Panel' }){
  return (
    <header className="h-14 border-b border-white/10 flex items-center justify-between px-4 bg-[#0b0d10]/60 backdrop-blur">
      <h1 className="text-base font-semibold">{title}</h1>
      <div className="flex items-center gap-2">
        <button className="ec-btn ec-btn-ghost">My Portal</button>
      </div>
    </header>
  );
}
