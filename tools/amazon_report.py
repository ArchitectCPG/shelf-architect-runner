#!/usr/bin/env python3
"""Amazon lane report for one client. Reads blocks_gen/<cid>/amazon/*.json and data/amazon/<block>/<date>.json,
writes data/clients_<cid>_amazon_report.json and prints a markdown table.
SEPARATE from retail: never reads or writes data/<retailer>/, never feeds client_report / mapper / landing,
and never touches the 40/15/20 retail waterfall. Target home for these rows is amazon_comps (manual audit), not retail_entries.
No size-of-prize estimate here on purpose: bought_past_month is Amazon's own rounded floor, shown as that, nothing derived from BSR.
Usage: amazon_report.py <client_id>"""
import json,sys,glob,os,re,statistics
sys.path.insert(0,os.path.dirname(__file__)); from normalize import build_hints,brand_of,relevant
cid=sys.argv[1]; C=json.load(open(f'clients/{cid}.json'))
def num(s):
    m=re.search(r'(\d+(?:\.\d+)?)',str(s or '').replace(',','')); return float(m.group(1)) if m else None
PACK=[re.compile(p,re.I) for p in (r'pack of (\d{1,3})',r'(\d{1,3})\s?-?\s?(?:pack|pk)\b',r'(\d{1,3})\s?(?:count|ct)\b',r'\((\d{1,3}) (?:cans|bottles|jars|pouches|bags|units)\)',r'(\d{1,3}) (?:cans|bottles|jars|pouches|bags)\b',r'case of (\d{1,3})')]
def pack_count(name):
    for rx in PACK:
        m=rx.search(name or '')
        if m: return int(m.group(1))
    return 1
def bpm(h):
    v=h.get('bought_past_month'); t=h.get('bought_past_month_text') or ''
    if v not in (None,''): return num(v)
    m=re.search(r'(\d+)(K?)\+?',t.replace(',',''))
    return (float(m.group(1))*(1000 if m.group(2) else 1)) if m else None
skipped=os.path.exists(f'blocks_gen/{cid}/amazon/SKIPPED.txt')
if skipped: print(open(f'blocks_gen/{cid}/amazon/SKIPPED.txt').read().strip())
rows=[]; items=[]; hints=build_hints(C)
for f in sorted(glob.glob(f'blocks_gen/{cid}/amazon/*.json')):
    b=json.load(open(f)); bid=re.sub(r'[^a-z0-9@_.-]','_',b['block_id'],flags=re.I)
    fs=sorted(x for x in glob.glob(f"data/amazon/{bid}/*.json") if not x.endswith('-error.json'))
    if not fs: rows.append(dict(neighborhood=b['neighborhood'],term=b['term'],status='NO DATA',houses=0)); continue
    d=json.load(open(fs[-1])); nb=next(n for n in C['neighborhoods'] if n['id']==b['neighborhood'])
    hs=[]
    for h in d.get('houses',[]):
        nm=(h.get('name') or ''); pc=pack_count(nm); p=num(h.get('price'))
        x=dict(asin=h.get('asin'),name=nm[:140],brand=h.get('brand'),brand_norm=brand_of(h,hints),price=p,
               pack=pc,per_unit=round(p/pc,2) if p and pc else None,size=h.get('size'),
               bought_past_month=bpm(h),bs_rank=h.get('bs_rank'),bs_category=h.get('bs_category'),
               root_bs_rank=h.get('root_bs_rank'),rating=h.get('rating'),reviews=h.get('reviews'),
               sponsored=bool(h.get('sponsored')),badge=h.get('badge'),prime=h.get('prime'),seller=h.get('seller'),
               coupon=h.get('coupon'),link=h.get('link'),neighborhood=b['neighborhood'],relevant=relevant(h,nb))
        blob=nm+' '+(x['brand'] or '')
        x['client']=any(re.search(t,blob,re.I) for t in C['brand_terms']) and not (C.get('brand_exclude') and re.search(C['brand_exclude'],blob,re.I))
        x['comp']=[k for k,ts in C['competitor_terms'].items() if any(re.search(t,blob,re.I) for t in ts)]
        hs.append(x)
    rel=[x for x in hs if x['relevant']]; org=[x for x in rel if not x['sponsored']]
    pu=[x['per_unit'] for x in rel if x['per_unit']]
    rows.append(dict(neighborhood=b['neighborhood'],term=b['term'],status='OK' if len(hs)>=5 and not d.get('error') else 'WEAK',
        houses=len(hs),relevant=len(rel),organic=len(org),client=sum(1 for x in hs if x['client']),comp=sum(1 for x in hs if x['comp']),
        per_unit_med=round(statistics.median(pu),2) if pu else None,
        top_bpm=sorted(((x['bought_past_month'] or 0,x['brand_norm'] or x['brand'] or '?') for x in rel),reverse=True)[:3],
        err=str(d.get('error') or '')[:80]))
    items+=hs
json.dump(dict(client=cid,channel='amazon',skipped=skipped,temperature=(C.get('amazon') or {}).get('temperature'),rows=rows,
    client_items=[x for x in items if x['client']],comp_items=[x for x in items if x['comp']],
    all_relevant=[x for x in items if x['relevant']]),open(f'data/clients_{cid}_amazon_report.json','w'),indent=1)
print('| neighborhood | term | status | houses | relevant | organic | client | comp | median $/unit | top bought/mo |'); print('|---|---|---|---|---|---|---|---|---|---|')
for r in rows: print('|',r['neighborhood'],'|',r['term'],'|',r['status'],'|',r['houses'],'|',r.get('relevant',''),'|',r.get('organic',''),'|',r.get('client',''),'|',r.get('comp',''),'|',r.get('per_unit_med',''),'|',', '.join(f"{b} {int(v):,}" for v,b in r.get('top_bpm',[])),r.get('err',''),'|')
