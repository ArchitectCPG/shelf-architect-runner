#!/usr/bin/env python3
"""Hybrid block cap (pull_process.run_caps, pc-2026-10-05-09 and -12) on mapped runner rows.
One row per brand in page order, then fill to 20 with those brands' other SKUs. Over 20 brands: one per brand, no fill.
Usage: block_cap.py <client> -> mapped/<client>/capped/*.json + cap_summary.json"""
import json,glob,os,re,sys,shutil
from collections import OrderedDict,defaultdict
cid=sys.argv[1]; md=f'mapped/{cid}'; CAP=20
al=lambda s:re.sub(r'[^a-z0-9]','',(s or '').lower())
rows={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(md+'/'+(os.environ.get('CAP_SRC','retail_entries'))+'/*.json')}
# page order from raw runner output: data/<banner>/<client>_<block>-<market>/<date>.json houses[]
order={}
for f in glob.glob(f'data/*/{cid}_*/*.json'):
    try: d=json.load(open(f))
    except Exception: continue
    for i,h in enumerate(d.get('houses',[])): order.setdefault((al(d.get('retailer')),al(h.get('name'))),i)
by=defaultdict(list)
for k,r in rows.items(): by[r['block']].append(k)
out={}; summ={}
for b,ks in sorted(by.items()):
    def rank(k):
        r=rows[k]; n=al(r['product_name'])
        for (ret,name),i in order.items():
            if name==n or name.startswith(n) or n.startswith(name): return i
        return 10**6
    ks=sorted(ks,key=lambda k:(rank(k),k))
    brands=OrderedDict()
    for k in ks: brands.setdefault(rows[k]['brand'],[]).append(k)
    keep=[v[0] for v in brands.values()]
    mode='wide shelf, one row per brand, no fill' if len(brands)>CAP else 'one row per brand then fill to 20'
    if len(brands)<=CAP:
        rest=[k for k in ks if k not in keep]; keep+=rest[:CAP-len(keep)]
    for k in keep: out[k]=rows[k]
    summ[b]=dict(rows_in=len(ks),brands=len(brands),rows_out=len(keep),mode=mode)
shutil.rmtree(md+'/capped',ignore_errors=True); os.makedirs(md+'/capped')
for k,r in out.items(): json.dump(r,open(f'{md}/capped/{k}.json','w'))
json.dump(summ,open(md+'/cap_summary.json','w'),indent=1)
print(json.dumps(summ,indent=1)); print('rows out',len(out))
