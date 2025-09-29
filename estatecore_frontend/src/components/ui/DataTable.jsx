import { useMemo, useState, useEffect } from 'react';
export default function DataTable({ columns=[], rows=[], pageSize=10, initialSort=null, searchable=true, filterDefs={} }){
  const [q,setQ]=useState(''),[page,setPage]=useState(1),[sort,setSort]=useState(initialSort),[filters,setFilters]=useState({});
  useEffect(()=>setPage(1),[q,JSON.stringify(filters)]);
  const filtered=useMemo(()=>{let out=[...(rows||[])];
    Object.entries(filters).forEach(([name,val])=>{if(!val)return;const def=filterDefs[name];if(!def)return;const key=def.key||name;out=out.filter(r=>String(r?.[key]??'').toLowerCase()===String(val).toLowerCase());});
    if(q.trim()){const n=q.toLowerCase();out=out.filter(r=>Object.values(r??{}).some(v=>String(v??'').toLowerCase().includes(n)));}
    if(sort?.key){const dir=sort.dir==='desc'?-1:1;out.sort((a,b)=>{const av=a?.[sort.key],bv=b?.[sort.key];if(av==null&&bv==null)return 0;if(av==null)return 1;if(bv==null)return -1;if(typeof av==='number'&&typeof bv==='number')return (av-bv)*dir;return String(av).localeCompare(String(bv))*dir;});}
    return out;},[rows,q,sort,filters,JSON.stringify(filterDefs)]);
  const pages=Math.max(1,Math.ceil(filtered.length/pageSize)),start=(page-1)*pageSize,paged=filtered.slice(start,start+pageSize);
  const toggleSort=(key)=>{setPage(1);setSort(s=>!s||s.key!==key?{key,dir:'asc'}:s.dir==='asc'?{key,dir:'desc'}:null)};
  return(<div className="space-y-3">
    <div className="flex flex-col md:flex-row md:items-center gap-2">
      {searchable&&<input className="ec-input md:w-80" placeholder="Search..." value={q} onChange={e=>setQ(e.target.value)}/>}
      <div className="flex gap-2 flex-wrap">{Object.entries(filterDefs).map(([name,def])=>(
        <div key={name} className="flex items-center gap-2">
          <label className="text-xs text-slate-400">{def.label||name}</label>
          <select className="ec-input" value={filters[name]||''} onChange={e=>setFilters(f=>({...f,[name]:e.target.value}))}>
            <option value="">All</option>
            {(def.values||[]).map(opt=><option key={opt.value} value={opt.value}>{opt.label??opt.value}</option>)}
          </select>
        </div>))}
      </div>
    </div>
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="text-left text-slate-400">
          <tr>{columns.map(col=>(<th key={col.key} className="py-2 pr-4">
            <button className="inline-flex items-center gap-1 hover:text-white" onClick={()=>col.sortable!==false&&toggleSort(col.key)} disabled={col.sortable===false} title={col.sortable===false?'':'Sort'}>
              {col.label}{sort?.key===col.key&&<span>{sort.dir==='asc'?'▲':'▼'}</span>}
            </button></th>))}
          </tr>
        </thead>
        <tbody>{paged.map((row,i)=>(<tr key={row.id??i} className="border-t border-white/5">
          {columns.map(col=>(<td key={col.key} className="py-2 pr-4">{col.render?col.render(row):(row?.[col.key]??'-')}</td>))}
        </tr>))}</tbody>
      </table>
    </div>
    <div className="flex items-center justify-between pt-2">
      <div className="text-xs text-slate-400">{filtered.length} items • Page {page}/{pages}</div>
      <div className="flex gap-2">
        <button className="ec-btn ec-btn-ghost" onClick={()=>setPage(p=>Math.max(1,p-1))} disabled={page===1}>Prev</button>
        <button className="ec-btn ec-btn-ghost" onClick={()=>setPage(p=>Math.min(pages,p+1))} disabled={page===pages}>Next</button>
      </div>
    </div>
  </div>)};
