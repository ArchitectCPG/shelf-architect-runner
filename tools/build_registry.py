#!/usr/bin/env python3
"""Build registry/banners.json: one row per banner in the universe, with what the runner has proven.

Inputs (all on disk, no network):
  registry/source/retailers_snapshot.json  compact export of the main instance retailers collection
  registry/source/acv.json                 slug -> ACV weight (app_meta/acv_adjusted)
  registry/source/excluded.json            slug -> reason (parent and division docs, duplicates; app_meta/platform_bridge)
  clients/*.json                           routes and market pins the runner has used
  data/<runner_banner>/<block>/<date>.json pull results (proof and dates)
Run: python3 tools/build_registry.py   (rewrites registry/banners.json, prints a summary)
"""
import json, glob, os, re, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(ROOT, p)))

# runner banner key (data dir / client config banner) -> retailers doc id
RUNNER_MAP = {
 'acmemarkets':'acme-markets','albertsons':'albertsons','aldi':'aldi','amazon-fresh':'amazon-fresh-e-comm-stores','bjs':'bjs',
 'bristol-farms':'bristol-farms','brookshires':'brookshire-grocery','central-market':'central-market','citymarket':'city-market',
 'citymarket-api':'city-market','costco':'costco','costco-ic':'costco','costco-online':'costco','cub':'cub-foods','cvs':'cvs',
 'dollargeneral':'dollar-general-popshelf','erewhon':'erewhon','foodcity':'food-city-stores','foodlion':'food-lion',
 'fredmeyer':'fred-meyer','freshthyme':'fresh-thyme-market','gelsons':'gelsons','giant-eagle':'giant-eagle','giantfood':'giant-food',
 'hannaford':'hannaford','harristeeter':'harris-teeter','heb':'heb','hyvee':'hyvee','ingles':'ingles','jewel-osco':'jewel-osco',
 'key-food':'key-food','kingsoopers':'king-soopers','kingsoopers-api':'king-soopers','kingsoopers-ic':'king-soopers','kroger':'kroger',
 'lowesfoods':'lowe-s-foods','marianos':'marianos','marianos-api':'marianos','marketbasket':'market-basket','meijer':'meijer',
 'naturalgrocers':'natural-grocers','plum-market':'plum-market','pricechopper':'northeast-grocers-price-chopper','publix':'publix',
 'raleys':'raleys','ralphs':'ralphs','ralphs-api':'ralphs','randalls':'albertsons-safeway-southern-randall-s-tom-thumb',
 'tomthumb':'albertsons-safeway-southern-randall-s-tom-thumb','safeway':'safeway','safeway-ic':'safeway','samsclub':'sams-club',
 'savemart':'lucky-s-savemart','schnucks':'schnucks','shaws':'shaws','shoprite':'shoprite','smartandfinal':'smart-final',
 'smiths':'smiths','sprouts':'sprouts','staterbros':'stater-bros','stopandshop':'stop-shop','target':'target',
 'thefreshmarket':'the-fresh-market','tops':'northeast-grocers-tops','vons':'vons','walgreens':'walgreens','walmart':'walmart',
 'wegmans':'wegmans','weis':'weis-markets','whole-foods':'whole-foods','wholefoods':'whole-foods','wholefoods-socal':'whole-foods',
 'winco':'winco','winn-dixie':'winn-dixie','woodmans':'woodmans','fareway':None,
}
NO_ECOMM = {'trader-joes','7-eleven-us','circle-k','wawa','sheetz','speedway','quiktrip','maverik','us-defense-commissaries-deca',
            'nex-navy-exchange','grocery-outlet','plaid-pantry','otg-cibo-markets'}
STALE_DAYS = 30

def lane_of(key, d):
    ss = str(d.get('store_set') or ''); url = str(d.get('url_final') or '')
    if key.endswith('-api'): return 'kroger_api', None
    m = re.search(r'retailer ([a-z0-9-]+)', ss)
    if ss.startswith('API zip') and m: return 'instacart', m.group(1)
    if key in ('target', 'walmart'): return 'api', None
    if 'instacart.com' in url or 'shop.sprouts.com' in url or key.endswith('-ic'):
        m2 = re.search(r'/store/([a-z0-9-]+)', url); return 'instacart', (m2.group(1) if m2 else None)
    return 'recipe', None

def main():
    snap = J('registry/source/retailers_snapshot.json'); acv = J('registry/source/acv.json'); excl = J('registry/source/excluded.json')
    today = datetime.date.today()
    reg = {}
    for r in snap:
        rid = r['id']
        reg[rid] = {'id': rid, 'name': r['name'], 'channel': r.get('channel'), 'parent': r.get('parent_company'),
                    'distributor_primary': r.get('dist_primary'), 'distributors': r.get('distributors', []),
                    'doors': r.get('doors') or 0, 'acv_weight': acv.get(rid), 'hq_state': r.get('hq_state'),
                    'states': r.get('states', []), 'counted': rid not in excl, 'excluded_reason': excl.get(rid),
                    'status': 'no_ecomm' if rid in NO_ECOMM else 'unproven', 'routes': [], 'pins': []}
    # pins and declared routes from client configs
    for cf in sorted(glob.glob(os.path.join(ROOT, 'clients', '*.json'))):
        if cf.endswith('.forecast.json'): continue
        C = json.load(open(cf)); mk = C.get('markets', {})
        for rr in C.get('retailers', []):
            rid = RUNNER_MAP.get(rr['banner']) or RUNNER_MAP.get(re.sub(r'-(socal|chicago|denver|boise|houston)$', '', rr['banner']))
            if not rid or rid not in reg: continue
            m = mk.get(rr.get('market'), {})
            pin = {'market': rr.get('market'), 'zip': m.get('zip'), 'store_expect': rr.get('store_expect') or m.get('store_expect'),
                   'lat': m.get('lat'), 'lng': m.get('lng'), 'from_client': C['client_id']}
            if pin['zip'] and not any(p['market'] == pin['market'] for p in reg[rid]['pins']): reg[rid]['pins'].append(pin)
            cfg = {k: rr[k] for k in ('lane', 'slug', 'url', 'template', 'host', 'chain', 'fallback') if k in rr}
            cfg['runner_banner'] = rr['banner']
            reg[rid].setdefault('_cfg', {})[(rr['banner'], rr['lane'])] = cfg
    # proof from pull results
    per = {}
    for f in glob.glob(os.path.join(ROOT, 'data', '*', '*', '*.json')):
        key = f.split(os.sep)[-3]; date = os.path.basename(f)[:10]
        if key in ('diag', 'packshots', 'amazon') or f.split(os.sep)[-2].startswith('diag'): continue
        try: d = json.load(open(f))
        except Exception: continue
        n = len(d.get('houses') or []); ok = n > 0 and not d.get('error')
        lane, slug = lane_of(key, d)
        e = per.setdefault((key, lane), {'last_try': '', 'last_ok': '', 'houses': 0, 'slug': None, 'store_set': None, 'tries': 0, 'oks': 0})
        e['tries'] += 1; e['oks'] += ok
        if date > e['last_try']: e['last_try'] = date
        if ok and date >= e['last_ok']:
            e['last_ok'] = date; e['houses'] = max(n, e['houses'] if date == e['last_ok'] else 0) or n
            e['slug'] = slug or e['slug']; e['store_set'] = str(d.get('store_set'))[:120]
    unmapped = set()
    for (key, lane), e in sorted(per.items()):
        rid = RUNNER_MAP.get(key)
        if rid is None or rid not in reg: unmapped.add(key); continue
        cfg = reg[rid].get('_cfg', {}).get((key, lane), {})
        route = {'runner_banner': key, 'lane': lane, 'slug': e['slug'] or cfg.get('slug'), 'last_ok': e['last_ok'] or None,
                 'last_try': e['last_try'], 'houses_last_ok': e['houses'], 'store_set': e['store_set'], 'tries': e['tries'], 'oks': e['oks']}
        for k in ('url', 'template', 'host', 'chain', 'fallback'):
            if k in cfg: route[k] = cfg[k]
        if e['last_ok']:
            age = (today - datetime.date.fromisoformat(e['last_ok'])).days
            route['state'] = 'proven' if age <= STALE_DAYS else 'stale'
        else: route['state'] = 'failed'
        reg[rid]['routes'].append(route)
    # family inheritance: one recipe covers every banner on the same engine; an untested sister banner is 'family', gate before use
    FAM = [('kroger', lambda b: 'kroger' in (b['parent'] or '').lower(), 'kroger'),
           ('albertsons', lambda b: 'albertsons' in (b['parent'] or '').lower(), 'recipe')]
    for fam, test, lane in FAM:
        donors = [b for b in reg.values() if test(b) and any(r['state'] in ('proven', 'stale') and r['lane'] in (lane, 'kroger_api') for r in b['routes'])]
        if not donors: continue
        for b in reg.values():
            if test(b) and not b['routes'] and b['status'] == 'unproven':
                b['status'] = 'family'; b['family'] = fam; b['family_donor'] = donors[0]['id']
    order = {'proven': 0, 'stale': 1, 'failed': 2}
    for r in reg.values():
        r.pop('_cfg', None)
        r['routes'].sort(key=lambda x: (x.get('fallback', False), order[x['state']], -(x['oks'] or 0)))
        if r['routes']:
            best = r['routes'][0]['state']; r['status'] = best if best != 'failed' else 'failed'
    out = {'built': today.isoformat(), 'stale_days': STALE_DAYS, 'count': len(reg), 'banners': sorted(reg.values(), key=lambda x: x['id'])}
    json.dump(out, open(os.path.join(ROOT, 'registry', 'banners.json'), 'w'), indent=1)
    from collections import Counter
    c = Counter((b['channel'], b['status']) for b in out['banners'] if b['counted'])
    print('registry/banners.json:', len(reg), 'banners;', sum(1 for b in out['banners'] if b['routes']), 'with a runner route')
    for ch in sorted({k[0] or 'None' for k in c}):
        print(' ', ch.ljust(14), {s: c[(ch if ch != 'None' else None, s)] for s in ('proven', 'stale', 'family', 'failed', 'unproven', 'no_ecomm') if c[(ch if ch != 'None' else None, s)]})
    if unmapped: print('  data dirs with no registry banner:', sorted(unmapped))
if __name__ == '__main__': main()
