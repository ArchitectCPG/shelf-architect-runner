const { chromium } = require('playwright');
const http=require('http'), fs=require('fs'), path=require('path');
function serve(dir, port){ return http.createServer((q,r)=>{ const f=path.join(dir, decodeURIComponent(q.url.split('?')[0])); if(fs.existsSync(f)&&fs.statSync(f).isFile()){ r.writeHead(200,{'content-type':f.endsWith('.json')?'application/json':'text/html'}); r.end(fs.readFileSync(f)); } else { r.writeHead(404); r.end(); } }).listen(port); }
(async()=>{
  const main={ 'retailers/a':{name:'A',banner:'A',channel:'Natural'}, 'retailers/b':{name:'B',banner:'B'}, 'review_calendar/r1':{retailer:'A'},
    'insights/g1':{client_id:'general',title:'g'}, 'insights/c1':{client_id:'vosges',title:'secret'}, 'app_meta/pull_process':{version:85,x:1},
    'app_meta/dropdowns':{a:[1]}, 'app_meta/instances':{secret:true}, 'forecast_images/retail-marketing-framework':{url:'files/retail-marketing-framework.jpg'},
    'retail_entries/x':{client_id:'vosges'}, 'clients/vosges':{name:'Vosges'} };
  fs.mkdirSync('srvA',{recursive:true}); fs.copyFileSync('main_after.html','srvA/index.html');
  const sA=serve('srvA',8701);
  const br=await chromium.launch({executablePath:'/usr/bin/google-chrome'});
  const errs=[];
  let p=await br.newPage(); p.on('pageerror',e=>errs.push('A '+e.message));
  await p.addInitScript(`window.__STORE_INIT=${JSON.stringify(main)};`); await p.addInitScript({path:'stub.js'});
  await p.goto('http://localhost:8701/index.html'); await p.waitForTimeout(1500);
  const seedHiddenA=await p.$eval('#refSeed',e=>e.hidden);
  await p.click('#refExport'); await p.waitForTimeout(800);
  const saved=await p.evaluate(()=>window.__SAVED);
  const b=JSON.parse(saved.text);
  console.log('A seed button hidden:',seedHiddenA,'| file',saved.filename,'| docs',b.doc_count,'| paths',b.docs.map(d=>d.path).join(' '));
  console.log('A status:',await p.textContent('#refStatus'));
  // Instance B: empty store, bundle served; one pre-existing local field to prove merge
  fs.mkdirSync('srvB/seed',{recursive:true}); fs.copyFileSync('main_after.html','srvB/index.html'); fs.writeFileSync('srvB/seed/reference_set.json',saved.text);
  const sB=serve('srvB',8702);
  p=await br.newPage(); p.on('pageerror',e=>errs.push('B '+e.message));
  await p.addInitScript(`window.__STORE_INIT=${JSON.stringify({'app_meta/pull_process':{version:84,local_note:'keep'}})};`); await p.addInitScript({path:'stub.js'});
  await p.goto('http://localhost:8702/index.html'); await p.waitForTimeout(1500);
  console.log('B banner:',await p.$eval('#seedBanner',e=>e.style.display+' | '+e.textContent.trim()));
  console.log('B seed hidden:',await p.$eval('#refSeed',e=>e.hidden));
  await p.click('#seedBannerBtn'); console.log('B after 1 tap:',await p.textContent('#refSeed'));
  await p.click('#seedBannerBtn'); await p.waitForTimeout(1500);
  const st=await p.evaluate(()=>window.__STORE);
  console.log('B status:',await p.textContent('#refStatus'),'| banner',await p.$eval('#seedBanner',e=>e.style.display));
  console.log('B keys:',Object.keys(st).sort().join(' '));
  console.log('B pull_process:',JSON.stringify(st['app_meta/pull_process']),'| seed_log created/merged',st['app_meta/seed_log'].created,st['app_meta/seed_log'].merged);
  await p.screenshot({path:'B.png'});
  console.log('errors:',errs.length?errs:'none');
  await br.close(); sA.close(); sB.close();
})();
