// In-page Instacart whitelabel search pinned to a zip. Vars: SLUG, ZIP, LAT, LNG, TERM. Uses the site's own persisted graphql queries.
const H={DefaultShop:'d389a8d33d63801f1ce5c4929fb181dd10c57b49c3a2dcb6a6baa44212e8e069',SRP:'57508d039f29d674f1ce4f68f268bb9c5be5814e27d17c2a83a5500dc9270b1c',Items:'8fe60a2c4c74b994076e8fc97883141aec582e7f6e2402d82c9902772432f183'};
const dbg=[];
const gq=async(op,vars,hash)=>{const u='/graphql?operationName='+op+'&variables='+encodeURIComponent(JSON.stringify(vars))+'&extensions='+encodeURIComponent(JSON.stringify({persistedQuery:{version:1,sha256Hash:hash}}));const r=await fetch(u,{credentials:'include',headers:{'content-type':'application/json'}});const t=await r.text();dbg.push(op+' '+r.status+' '+t.length);return JSON.parse(t);};
const coords={latitude:LAT,longitude:LNG};
const ds=await gq('DefaultShop',{postalCode:ZIP,coordinates:coords,addressId:null},H.DefaultShop);
const shop=ds.data&&ds.data.defaultShop; if(!shop) return JSON.stringify({houses:[],debug:dbg.join('|')+' noshop '+JSON.stringify(ds).slice(0,500)});
const shopId=shop.id; const sj=JSON.stringify(shop);
let zoneId=(sj.match(/"zoneId":"?(\d+)/)||[])[1]||null;
const locId=shop.retailerLocationId;
// zone from IP-default page calls if not in DefaultShop
if(!zoneId){const m=performance.getEntriesByType('resource').map(e=>decodeURIComponent(e.name)).join(' ').match(/"zoneId":"(\d+)"/); zoneId=m?m[1]:null;}
const vars={action:null,query:TERM,pageViewId:crypto.randomUUID(),elevatedProductId:null,searchSource:'search',filters:[],disableReformulation:false,disableLlm:false,forceInspiration:false,orderBy:'bestMatch',clusterId:null,includeDebugInfo:false,clusteringStrategy:null,contentManagementSearchParams:{itemGridColumnCount:5},shopId,postalCode:ZIP,zoneId:zoneId||'0',first:60};
const sr=await gq('SearchResultsPlacements',vars,H.SRP);
const ids=[...new Set((JSON.stringify(sr).match(/items_\d+-\d+/g)||[]))];
dbg.push('shop '+shopId+' loc '+locId+' zone '+zoneId+' ids '+ids.length);
const houses=[];
for(let i=0;i<ids.length&&i<120;i+=30){const it=await gq('Items',{ids:ids.slice(i,i+30),shopId,zoneId:zoneId||'0',postalCode:ZIP},H.Items);
 for(const x of ((it.data&&it.data.items)||[])){const pr=x.price&&x.price.viewSection; houses.push({name:x.name,size:x.size||null,brand:x.brandName||null,price:(pr&&(pr.itemCard&&pr.itemCard.priceString||pr.priceString))||null,item_id:x.id,product_id:x.productId||null,img:(x.viewSection&&x.viewSection.itemImage&&x.viewSection.itemImage.url)||null,availability:(x.availability&&x.availability.stockLevel)||null});}}
if(!houses.length) dbg.push('items0 '+JSON.stringify(sr).slice(0,600));
return JSON.stringify({store:'API zip '+ZIP+' shop '+shopId+' location '+locId,houses,debug:dbg.join(' | ')});
