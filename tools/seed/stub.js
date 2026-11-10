(function(){
  const store = window.__STORE = window.__STORE_INIT || {};
  const sleep = ms => new Promise(r=>setTimeout(r,ms));
  function snapDoc(path){ const id=path.split('/').pop(); const d=store[path]; return {id, exists:!!d, data:()=>d?JSON.parse(JSON.stringify(d)):undefined, metadata:{fromCache:false,hasPendingWrites:false}}; }
  function merge(a,b){ for(const k in b){ if(b[k]&&typeof b[k]==='object'&&!Array.isArray(b[k])&&a[k]&&typeof a[k]==='object'&&!Array.isArray(a[k])) merge(a[k],b[k]); else a[k]=JSON.parse(JSON.stringify(b[k])); } return a; }
  window.__CALLS=0;
  function docRef(path){ return { id:path.split('/').pop(), path,
    get: async()=>{window.__CALLS++; await sleep(1); return snapDoc(path);},
    set: async(d)=>{window.__CALLS++; store[path]=JSON.parse(JSON.stringify(d));},
    update: async(d)=>{window.__CALLS++; if(!store[path]) throw {code:'invalid_argument',message:'missing'}; merge(store[path],d);},
    delete: async()=>{delete store[path];},
    onSnapshot:(n)=>{ setTimeout(()=>n(snapDoc(path)),5); return ()=>{}; },
    collection:(p)=>colRef(path+'/'+p) }; }
  function colRef(name, filters=[], lim=null){
    const run=()=>{ let docs=Object.keys(store).filter(p=>p.startsWith(name+'/')&&p.split('/').length===name.split('/').length+1).sort().map(snapDoc);
      filters.forEach(([f,op,v])=>{ docs=docs.filter(d=>{const x=d.data()[f]; return op==='=='?x===v:op==='in'?v.includes(x):op==='array-contains'?(x||[]).includes(v):true;}); });
      if(lim) docs=docs.slice(0,lim); return {docs,size:docs.length,empty:!docs.length,docChanges:()=>[],metadata:{fromCache:false,hasPendingWrites:false}}; };
    return { path:name, where:(f,o,v)=>colRef(name,filters.concat([[f,o,v]]),lim), orderBy:()=>colRef(name,filters,lim), limit:(n)=>colRef(name,filters,n),
      get: async()=>{window.__CALLS++; return run();}, onSnapshot:(n)=>{ setTimeout(()=>n(run()),5); return ()=>{}; },
      doc:(id)=>docRef(name+'/'+(id||Math.random().toString(36).slice(2))), add: async(d)=>{const r=docRef(name+'/'+Math.random().toString(36).slice(2)); await r.set(d); return r;} }; }
  const db={ doc:docRef, collection:(n)=>colRef(n) };
  window.__SAVED=null;
  const downloads={ save: async({filename,data})=>{ window.__SAVED={filename, text: await data.text()}; } };
  window.claude={ use: async(n)=> n==='db'?db : n==='downloads'?downloads : null };
})();
