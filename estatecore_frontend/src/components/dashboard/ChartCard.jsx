import { useEffect, useRef } from 'react';

// super-lightweight inline chart using canvas to avoid extra deps
export default function ChartCard({ title='Income vs Cost', series=[12,16,14,18,20,22,19,24] }){
  const ref = useRef(null);
  useEffect(()=>{
    const c = ref.current; if(!c) return;
    const ctx = c.getContext('2d');
    const w = c.width = c.offsetWidth, h = c.height = 120;
    ctx.clearRect(0,0,w,h);
    const max = Math.max(...series, 1), pad = 8, step = (w- pad*2) / (series.length-1);
    ctx.lineWidth = 2;
    // line
    ctx.beginPath();
    series.forEach((v,i)=>{
      const x = pad + i*step;
      const y = h - pad - (v/max)*(h-pad*2);
      i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
    });
    ctx.strokeStyle = 'rgba(194,163,90,0.9)';
    ctx.stroke();
    // fill
    const grad = ctx.createLinearGradient(0,0,0,h);
    grad.addColorStop(0,'rgba(194,163,90,0.25)'); grad.addColorStop(1,'rgba(194,163,90,0)');
    ctx.lineTo(w-pad,h-pad); ctx.lineTo(pad,h-pad); ctx.closePath();
    ctx.fillStyle = grad; ctx.fill();
  }, [series]);
  return (
    <div className="ec-card p-4">
      <div className="text-sm text-slate-300 mb-2">{title}</div>
      <div className="w-full"><canvas ref={ref} className="w-full" /></div>
    </div>
  );
}
