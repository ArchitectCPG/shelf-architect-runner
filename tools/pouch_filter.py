#!/usr/bin/env python3
"""Pre-landing on-neighborhood filter for the Vosges chocolate-bites-pouch landing (Fable, 2026-11-06).
Writes mapped/<client>/filtered/*.json (rows to cap and land) and filter_summary.json. Off-neighborhood bars and excluded items stay in mapped/retail_entries."""
import json,glob,os,re,sys,shutil,collections
cid=sys.argv[1]; md=f'mapped/{cid}'
EXC=re.compile(r"chips?\b|baking|cocoa powder|hot (cocoa|chocolate)|syrup|sauce|protein|granola|cereal|\boats?\b|oatmeal|ice cream|frozen|cookie|brownie|cake|spread|drink|pudding|coffee|espresso|\btea\b|candle|\bdog\b|\bpet\b|mushroom|gumm(y|ies)|licorice|marshmallow|cracker|popcorn|trail mix|biscuit|cocoa mix|\bmix\b|chocolate milk|\bmilk,|ultra-filtered|almond milk|oat milk|\bmalk\b|creamer|kefir|yogurt|shake|smoothie|powder|blend|croissant|chicken|tacos?|jalape|pizza|bread|muffin|donut|pastry|\bpie\b|cheesecake|waffle|pancake|\bcones?\b|supplement|vitamin|collagen|melting|cheerios|pop.?tarts|dates?\b(?!.*chocolate)|\bnuts?\b(?!.*chocolate)|fudge bar|\bmilk\b(?!\s*chocolate)|\bwhey\b|sausage|gravy|pan+ettone|bakery|dairy|family farms?|egg bites|bagel|cannoli|sprinkles|zipper|coca.?cola|soda|morsels|\bsleep\b|\bcalm\b|\d+\s?mg\b|chocolate chip|\bchunks\b|jerky|salami|cheese|hummus|noodle|rice\b|bean|soup|pasta|salad|sushi|sandwich|wrap\b|burrito|empanada|dumpling|potato|fries|veggie|vegetable|fruit snack|\bmilk\b(?!\s*chocolate)",re.I)
POUCH=re.compile(r"truffle|bonbon|bites?|squares?|minis?|thins?|bark|pieces|wrapped|share|stand.?up|pouch|\bbag\b|gems|drops|melts|cups?|clusters?|balls?|covered|dipped|enrobed|nuggets|morsels|snack|candy|family|coins|assort|promises|kisses|eggs?|hearts?",re.I)
BAR=re.compile(r"\bbars?\b|\b\d{2}%|single origin|cacao\b|tablette",re.I)
CHOC=re.compile(r"chocolat|cacao|cocoa|truffle|bonbon|\bbark\b|toffee|fudge|praline|nonpareil|m&m|m&amp;m|kisses|reese|snickers|twix|kit.?kat|lindor|lindt|ghirardelli|hershey|\bdove\b|cadbury|milky way|godiva|ferrero|rocher|sugarfina|maltesers|whoppers|rolo|twizzler|brookside|barkthins|unreal|justin|hu\b|tony'?s|chocolonely|sixlets|raisinets|buncha crunch|crunch bar|mounds|almond joy|york peppermint|heath|skor|butterfinger|baby ruth|3 musketeers|caramello|take 5|whatchamacallit|payday|lion\b|aero\b|kinder|toblerone|ritter|loacker|pirouline|violet crumble|see'?s|russell stover|whitman|\bchoc\b|skinnydipped|skinny dipped|chocolove|muddy bites|st\. amour|harken|alter eco|theo\b|taza|raaka|endangered species|lily'?s|divine|green & black|compartes|chuao|venchi|lake champlain|moonstruck|jcoco|seattle chocolate|guittard|valrhona|tcho|hu kitchen|seed and bean|perugina|baci",re.I)
rows={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(md+'/retail_entries/*.json')}
keep={};why=collections.Counter()
for k,r in rows.items():
    if r['neighborhood']!='chocolate-bites-pouch': why['other neighborhood']+=1; continue
    t=r['brand']+' '+r['product_name']
    if r['brand']=='Unbranded': why['unbranded, held']+=1; continue
    if EXC.search(t): why['excluded, not the shelf']+=1; continue
    if not CHOC.search(t): why['no chocolate word, not the shelf']+=1; continue
    if not POUCH.search(t) and (BAR.search(t) or ((r.get('size_oz') or 0)<=3.6 and not r.get('count'))): why['off-neighborhood bar, waits for the bars term']+=1; continue
    keep[k]=r; why['kept']+=1
shutil.rmtree(md+'/filtered',ignore_errors=True); os.makedirs(md+'/filtered')
for k,r in keep.items(): json.dump(r,open(f'{md}/filtered/{k}.json','w'))
json.dump(dict(why),open(md+'/filter_summary.json','w'),indent=1); print(dict(why))
