const { chromium } = require('playwright'); const http=require('http'),fs=require('fs');
(async()=>{ fs.mkdirSync('srvC',{recursive:true}); fs.copyFileSync('main_after2.html','srvC/index.html');
 const sv=http.createServer((q,r)=>{const f='srvC'+q.url.split('?')[0]; if(fs.existsSync(f)&&fs.statSync(f).isFile()){r.end(fs.readFileSync(f));}else{r.writeHead(404);r.end();}}).listen(8703);
 const br=await chromium.launch({executablePath:'/usr/bin/google-chrome'}); const p=await br.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(e.message));
 const st={}; for(let i=0;i<5;i++) st['retail_entries/r'+i]={brand:'B'+i,price:i}; st['retailers/x']={name:'x'};
 await p.addInitScript(`window.__STORE_INIT=${JSON.stringify(st)};`); await p.addInitScript({path:'stub.js'});
 await p.goto('http://localhost:8703/index.html'); await p.waitForTimeout(1200); await p.click('#refExportRows'); await p.waitForTimeout(500);
 const s=await p.evaluate(()=>window.__SAVED); const b=JSON.parse(s.text); console.log(s.filename,b.kind,b.count,b.rows[0]); console.log(await p.textContent('#refStatus'),'errors',errs);
 await br.close(); sv.close(); })();
