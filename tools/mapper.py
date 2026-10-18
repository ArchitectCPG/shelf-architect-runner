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

ELL=re.compile(r'\.\.\.|\u2026')
def _an(t): return re.sub(r'[^a-z0-9]','',(t or '').lower())
def _strip_size(t): return re.sub(r',?\s*[-,]?\s*\d+(\.\d+)?\s?(fl\.?\s?oz|oz|lb|lbs|ct|count|g|ml)\b.*$','',t or '',flags=re.I).strip(' ,-')
def slug_name(url):
    m=re.search(r'/shop/pd/([a-z0-9-]+?)/\d+',url or '')
    return ' '.join(w.capitalize() if not w.isdigit() else w for w in m.group(1).split('-')) if m else None
def repair_name(nm,brand,url,known):
    """Return (name, status). status: ok | slug | known | truncated."""
    if not ELL.search(nm or ''): return nm,'ok'
    head,_,tail=ELL.split(nm,1)[0],None,ELL.split(nm,1)[1]
    hn,tn=_an(head),_an(_strip_size(tail))
    sl=slug_name(url)
    if sl:
        sn=_an(sl)
        if not tn or tn in sn: return sl,'slug'
    cands={k for k in known if len(_an(k))>len(hn)+len(tn) and (_an(k).startswith(hn) or _an(brand+k).startswith(hn)) and (not tn or _an(k).endswith(tn))}
    # tolerate brand-prefixed known names: compare with brand label stripped
    if len(cands)==1: return next(iter(cands)),'known'
    return nm,'truncated'
today=datetime.date.today().isoformat()

# ---- storage class (maps to the DB `format` field: Frozen / Refrigerated / Shelf-stable) ----
KR_FROZEN={'frozen'}
KR_REFRIG={'deli','dairy','meat & seafood','refrigerated','bakery','produce'}
KR_SHELF={'canned & packaged','snacks','candy','baking goods','condiments, spices & bake','pasta, sauces, grain','beverages','breakfast','cereal','soups'}
RX_FROZEN=re.compile(r'\bfrozen\b|\bfreezer\b|\bflash[- ]frozen\b',re.I)
RX_SHELF=re.compile(r'shelf[- ]?stable|\bcanned\b|\bcan\b|\bjar\b|tortilla chips?|\bchips\b|\bcandy\b|\bchewy\b|enchilada sauce|\bhot sauce\b|\bdiced (fire[- ]roasted )?green chiles?\b|\bchopped green chile\b',re.I)
RX_REFRIG=re.compile(r'refrigerated|\bchilled\b|\bfresh\b|\bdeli\b',re.I)
RX_SHELF_X=re.compile(r'shelf[- ]?stable',re.I)
def storage_class(h,nm,kapi):
    """returns (format, source) or (None,None). Never guesses: ambiguous -> None."""
    cats=[c.lower() for c in (h.get('categories') or [])] if kapi else []
    if cats:
        if any(c in KR_FROZEN for c in cats): return 'Frozen','kroger-category'
        if any(c in KR_REFRIG for c in cats): return 'Refrigerated','kroger-category'
        if any(c in KR_SHELF for c in cats): return 'Shelf-stable','kroger-category'
    ct=' '.join(x for x in (h.get('card_text') or []) if '$' not in x)
    t=(nm or '')+' '+(h.get('name') or '')
    if RX_FROZEN.search(t) or RX_FROZEN.search(ct): return 'Frozen','name'
    if RX_SHELF.search(t) or RX_SHELF_X.search(ct): return 'Shelf-stable','name'
    if RX_REFRIG.search(t) or RX_REFRIG.search(ct): return 'Refrigerated','name'
    return None,None

rows={}; blocks_out=[]; stats={'blocks':0,'houses_in':0,'rows':0,'dropped_irrelevant':0}
def latest(b):
    bid=re.sub(r'[^a-z0-9@_.-]','_',b['block_id'],flags=re.I)
    fs=sorted(x for x in glob.glob(f"data/{b['retailer']}/{bid}/*.json") if not x.endswith('-error.json'))
    for fp in reversed(fs):
        j=json.load(open(fp))
        if j.get('houses'): j['_file']=fp; return j
    return None
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
RET={'kingsoopers':('King Soopers','king-soopers'),'citymarket':('City Market','city-market'),'safeway':('Safeway','safeway'),'heb':('H-E-B','heb'),'walmart':('Walmart','walmart'),'target':('Target','target'),'sprouts':('Sprouts Farmers Market','sprouts'),'wholefoods':('Whole Foods Market','wholefoods'),'costco':('Costco','costco'),'albertsons':('Albertsons','albertsons'),'jewel-osco':('Jewel-Osco','jewel-osco'),'costco-online':('Costco','costco')}
KNOWN_NAMES=set()
_sd=os.environ.get('BRAND_SEED_DIR')
if _sd:
    for _f in glob.glob(_sd+'/*.json'):
        try:
            _o=json.load(open(_f)); _o=_o.get('data',_o)
            if _o.get('client_id')==cid and _o.get('product_name') and not ELL.search(_o['product_name']):
                KNOWN_NAMES.add(clean_name(_o['product_name'],_o.get('brand')))
        except Exception: pass
for _f in glob.glob(f'blocks_gen/{cid}/*.json'):
    try:
        _d=latest(json.load(open(_f)))
        for _h in (_d or {}).get('houses',[]):
            if _h.get('name') and not ELL.search(_h['name']): KNOWN_NAMES.add(_strip_size(_h['name']))
    except Exception: pass
os.makedirs(out+'/held',exist_ok=True); held={}
for f in sorted(glob.glob(f'blocks_gen/{cid}/*.json')):
    b=json.load(open(f)); d=latest(b); nb=next(n for n in C['neighborhoods'] if n['id']==b['neighborhood'])
    stats['blocks']+=1
    if not d: blocks_out.append(dict(block=b['block_id'],last_result='no data')); continue
    banner=b['retailer'].replace('-api',''); kapi=(d.get('runner') or '').endswith('kroger-api'); ic=banner=='costco-ic' or (d.get('store_set') or '').startswith('API zip') and 'shop' in (d.get('store_set') or '')
    price_basis='instacart_quote' if ('shop ' in str(d.get('store_set')) and 'location' in str(d.get('store_set'))) else 'shelf'
    retailer_slug='costco' if banner=='costco-ic' else banner
    kept=0; brands=set()
    for h in d.get('houses',[]):
        stats['houses_in']+=1
        if h.get('via')=='text' and h.get('card_text'):
            _n=re.sub(r'[^a-z0-9]','',(h.get('name') or '').lower())
            if not any(_n and _n in re.sub(r'[^a-z0-9]','',t.lower()) for t in h['card_text']): stats['dropped_misattributed']=stats.get('dropped_misattributed',0)+1; continue
        x=normalize(h,C,nb)
        nm=(x.get('name') or '')
        is_own=any(re.search(t,nm+' '+(x.get('brand') or ''),re.I) for t in C['brand_terms']) and not (C.get('brand_exclude') and re.search(C['brand_exclude'],nm,re.I))
        if not x['relevant'] and not is_own: stats['dropped_irrelevant']+=1; continue
        if C.get('brand_exclude') and re.search(C['brand_exclude'],nm,re.I) and not is_own and x['brand_norm'] and re.search(C['brand_terms'][0],x['brand_norm'],re.I): continue
        brand=fix_brand(x['brand_norm'],nm) or 'Unbranded'; oz,ct=parse_size((h.get('size') or '')+' '+nm+' '+' '.join(t for t in (h.get('card_text') or []) if '$' not in t and 'discounted' not in t))
        size_src='label'
        if not oz and not ct:
            ct_txt=' '.join(h.get('card_text') or [])
            um=re.search(r'\$(\d+(?:\.\d+)?)\s*/\s*(fl\.? ?oz|oz|lb|ct|count)\b',ct_txt,re.I)
            if um:
                unit=float(um.group(1)); u=um.group(2).lower()
                best=None
                for p_ in {v for v in (x['price_promo'],x['price_regular']) if v}:
                    q=p_/unit; q=q*16 if u=='lb' else q
                    err=abs(q*2-round(q*2))
                    if best is None or err<best[0]: best=(err,q)
                if best and best[0]<0.12:
                    if u in('ct','count'): ct=int(round(best[1]))
                    else: oz=round(best[1]*2)/2
                    size_src='derived_unit_price'
        nm,_nst=repair_name(nm,brand,h.get('link') or d.get('url_final'),KNOWN_NAMES)
        pname=clean_name(nm,brand)
        disp,idp=RET.get(retailer_slug,(retailer_slug,retailer_slug)); rid=f"{idp}_{slug(brand)}_{slug(pname)}_{size_slug(oz,ct)}"
        reg=x['price_regular']; pro=x['price_promo']
        block=f"{b['zip']}/{b['neighborhood']}@{banner}"
        r=rows.get(rid)
        if r is None:
            r=dict(brand=brand,product_name=pname,retailer=disp,client_id=cid,is_own_brand=is_own,
              is_private_label=bool(PL.match(brand)) and not is_own,source_type='scrape',price=(pro or reg),
              price_regular=reg,price_basis=price_basis,size_oz=oz,size_source=size_src,count=ct,
              price_per_oz=(round((pro or reg)/oz,4) if oz and (pro or reg) else None),
              price_history=[{'date':today,'price':(pro or reg)}],last_pulled=today,pulled_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              region=str(d.get('store_set') or ''),route='runner-'+('kroger-api' if kapi else 'instacart' if price_basis=='instacart_quote' else 'api' if str(d.get('store_set','')).startswith('API') else 'recipe'),upc=h.get('upc'),
              block=block,zip=b['zip'],neighborhood=b['neighborhood'],neighborhoods=[b['neighborhood']],blocks=[block],
              pull_url=h.get('link') or d.get('url_final'),notes=f"Runner pull {today}, lane {b.get('retailer')}, store: {d.get('store_set')}."+(" Instacart quote, carries marketplace markup; pricing intel, not shelf price." if price_basis=='instacart_quote' else ''),
              category=C.get('department'))
            if pro: r['sale_price']=pro
            _f,_fs=storage_class(h,nm,kapi)
            if _f: r['format']=_f; r['format_source']=_fs
            if banner in DOLLAR: r['pricing_cohort']='dollar'
            if _nst=='truncated': r['name_truncated']=True; r['hold_reason']='name truncated, needs full title'
            elif _nst!='ok': r['name_repaired']=_nst
            rows[rid]=r
            if not oz and not ct and not r.get('hold_reason'): r['hold_reason']='no size parsed'
        else:
            if b['neighborhood'] not in r['neighborhoods']: r['neighborhoods'].append(b['neighborhood'])
            if block not in r['blocks']: r['blocks'].append(block)
        kept+=1; brands.add(brand)
    blocks_out.append(dict(block=b['block_id'],last_walked=today,last_result=f"walked: {kept} houses across {len(brands)} brands",store=d.get('store_set'),error=d.get('error')))

# ---- propagate storage class across retailers for the same brand+product (only from authoritative or curated sources) ----
def pkey(r):
    n=re.sub(r'\b(\d+(\.\d+)?\s*(oz|ct|lb)|pack|of|count|the|and|with|style|medium|mild|hot|original|flavor)\b','',(r.get('product_name') or '').lower())
    return slug(r.get('brand'))+'|'+re.sub(r'[^a-z]','',n)[:24]
KNOWN={}
for rid,r in rows.items():
    if r.get('format') and r.get('format_source')=='kroger-category': KNOWN.setdefault(pkey(r),r['format'])
_seed=os.environ.get('BRAND_SEED_DIR')
if _seed:
    for f in glob.glob(_seed+'/*.json'):
        o=json.load(open(f)); o=o.get('data',o)
        if o.get('format') and o.get('client_id')==cid: KNOWN.setdefault(pkey(o),re.sub(r'(?i)shelf-stable','Shelf-stable',o['format']))
nprop=0
for rid,r in rows.items():
    if not r.get('format') and pkey(r) in KNOWN: r['format']=KNOWN[pkey(r)]; r['format_source']='same-product-elsewhere'; nprop+=1
stats['format_propagated']=nprop
stats['format_set']=sum(1 for r in rows.values() if r.get('format'))
stats['format_blank']=sum(1 for r in rows.values() if not r.get('format'))
for rid,r in rows.items():
    tgt='held' if r.get('hold_reason') else 'retail_entries'
    json.dump(r,open(f'{out}/{tgt}/{rid}.json','w'),indent=1)
stats['held_no_size']=sum(1 for r in rows.values() if r.get('hold_reason'))
stats['rows']=len(rows)
json.dump(blocks_out,open(out+'/matrix_blocks.json','w'),indent=1); json.dump(stats,open(out+'/summary.json','w'),indent=1)
print(json.dumps(stats))
