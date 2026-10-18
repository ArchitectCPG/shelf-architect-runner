#!/usr/bin/env python3
"""Roll up the latest pull per generated block for a client into one scored report (markdown + json). Sandbox only."""
import json,sys,glob,os,re,statistics
sys.path.insert(0,os.path.dirname(__file__)); from normalize import normalize
cid=sys.argv[1]; C=json.load(open(f'clients/{cid}.json'))
def price(p):
    m=re.search(r'(\d+(?:\.\d+)?)',str(p or '').replace(',','')); return float(m.group(1)) if m else None
rows=[]; allh=[]
for f in sorted(glob.glob(f'blocks_gen/{cid}/*.json')):
    b=json.load(open(f)); bid=re.sub(r'[^a-z0-9@_.-]','_',b['block_id'],flags=re.I)
    fs=sorted(glob.glob(f"data/{b['retailer']}/{bid}/*.json")); fs=[x for x in fs if not x.endswith('-error.json')]
    if not fs: rows.append(dict(banner=b['retailer'],term=b['term'],status='NO DATA',houses=0)); continue
    d=json.load(open(fs[-1])); h=d.get('houses',[])
    nb=next(n for n in C['neighborhoods'] if b['neighborhood']==n['id'])
    h=[normalize(x,C,nb) for x in h]
    for x in h:
        nm=(x.get('name') or '')+' '+(x.get('brand') or '')
        x['_banner']=b['retailer']; x['_term']=b['term']; x['_sg']=any(re.search(t,nm,re.I) for t in C['brand_terms']) and not (C.get('brand_exclude') and re.search(C['brand_exclude'],nm,re.I))
        x['_comp']=[k for k,ts in C['competitor_terms'].items() if any(re.search(t,nm,re.I) for t in ts)]
        allh.append(x)
    hr=[x for x in h if x['relevant']]; ps=[price(x.get('price')) for x in hr if price(x.get('price'))]
    rows.append(dict(banner=b['retailer'],term=b['term'],status='OK' if len(h)>=5 and not d.get('error') else 'WEAK',houses=len(h),relevant=len(hr),store=str(d.get('store_set') or '')[:60],
        sg=sum(1 for x in h if x['_sg']),comp=sum(1 for x in h if x['_comp']),pmed=round(statistics.median(ps),2) if ps else None,err=str(d.get('error') or '')[:60]))
json.dump(dict(client=cid,rows=rows,sg_items=[{k:v for k,v in x.items() if k in('name','brand_norm','price','price_regular','price_promo','size','_banner','_term','relevant')} for x in allh if x['_sg']],
    comp_items=[{k:v for k,v in x.items() if k in('name','brand_norm','price','price_regular','price_promo','size','_banner','_term','_comp','relevant')} for x in allh if x['_comp']]),open(f'data/clients_{cid}_report.json','w'),indent=1)
print('| banner | term | status | houses | relevant | store | SG | comp | median $ |'); print('|---|---|---|---|---|---|---|---|---|')
for r in rows: print('|',r['banner'],'|',r['term'],'|',r['status'],'|',r['houses'],'|',r.get('relevant',''),'|',r.get('store',''),'|',r.get('sg',''),'|',r.get('comp',''),'|',r.get('pmed',''),r.get('err',''),'|')
