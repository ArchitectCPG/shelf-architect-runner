#!/usr/bin/env python3
"""Build Vosges stage-2 landing batches + pull_matrix block stamps from mapped/vosges_s2 hygiene output. Files only."""
import json,os,glob,collections,re
md='mapped/vosges_s2'; out=md+'/landing'; os.makedirs(out,exist_ok=True)
for f in glob.glob(out+'/*.json'): os.remove(f)
new=json.load(open(md+'/new.json')); upd=json.load(open(md+'/update.json')); dele=json.load(open(md+'/delete.json'))
ops=[{'op':'delete','path':f'retail_entries/{k}','ifVersion':1} for k in dele]
ops+=[{'op':'update','path':f'retail_entries/{k}','ifVersion':1,'data':d} for k,d in upd.items()]
ops+=[{'op':'set','path':f'retail_entries/{k}','data':r} for k,r in new.items()]
B=20; n=0
for i in range(0,len(ops),B): json.dump(ops[i:i+B],open(f'{out}/batch_{n:02d}.json','w')); n+=1
blocks=json.load(open('mapped/vosges/pull_matrix_blocks_writeback.json'))
RAW={'albertsons-boise':'albertsons','bristol-farms-socal':'bristol-farms','central-market-houston':'central-market','costco-chicago':'costco-online','erewhon-socal':'erewhon','fresh-thyme-market-chicago':'freshthyme','gelsons-socal':'gelsons','heb-houston':'heb','jewel-osco-chicago':'jewel-osco','king-soopers-denver':'kingsoopers-api','marianos-chicago':'marianos-api','meijer-chicago':'meijer','natural-grocers-vitamin-cottage-denver':'naturalgrocers','plum-market-chicago':'plum-market','ralphs-socal':'ralphs-api','safeway-denver':'safeway','sprouts-socal':'sprouts','target-chicago':'target','the-fresh-market-chicago':'thefreshmarket','walmart-chicago':'walmart','wegmans-nyc':'wegmans','whole-foods-chicago':'wholefoods','whole-foods-socal':'wholefoods-socal','woodmans-madison':'woodmans'}
houses={}
for f in glob.glob('data/*/vosges_*/2026-11-06*.json'):
    if f.endswith('-error.json'): continue
    houses[f.split('/')[2][7:]]=len(json.load(open(f)).get('houses') or [])
cnt=collections.Counter(b for r in new.values() for b in r['blocks'])
for d in upd.values():
    for b in d['blocks']: cnt[b]+=1
stamped=[];weak=[]
for b in blocks:
    if b['neighborhood']=='chocolate-bites-pouch': continue
    nb,rm=b['block'].split('/')[1].split('@'); banner=RAW[rm]; mk=rm.rsplit('-',1)[1]
    h=houses.get(f'{nb}@{banner}-{mk}')
    if h is None: b['last_result']='no pull file for this term'; weak.append((b['block'],'no file')); continue
    b['last_walked']='2026-11-06'; rows=cnt.get(b['block'],0)
    if h==0: b['last_result']='walked: 0 houses, retry or attended walk'; weak.append((b['block'],0))
    elif h<5: b['last_result']=f'walked: {h} houses, thin, retry'; weak.append((b['block'],h))
    else: b['last_result']=f'walked: {h} houses, {rows} rows on the block after relevance and cap'
    stamped.append(b['block'])
json.dump(blocks,open(md+'/pull_matrix_blocks_writeback.json','w'),indent=1)
summ=dict(delete=len(dele),update=len(upd),new=len(new),new_by_nb=collections.Counter(r['neighborhood'] for r in new.values()),batches=n,
          blocks_stamped=len(stamped),weak_blocks=weak,per_block=dict(sorted(cnt.items())),ids_new=sorted(new),ids_update=sorted(upd),ids_delete=dele)
json.dump(summ,open(md+'/landing_summary.json','w'),indent=1)
print({k:v for k,v in summ.items() if k not in('ids_new','ids_update','ids_delete','per_block')})
