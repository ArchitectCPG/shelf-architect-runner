#!/usr/bin/env python3
"""Numbers audit (SOP v85, conventions.numbers_audit_gate). Client-agnostic: no category word in this file.
A figure quoted in copy (launch plan note, thesis, synopsis, dashboard text) is recomputed from the rows by a second method
before the copy is written. A mismatch, or a figure with no claim behind it in --strict mode, exits non-zero and the write does not happen.

Usage:
  numbers_audit.py --selftest
  numbers_audit.py <client> --rows <dir|file.json> --claims <claims.json> [--text copy.txt] [--allow 8.99,9.99] [--strict] [--cohorts a,b,c] [--report out.json]

--rows    a directory of retail_entries JSON files, or one JSON file (list of rows, or {id: row}). Export the collection first;
          the audit reads what the DB holds, not what a mapper run produced.
--claims  JSON list. Each claim: {"id","quote","claim","metric":{...},"tol"}.
          metric: {"stat": count|banners|brands|min|max|mean|median|p<N>|share_ge|share_le|share_gt|share_lt,
                   "field": price|price_per_oz|size_oz (default price), "threshold": N (share_*),
                   "set": price|presence (default price), "method": linear|lower|higher|nearest (percentiles, default linear),
                   "filter": {"neighborhood","retailer","brand","size_min","size_max","own_brand","is_private_label","block"}}
          "claim" is the number as written in the copy; share_* claims are percent (27 means 27 percent).
--text    the copy block. Every figure in it ($ amounts, percents, counts before rows/banners/houses/packs/brands/doors) must match a claim
          or be allowed; with --strict an uncovered figure fails the audit.
The price set follows the app (conventions.pricing_cohorts, shelf_read_is_the_shelf, distribution_is_not_price): the median set drops rows in the
dollar, size-unverified, off-neighborhood and any '-premium' cohort and rows whose notes start 'PRICING CAVEAT'; the presence set (count, banners, brands)
drops only off-neighborhood rows. Median is the average of the two middle values on an even set."""
import json,sys,os,re,glob

PRICE_DROP_COHORTS={'dollar','size-unverified','off-neighborhood'}
PRESENCE_DROP_COHORTS={'off-neighborhood'}

def load_rows(path):
    if os.path.isdir(path):
        return [json.load(open(f)) for f in sorted(glob.glob(path+'/*.json'))]
    d=json.load(open(path))
    if isinstance(d,dict) and isinstance(d.get('rows'),list): d=d['rows']   # page Export rows bundle
    elif isinstance(d,dict): d=[dict(v,_id=k) for k,v in d.items()]
    return [x.get('data',x) for x in d]

def in_set(r,kind):
    c=(r.get('pricing_cohort') or '')
    if kind=='presence': return c not in PRESENCE_DROP_COHORTS
    if c in PRICE_DROP_COHORTS or c.endswith('-premium'): return False
    if str(r.get('notes') or '').startswith('PRICING CAVEAT'): return False
    return True

def matches(r,f):
    nb=r.get('neighborhoods') or [r.get('neighborhood')]
    if f.get('neighborhood') and f['neighborhood'] not in nb: return False
    if f.get('retailer') and str(r.get('retailer','')).lower()!=f['retailer'].lower(): return False
    if f.get('brand') and str(r.get('brand','')).lower()!=f['brand'].lower(): return False
    if f.get('block') and f['block'] not in (r.get('blocks') or [r.get('block')]): return False
    if 'own_brand' in f and bool(r.get('is_own_brand'))!=f['own_brand']: return False
    if 'is_private_label' in f and bool(r.get('is_private_label'))!=f['is_private_label']: return False
    sz=r.get('size_oz')
    if f.get('size_min') is not None and (sz is None or sz<f['size_min']): return False
    if f.get('size_max') is not None and (sz is None or sz>f['size_max']): return False
    return True

def percentile(vals,p,method='linear'):
    v=sorted(vals); n=len(v)
    if not n: return None
    k=(n-1)*p/100.0; lo=int(k//1); hi=min(lo+1,n-1); fr=k-lo
    if method=='lower': return v[lo]
    if method=='higher': return v[hi]
    if method=='nearest': return v[int(round(k))]
    return v[lo]+(v[hi]-v[lo])*fr

def median(vals):
    v=sorted(vals); n=len(v)
    if not n: return None
    return v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2   # average of the two middles, never the upper one (audit_the_numbers_not_the_code)

def compute(rows,m):
    stat=m['stat']; field=m.get('field','price'); kind=m.get('set','presence' if stat in('count','banners','brands') else 'price')
    rs=[r for r in rows if in_set(r,kind) and matches(r,m.get('filter',{}))]
    if stat=='count': return len(rs),len(rs)
    if stat=='banners': return len({str(r.get('retailer')).lower() for r in rs}),len(rs)
    if stat=='brands': return len({str(r.get('brand')).lower() for r in rs}),len(rs)
    vals=[r[field] for r in rs if isinstance(r.get(field),(int,float))]
    if not vals: return None,0
    if stat=='min': return min(vals),len(vals)
    if stat=='max': return max(vals),len(vals)
    if stat=='mean': return sum(vals)/len(vals),len(vals)
    if stat=='median': return median(vals),len(vals)
    mm=re.fullmatch(r'p(\d+(?:\.\d+)?)',stat)
    if mm: return percentile(vals,float(mm.group(1)),m.get('method','linear')),len(vals)
    ms=re.fullmatch(r'share_(ge|le|gt|lt)',stat)
    if ms:
        t=m['threshold']; op={'ge':lambda x:x>=t,'le':lambda x:x<=t,'gt':lambda x:x>t,'lt':lambda x:x<t}[ms.group(1)]
        return 100.0*sum(1 for x in vals if op(x))/len(vals),len(vals)
    raise ValueError('unknown stat '+stat)

def audit_claims(rows,claims):
    out=[]
    for c in claims:
        got,n=compute(rows,c['metric'])
        tol=c.get('tol',0.5 if c['metric']['stat'].startswith('share') else (0 if c['metric']['stat'] in('count','banners','brands') else 0.005))
        ok=got is not None and abs(got-c['claim'])<=tol+1e-9
        out.append(dict(id=c['id'],quote=c.get('quote',''),claim=c['claim'],recomputed=None if got is None else round(got,4),n=n,tol=tol,ok=ok))
    return out

FIG=re.compile(r'(\$\s?\d[\d,]*(?:\.\d+)?)|(\d+(?:\.\d+)?)\s?(?:%|percent)|(\d[\d,]*)\s+(?:rows?|banners?|houses?|packs?|brands?|doors?|SKUs?|items?)\b',re.I)
def figures(text):
    res=[]
    for m in FIG.finditer(text):
        raw=m.group(0); g=next(x for x in m.groups() if x)
        res.append((raw,float(re.sub(r'[$,\s]','',g))))
    return res

def audit_text(text,claims,allow):
    vals={float(c['claim']) for c in claims}|{float(a) for a in allow}
    return [dict(figure=raw,value=v,covered=any(abs(v-x)<1e-9 for x in vals)) for raw,v in figures(text)]

def selftest():
    rows=[dict(retailer='a',brand='X',neighborhoods=['s'],price=p,size_oz=3.0,price_per_oz=p/3) for p in (1,2,3,4)]
    rows+=[dict(retailer='b',brand='Y',neighborhoods=['s'],price=100,size_oz=3.0,pricing_cohort='dollar'),
           dict(retailer='c',brand='Z',neighborhoods=['s'],price=50,size_oz=3.0,pricing_cohort='x-premium'),
           dict(retailer='d',brand='W',neighborhoods=['s'],price=60,size_oz=3.0,notes='PRICING CAVEAT: markup'),
           dict(retailer='e',brand='V',neighborhoods=['other'],price=9,size_oz=3.0)]
    f={'neighborhood':'s'}; T=[]
    T.append(('even median is the average of the middles',compute(rows,{'stat':'median','filter':f})[0]==2.5))
    T.append(('dollar, premium and caveat rows stay out of the price set',compute(rows,{'stat':'max','filter':f})[0]==4))
    T.append(('presence keeps premium and caveat rows, drops off-neighborhood only',compute(rows,{'stat':'banners','filter':f})[0]==4))
    T.append(('p75 linear',abs(compute(rows,{'stat':'p75','filter':f})[0]-3.25)<1e-9))
    T.append(('share_ge is a percent',compute(rows,{'stat':'share_ge','threshold':3,'filter':f})[0]==50.0))
    T.append(('size filter',compute(rows,{'stat':'count','filter':{'neighborhood':'s','size_min':3.5}})[0]==0))
    bad=audit_claims(rows,[dict(id='planted',claim=2.0,metric={'stat':'median','filter':f})])
    T.append(('a planted wrong median fails',bad[0]['ok'] is False))
    good=audit_claims(rows,[dict(id='right',claim=2.5,metric={'stat':'median','filter':f})])
    T.append(('the right median passes',good[0]['ok'] is True))
    t=audit_text('Median $2.50, 4 banners, 50 percent at $3 or more, $9.99 SRP.',[dict(claim=2.5),dict(claim=4),dict(claim=50),dict(claim=3)],[])
    T.append(('text scan flags the uncovered figure',[x['covered'] for x in t]==[True,True,True,True,False]))
    for name,ok in T: print(('PASS ' if ok else 'FAIL ')+name)
    return all(ok for _,ok in T)

if __name__=='__main__':
    a=sys.argv[1:]
    if '--selftest' in a: sys.exit(0 if selftest() else 1)
    opt=lambda k:(a[a.index(k)+1] if k in a else None)
    if len(a)<1 or not opt('--rows') or not opt('--claims'): print(__doc__); sys.exit(2)
    if opt('--cohorts'):   # the client's client_config.pricing_exclude_cohorts; the price set must match the app's
        PRICE_DROP_COHORTS.clear(); PRICE_DROP_COHORTS.update(x for x in opt('--cohorts').split(',') if x)
    rows=load_rows(opt('--rows')); claims=json.load(open(opt('--claims')))
    res=audit_claims(rows,claims); bad=[r for r in res if not r['ok']]
    print(f'| claim | quoted | recomputed | n | result |\n|---|---|---|---|---|')
    for r in res: print(f"| {r['id']} | {r['claim']} | {r['recomputed']} | {r['n']} | {'ok' if r['ok'] else 'MISMATCH'} |")
    unc=[]
    if opt('--text'):
        txt=open(opt('--text')).read(); allow=[x for x in (opt('--allow') or '').split(',') if x]
        ft=audit_text(txt,claims,allow); unc=[x for x in ft if not x['covered']]
        print(f"\ntext: {len(ft)} figures, {len(ft)-len(unc)} covered, {len(unc)} uncovered"+(': '+', '.join(x['figure'] for x in unc) if unc else ''))
    fail=bool(bad) or (bool(unc) and '--strict' in a)
    if opt('--report'): json.dump(dict(client=a[0],results=res,uncovered=unc,pass_=not fail),open(opt('--report'),'w'),indent=1)
    print('\nAUDIT','FAIL' if fail else 'PASS'); sys.exit(1 if fail else 0)
