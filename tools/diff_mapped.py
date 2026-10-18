#!/usr/bin/env python3
"""Diff mapper output against existing DB rows (fuzzy key: retailer family + brand alnum + product alnum prefix)."""
import json,glob,re,sys
new_dir,old_dir=sys.argv[1],sys.argv[2]
FAM={'king-soopers':'kingsoopers','city-market':'citymarket','whole-foods':'wholefoods','costco-online':'costco'}
def al(s): return re.sub(r'[^a-z0-9]','',(s or '').lower())
def key(r):
    ret=al(FAM.get(r.get('retailer','').lower().replace(' ','-'),r.get('retailer','')))
    return ret,al(r.get('brand'))[:10],al(r.get('product_name'))[:18]
def load(d):
    out={}
    for f in glob.glob(d+'/**/*.json',recursive=True):
        j=json.load(open(f)); j=j.get('data',j)
        if 'brand' in j: out[key(j)]=j
    return out
N,O=load(new_dir),load(old_dir)
# restrict old to banners the runner covered
cov={k[0] for k in N}; O={k:v for k,v in O.items() if k[0] in cov}
both=set(N)&set(O); onlyN=set(N)-set(O); onlyO=set(O)-set(N)
print(f'runner rows {len(N)} | existing rows at same banners {len(O)} | matched {len(both)} | new {len(onlyN)} | missing from runner {len(onlyO)}')
d=[(k,O[k].get('price'),N[k].get('price')) for k in both if O[k].get('price') and N[k].get('price')]
moves=[(k,a,b) for k,a,b in d if abs(a-b)>0.01]
print(f'price compared {len(d)}, differ {len(moves)}')
for k,a,b in sorted(moves,key=lambda t:-abs(t[2]-t[1]))[:10]: print('  ',k,a,'->',b)
own_old=[v['product_name'] for k,v in O.items() if v.get('is_own_brand')]; own_new=[v['product_name'] for k,v in N.items() if v.get('is_own_brand')]
print('SG own rows existing',len(own_old),'runner',len(own_new))
from collections import Counter
print('missing by banner',Counter(k[0] for k in onlyO).most_common(8))
