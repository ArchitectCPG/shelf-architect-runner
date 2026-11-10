#!/usr/bin/env python3
"""Stage-2 hygiene for Vosges bars/gifting/brand (Fable, 2026-11-06). Reads mapped/vosges_s2/capped, writes mapped/vosges_s2/{new,update,held,excluded}.json + hygiene_summary.json. No DB writes."""
import json,glob,os,re,collections,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import hygiene
C=json.load(open('clients/vosges.json')); H=hygiene.load(C)   # patterns live in clients/vosges.json (hygiene, retailers[].matrix_suffix), engine in tools/hygiene.py
md='mapped/vosges_s2'
rows={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(md+'/capped/*.json')}
landed=json.load(open('mapped/vosges/landed_final_summary.json'))['ids']
held_prev=set(json.load(open('mapped/vosges/held_wholefoods_pseudobrand.json')))
skipped_prev=set(json.load(open('mapped/vosges/skipped_dupes.json')))
# landed row contents (blocks/neighborhoods) from landed batches
L={}
for f in sorted(glob.glob('mapped/vosges/landing/batch_0[0-2].json'))+sorted(glob.glob('mapped/vosges/landing2/batch_*.json')):
    for op in (lambda j: j if isinstance(j,list) else j.get("ops",[]))(json.load(open(f))):
        if op.get('op')=='set': L[op['path'].split('/')[-1]]=op['data']
L={k:v for k,v in L.items() if k in set(landed)}
def fixbrand(b): return hygiene.canon_brand(H,b)

# canonical block strings (matrix convention candy-chocolate/<nb>@<retailer>-<market>), same as the pouch landing used
def canon_block(b): return hygiene.canon_block(H,b)
new,upd,held,excl,skip=[],[],[],[],[]
why=collections.Counter()
for k,r in rows.items():
    r=dict(r); r['brand']=fixbrand(r['brand']); r['is_private_label']=hygiene.is_private_label(H,r['brand']) or r['is_private_label']; r['block']=canon_block(r['block']); r['blocks']=sorted(set(canon_block(b) for b in r['blocks']))
    nb=r['neighborhood']
    if k in held_prev: held.append((k,'held previously, Whole Foods pseudo-brand')); why['held prev']+=1; continue
    if k in skipped_prev: skip.append((k,'skipped previously as dupe')); why['skip prev']+=1; continue
    if (H.exclude and H.exclude.search(r['brand'])): excl.append((k,r['brand'],r['product_name'])); why['excluded brand']+=1; continue
    wf=r['retailer'].lower().startswith('whole')
    if (H.fragment and H.fragment.match(r['brand'])) or r['brand']=='Unbranded':
        held.append((k,'brand is a product fragment or Unbranded: '+r['brand']+' | '+r['product_name'])); why['held fragment']+=1; continue
    if k in L:
        old=L[k]; nbs=sorted(set(old.get('neighborhoods') or [old['neighborhood']])|set(r['neighborhoods'])); bls=sorted(set(old.get('blocks') or [old['block']])|set(r['blocks']))
        if nbs!=sorted(set(old.get('neighborhoods') or [old['neighborhood']])) or bls!=sorted(set(old.get('blocks') or [old['block']])):
            upd.append((k,{'neighborhoods':nbs,'blocks':bls})); why['update landed (add block)']+=1
        else: why['landed, unchanged']+=1
        continue
    if nb=='chocolate-bites-pouch' and wf: new.append((k,r)); why['new pouch (Whole Foods realigned, replaces misaligned rows)']+=1; continue
    if nb=='chocolate-bites-pouch': skip.append((k,'pouch row not landed before, new relevance; hold for pouch top-up')); why['pouch not landed, hold']+=1; continue
    new.append((k,r)); why['new '+nb]+=1
json.dump(dict(new),open(md+'/new.json','w'),indent=1); json.dump(dict(upd),open(md+'/update.json','w'),indent=1)
json.dump(held,open(md+'/held.json','w'),indent=1); json.dump(excl,open(md+'/excluded.json','w'),indent=1); json.dump(skip,open(md+'/skipped.json','w'),indent=1)
dele=[k for k in landed if k.startswith('wholefoods') and k not in rows]; json.dump(dele,open(md+'/delete.json','w'),indent=1); why['delete landed WF misaligned']=len(dele)
json.dump(dict(why),open(md+'/hygiene_summary.json','w'),indent=1); print(dict(why))
