#!/usr/bin/env python3
"""Roll up the latest pull per generated block for a client into one scored report (markdown + json). Sandbox only."""
import json,sys,glob,os,re,statistics
cid=sys.argv[1]; C=json.load(open(f'clients/{cid}.json'))
def price(p):
    m=re.search(r'(\d+(?:\.\d+)?)',str(p or '').replace(',','')); return float(m.group(1)) if m else None
rows=[]; allh=[]
for f in sorted(glob.glob(f'blocks_gen/{cid}/*.json')):
    b=json.load(open(f)); bid=re.sub(r'[^a-z0-9@_.-]','_',b['block_id'],flags=re.I)
    fs=sorted(glob.glob(f"data/{b['retailer']}/{bid}/*.json")); fs=[x for x in fs if not x.endswith('-error.json')]
    if not fs: rows.append(dict(banner=b['retailer'],term=b['term'],status='NO DATA',houses=0)); continue
    d=json.load(open(fs[-1])); h=d.get('houses',[])
    for x in h:
        nm=(x.get('name') or '')+' '+(x.get('brand') or '')
        x['_banner']=b['retailer']; x['_term']=b['term']; x['_sg']=any(t in nm.lower() for t in C['brand_terms'])
        x['_comp']=[k for k,ts in C['competitor_terms'].items() if any(t in nm.lower() for t in ts)]
        allh.append(x)
    ps=[price(x.get('price')) for x in h if price(x.get('price'))]
    rows.append(dict(banner=b['retailer'],term=b['term'],status='OK' if len(h)>=5 and not d.get('error') else 'WEAK',houses=len(h),store=str(d.get('store_set') or '')[:60],
        sg=sum(1 for x in h if x['_sg']),comp=sum(1 for x in h if x['_comp']),pmed=round(statistics.median(ps),2) if ps else None,err=str(d.get('error') or '')[:60]))
json.dump(dict(client=cid,rows=rows,sg_items=[{k:v for k,v in x.items() if k in('name','price','size','_banner','_term')} for x in allh if x['_sg']],
    comp_items=[{k:v for k,v in x.items() if k in('name','price','size','_banner','_term','_comp')} for x in allh if x['_comp']]),open(f'data/clients_{cid}_report.json','w'),indent=1)
print('| banner | term | status | houses | store | SG | comp | median $ |'); print('|---|---|---|---|---|---|---|---|')
for r in rows: print('|',r['banner'],'|',r['term'],'|',r['status'],'|',r['houses'],'|',r.get('store',''),'|',r.get('sg',''),'|',r.get('comp',''),'|',r.get('pmed',''),r.get('err',''),'|')
