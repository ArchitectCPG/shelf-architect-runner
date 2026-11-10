#!/usr/bin/env python3
"""Pre-landing on-shelf filter for one neighborhood, driven entirely by clients/<id>.json (replaces the Vosges-only pouch_filter.py, SOP v85 build 2).
Usage: shelf_filter.py <client> <neighborhood>
Reads mapped/<client>/retail_entries, applies the neighborhood's relevance and hard_exclude plus tools/hygiene.py judge(), writes
mapped/<client>/filtered/*.json (rows to cap and land) and filter_summary.json. Excluded and off-shelf rows are counted by reason, never silent."""
import json,glob,os,re,sys,shutil,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import hygiene
cid,nbid=sys.argv[1],sys.argv[2]; md=f'mapped/{cid}'
C=json.load(open(f'clients/{cid}.json')); H=hygiene.load(C); nb=next(n for n in C['neighborhoods'] if n['id']==nbid)
rel=re.compile(nb['relevance'],re.I) if nb.get('relevance') else None; hard=re.compile(nb['hard_exclude'],re.I) if nb.get('hard_exclude') else None
rows={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(md+'/retail_entries/*.json')}
keep={};why=collections.Counter()
for k,r in rows.items():
    if r['neighborhood']!=nbid: why['other neighborhood']+=1; continue
    t=r['brand']+' '+r['product_name']
    if r['brand']=='Unbranded': why['unbranded, held']+=1; continue
    if hard and hard.search(t): why['excluded, not the shelf']+=1; continue
    if rel and not rel.search(t): why['no shelf word, not the shelf']+=1; continue
    v,reason=hygiene.judge(H,nbid,r['brand'],r['product_name'],r.get('size_oz'),r.get('count'))
    if v=='elsewhere': why[reason]+=1; continue
    keep[k]=r; why['kept']+=1
shutil.rmtree(md+'/filtered',ignore_errors=True); os.makedirs(md+'/filtered')
for k,r in keep.items(): json.dump(r,open(f'{md}/filtered/{k}.json','w'))
json.dump(dict(why),open(md+'/filter_summary.json','w'),indent=1); print(dict(why))
