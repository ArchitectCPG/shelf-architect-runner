#!/usr/bin/env python3
"""Merge plan: runner rows (mapped/<client>/retail_entries) vs existing DB rows (old_dir).
API-lane banners (UPC present): runner row canonical, matching existing rows fold in (history carried, curated fields kept).
Other banners: existing row canonical, runner price appended.
Usage: merge_plan.py <client> <old_dir> -> mapped/<client>/merge_plan.json"""
import json,glob,re,os,sys
from collections import defaultdict
cid,old=sys.argv[1],sys.argv[2]; md=f'mapped/{cid}'
def al(s): return re.sub(r'[^a-z0-9]','',(s or '').lower())
def ret(r):
    a=al(r.get('retailer',''))
    for k in ('wholefoods','sprouts','kingsoopers','citymarket','costco','heb'): 
        if a.startswith(k): return k
    return a
HEAT=re.compile(r'\b(hot|medium|mild|original|spicy|extra hot)\b',re.I)
def heat(r): m=HEAT.search(re.sub(r'hot sauce','',(r.get('product_name') or '')+' '+(r.get('flavor') or ''),flags=re.I)); return (m.group(1).lower() if m else None)
STOP={'the','and','with','style','dip','sauce','cheese','pack','oz','ct','can','jar','kosher','hot','medium','mild','original','spicy'}
BRAND_ALIAS={'505sw':'505southwestern','stinkingood':'stinkingood','hatchvalley':'hatchvalley','privateselection':'privateselection','signatureselect':'signatureselect','signaturecafe':'signaturecafe','delrealfoods':'delreal','laspalmas':'laspalmas'}
def bkey(b): b=al(b); b=re.sub(r'albertsonsprivatelabel','',b); return BRAND_ALIAS.get(b,b)[:10]
TOK=lambda s:set(t for t in re.findall(r'[a-z]+',(s or '').lower()) if len(t)>2 and t not in STOP)
N={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(md+'/retail_entries/*.json')}
O={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(old+'/*.json')}
cov={ret(n) for n in N.values()}; O={k:v for k,v in O.items() if ret(v) in cov}
Nb=defaultdict(list)
for k,n in N.items(): Nb[(ret(n),bkey(n['brand']))].append(k)
def score(o,n):
    if o.get('size_oz') and n.get('size_oz') and abs(float(o['size_oz'])-float(n['size_oz']))>0.6: return 0
    ho,hn=heat(o),heat(n)
    if ho and hn and ho!=hn: return 0
    a,b=TOK(o['product_name']),TOK(n['product_name'])
    if not a or not b: return 0
    j=len(a&b)/len(a|b)
    if a<=b or b<=a: j=max(j,0.8)
    return j
DEC=json.load(open(md+'/merge_decisions.json')) if os.path.exists(md+'/merge_decisions.json') else {}
plan=[]; taken=defaultdict(list)
for ok,o in sorted(O.items()):
    if ok in DEC:
        d=DEC[ok]
        if d=='keep_existing': plan.append(dict(action='keep_existing',existing=ok,reviewed=True))
        else: plan.append(dict(action='match',existing=ok,runner=d,reviewed=True)); taken[d].append(ok)
        continue
    if ok in N: plan.append(dict(action='exact',existing=ok,runner=ok)); taken[ok].append(ok); continue
    c=sorted(((score(o,N[nk]),nk) for nk in Nb.get((ret(o),bkey(o['brand'])),[])),reverse=True)
    if c and c[0][0]>=0.5: plan.append(dict(action='match',existing=ok,runner=c[0][1],score=round(c[0][0],2))); taken[c[0][1]].append(ok)
    elif c and c[0][0]>=0.3: plan.append(dict(action='review',existing=ok,runner=c[0][1],score=round(c[0][0],2)))
    else: plan.append(dict(action='keep_existing',existing=ok))
for nk in N:
    if nk not in taken: plan.append(dict(action='new',runner=nk))
# direction per banner: API lane (upc) -> runner canonical
for p in plan:
    if p['action'] in('match','exact'):
        n=N[p['runner']]; p['canonical']='runner' if n.get('upc') else 'existing'
json.dump(plan,open(md+'/merge_plan.json','w'),indent=0)
from collections import Counter
print(Counter(p['action'] for p in plan))
print('existing rows folding into one runner row (API banners):',sum(1 for k,v in taken.items() if len(v)>1),'groups,',sum(len(v)-1 for v in taken.values() if len(v)>1),'rows collapse')
for p in plan:
    if p['action']=='review': print('REVIEW',p['existing'][:60],'->',p['runner'][:60],p['score'])
