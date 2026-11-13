#!/usr/bin/env python3
"""Resolve a client's banner scope against registry/banners.json. Dry: reads files, dispatches nothing.

A client file may carry, in place of a hand-typed retailers list:
  "scope": {"preset": "universe" | "mulo" | "fdmc" | null,
            "channels": ["Natural","Specialty"],      # registry channel names, any case
            "distributors": ["UNFI"],                 # banner ships through any of these
            "states": ["Illinois","California"],      # banner has doors in any of these
            "min_doors": 0,
            "include": ["whole-foods"], "exclude": ["aldi"]}
Base set = preset (or the whole universe when no preset). channels, distributors, states and min_doors narrow it (AND).
include adds banners back; exclude always wins. Parent, division and duplicate docs are never in scope.

Usage:
  python3 tools/scope.py clients/<id>.json                 report for the client's scope
  python3 tools/scope.py --scope '<json>' --neighborhoods 4 report for an ad hoc scope (dry replay)
  add --emit to print the retailers list (client-config shape) for the banners with a usable route
"""
import json, os, re, sys, argparse, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FDMC = {'mulo', 'conventional', 'drug', 'mass', 'club', 'natural', 'specialty'}
norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())
MULO_ALIAS = {'albertsonssafeway': ['albertsons', 'safeway'], 'heb': ['heb'], 'samsclub': ['sams-club'], 'bjswholesale': ['bjs'],
              'wholefoodsmarket': ['whole-foods'], 'sproutsfarmersmarket': ['sprouts'], 'dollargeneral': ['dollar-general-popshelf'],
              'gianteagle': ['giant-eagle'], 'stopshop': ['stop-shop'], 'hyvee': ['hyvee'], 'winndixie': ['winn-dixie'],
              'wakefern': ['shoprite'], 'thegiantcompany': ['giant-food-stores'], 'southeasterngrocers': ['winn-dixie'],
              'afsassociatedfoods': ['associated-food-stores'], 'savemartluckyfoodmax': ['lucky-s-savemart'], 'ngvc': ['natural-grocers'],
              'shawsstar': ['shaws', 'star-market'], 'tops': ['northeast-grocers-tops'], 'kvatfoodcity': ['food-city-stores'],
              'pricechopper': ['northeast-grocers-price-chopper'], 'nwgrocers': ['northwest-grocer'], 'consentinos': ['cosentinos-food-stores']}

def mulo_ids(reg):
    by = {}
    for b in reg:
        if b['counted']: by.setdefault(norm(b['name']), b['id']); by.setdefault(norm(b['id']), b['id'])
    ids, miss = [], []
    p = os.path.join(ROOT, 'clients', 'mulo_retailers.tsv')
    for line in open(p):
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 2 or parts[1].lower() in ('retailer', 'name'): continue
        n = norm(parts[1]); hit = MULO_ALIAS.get(n) or ([by[n]] if n in by else None)
        if not hit:
            cand = [v for k, v in by.items() if (n and (k.startswith(n) or n.startswith(k)) and min(len(k), len(n)) >= 4)]
            hit = cand[:1] or None
        if hit: ids += hit
        else: miss.append(parts[1])
    return list(dict.fromkeys(ids)), miss

def resolve(scope, reg):
    idx = {b['id']: b for b in reg}; miss = []
    preset = (scope.get('preset') or 'universe').lower()
    if preset == 'mulo': base, miss = mulo_ids(reg); base = [idx[i] for i in base if i in idx]
    elif preset == 'fdmc': base = [b for b in reg if (b['channel'] or '').lower() in FDMC]
    else: base = list(reg)
    base = [b for b in base if b['counted']]
    ch = {c.lower() for c in scope.get('channels', [])}; ds = {d.lower() for d in scope.get('distributors', [])}
    st = {s.lower() for s in scope.get('states', [])}; md = scope.get('min_doors', 0)
    def keep(b):
        if ch and (b['channel'] or '').lower() not in ch: return False
        if ds and not ({(d or '').lower() for d in b['distributors']} & ds): return False
        if st and not ({s.lower() for s in b['states']} | {(b['hq_state'] or '').lower()}) & st: return False
        return (b['doors'] or 0) >= md
    out = {b['id']: b for b in base if keep(b)}
    for i in scope.get('include', []):
        if i in idx and idx[i]['counted']: out[i] = idx[i]
        else: miss.append(i)
    for i in scope.get('exclude', []): out.pop(i, None)
    return list(out.values()), miss

def usable(b):
    for r in b['routes']:
        if r['state'] in ('proven', 'stale') and not r.get('fallback'): return r
    return None

def report(scope, reg, n_nb, label, emit=False):
    banners, miss = resolve(scope, reg)
    tot_d = sum(b['doors'] for b in banners) or 1; tot_a = sum(b['acv_weight'] or 0 for b in banners) or 1
    ready, gate, uncovered, family = [], [], [], []
    for b in banners:
        r = usable(b)
        if r and b['pins']:
            ready.append((b, r))
            if r['state'] == 'stale': gate.append((b, 'stale, last good pull ' + r['last_ok']))
        elif r: gate.append((b, 'route proven but no market pin on file')); ready.append((b, r))
        elif b['status'] == 'family': family.append(b); gate.append((b, f"sister banner on the {b['family']} recipe, never run"))
        elif b['status'] == 'no_ecomm': uncovered.append((b, 'no online shelf'))
        elif b['status'] == 'failed': uncovered.append((b, 'route failed on last try'))
        else: uncovered.append((b, 'never probed'))
    cov_d = sum(b['doors'] for b, _ in ready); cov_a = sum(b['acv_weight'] or 0 for b, _ in ready)
    print(f"== {label}"); print(f"scope: {json.dumps(scope)}")
    fam_d = sum(b['doors'] for b in family)
    print(f"banners in scope: {len(banners)} | runner-ready: {len(ready)} | ready after a gate pass (family recipe): {len(family)} ({fam_d:,} doors) | no route: {len(uncovered)}")
    print(f"doors covered: {cov_d:,} of {tot_d:,} ({100*cov_d/tot_d:.0f}%) | ACV covered: {100*cov_a/tot_a:.0f}% of the scope's rated ACV")
    print(f"blocks at {n_nb} neighborhoods: {len(ready)*n_nb} pull (+{len(family)*n_nb} if the family banners pass) + {len(gate)} gate; {len(ready)+len(family)-len(gate)} banners skip the gate")
    from collections import Counter
    print("ready by lane:", dict(Counter(r['lane'] for _, r in ready)))
    print("ready by channel:", dict(Counter(b['channel'] for b, _ in ready)), "| in scope by channel:", dict(Counter(b['channel'] for b in banners)))
    top = sorted(uncovered, key=lambda x: -((x[0]['acv_weight'] or 0), x[0]['doors'])[0] * 1e6 - x[0]['doors'])[:8]
    print("biggest uncovered:", "; ".join(f"{b['name']} ({b['doors']:,} doors, {why})" for b, why in top) or "none")
    if gate: print("gate first:", "; ".join(f"{b['name']} ({why})" for b, why in gate[:10]) + (f" +{len(gate)-10} more" if len(gate) > 10 else ""))
    if miss: print("not matched to the registry:", ", ".join(miss[:15]))
    if emit:
        outl = []
        for b, r in ready:
            pin = b['pins'][0] if b['pins'] else {}
            e = {'banner': r['runner_banner'], 'registry_id': b['id'], 'lane': r['lane'], 'market': pin.get('market'), 'brand_check': True}
            for k in ('slug', 'url', 'template', 'host', 'chain'):
                if r.get(k): e[k] = r[k]
            outl.append(e)
        print(json.dumps(outl, indent=1))
    print()

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('client', nargs='?'); ap.add_argument('--scope'); ap.add_argument('--neighborhoods', type=int)
    ap.add_argument('--label'); ap.add_argument('--emit', action='store_true'); a = ap.parse_args()
    reg = json.load(open(os.path.join(ROOT, 'registry', 'banners.json')))['banners']
    if a.scope: report(json.loads(a.scope), reg, a.neighborhoods or 4, a.label or 'ad hoc scope', a.emit)
    else:
        C = json.load(open(a.client))
        if 'scope' not in C: sys.exit(f"{a.client} has no scope block (it still uses a hand-typed retailers list)")
        report(C['scope'], reg, a.neighborhoods or len(C.get('neighborhoods', [])) or 4, C.get('name', C['client_id']), a.emit)
