#!/usr/bin/env python3
"""Generate runner blocks for one client from clients/<id>.json. Usage: gen_client_blocks.py stinkin-good
Writes blocks_gen/<client>/<banner>__<neighborhood>.json and prints the dispatch list."""
import json,sys,os,re,glob
cid=sys.argv[1]; C=json.load(open(f'clients/{cid}.json')); out=f'blocks_gen/{cid}'; os.makedirs(out,exist_ok=True)
for f in glob.glob(out+'/*.json'): os.remove(f)
ic_js=open('src/instacart_api.js').read()
def load(name): return json.load(open(f'blocks/{name}-salsa.json'))
made=[]
for r in C['retailers']:
    if r.get('fallback'): continue  # plan-B lane kept in config, not generated
    m=C['markets'][r['market']]
    for n in C['neighborhoods']:
        if n.get('brand_only') and not r.get('brand_check'): continue
        term=n['term']; bid=f"{cid}/{n['id']}@{r['banner']}-{r['market']}"
        base={"block_id":bid,"retailer":r['banner'],"zip":C['department'],"neighborhood":n['id'],"term":term,"store_zip":m['zip'],"client_id":cid}
        if r['lane']=='kroger':
            t=load('kroger'); s=json.dumps(t['steps']).replace('www.kroger.com',r['host']); base['steps']=json.loads(s); base['store_js']=t['store_js']
        elif r['lane']=='instacart':
            url=r.get('url') or f"https://www.instacart.com/store/{r['slug']}/s?k={{{{term}}}}"
            pre=f"const SLUG='{r['slug']}',ZIP='{m['zip']}',LAT={m['lat']},LNG={m['lng']},TERM='{term}';\n"+(f"const COLLECTION='{r['collections'][n['id']]}';\n" if r.get('collections',{}).get(n['id']) else '')
            base['store_js']="(()=>null)()"; base['steps']=[{"goto":url},{"wait":10000},{"dismiss":["Close","No thanks","Not now","Continue","Got it"]},{"js_houses":pre+ic_js,"optional":True},{"wait":1000}]
        elif r['lane']=='kroger_api':
            base['kroger_api']={"chain":r['chain'],"max":150}
        elif r['lane']=='api':
            t=load(r['template']); base['api']=json.loads(json.dumps(t['api']))
        elif r['lane']=='recipe':
            t=load(r['template']); base['steps']=t['steps']; base['store_js']=t.get('store_js'); 
            for k in ('card_selector','store_patterns','no_reload','attempts','store_expect'):
                if k in t: base[k]=t[k]
            if not base.get('store_js'): base.pop('store_js')
        if 'steps' in base and 'attempts' not in base: base['attempts']=2
        fn=f"{out}/{r['banner']}__{n['id']}__{r['market']}.json"; json.dump(base,open(fn,'w'),indent=1); made.append(fn)
print(','.join(made)); print(len(made),'retail blocks',file=sys.stderr)

# ---- Amazon lane: separate from retail, gated on temperature state ----
# Blocks go to blocks_gen/<cid>/amazon/ and results to data/amazon/, so client_report, mapper and landing
# never see them. Runs only when the client product is shelf-stable (client-level amazon.temperature),
# and per neighborhood only when that neighborhood is shelf-stable too (neighborhood.temperature overrides).
A=C.get('amazon') or {}; aout=f'{out}/amazon'; os.makedirs(aout,exist_ok=True)
for f in glob.glob(aout+'/*'): os.remove(f)
amade=[]
if A.get('enabled'):
    ctemp=A.get('temperature','unknown')
    if ctemp!='shelf_stable':
        msg=f"amazon lane SKIPPED: client product temperature is '{ctemp}' (Amazon lane needs shelf_stable)"
        open(aout+'/SKIPPED.txt','w').write(msg+'\n'); print(msg,file=sys.stderr)
    else:
        for n in C['neighborhoods']:
            if n.get('brand_only') and not A.get('brand_check',True): continue
            ntemp=n.get('temperature',ctemp)
            if ntemp!='shelf_stable': print(f"amazon: skip {n['id']} ({ntemp})",file=sys.stderr); continue
            term=n.get('amazon_term') or n['term']
            b={"block_id":f"{cid}/{n['id']}@amazon","retailer":"amazon","zip":"amazon","neighborhood":n['id'],"term":term,
               "store_zip":A.get('zip',''),"client_id":cid,"temperature":ntemp,
               "api":{"amazon":True,"dataset_id":"gd_l7q7dkf244hwjntr0","discover_by":"keyword",
                      "input":{"keyword":"{{term}}","zipcode":"{{store_zip}}"},"limit":int(A.get('limit',48))}}
            fn=f"{aout}/amazon__{n['id']}.json"; json.dump(b,open(fn,'w'),indent=1); amade.append(fn)
            # SOP v82 rule 17 step 3: two or three shopper-typed terms per product line. Extra terms keep the same
            # neighborhood (same relevance filter) but get their own block id and output folder.
            for et in n.get('amazon_extra_terms') or []:
                slug=re.sub(r'[^a-z0-9]+','-',et.lower()).strip('-'); nid=f"{n['id']}--{slug}"
                eb=json.loads(json.dumps(b)); eb['block_id']=f"{cid}/{nid}@amazon"; eb['term']=et
                fn=f"{aout}/amazon__{nid}.json"; json.dump(eb,open(fn,'w'),indent=1); amade.append(fn)
if amade: print('AMAZON:'+','.join(amade)); print(len(amade),'amazon blocks',file=sys.stderr)
