#!/usr/bin/env python3
"""Normalize runner houses to the Shelf Architect row shape: brand, price_regular, price_promo, relevance.
Pure functions, used by client_report.py (and later the DB mapper). Sandbox only."""
import re
PR=re.compile(r'\$\s?(\d{1,4}(?:\.\d{2})?)')
def num(s):
    m=re.search(r'(\d+(?:\.\d+)?)',str(s or '').replace(',','')); return float(m.group(1)) if m else None
LAB=re.compile(r'(?:was|reg(?:ular)?\.?|orig(?:inal)?(?: price)?|list)\s*:?\s*\$\s?(\d{1,4}(?:\.\d{2})?)',re.I)
SALE=re.compile(r'\b(sale|now|rollback|clearance|price cut|save|special)\b',re.I)
def dual_price(h):
    """-> (regular, promo). promo None unless a real markdown is evidenced."""
    cur=num(h.get('price')); blob=' | '.join(h.get('card_text') or [])
    reg=None
    m=LAB.search(blob)
    if m: reg=float(m.group(1))
    elif num(h.get('initial_price')) and cur and num(h.get('initial_price'))>cur+0.005: reg=num(h['initial_price'])
    elif h.get('price_regular'): reg=num(h['price_regular'])
    else:
        ps=sorted({float(x) for x in PR.findall(blob)},reverse=True)
        if len(ps)==2 and cur in ps and SALE.search(blob) and ps[0]>cur: reg=ps[0]
    if reg and cur and reg>cur+0.005: return reg,cur
    return cur,None
def build_hints(C):
    hints=[(C['name'],t) for t in C.get('brand_terms',[])]
    for k,ts in C.get('competitor_terms',{}).items(): hints+=[(k,t) for t in ts]
    for k,t in (C.get('brand_hints') or {}).items(): hints.append((k,t))
    return hints
MARK=re.compile(r'^(.{2,40}?)\s?[®™]')
def brand_of(h,hints):
    nm=(h.get('name') or '')
    for lab,rx in hints:
        if re.search(rx,nm+' '+(h.get('brand') or ''),re.I): return lab
    b=(h.get('brand') or '').strip()
    if b: return b.title() if b.islower() else b
    m=MARK.match(nm)
    return m.group(1).strip() if m else None
def relevant(h,nb):
    rx=nb.get('relevance') or r'\b'+re.sub(r'\s+',r'\\W+',nb['term'])+r's?\b'
    txt=(h.get('name') or '')+' '+' '.join(h.get('card_text') or [])
    if not re.search(rx,txt,re.I): return False
    if nb.get('hard_exclude') and re.search(nb['hard_exclude'],(h.get('name') or ''),re.I): return False
    ex=nb.get('exclude')
    if ex and re.search(ex,(h.get('name') or ''),re.I) and not (nb.get('keep') and re.search(nb['keep'],(h.get('name') or ''),re.I)): return False
    return True
def normalize(h,C,nb):
    reg,pro=dual_price(h)
    return dict(h,brand_norm=brand_of(h,build_hints(C)),price_regular=reg,price_promo=pro,relevant=relevant(h,nb))

# Whole Foods (Amazon storefront) card realignment, Fable 2026-11-06. The price-leaf walk-up window for house N holds
# [brand_N, name_N, price_N, "Add to Cart", brand_N+1, name_N+1]; the longest-line name picker often takes the next card's
# name, so brand/name/price were shifted by one card. Rebuild card N from house N-1's tail (confirmed by house N's pre).
_PRODLINE=re.compile(r'(\d+(\.\d+)?\s?(oz|ounce|ct|lb|g)\b|,)',re.I)
_NOISE=re.compile(r'^(\$|\d+ flavors?, \d+ sizes?|join prime|.*% off|add to cart|sponsored|see options)',re.I)
def realign_wholefoods(houses):
    out=[];prev_tail=None
    for h in houses:
        ct=h.get('card_text') or []
        if 'Add to Cart' not in ct: out.append(h); prev_tail=None; continue
        i=ct.index('Add to Cart'); pre=[t for t in ct[:i] if not _NOISE.match(t)]; tail=[t for t in ct[i+1:] if not _NOISE.match(t)]
        brand=name=None
        preprod=[t for t in pre if _PRODLINE.search(t)]; prebrand=[t for t in pre if not _PRODLINE.search(t)]
        if prev_tail: brand=prev_tail[0]
        elif prebrand: brand=prebrand[0]
        if prev_tail and len(prev_tail)>=2: name=prev_tail[1]
        if preprod: name=preprod[-1]   # the card's own text wins over the previous window's tail (variant cards show different flavors)
        prev_tail=tail
        if name and name not in ct: ct=ct+[name]; h=dict(h,card_text=ct)
        if not name: h=dict(h,wf_dropped='no aligned card'); out.append(h); continue
        if brand and re.sub(r'\W','',brand.lower())==re.sub(r'\W','',name.lower()): name=None
        if not name: h=dict(h,wf_dropped='brand only'); out.append(h); continue
        nh=dict(h,name=name,brand=brand,wf_realigned=True)
        m=re.search(r'(\d+(?:\.\d+)?)\s?(oz|ounce)\b',name,re.I)
        if m: nh['size']=m.group(0)
        out.append(nh)
    return [x for x in out if not x.get('wf_dropped')]
