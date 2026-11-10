#!/usr/bin/env python3
"""Rule-based hygiene engine, client-agnostic (SOP v85, conventions.hygiene_rules_per_client).
No category word lives in this file. Every pattern comes from clients/<id>.json:
  hygiene.exclude_brands        regex on the brand: not this shelf, dropped and logged (never silent)
  hygiene.fragment_brands       regex on the brand: a product fragment or Unbranded, held for review
  hygiene.brand_canon           {lowercased spelling: canonical}, fixes casing and spelling
  hygiene.private_label_brands  regex on the brand: store brand
  neighborhood.format_rule      {belongs, elsewhere, small_single_oz_max, elsewhere_reason}: a row that does not read like this shelf's
                                format and reads like another's (or is a small single) waits for the other shelf's term
  retailers[].matrix_suffix     canonical '<retailer>-<market>' used in matrix block strings
Verdicts from judge(): land, exclude, elsewhere, review. Only review reaches a person."""
import re,types

def load(C):
    h=C.get('hygiene') or {}
    c=lambda k:(re.compile(h[k],re.I) if h.get(k) else None)
    R=types.SimpleNamespace(exclude=c('exclude_brands'),fragment=c('fragment_brands'),pl=c('private_label_brands'),
        canon=dict(h.get('brand_canon') or {}),
        formats={n['id']:{'belongs':re.compile(f['belongs'],re.I) if f.get('belongs') else None,'elsewhere':re.compile(f['elsewhere'],re.I) if f.get('elsewhere') else None,
                          'small':f.get('small_single_oz_max'),'reason':f.get('elsewhere_reason') or 'belongs on another shelf'}
                 for n in C.get('neighborhoods',[]) for f in [n.get('format_rule')] if f},
        suffix={r['banner'].replace('-api',''):r['matrix_suffix'] for r in C.get('retailers',[]) if r.get('matrix_suffix')},
        configured=bool(h))
    return R

def canon_brand(R,b):
    b=re.sub(r'[®™]','',b or '').strip().rstrip(',').strip()
    k=b.lower()
    if k in R.canon: return R.canon[k]
    b=re.sub(r"'S\b","'s",b); b=re.sub(r"’S\b","'s",b).replace('’',"'")
    if b.islower(): b=b.title()
    return b

def is_private_label(R,brand): return bool(R.pl and R.pl.match(brand or ''))

def canon_block(R,block):
    """candy-chocolate/<neighborhood>@<banner> -> .../<neighborhood>@<matrix_suffix>; unchanged when no suffix is configured."""
    head,_,suf=block.partition('@'); suf=suf.replace('-api','')
    return head+'@'+R.suffix.get(suf,suf)

def judge(R,nb_id,brand,name,size_oz=None,count=None):
    """-> (verdict, reason). Order: not-this-shelf brand, then fragment/unbranded (review), then the shelf's format rule."""
    if not R.configured: return 'land',None
    if R.exclude and R.exclude.search(brand or ''): return 'exclude','excluded brand: '+(brand or '')
    if not brand or brand=='Unbranded' or (R.fragment and R.fragment.match(brand)): return 'review','brand is a product fragment or Unbranded: '+(brand or '')
    f=R.formats.get(nb_id)
    if f and f['belongs']:
        t=(brand or '')+' '+(name or '')
        if not f['belongs'].search(t) and ((f['elsewhere'] and f['elsewhere'].search(t)) or (f['small'] is not None and (size_oz or 0)<=f['small'] and not count)):
            return 'elsewhere',f['reason']
    return 'land',None
