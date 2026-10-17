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
    return bool(re.search(rx,(h.get('name') or '')+' '+' '.join(h.get('card_text') or []),re.I))
def normalize(h,C,nb):
    reg,pro=dual_price(h)
    return dict(h,brand_norm=brand_of(h,build_hints(C)),price_regular=reg,price_promo=pro,relevant=relevant(h,nb))
