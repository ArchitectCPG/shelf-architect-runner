#!/usr/bin/env python3
"""Amazon lane mapper: data/amazon/<block>/<date>.json -> mapped/<cid>/amazon_comps_candidates.json
(SOP v82 rule 17). Pure file transform: no network, no database. Rows are candidates for amazon_comps.
Emits when the scraper provides it: search_term, est_monthly_units (+ basis amazon_badge_floor; null badge stays null,
the app renders '<50'), parent_asin, seller (seller of record), fulfillment (FBA|FBM|None), inventory_note, bs_rank,
sponsored, is_collision. Own listings are confirmed by ASIN list (client.own_asins) or title term (client.product_terms),
never by brand string alone; a brand-string-only match lands with is_own_brand false and is_collision true.
Comps: top 5 organic per search term by bought-past-month floor. No revenue is derived from badge or rank.
Usage: amazon_comps.py <client_id>"""
import json,sys,glob,os,re
sys.path.insert(0,os.path.dirname(__file__)); from normalize import build_hints,brand_of,relevant

def num(s):
    m=re.search(r'(\d+(?:\.\d+)?)',str(s or '').replace(',','')); return float(m.group(1)) if m else None
PACK=[re.compile(p,re.I) for p in (r'pack of (\d{1,3})',r'(\d{1,3})\s?-?\s?(?:pack|pk)\b',r'(\d{1,3})\s?(?:count|ct)\b',r'\((\d{1,3}) (?:cans|bottles|jars|pouches|bags|units)\)',r'(\d{1,3}) (?:cans|bottles|jars|pouches|bags)\b',r'case of (\d{1,3})')]
def pack_count(name):
    for rx in PACK:
        m=rx.search(name or '')
        if m: return int(m.group(1))
    return 1
def floor_units(h):
    v=h.get('bought_past_month')
    if v not in (None,''): return num(v)
    m=re.search(r'(\d+)(K?)\+?',(h.get('bought_past_month_text') or '').replace(',',''))
    return (float(m.group(1))*(1000 if m.group(2) else 1)) if m else None
LOW=re.compile(r'only \d+ left|low stock|left in stock|ships? in|usually ships|temporarily|out of stock|back ?order',re.I)
def inventory_note(h):
    a=h.get('availability') or ''
    return a.strip() if LOW.search(a) else None
def is_amazon(sl): return bool(re.match(r'^\s*(amazon(\.com)?|amazon\.com services.*)\s*$',sl or '',re.I))
def fulfillment(h):
    """FBA or FBM only when derivable. ships_from (if the scraper returns it) is authoritative. Without it:
    a third-party seller of record with Prime is FBA (or Seller Fulfilled Prime, indistinguishable here, stated in notes);
    Amazon.com as seller is first party, not FBA/FBM, so None. Anything else is not derivable -> None."""
    sf=h.get('ships_from'); sl=h.get('seller')
    if sf: return 'FBA' if re.search(r'amazon',sf,re.I) else 'FBM'
    if sl and not is_amazon(sl) and h.get('prime') is True: return 'FBA'
    return None
def slug(s): return re.sub(r'[^a-z0-9]+','-',(s or '').lower()).strip('-')

def main(cid):
    C=json.load(open(f'clients/{cid}.json')); hints=build_hints(C)
    own_asins={a.upper() for a in C.get('own_asins',[])}
    prod_rx=[re.compile(t,re.I) for t in C.get('product_terms',[])]
    brand_rx=[re.compile(t,re.I) for t in C.get('brand_terms',[])]
    excl=re.compile(C['brand_exclude'],re.I) if C.get('brand_exclude') else None
    label=C.get('own_brand_label') or C['name']
    own={}; comps={}; seen=set()
    for f in sorted(glob.glob(f'blocks_gen/{cid}/amazon/*.json')):
        b=json.load(open(f)); bid=re.sub(r'[^a-z0-9@_.-]','_',b['block_id'],flags=re.I)
        fs=sorted(x for x in glob.glob(f'data/amazon/{bid}/*.json') if not x.endswith('-error.json'))
        if not fs: continue
        d=json.load(open(fs[-1])); day=d['pulled_at'][:10]
        nb=next(n for n in C['neighborhoods'] if n['id']==b['neighborhood']); term=b['term']
        for h in d.get('houses',[]):
            asin=(h.get('asin') or '').upper(); nm=h.get('name') or ''
            if not asin or (asin,term) in seen: continue
            seen.add((asin,term))
            blob=nm+' '+(h.get('brand') or '')
            brand_hit=any(r.search(blob) for r in brand_rx)
            confirmed=asin in own_asins or (any(r.search(nm) for r in prod_rx) and not (excl and excl.search(blob)))
            collision=brand_hit and not confirmed
            p=num(h.get('price')); pc=pack_count(nm); fl=floor_units(h)
            notes=[f"Runner Amazon lane {day}, national search '{term}'."]
            if h.get('sponsored'): notes.append('Sponsored placement.')
            if collision: notes.append(f"Brand-string match only: {h.get('brand')!r} not confirmed by ASIN list or product term. Finding, not an own listing.")
            if fulfillment(h) and not h.get('ships_from'): notes.append('Fulfillment inferred: third-party seller with Prime (FBA or Seller Fulfilled Prime); ships_from not returned.')
            brand=label if confirmed else (brand_of(h,hints) or h.get('brand'))
            row={"doc_id":f"{cid}_{slug(brand)}_{asin.lower()}","data":{
                "brand":brand,"client_id":cid,"is_own_brand":bool(confirmed),"is_collision":bool(collision),
                "product_title":nm,"price":p,"pack_size":pc,"price_per_unit":round(p/pc,2) if p and pc else None,
                "rating":h.get('rating'),"review_count":h.get('reviews'),
                "est_monthly_units":fl,"est_monthly_units_basis":'amazon_badge_floor' if fl is not None else None,
                "est_monthly_revenue":None,"bs_rank":h.get('bs_rank'),"bs_category":h.get('bs_category'),
                "asin":asin,"parent_asin":(h.get('parent_asin') or None),"seller":h.get('seller'),
                "fulfillment":fulfillment(h),"inventory_note":inventory_note(h),"sponsored":bool(h.get('sponsored')),
                "search_term":term,"url":h.get('link'),"subcategory":nb['id'],
                "source":"runner-brightdata-amazon","pulled_at":day,"notes":' '.join(notes)}}
            relv=relevant(h,nb)
            if confirmed or collision: own.setdefault(asin,row)   # control findings: every own listing and every collision
            elif relv and not h.get('sponsored'): comps.setdefault(term,{}).setdefault(asin,row)
    out=list(own.values())
    for term,rs in comps.items():
        top=sorted(rs.values(),key=lambda r:-(r['data']['est_monthly_units'] or 0))[:5]
        out+=[r for r in top if r['data']['asin'] not in own]
    os.makedirs(f'mapped/{cid}',exist_ok=True)
    json.dump(out,open(f'mapped/{cid}/amazon_comps_candidates.json','w'),indent=1)
    print(f"{cid}: {sum(1 for r in out if r['data']['is_own_brand'])} own, {sum(1 for r in out if r['data']['is_collision'])} collisions, {sum(1 for r in out if not r['data']['is_own_brand'] and not r['data']['is_collision'])} comps -> mapped/{cid}/amazon_comps_candidates.json")
if __name__=='__main__': main(sys.argv[1])
