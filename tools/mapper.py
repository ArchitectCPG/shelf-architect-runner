#!/usr/bin/env python3
"""Map runner pulls to Shelf Architect retail_entries row JSONs (files only; no DB writes).
Usage: mapper.py <client_id> [outdir]. Writes <outdir>/retail_entries/<id>.json, matrix_blocks.json, summary.json."""
import json,sys,os,re,glob,datetime
sys.path.insert(0,os.path.dirname(__file__)); from normalize import normalize,num
cid=sys.argv[1]; out=sys.argv[2] if len(sys.argv)>2 else f'mapped/{cid}'
C=json.load(open(f'clients/{cid}.json')); os.makedirs(out+'/retail_entries',exist_ok=True)
PL=re.compile(r"^(kroger|simple truth|private selection|signature (select|care|farms)|o organics|great value|good & gather|market pantry|up & up|sprouts|365|wegmans|publix|h-?e-?b|mi tienda|meijer|true goodness|safeway|lucky|trader|kirkland|member'?s mark|giant|stop & shop|food lion|hannaford|harris teeter|whole foods)\b",re.I)
DOLLAR={'dollargeneral','dollartree','familydollar','popshelf'}
def slug(s): return re.sub(r'-+','-',re.sub(r"[^a-z0-9]+","-",re.sub(r"['’]","",(s or '').lower()))).strip('-')
def parse_size(txt):
    t=(txt or '')
    m=re.search(r'(\d+(?:\.\d+)?)\s?(fl\.?\s?oz|oz|ounce|lbs?|pounds?|g|grams?|ml|l)\b',t,re.I)
    oz=None;unit=None
    if m:
        v=float(m.group(1)); u=m.group(2).lower().replace(' ','').replace('.','')
        if u in('oz','ounce','floz'): oz=v
        elif u.startswith('lb') or u.startswith('pound'): oz=v*16
        elif u in('g','gram','grams'): oz=round(v/28.3495,2)
        elif u=='ml': oz=round(v/29.5735,2)
        elif u=='l': oz=round(v*33.814,2)
    c=re.search(r'(\d+)\s?[-]?\s?(ct|count|pk|pack)\b',t,re.I)
    return oz,(int(c.group(1)) if c else None)
def size_slug(oz,ct):
    if oz: s=('%g'%round(oz,2)).replace('.','-')+'oz'
    elif ct: s=f'{ct}ct'
    else: s='na'
    return s
def clean_name(name,brand_label):
    n=re.sub(r'[®™]','',name or '').strip()
    n=re.sub(r',?\s*\d+(\.\d+)?\s?(fl\.?\s?oz|oz|lb|lbs|ct|count|g|ml)\b.*$','',n,flags=re.I).strip(' ,-')
    if brand_label and n.lower().startswith(brand_label.lower()+' '): n=n[len(brand_label)+1:]
    return n or name
today=datetime.date.today().isoformat()
rows={}; blocks_out=[]; stats={'blocks':0,'houses_in':0,'rows':0,'dropped_irrelevant':0}
def latest(b):
    bid=re.sub(r'[^a-z0-9@_.-]','_',b['block_id'],flags=re.I)
    fs=sorted(x for x in glob.glob(f"data/{b['retailer']}/{bid}/*.json") if not x.endswith('-error.json'))
    return json.load(open(fs[-1])) if fs else None
JUNK=re.compile(r'^(price per|unbranded|sale|new|hatch \(brand\)|\(brand\)|sponsored|add|\$.*|.*\(brand\))$',re.I)
from collections import Counter as _C
_cnt=_C()
for _f in glob.glob(f'blocks_gen/{cid}/*.json'):
    _b=json.load(open(_f)); _d=latest(_b) if False else None
def _build_lex():
    cnt=_C()
    for f in glob.glob(f'blocks_gen/{cid}/*.json'):
        b=json.load(open(f)); bid=re.sub(r'[^a-z0-9@_.-]','_',b['block_id'],flags=re.I)
        fs=sorted(x for x in glob.glob(f"data/{b['retailer']}/{bid}/*.json") if not x.endswith('-error.json'))
        if not fs: continue
        for h in json.load(open(fs[-1])).get('houses',[]):
            br=(h.get('brand') or '').strip()
            if br and not JUNK.match(br) and len(br)>2: cnt[br]+=1
    return sorted([b for b,c in cnt.items() if c>=1],key=lambda t:-len(t))
LEX=_build_lex()
import os
_seed=os.environ.get('BRAND_SEED_DIR')
if _seed:
    _sb=set()
    for _f in glob.glob(_seed+'/**/*.json',recursive=True):
        _j=json.load(open(_f)); _j=_j.get('data',_j); _b=(_j.get('brand') or '').strip()
        if _b and not JUNK.match(_b) and len(_b)>2 and '(' not in _b: _sb.add(_b)
    LEX=sorted(set(LEX)|_sb,key=lambda t:-len(t))
STOP=re.compile(r'^(queso|salsa|green|red|chile|chili|chiles|chilies|tamales?|dip|cheese|sauce|hot|mild|medium|organic|fresh|diced|roasted|flame|fire|original|classic|tortilla|enchilada|pork|beef|chicken|vegan|vegetarian|premium|authentic|restaurant|spicy|con|blanco|verde|jalapeno|white|yellow|creamy|chunky|mexican|southwest(ern)?|hatch|new)$',re.I)
def fix_brand(brand,nm):
    if brand and not JUNK.match(brand): return brand
    low=nm.lower()
    for b in LEX:
        if low.startswith(b.lower()+' ') or low.startswith(b.lower()+"'"): return b
    for b in LEX:
        if len(b)>4 and re.search(r'\b'+re.escape(b.lower())+r'\b',low): return b
    w=nm.split()
    out=[]
    for t in w:
        if STOP.match(t.strip(',')) or not t[:1].isalpha(): break
        out.append(t)
        if len(out)==3: break
    if out and 1<=len(out)<=3 and len(' '.join(out))>2 and not re.match(r'^(the|a|an)$',out[0],re.I): return ' '.join(out)
    return None
for f in sorted(glob.glob(f'blocks_gen/{cid}/*.json')):
    b=json.load(open(f)); d=latest(b); nb=next(n for n in C['neighborhoods'] if n['id']==b['neighborhood'])
    stats['blocks']+=1
    if not d: blocks_out.append(dict(block=b['block_id'],last_result='no data')); continue
    banner=b['retailer']; ic=banner=='costco-ic' or (d.get('store_set') or '').startswith('API zip') and 'shop' in (d.get('store_set') or '')
    price_basis='instacart_quote' if ('shop ' in str(d.get('store_set')) and 'location' in str(d.get('store_set'))) else 'shelf'
    retailer_slug='costco' if banner=='costco-ic' else banner
    kept=0; brands=set()
    for h in d.get('houses',[]):
        stats['houses_in']+=1
        x=normalize(h,C,nb)
        nm=(x.get('name') or '')
        is_own=any(re.search(t,nm+' '+(x.get('brand') or ''),re.I) for t in C['brand_terms']) and not (C.get('brand_exclude') and re.search(C['brand_exclude'],nm,re.I))
        if not x['relevant'] and not is_own: stats['dropped_irrelevant']+=1; continue
        if C.get('brand_exclude') and re.search(C['brand_exclude'],nm,re.I) and not is_own and x['brand_norm'] and re.search(C['brand_terms'][0],x['brand_norm'],re.I): continue
        brand=fix_brand(x['brand_norm'],nm) or 'Unbranded'; oz,ct=parse_size((h.get('size') or '')+' '+nm+' '+' '.join(h.get('card_text') or []))
        pname=clean_name(nm,brand)
        rid=f"{retailer_slug}_{slug(brand)}_{slug(pname)}_{size_slug(oz,ct)}"
        reg=x['price_regular']; pro=x['price_promo']
        block=f"{b['zip']}/{b['neighborhood']}@{banner}"
        r=rows.get(rid)
        if r is None:
            r=dict(brand=brand,product_name=pname,retailer=retailer_slug,client_id=cid,is_own_brand=is_own,
              is_private_label=bool(PL.match(brand)) and not is_own,source_type='scrape',price=(pro or reg),
              price_regular=reg,price_basis=price_basis,size_oz=oz,count=ct,
              price_per_oz=(round((pro or reg)/oz,4) if oz and (pro or reg) else None),
              price_history=[{'date':today,'price':(pro or reg)}],last_pulled=today,pulled_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              region=str(d.get('store_set') or ''),route='runner-'+('instacart' if price_basis=='instacart_quote' else 'api' if str(d.get('store_set','')).startswith('API') else 'recipe'),
              block=block,zip=b['zip'],neighborhood=b['neighborhood'],neighborhoods=[b['neighborhood']],blocks=[block],
              pull_url=h.get('link') or d.get('url_final'),notes=f"Runner pull {today}, lane {b.get('retailer')}, store: {d.get('store_set')}."+(" Instacart quote, carries marketplace markup; pricing intel, not shelf price." if price_basis=='instacart_quote' else ''),
              channel=None,category=C.get('department'))
            if pro: r['sale_price']=pro
            if banner in DOLLAR: r['pricing_cohort']='dollar'
            rows[rid]=r
        else:
            if b['neighborhood'] not in r['neighborhoods']: r['neighborhoods'].append(b['neighborhood'])
            if block not in r['blocks']: r['blocks'].append(block)
        kept+=1; brands.add(brand)
    blocks_out.append(dict(block=b['block_id'],last_walked=today,last_result=f"walked: {kept} houses across {len(brands)} brands",store=d.get('store_set'),error=d.get('error')))
for rid,r in rows.items(): json.dump(r,open(f'{out}/retail_entries/{rid}.json','w'),indent=1)
stats['rows']=len(rows)
json.dump(blocks_out,open(out+'/matrix_blocks.json','w'),indent=1); json.dump(stats,open(out+'/summary.json','w'),indent=1)
print(json.dumps(stats))
