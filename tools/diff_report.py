#!/usr/bin/env python3
"""Loose diff: mapped rows vs existing DB rows. Writes markdown report. Usage: diff_report.py new_dir old_dir out.md"""
import json,glob,re,sys
from collections import Counter,defaultdict
new_dir,old_dir,out=sys.argv[1:4]
FAM={'king-soopers':'kingsoopers','city-market':'citymarket','whole-foods':'wholefoods','costco-online':'costco'}
def al(s): return re.sub(r'[^a-z0-9]','',(s or '').lower())
def ret(r):
    a=al(r.get('retailer',''))
    for k in ('wholefoods','sprouts','kingsoopers','citymarket','costco','heb'):
        if a.startswith(k): return k
    return a
TOK=lambda s:set(t for t in re.findall(r'[a-z]+',(s or '').lower()) if len(t)>2 and t not in {'the','and','with','style','dip','sauce','cheese','pack','oz','ct'})
def load(d):
    L=[]
    for f in glob.glob(d+'/**/*.json',recursive=True):
        j=json.load(open(f)); j=j.get('data',j)
        if 'brand' in j: L.append(j)
    return L
import os
def ids(d): return {os.path.basename(f)[:-5]:f for f in glob.glob(d+'/**/*.json',recursive=True)}
IN,IO=ids(new_dir),ids(old_dir)
exact=set(IN)&set(IO)
N,O=load(new_dir),load(old_dir)
cov={ret(r) for r in N}; O=[o for o in O if ret(o) in cov]
used=set(); pairs=[]; 
byb=defaultdict(list)
for i,n in enumerate(N): byb[(ret(n),al(n['brand'])[:8])].append(i)
for o in O:
    best=None;bs=0
    for i in byb.get((ret(o),al(o['brand'])[:8]),[]):
        if i in used: continue
        a,b=TOK(o['product_name']),TOK(N[i]['product_name'])
        s=len(a&b)/max(1,len(a|b))
        if s>bs: best,bs=i,s
    if best is not None and bs>=0.5: used.add(best); pairs.append((o,N[best],bs))
    else: pairs.append((o,None,0))
matched=[p for p in pairs if p[1]]; missing=[p[0] for p in pairs if not p[1]]
newrows=[n for i,n in enumerate(N) if i not in used]
chg=[(o,n) for o,n,_ in matched if o.get('price') and n.get('price') and abs(o['price']-n['price'])>0.01]
L=[f'# EXACT id matches (safe to append price history): {len(exact)}\n',f'# SG runner vs existing DB (banners covered by runner)\n',
 f'- runner rows {len(N)}; existing rows at those banners {len(O)}',
 f'- matched {len(matched)} ({len(chg)} price changes); existing-only {len(missing)}; runner-only (new) {len(newrows)}\n',
 '## Price changes (existing -> runner)']
for o,n in sorted(chg,key=lambda t:-abs(t[0]['price']-t[1]['price'])): L.append(f"- {ret(o)} | {o['brand']} {o['product_name']}: {o['price']} -> {n['price']}")
L.append('\n## Existing-only (runner did not see), by banner/brand')
c=Counter((ret(o),o['brand']) for o in missing)
for (r,b),k in c.most_common(): L.append(f'- {r} | {b}: {k}')
L.append('\n## New rows by banner'); 
for r,k in Counter(ret(n) for n in newrows).most_common(): L.append(f'- {r}: {k}')
own=[n for n in newrows if n.get('is_own_brand')]
L.append('\n## SG own rows: existing vs runner')
for o in O:
    if o.get('is_own_brand'): L.append(f"- existing {ret(o)} | {o['product_name']} | {o.get('price')}")
for n in N:
    if n.get('is_own_brand'): L.append(f"- runner {ret(n)} | {n['product_name']} | {n.get('price')}")
na=sum(1 for n in newrows if str(n.get('size_oz') or '')=='' and not n.get('count'))
L.append(f'\n## New rows with no size parsed: {na}')
open(out,'w').write('\n'.join(L)); print('\n'.join(L[:6]))
