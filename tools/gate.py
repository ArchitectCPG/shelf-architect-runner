#!/usr/bin/env python3
"""Stage 0 gate for a runner client (SOP v85, conventions.stage0_gate_code_checks). Client-agnostic: no category words here.

Two halves.
  pre  (before blocks are generated): config check. Used by gen_client_blocks.py, which refuses to emit on failure.
       1. every neighborhood has `relevance`; every non-brand_only neighborhood has the key `hard_exclude` (explicit "" means none decided)
       2. the client has a brand_only neighborhood, and every banner gets a brand block unless it sets brand_check false with brand_skip_reason
       3. every block resolves a store_expect: retailer.store_expect, else its market's store_expect. None resolved = refuse.
  post (after a sandbox pass): data check. Used by client_report.py and the mapper.
       4. store: the store the page landed on must match the block's gate_store_expect. Unpinned or mismatch = not landed.
       5. brand: every banner has a brand block with data.
       6. term precision per neighborhood: share of returned items that pass relevance. Under 0.5 = fix the term or the rules.

Usage: gate.py <client> [pre|post|all|stamp] [--min-precision 0.5] [--min-sample 30]. Exit 1 on any failure."""
import json,sys,os,re,glob
sys.path.insert(0,os.path.dirname(__file__))
MIN_PRECISION=0.5; MIN_SAMPLE=30

def load_client(cid): return json.load(open(f'clients/{cid}.json'))

def store_expect_for(C,r):
    """retailer pin wins, then the market regex. Raises ValueError when neither exists."""
    se=r.get('store_expect') or (C['markets'].get(r['market']) or {}).get('store_expect')
    if not se: raise ValueError(f"no store_expect for banner {r['banner']} (retailer pin or market '{r['market']}' store_expect)")
    re.compile(se)
    return se

def brand_wanted(r):
    """Brand term is walked at every banner. Skipped only with brand_check false AND a written reason."""
    if r.get('brand_check') is False:
        if not r.get('brand_skip_reason'): raise ValueError(f"banner {r['banner']}: brand_check false needs brand_skip_reason")
        return False
    return True

def check_config(C):
    errs=[]
    nbs=C.get('neighborhoods',[])
    if not any(n.get('brand_only') for n in nbs): errs.append('no brand_only neighborhood: the brand term cannot be walked at each banner')
    for n in nbs:
        if not n.get('relevance'): errs.append(f"neighborhood {n['id']}: relevance missing")
        elif True:
            try: re.compile(n['relevance'])
            except re.error as e: errs.append(f"neighborhood {n['id']}: relevance does not compile ({e})")
        if not n.get('brand_only') and 'hard_exclude' not in n: errs.append(f"neighborhood {n['id']}: hard_exclude key missing (use \"\" if none is decided)")
    for k,v in (C.get('hygiene') or {}).items():
        if k in('exclude_brands','fragment_brands','private_label_brands') and v:
            try: re.compile(v)
            except re.error as e: errs.append(f"hygiene.{k} does not compile ({e})")
    for n in nbs:
        for k in ('belongs','elsewhere'):
            v=(n.get('format_rule') or {}).get(k)
            if v:
                try: re.compile(v)
                except re.error as e: errs.append(f"neighborhood {n['id']}: format_rule.{k} does not compile ({e})")
    for r in C.get('retailers',[]):
        if r.get('fallback'): continue
        if r['market'] not in C.get('markets',{}): errs.append(f"banner {r['banner']}: market {r['market']} not in markets"); continue
        try: store_expect_for(C,r)
        except (ValueError,re.error) as e: errs.append(str(e))
        try: brand_wanted(r)
        except ValueError as e: errs.append(str(e))
    return errs

def latest_data(b):
    bid=re.sub(r'[^a-z0-9@_.-]','_',b['block_id'],flags=re.I)
    fs=[x for x in sorted(glob.glob(f"data/{b['retailer']}/{bid}/*.json")) if not x.endswith('-error.json')]
    return json.load(open(fs[-1])) if fs else None

def block_store_verdict(b,d):
    """-> 'ok' or a reason string. Amazon blocks are a separate lane and are never judged here."""
    if b.get('retailer')=='amazon' or not d: return 'ok' if b.get('retailer')=='amazon' else 'NO DATA'
    se=b.get('gate_store_expect') or b.get('store_expect')
    if not se: return 'NO store_expect on block'
    ss=str(d.get('store_set') or '')
    # SOP v89: Walmart search-page fallback lands, tagged online_default_store (default-store price, not the pinned zip). Only Walmart; never a silent pass for other banners.
    if b.get('retailer')=='walmart' and d.get('price_basis')=='online_default_store': return 'ok'
    if not ss or re.search(r'UNPINNED|^none$|^null$',ss,re.I): return 'UNPINNED'
    if not re.search(se,ss,re.I): return f"WRONG MARKET (landed: {ss[:60]})"
    return 'ok'

def post_checks(C,cid,min_prec=MIN_PRECISION,min_sample=MIN_SAMPLE):
    from normalize import normalize
    blocks=[json.load(open(f)) for f in sorted(glob.glob(f'blocks_gen/{cid}/*.json'))]
    res={'store':{},'brand':{},'precision':{},'fail':[]}
    by_nb={}; banners=set(); brand_ok=set()
    for b in blocks:
        d=latest_data(b); v=block_store_verdict(b,d)
        banners.add(b['retailer'])
        nb=next(n for n in C['neighborhoods'] if n['id']==b['neighborhood'])
        if nb.get('brand_only') and d and not d.get('error'): brand_ok.add(b['retailer'])
        if v!='ok': res['store'][b['block_id']]=v
        if not d or v!='ok': continue
        hs=[normalize(x,C,nb) for x in d.get('houses',[])]
        a=by_nb.setdefault(b['neighborhood'],[0,0,bool(nb.get('brand_only'))]); a[0]+=len(hs); a[1]+=sum(1 for x in hs if x['relevant'])
    for bn in sorted(banners):
        if bn=='amazon': continue
        if bn not in brand_ok: res['brand'][bn]='no brand block with data'
    for nid,(n,rel,bo) in by_nb.items():
        p=round(rel/n,3) if n else None
        verdict='brand search, not judged' if bo else ('thin sample, not judged' if n<min_sample else ('FAIL: fix term or rules' if p<min_prec else 'ok'))
        res['precision'][nid]={'returned':n,'relevant':rel,'precision':p,'verdict':verdict}
    res['fail']=sorted(
        [f"store: {k} {v}" for k,v in res['store'].items() if v not in ('NO DATA',)]
        +[f"brand: {k} {v}" for k,v in res['brand'].items()]
        +[f"precision: {k} {v['precision']} ({v['relevant']}/{v['returned']})" for k,v in res['precision'].items() if v['verdict'].startswith('FAIL')])
    return res

def print_post(res):
    print('\n## Stage 0 gate (post)')
    print('| check | result |'); print('|---|---|')
    nd=sum(1 for v in res['store'].values() if v=='NO DATA'); print('| store | %d blocks fail, %d not pulled yet |'%(len(res['store'])-nd,nd))
    print('| brand | %d banners without a brand block with data |'%len(res['brand']))
    print('| precision | %s |'%(', '.join(f"{k} {int((v['precision'] or 0)*100)}% ({v['verdict']})" for k,v in res['precision'].items()) or 'no data'))
    for f in res['fail']: print('FAIL',f)
    print('GATE', 'FAIL' if res['fail'] else 'PASS')

def stamp(C,cid):
    """Retrofit: write gate_store_expect (and store_expect on recipe-lane blocks) onto blocks that already exist, without regenerating.
    gen_client_blocks.py wipes and rebuilds the whole folder, which would drop hand-added blocks (scout shelves, extra terms); stamp touches only those two keys."""
    n=0; miss=[]
    for f in sorted(glob.glob(f'blocks_gen/{cid}/*.json')):
        b=json.load(open(f))
        r=next((x for x in C['retailers'] if x['banner']==b['retailer'] and (C['markets'].get(x['market']) or {}).get('zip')==b.get('store_zip')),None)
        if not r: miss.append(os.path.basename(f)); continue
        se=store_expect_for(C,r); ch=False
        if b.get('gate_store_expect')!=se: b['gate_store_expect']=se; ch=True
        if r['lane']=='recipe' and b.get('store_expect')!=se: b['store_expect']=se; ch=True
        if ch: json.dump(b,open(f,'w'),indent=1); n+=1
    return n,miss

if __name__=='__main__':
    a=[x for x in sys.argv[1:] if not x.startswith('--')]; cid=a[0]; mode=a[1] if len(a)>1 else 'all'
    mp=float(next((x.split('=')[1] for x in sys.argv if x.startswith('--min-precision=')),MIN_PRECISION))
    C=load_client(cid); bad=False
    if mode in('pre','all'):
        errs=check_config(C)
        for e in errs: print('CONFIG FAIL',e)
        print('config', 'FAIL' if errs else 'PASS'); bad=bad or bool(errs)
    if mode=='stamp':
        n,miss=stamp(C,cid); print(f'stamped {n} blocks; unmatched {len(miss)}',miss); sys.exit(0)
    if mode in('post','all'):
        r=post_checks(C,cid,mp); print_post(r)
        json.dump(r,open(f'data/clients_{cid}_gate.json','w'),indent=1); bad=bad or bool(r['fail'])
    sys.exit(1 if bad else 0)
