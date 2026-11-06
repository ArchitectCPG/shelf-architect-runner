#!/usr/bin/env python3
"""Stage-2 hygiene for Vosges bars/gifting/brand (Fable, 2026-11-06). Reads mapped/vosges_s2/capped, writes mapped/vosges_s2/{new,update,held,excluded}.json + hygiene_summary.json. No DB writes."""
import json,glob,os,re,collections
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
CANON={"hershey's":"Hershey's","hershey'S":"Hershey's","cadbury":"Cadbury","mounds":"Mounds","russell stover":"Russell Stover","elements truffles":"Elements Truffles","milkboy":"Milkboy","beyond good":"Beyond Good","central market":"Central Market","alden’s organic":"Alden's Organic","nelly's organics":"Nelly's Organics","see's candies":"See's Candies","see’s candies":"See's Candies","bissinger's":"Bissinger's","terry's":"Terry's","m&m's":"M&M's","kit kat":"Kit Kat","rolo":"Rolo","signature reserve sea":"Signature Reserve","mid-day squares":"Mid-Day Squares","honey mama's":"Honey Mama's","kate's real food":"Kate's Real Food","jeni's ice creams":"Jeni's Ice Creams","toffifay":"Toffifay"}
EXCL_BRAND=re.compile(r"^(gomacro|barnana|kind|clif bar|clif|rxbar|nassau candy|the gfb|mosh|sabatino tartufi|pocky|snack factory|woodstock|mitica|gato dates|sweet jubilee|harry & david|wonderful|mauna loa|walkers|bahlsen|bonne maman|olyra|sillycow|teeccino|republic of tea|quest|barebells)\b",re.I)
FRAG=re.compile(r"^(sea salt dark|orange|bonbon|chocolate covered figs|dark chocolate|milk chocolate|chocolate|unbranded)$",re.I)
def fixbrand(b):
    b=re.sub(r'[®™]','',b or '').strip().rstrip(',').strip()
    k=b.lower()
    if k in CANON: return CANON[k]
    b=re.sub(r"'S\b","'s",b); b=re.sub(r"’S\b","'s",b).replace('’',"'")
    if b.islower(): b=b.title()
    return b

# canonical block strings (matrix convention candy-chocolate/<nb>@<retailer>-<market>), same as the pouch landing used
CANON_RET={'albertsons':'albertsons-boise','bristol-farms':'bristol-farms-socal','central-market':'central-market-houston','costco-online':'costco-chicago','erewhon':'erewhon-socal','freshthyme':'fresh-thyme-market-chicago','gelsons':'gelsons-socal','heb':'heb-houston','jewel-osco':'jewel-osco-chicago','kingsoopers':'king-soopers-denver','marianos':'marianos-chicago','meijer':'meijer-chicago','naturalgrocers':'natural-grocers-vitamin-cottage-denver','plum-market':'plum-market-chicago','ralphs':'ralphs-socal','safeway':'safeway-denver','sprouts':'sprouts-socal','target':'target-chicago','thefreshmarket':'the-fresh-market-chicago','walmart':'walmart-chicago','wegmans':'wegmans-nyc','wholefoods':'whole-foods-chicago','wholefoods-socal':'whole-foods-socal','woodmans':'woodmans-madison'}
def canon_block(b):
    head,suf=b.split('@'); suf=suf.replace('-api','')
    if suf in CANON_RET.values(): return b
    return head+'@'+CANON_RET[suf]
new,upd,held,excl,skip=[],[],[],[],[]
why=collections.Counter()
for k,r in rows.items():
    r=dict(r); r['brand']=fixbrand(r['brand']); r['block']=canon_block(r['block']); r['blocks']=sorted(set(canon_block(b) for b in r['blocks']))
    nb=r['neighborhood']
    if k in held_prev: held.append((k,'held previously, Whole Foods pseudo-brand')); why['held prev']+=1; continue
    if k in skipped_prev: skip.append((k,'skipped previously as dupe')); why['skip prev']+=1; continue
    if EXCL_BRAND.search(r['brand']): excl.append((k,r['brand'],r['product_name'])); why['excluded brand']+=1; continue
    wf=r['retailer'].lower().startswith('whole')
    if FRAG.match(r['brand']) or r['brand']=='Unbranded':
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
