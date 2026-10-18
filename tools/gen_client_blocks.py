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
        elif r['lane']=='api':
            t=load(r['template']); base['api']=json.loads(json.dumps(t['api']))
        elif r['lane']=='recipe':
            t=load(r['template']); base['steps']=t['steps']; base['store_js']=t.get('store_js'); 
            for k in ('card_selector','store_patterns','no_reload','attempts','store_expect'):
                if k in t: base[k]=t[k]
            if not base.get('store_js'): base.pop('store_js')
        if 'steps' in base and 'attempts' not in base: base['attempts']=2
        fn=f"{out}/{r['banner']}__{n['id']}__{r['market']}.json"; json.dump(base,open(fn,'w'),indent=1); made.append(fn)
print(','.join(made)); print(len(made),'blocks',file=sys.stderr)
