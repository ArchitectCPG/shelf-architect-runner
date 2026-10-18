#!/usr/bin/env python3
"""Build landing batches from merge_plan: writes mapped/<client>/landing/batch_NN.json (ArtifactData batch bodies) + landing_summary.json.
Usage: landing.py <client> <old_dir>"""
import json,glob,os,sys,datetime
cid,old=sys.argv[1],sys.argv[2]; md=f'mapped/{cid}'; today='2026-10-18'
P=json.load(open(md+'/merge_plan.json'))
N={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(md+'/retail_entries/*.json')}
O={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(old+'/*.json')}
CUR=['flavor','format','protein','priority','channel','category','notes','upc','store_count_note','source_url']
def hist(a,b):
    seen={};
    for h in (a or [])+(b or []):
        if h.get('date') and h.get('price') is not None: seen[h['date']]=h
    return [seen[k] for k in sorted(seen)]
writes=[]; summary=dict(new=0,append=0,fold=0,delete=0,keep=0)
groups={}
for p in P:
    if p['action']=='new':
        r=dict(N[p['runner']]); r.pop('hold_reason',None); writes.append(dict(op='set',collection='retail_entries',doc_id=p['runner'],data=r)); summary['new']+=1
    elif p['action'] in('exact','match'): groups.setdefault(p['runner'],[]).append(p['existing'])
    else: summary['keep']+=1
for rk,exs in groups.items():
    n=dict(N[rk]); n.pop('hold_reason',None)
    old_rows=[O[e] for e in exs]
    if n.get('upc'):
        # runner canonical: fold existing into runner row
        h=n['price_history']
        for o in old_rows: h=hist(o.get('price_history'),h)
        n['price_history']=h
        for k in CUR:
            vals=[o.get(k) for o in old_rows if o.get(k) not in (None,'','N/A')]
            if vals and k!='upc': n[k]=vals[0] if k!='notes' else (vals[0]+' | '+n.get('notes','')).strip(' |')
        n['merged_from']=[e for e in exs if e!=rk]
        n['neighborhoods']=sorted(set(n.get('neighborhoods',[]))|{o.get('neighborhood') for o in old_rows if o.get('neighborhood')})
        ex_same=[e for e in exs if e==rk]
        writes.append(dict(op='set',collection='retail_entries',doc_id=rk,data=n,**({'_existing':rk} if ex_same else {})))
        for e in exs:
            if e!=rk: writes.append(dict(op='delete',collection='retail_entries',doc_id=e,_existing=e)); summary['delete']+=1
        summary['fold']+=1
    else:
        # existing canonical: append runner price
        e=exs[0]; o=dict(O[e]); 
        o['price_history']=hist(o.get('price_history'),n['price_history']); o['price']=n['price']; o['last_pulled']=today; o['pulled_at']=n['pulled_at']
        if n.get('sale_price'): o['sale_price']=n['sale_price']
        o['regular_price']=n.get('price_regular'); o['route']=n['route']; o['block']=n['block']; o['region']=n['region']
        o['notes']=(o.get('notes','')+f" | Runner append {today}.").strip(' |')
        writes.append(dict(op='set',collection='retail_entries',doc_id=e,data=o,_existing=e)); summary['append']+=1
os.makedirs(md+'/landing',exist_ok=True)
for f in glob.glob(md+'/landing/*.json'): os.remove(f)
for i in range(0,len(writes),50):
    json.dump(writes[i:i+50],open(f'{md}/landing/batch_{i//50:02d}.json','w'))
summary['writes']=len(writes); summary['batches']=(len(writes)+49)//50
json.dump(summary,open(md+'/landing_summary.json','w'),indent=1); print(summary)
