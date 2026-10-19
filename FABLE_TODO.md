# Fable TODO: Shelf Architect runner (sandbox, no DB writes until Steve OKs)

## START HERE (next session)
Read this file top to bottom, then README.md. Repo ArchitectCPG/shelf-architect-runner main is clean. Dispatch: gh api -X POST repos/ArchitectCPG/shelf-architect-runner/actions/workflows/pull.yml/dispatches -f ref=main -f 'inputs[blocks]=all' (or a comma list of blocks/*.json). Wait ~6-10 min, git pull, score data/*/*/<date>.json. Steve wants plain-words, step-by-step help on his own loose ends (section at bottom).

Order of work now:
1. Map remaining banners live in Chrome with Steve (2-3 min each, same pattern as the Kroger/Albertsons/Meijer work: open the store picker, type zip, pick first store, confirm): publix.com, hy-vee, giant eagle, food lion, stop & shop, wegmans, aldi, sprouts.com (own site, not Instacart), fresh thyme. Encode as blocks with store_js.
2. Full rescore of all blocks, score table into README.md.
3. Widen toward the ~241 list (read the DB read-only, bucket by platform, generate blocks per family).
4. Hybrid lanes decision and cost/time estimate, then draft the pull_process change for Steve's OK with a backup zip. Not before.
5. Steve's loose ends (bottom of file), walk him through them.

## 2026-10-13 PM: API LANE LIVE (Target solved properly)
Steve rotated the Bright Data API key (twice; both old keys die 20-10) and put the new one in GitHub as BRD_API_TOKEN. Loose end 1 DONE. The runner now has an API lane: a block with an "api" field calls Bright Data's prebuilt scraper (dataset trigger -> poll -> download) instead of the browser. Job timeout raised 15->45 min (scrapers run 10-25 min).
- Target: API lane VERIFIED. 48 houses at zip 60615, with brand, UPC (item_number), stock status. Richer than any browser pull. blocks/target-salsa.json is now api-lane.
- Walmart: blocks/walmart-salsa.json api-lane (dataset gd_m693oc1r1gebnayxq, keyword + zip_code), first full run in flight.
- This is the lane for any banner with a prebuilt scraper where the site blocks the browser (search_scrapers tool or dashboard lists 1,200+ sites; check Publix/H-E-B/Walgreens there too before waiting on the robots.txt unblock).

## 2026-10-17 PM: open-ten pass
- Wegmans: WORKS unpinned (search?query=, 91 houses, store = IP default). wegmans.com/stores has NO zip box, it is a state/city list of store-name links. Pin = click store by name (add store_name to client config for wegmans). Parser: strip leading "Quantity of " from names.
- Smart & Final: WORKS unpinned (Mi9 platform; store id in URL /sm/pickup/rsid/<id>; 522 Montebello default). Pin = rsid lookup by zip. 31 houses.
- Giant Eagle: PARKED. Driving the "Select a Store" modal (type zip into input[name=zipcode]) closes the browser context both times; bot defense. Attended-only if a client needs it.
- Ahold (Stop & Shop, Food Lion, Giant Food, Hannaford): still on "Maintenance" page 10/17. Recheck weekly; one recipe for all four when back.
- scraping_browser1 zone: API key lacks delete permission (403, correct scope). Steve deletes in dashboard or leaves it. Runner gained api_call step (generic Bright Data API).
- Count vs MULO 94: 27 pulling (added Walgreens, Wegmans, Smart & Final today).

## 2026-10-16: KYC APPROVED (Bright Data residential/robots gate lifted; +$5 credit)
- H-E-B: WORKS via homepage -> search box (direct search URL trips H-E-B's own bot page). 60 salsa houses, clean. PINNED unattended: In-store at -> Change store -> #address-input zip -> first 'Select Store'. 77005 = Buffalo Market H-E-B, 65 houses. Added to SG config (houston market).
- CVS: search page loads (Chicago store). Parser now skips ExtraBucks/stock lines. Remaining issue: cvs.com 'salsa' search leads with sponsored beauty items and lazy-loads the rest (109 products, ~20 captured); needs scroll/pagination work. Low priority unless a drug-channel client.
- Walgreens: SOLVED 2026-10-17. Direct results URL is refused from the cloud browser; typing into the homepage search box works (38 houses). Store pin: 'Nearest store' -> zip box -> first 'Shop this store' -> 5036 S Cottage Grove Chicago. Unattended, attempts=2.
- BJ's: Akamai "Access Denied" on homepage intermittently (loaded once, denied next). Parked.
- Stop & Shop: site down (Ahold outage, same as Food Lion). Retry later.
- Loose end 6 (robots unblock request) is DONE via KYC. Compliance call that was scheduled for Friday did not block approval.

## 2026-10-14 AM: Costco / H-E-B / Whole Foods / Kroger
- Cadence rule from Steve: one run per prospect, monthly max on retainer. No cron. Prospect run is the default.
- Costco: costco.com search works in the browser lane with no KYC (22 houses, national online pricing, flagged as such in store_set). Warehouse-local pricing only via sameday.costco.com (Instacart) which requires a member login -> skip. Bright Data KYC is NOT needed for costco.com browser pulls.
- H-E-B: blocked in BOTH browser and unlocker lanes until Bright Data KYC ("not available for immediate residential (no KYC) access"). KYC is the one action that unlocks H-E-B, Publix.com, Stop & Shop, BJ's, Walgreens. Steve does the KYC form himself.
- Whole Foods: search?text= page, click "Update Location" button, #zipCode, Apply. The location bar only renders on some loads, so the block uses attempts=3 (new runner feature: rerun recipe in a fresh page until store_set matches store_expect). Verified 60615 pinned.
- Kroger API: DECIDED 2026-10-14 NOT to use it. Kroger developer Terms 4a (no competitive/comparative analysis targeting Kroger) and 5e (no databases/permanent copies/redistribution) cut against Shelf Architect use; Steve's app registration was approved with his stated use, but 10c makes the written Terms the whole agreement. Gain over the browser lane is marginal (UPC, store id). Kroger banners stay on the Bright Data browser recipes. Lane code removed; app 'ShelfArchitect' left untouched (no secret refresh).
- BUG FIXED: {{term}} substituted block.neighborhood instead of block.term (SG searches ran as "green-chile"). Now block.term first.

## 2026-10-13 night: STINKIN' GOOD CLIENT TEST (see CLIENTS.md)
Client = one config file (clients/stinkin-good.json). tools/gen_client_blocks.py builds blocks, tools/client_report.py scores. 24 blocks: King Soopers (native + Instacart), City Market, Walmart, Target, Sprouts, Safeway, Whole Foods x green chile / queso / tamales, Denver 80202 and Grand Junction 81501.
Result: 22 of 24 usable. SG found at City Market (Schlereth's Stinkin' Good Green Chile Sauce $6.99 and $6.49) and King Soopers via Instacart ($7.99 vs $6.99 SRP, Instacart markup). Not seen on native King Soopers search page 1 (verify). Competitors (505, Del Real, Santiago's, Hatch) all appear; matcher is loose, tighten before using the numbers.
Open: Walmart 0 houses at 80202 (works at 60615; try another Denver zip or store_id), Whole Foods green chile store drift (Montrose), Fresh Thyme not on Instacart at 60563 (ShopCollection empty), Costco blocked (KYC), SG tamales not found anywhere.

## 2026-10-13 evening: INSTACART WHITELABEL SOLVED (Sprouts + Aldi pinned, unattended)
Method: skip the store-picker UI. Load the site, then (js_houses step, src/instacart_api.js) call Instacart's own graphql from inside the page: DefaultShop(zip, lat/lng) -> shop id, SearchResultsPlacements(term, shop) -> item ids, Items(ids) -> name/brand/size/price/stock. Runner overrides page houses with these.
- Sprouts zip 60563: shop 4117, location 11199, 120 houses with brand + stock. Aldi zip 60615: shop 273531, location 12268, 120 houses.
- Same 3 persisted query hashes work on any Instacart whitelabel domain, so this should cover most of the 146 independents: per banner only the domain/slug, zip and lat/lng change.
- Known gaps: (1) zoneId is taken from the page's IP-default calls, not the target zip (looks like it only affects ads; verify prices vs a manual check once). (2) Results include adjacent items (chips, guac); filter at scoring. (3) Human store name not yet resolved from location id (GetRetailerLocationAddress query, hash not captured yet). (4) Hashes can rotate when Instacart deploys; if DefaultShop/Items start returning errors, recapture with the netlog step.
NEXT: probe independents with this method (Fresh Thyme first), Wegmans + Giant Eagle capture, full rescore.

## 2026-10-13 late PM: Bright Data catalog checked (1,859 datasets, listed via runner api_list/api_get modes)
- Prebuilt scrapers exist for Sprouts, Instacart, H-E-B, Stop & Shop, Walgreens, BJ's, Costco, CVS, Sam's, Dollar General, Meijer, Safeway, Albertsons, Whole Foods, Kroger.
- BUT all of those (except Target gd_ltppk5mx2lp0v1k0vo and Walmart gd_m693oc1r1gebnayxq, already live) take a PRODUCT URL as input, no keyword and no zip. Kroger.com has a zip_code output field only. So they do NOT solve store pinning or search discovery. Usable only as a detail lane once product URLs are known (they bypass the robots.txt block for H-E-B, Stop & Shop, Walgreens, BJ's, Costco).
- Runner modes added: block.api_list (catalog) and block.api_get (list of API paths). Diag blocks removed.
- Sprouts/Aldi (Instacart whitelabel) pinning still open; next idea: capture the whitelabel's own graphql call for set-postal-code and replay it via page fetch.

## Target browser recipe (superseded by API lane, kept for reference)
Confirmed (not a timing/selector bug): Target's zip-lookup inside the store-picker drawer returns a persistent server-side error in Bright Data's cloud browser - "We're sorry, something went wrong. Please try again." - reproduced 4x in a row on a fresh page load, retries do not clear it. Same flow works instantly in Steve's real Chrome, so this reads as anti-bot/proxy-IP blocking on that one endpoint, not something a wait or selector fix solves.
Fix applied: target-salsa.json no longer tries to pin a store (was throwing and failing the whole block after a 6-loop timeout). It now pulls Target's IP-default store unpinned, flags it plainly in store_set, and does not fail. Verified: 47 clean salsa houses, no error.
Net: Target is back to producing data, just not Chicago-pinned. Leave as-is unless Steve wants to spend more on it - options if revisited: Bright Data's prebuilt Target scraper, or Target's separate store-locator page instead of the drawer.

## 1. Store pinning (the core problem) - mostly solved
Kroger platform (7/7), Albertsons platform (8/8), Meijer: pinned and unattended. Target: unpinned by design now (see above). Walmart: mapped live, not yet verified unattended. Instacart banners: no unattended path, need retailer-owned sites instead (see below).

## 2. Reliability
- Add per-block retry (re-run whole block once if houses < threshold or store_set empty).
- Watch for Bright Data no_peer/502 spikes; goto already retries on them.

## 3. Extraction quality
- Text-fallback parser plus reload-once-if-<5-houses is working well across the Kroger/Albertsons families. Revisit badge-picking names (Kroger/Walmart) only if it scores badly on full rescore.

## 4. Universe growth (sandbox)
- Sweep covers 37 banners on the salsa neighborhood now, 15 with confirmed unattended store pinning.
- Pull the full ~241 banner list from the DB (read only) and bucket by platform (Kroger, Albertsons, Instacart, Ahold, Walmart, Hy-Vee, independents) so one recipe covers a whole family.
- Extend beyond salsa to the other neighborhoods in a client matrix, using search term and collection routes.
- More banners to add once the above lands: Costco (KYC first), Grocery Outlet, Lidl, WinCo, Smart & Final, Save A Lot, Stater Bros, Raley's, Price Chopper, Weis, Harps, Brookshire's, Ingles, Lowes Foods, Piggly Wiggly, Bashas', Fareway, Dierbergs, Big Y, Erewhon, Earth Fare, Fairway, Gelson's, Dollar Tree, Family Dollar, Five Below, 7-Eleven, Casey's, Thrive Market, Amazon main, FreshDirect.

## 5. Hybrid lanes decision
- Compare per banner: Bright Data prebuilt scraper with zipcode vs runner vs Claude in Chrome. Pick one lane per banner, record in the retailer docs.
- Cost per full sweep (credits used vs $8/GB), time saved vs current process, what is lost (member pricing, logged-in assortment, attended-only banners).

## 6. Only after the above scores well
- Draft a pull_process change (app_meta/pull_process, onboarding_runbook, pull_prompt_template) for Steve's OK, with a backup zip for the Drive folder. Do not write to the DB before his OK.

## Instacart banners - re-routed, not store-pinnable via Instacart
Safeway, Publix, Fresh Thyme, Sprouts (via Instacart) hit a login wall setting a delivery/zip address; zip_code URL param is ignored. Use each retailer's own branded site instead (publix.com, safeway.com are already Albertsons-family-pinned; sprouts.com and freshthyme need their own live mapping, see "Order of work" above).

## Design rule confirmed
store_zip is per banner per market, not one universal zip. Zips in use: 60615 (Chicago banners), 45202 kroger, 97202 fredmeyer, 90024 ralphs, 84101 smiths, 28202 harristeeter, 83702 albertsons, 90210 vons, 94110 safeway, 19103 acme, 02116 shaws, 77005 randalls, 75205 tomthumb.

## STEVE'S LOOSE ENDS (Steve needs hand-holding on these; walk him through one at a time, plain steps, exactly what to click and paste, no jargon)
1. DONE 2026-10-13: Bright Data API key rotated, new key lives only in GitHub secret BRD_API_TOKEN, old keys expire 20-10-2026.
2. Delete the redundant Bright Data zone scraping_browser1 (keep mcp_unlocker and mcp_browser).
3. Costco: complete Bright Data identity verification (KYC) so Costco can be scraped. Steve does the ID step himself; Claude only guides and never enters IDs or documents.
4. Send the Ed Lavery email (store-location data ask plus how Steve will use the Placer file). Draft was composed earlier, not sent. Re-draft in Steve's voice (steve-voice skill, no em dashes), show it, and send only after his yes.
5. Clean-up check: Bright Data balance (about $54), $5 consumed alert on, auto-recharge off. Confirm nothing is spending unattended.
6. (Optional now; check prebuilt scrapers first.) Ask Bright Data to allow these sites that are currently blocked by robots.txt in the Scraping Browser: publix.com, stopandshop.com, heb.com, bjs.com, walgreens.com. Error text to paste: "Requested URL is restricted in accordance with robots.txt. Ask your account manager to get full access for targeting this site (brob)". Until then those 5 banners are attended-only (Publix also pulls via the Instacart storefront, unpinned).

## 2026-10-13 PM (Sonnet 5.5): banner mapping via cloud diagnostics, no Chrome needed
Method: the runner dumps each site's picker (dump/js steps) and I read the committed JSON. No live browser sessions needed.
- Hy-Vee: PINNED unattended (Sycamore IL, 61 houses). Flow: store-change button -> type zip in "City, State or Zip Code" -> first "Select" -> reload search.
- Sprouts (own shop.sprouts.com, Instacart whitelabel): Change store -> Edit -> zip box -> "Set as my store" list. The zip box ignores scripted typing and the visible input could not be targeted (tabindex/hidden ios input trap). Parked: pulls UNPINNED (default store, flagged). Aldi shop.aldi.us is the same Instacart whitelabel, same fix will serve both.
- Target and Walmart: use Bright Data prebuilt scrapers with a zip field instead of recipes. Target tested with 60615: clean records (brand, price, stock). Walmart "products zipcodes" scraper (gd_m693oc1r1gebnayxq, keyword + zip_code) test was still running. These need a runner lane (Actions calling the Bright Data API), not a block file.
- Wegmans: search works via /shop/search?query=, picker input is "Enter City or Zip" then "Select"; drawer text not yet captured. Giant Eagle: "Select a Store" opens a React modal with FindYourStore input; store list not yet captured.
- Publix, Stop & Shop, H-E-B, BJ's, Walgreens: blocked by Bright Data robots.txt policy (see loose end 6). Food Lion: site is down for maintenance (status page says use Instacart).
- Universe: all 241 banners bucketed in UNIVERSE.md. 146 independents need a one-time probe; most are likely Instacart whitelabel (fix Sprouts/Aldi once, unlock many).
NEXT (Sonnet is fine): (1) Instacart whitelabel picker fix (Sprouts, Aldi, then probe independents), (2) Wegmans + Giant Eagle drawer capture, (3) add Bright Data API lane for Target and Walmart, (4) full rescore into README.

## Prior session logs (kept for reference, most-recent decisions above supersede)

### Sweep 2 result (2026-10-07 ~2 PM CT, 37 banners, salsa)
Got products: whole-foods 23 (Chicago 60615 pinned, recovered), sprouts 40, target 40, hyvee 132 (suspect: returns site-wide items like ground chuck, not salsa), foodlion 33 (names are search-suggestion junk), publix 37 (some non-salsa items), fredmeyer 23, walmart 26, safeway 12, acmemarkets 8, randalls 9, tomthumb 9, shaws 6, jewel 5, albertsons 1.
Zero products, no error (page loaded, extractor found nothing; need recipe/selector): aldi, amazon-fresh, freshthyme, giant-eagle, meijer (regressed from 45), naturalgrocers, ralphs, shoprite, smiths, thefreshmarket, vons, wegmans, schnucks (store Rockford Pl set, 0 houses).
Errors: bjs, heb, stopandshop, walgreens (goto blocked or restricted), cvs (tunnel failed), dollargeneral (timeout), harristeeter (CDP websocket error, transient), kroger (execution context destroyed on evaluate, page redirect, add retry), samsclub (context closed).

### 2026-10-12 session (Fable, Steve light on data)
DONE: (a) Geo test: -country-us-state-il connects but does NOT pin a store (Target landed Indiana 46516, Meijer still Michigan); -city-chicago ignored (SC). Verdict: proxy geo cannot pin stores, each banner needs a set-store step in its own UI. (b) Extractor: new text-fallback parser plus reload-once when <5 houses. Albertsons 1->49, Jewel 5->43, Vons 0->39, Kroger 0->184, Ralphs 0->28, Safeway 0->25, Walmart 26->67, names clean. (c) Aldi URL -> new.aldi.us/results?q= (still 0, check png).

### 2026-10-13 store pinning diagnostics (6 passes)
Kroger/Meijer/Target/Walmart/Albertsons/Instacart selector notes that fed the live-mapping session below.

### 2026-10-13 LIVE MAPPING RESULT (Chrome session with Steve, 15 min)
Full selector-level recipes for Kroger platform, Albertsons platform, Meijer, Target, Walmart - encoded into blocks/*.json. Runner gained js/store_js/click_sel/type_sel steps plus desktop viewport fix this session.

### HANDOFF 2026-10-13 noon CT (Fable -> Sonnet)
15 of 16 store-pinning blocks confirmed working unattended at handoff; Target was the one holdout, now resolved per the top of this file (deprioritized, not failing).

## 2026-10-17 eve: independents probe (Instacart lane, zip 60615)
- Pull clean (120 houses): Brookshire's, Ingles, Key Food, Market Basket, Schnucks, ShopRite, The Fresh Market, Weis, WinCo, Winn-Dixie (10 of 20).
- Zero or failed: Cub (own Instacart storefront at cub.com, wrong slug), Fareway, Lowes Foods, Save Mart (Swiftly), Tops, Food City, Price Chopper, Natural Grocers, Raley's, Stater Bros (timeouts or not on Instacart at that zip). Recheck slugs or use own platform recipes.
- Lesson: Bright Data allows one domain per browser session (navigate_domains_limit). One goto domain per block.
- Built: tools/normalize.py (brand, regular+promo price, relevance filter) wired into client_report.py. Next: collection route, then DB wiring (needs Fable + backup + Steve's OK).

## 2026-10-17 late: slugs + collection route (Sonnet)
- Instacart slugs that work: cub, food-city, natural-grocers (13 of 20 independents now pull). lucky-supermarkets pulls (that is Lucky, not Save Mart; Save Mart itself is Swiftly).
- Transient (execution context destroyed / tunnel errors, retry): price-chopper, raleys, stater-bros, tops-markets. No Instacart hit: fareway, lowes-foods.
- Collection route built (src/instacart_api.js, COLLECTION const, generator key retailers[].collections {neighborhood_id: slug}). Uses data.collectionProducts.itemIds = full aisle (837 ids at Sprouts condiments-sauces). Hash 374c333a... can rotate. Verified at Sprouts Denver. Full aisles are big: relevance filter does the narrowing.
- Next: retry the 4 transients, then DB mapping design (Fable) and SOP text (Fable).

## 2026-10-17 night: Costco via Instacart (slug costco) WORKS
- SG Denver 80202: green chile 57 houses, queso 123, tamales 74. Finds Stinkin Good Green Chili Pork Sauce 30 oz at $11.49 (warehouse tag $9.99, so Instacart markup ~15%), 505, Hatch, Del Real tamales $20.69.
- Added as retailer banner "costco-ic" in clients/stinkin-good.json. Label price as Instacart quote in any client output. costco.com stays as assortment cross-check; attended member Chrome stays plan B for true warehouse price.
- Retry of Price Chopper, Raley's, Stater Bros, Tops failed again (parked; check their own Instacart storefront domains).

## 2026-10-17 night: brand-check blocks (SG)
- Category searches only load ~50 products, so the client brand can drop out between runs (City Market had it Oct 14, not Oct 16). Fix: neighborhood "brand_only" + retailers[].brand_check in the client config runs a search of the brand name at expected doors. SG result: City Market 4 listings (Green Chili $6.99 x3 incl. Schlereth's naming, Blanco Queso Medium $8.99); King Soopers Green Chili $6.99; Costco-IC Green Chili Pork Sauce $11.49 to $12.43 (Instacart price moves between pulls).
- Rule for DB wiring: SG presence at a door = union of category and brand-check pulls, never one category run alone.

## 2026-10-17 late: SOP draft v78 (pending Steve approve), additions from review
- 72 benchmark read from the 72 instance pull_matrix: 25 retailers, 225 blocks, 135 walked, 776 houses, 18 unattended, 7 attended-only. Runner today covers 16 of those 25 unattended (4 of 72's attended-only now hands-off: Sprouts, HEB, Publix, Natural Grocers); 5 untested small natural; 4 attended (BJ's, Sam's, Giant Eagle, Fresh Thyme).
- Coverage is measured in ACV (doors as proxy until per-banner ACV field exists), not banner count. Runner ~19K of ~25K non-drug doors on the 94 list. Drug 17K doors pulls, parser rough.
- NEW SOP RULE, coverage marker (Steve 2026-10-17): after every client run, Stage 2 report ends with a coverage line: in-scope banners pulled / not found / attended pending, doors and ACV share covered, biggest uncovered ACV named. Then it asks one question: search more banners, or move on to the read. Steve answers; the run is not "done" until he does. Never auto-expand.
- ACV work order: 1 CVS/Walgreens parser, 2 Ahold group recheck, 3 Costco-IC reliability, 4 mid-tail probes (Save Mart, Stater, Tops, Price Chopper, Fareway, Raley's, Lowes), 5 small natural only on client need.

## 2026-10-18 (late Sat): KROGER API RESTORED (Steve decision)
- Steve reversed the Oct 14 decision. Reasoning for SOP: Shelf Architect is category-wide/aggregate pricing; Kroger-specific cuts only when pitching Kroger. Accepted exposure: Terms 5e (stored rows). Kroger Terms 4a read as not applying to aggregate category analysis. Lane code restored (kroger_api), secrets KROGER_CLIENT_ID/SECRET added to repo by Steve.
- Store lookup now: locations near zip (radius 40, no chain filter), match banner in results. chain codes: KINGSOOPERS, CITYMARKET. Stores: King Soopers Union Station (62000115) Denver 80202; City Market 12th St (62000444) Grand Junction 81501.
- API rows carry brand, exact size, UPC. SG own UPCs: 0089351100269 Green Chili, 0089351100270 and 0089351100272 Schlereth's sauce, 0089351100205 Blanco Queso. Browser Kroger lane kept as fallback (retailers[].fallback=true; blocks in blocks_fallback/).
- Text-lane bug (Kroger browser): cards misattributed prices to neighbor names; mapper drops cards whose card_text lacks their own name. Proper fix if browser lane is ever primary again: parse houses_dom.
- Mapper (tools/mapper.py) + diff (tools/diff_report.py): mapped/stinkin-good = 577 rows to land, 18 held (no size), 22 exact-id matches. Dedupe pass vs existing King Soopers/City Market/Safeway rows still to do, then SOP v78 one-page, backup zip, Steve OK, land.

## 2026-10-18 ~00:40: FIRST RUNNER LANDING DONE (Steve approved SOP v78 + landing "Looks good")
- Backup first: shelf-architect-backup-2026-10-18_1.zip in Mac archives/ (23 MB, 1,428 docs, 29 collections, app.html, RESTORE.md). Note: ArtifactData list pages are byte-capped (~2-3 MB), slide collections need several pages.
- app_meta/pull_process is v78: runner_lane key (12 rules from SOP_v78.md), Kroger API decision recorded in Steve's framing, refresh_cadence caveat superseded for runner banners.
- retail_entries: 544 writes in 14 batches (397 new, 75 Kroger rows with hand-pull history folded in, 67 duplicate ids retired, 5 Safeway appends), then 39 noise rows deleted (candy, sausage, crema, peppers, chowder). SG own rows: 9 (King Soopers 4, City Market 4, Costco-IC 1) with UPCs; old kingsoopers_stinkingood_quesoblanco-medium (Mild, $6.99) kept separate from runner Blanco Queso Medium ($8.99), different heat.
- pull_matrix/stinkin-good v7: 34 runner blocks added (route runner-kroger-api / runner-instacart / runner-api / runner-recipe), 11 hand-pulled blocks kept.
- Relevance tightened before landing: per-neighborhood exclude/keep/hard_exclude in clients/stinkin-good.json (queso: no fresco/snacks; green-chile: no tomatoes/beans/meals/etc; tamales: no candy). Still leaky: name-only filtering cannot catch everything, a Fable eyeball of new rows before landing stays in the process.
- Tools: tools/merge_plan.py (heat-aware match, merge_decisions.json), tools/landing.py (batch bodies), c*.json call files under mapped/stinkin-good/landing/ (40 writes each; the tool max is 50).
- KNOWN ODDITY (pre-existing, not touched): ~19 old store-brand rows (Signature Select, Food Lion, Hy-Vee...) carry is_own_brand=true. Looks like an old "retailer own brand" meaning. Fix in a Fable pass with Steve.
- Next: refresh the published Runbook page (claude/runbook-page-generator.py) from v78; browser Kroger lane DOM parser only if the API ever goes away; Pura landing uses the same path.

## 2026-10-18 AM: AMAZON LANE BUILT (Fable, Steve: "always separate from retail, and still depends on temperature state")
- Lane = Bright Data "Amazon products" dataset gd_l7q7dkf244hwjntr0, discover_by keyword, zipcode blank (national). Same trigger/poll code as Target/Walmart; block.api.amazon=true routes output to data/amazon/ and keeps asin, bought_past_month(_text), bs_rank/bs_category, root_bs_rank, sponsored, badge, amazon_choice, prime, seller, coupon, prices_breakdown.
- Separation: own blocks folder, own data folder, own report (tools/amazon_report.py). Retail tools never glob it. Never lands in retail_entries.
- Temperature gate in gen_client_blocks.py: client amazon.temperature must be shelf_stable; per-neighborhood temperature override; SKIPPED.txt otherwise. Pura = shelf_stable (ran), Stinkin' Good = refrigerated (refused, by design).
- Pura result: 4/4 blocks OK. Pura own listings found only in the brand search (10 listings: soda 24pk $34.99 = $1.46/can, 12pk $24.99 = $2.08/can, kids 24pk $26.99 = $1.12, Kids Box 6ct $15.48 = $2.58; BSR 384 in soda subcategory; two listings show 1K and 200 bought last month). Pura absent from page-1 category results for natural soda, kids drinks, hydration (0 of ~140). Category medians per unit: natural soda $1.09, kids drinks $0.53, hydration $1.90 (mixed units, packets vs bottles). Leaders by bought/mo: Spindrift 20pk $0.81/can 30K, San Pellegrino 12pk $1.16 40K, Liquid I.V., Ultima, LMNT 40 to 60K.
- Known rough edges: pack parser is title-based (fixed 12pk/24pk; "20 packets" style still reads as 1); hydration mixes powder packets and RTD, so $/unit needs a form split before it means anything; relevance regex for the brand neighborhood misses "PuraSoda" (no word boundary), harmless.
- NOT DONE, needs Steve: SOP v79 rule 16 (drafted in SOP_v79_DRAFT.md), amazon_comps mapping and landing, app render of bought-past-month. Nothing in the DB.
- Note: a parallel session is running SG competitive markets (Boise, Chicago) and drafting v79 rules 13 to 15 in the same file; keep rule numbers in sync.

## 2026-10-18 09:52 CT: SOP v79 LANDED (Steve "Yes")
- Backup first: shelf-architect-backup-2026-10-18_2.zip (main instance, 21 collections, 1,503 docs, app.html, RESTORE.md). Mac archives folder could not be granted from the cloud session, so the zip was handed to Steve in chat to drop in Desktop/Shelf Architect/archives/ himself.
- app_meta/pull_process now v79: rule 8 amended (runner fills format only where blank), rules 13 storage class, 14 standard banner set, 15 competitive pulls follow competitors, 16 intake lists competitive markets, 17 Amazon lane separate and temperature-gated. The two parallel v79 draft files were merged into one numbering (SOP_v79.md in repo). Published Runbook page republished (v6) from the v79 docs; generator VERSIONS updated in DB.
- No rows landed in this step. The SG competitive-market rows (Boise, Chicago) belong to the session that ran them and land on their own approval.

## 2026-10-18 10:05 CT: STORAGE-CLASS BACKFILL LANDED + SG COMPETITIVE MARKETS PULLED (Sonnet, Steve "Go")
- Mapper (tools/mapper.py) now sets `format` (Frozen / Refrigerated / Shelf-stable) plus `format_source` (kroger-category > name > same-product-elsewhere), blank when no evidence. Landing folds curated `format` first, so hand values always win. SG coverage on the full 594-row map: 376 flagged, 218 blank.
- BACKFILL LANDED: 227 SG retail_entries updated with format + format_source (5 pinned batches, 153 Shelf-stable, 49 Refrigerated, 25 Frozen). Existing format values untouched (373 already had one). 131 runner rows stay blank (no evidence).
- Backup first: shelf-architect-backup-2026-10-18_3-partial-retail-entries.zip in Mac archives/ (all 1,062 retail_entries + pull_process v78 doc; the parallel session's full backup is the _2 zip Steve holds from chat).
- Competitive markets pulled, NOT landed: clients/stinkin-good.json markets boise (83702) and chicago (60615), role competitive. Albertsons Boise pinned to 1650 W State St (38 rows after map, 0 UPC); Jewel-Osco Chicago pinned to 6014 S Cottage Grove (52 rows). Jewel tamales block failed once (page error) and passed on retry. Albertsons at Denver 80202 pinned to an Idaho store (4700 N Eagle Rd): Denver has no Albertsons doors, so it was dropped, which is what led to rule 15.
- Lands next: merge plan vs the 69 Albertsons and 17 Jewel hand-pulled SG rows (text lane, no UPC, only 7 exact-id matches, expect 30 to 50 review items), then Steve reviews, then backup + OK + land.
- QUALITY NOTES: propagated flags can disagree within a family (Santiago's mild 28oz Frozen from Kroger category, Santiago's authentic 28oz Refrigerated same-product-elsewhere); Hatch Valley flame-roasted 24oz propagated Refrigerated; both worth a Fable eyeball. Fillo's Walking Tamales is Shelf-stable at Walmart (listing says so) and Frozen at Kroger/Sprouts: a product can differ by retailer, so propagation is a hint, not a fact.
- Not done: thesis re-cut by storage class (needs Fable read), is_own_brand cleanup on store-brand rows.

## 2026-10-18 10:35 CT: ALBERTSONS (Boise) + JEWEL-OSCO (Chicago) PARTIAL LANDING
- Landed with Steve's OK, 37 writes in 2 atomic batches: 7 price/history updates on exact id matches, 30 new rows (5 Albertsons, 25 Jewel-Osco). Backups: _4-full (before), _5-full (after), both in Mac archives.
- Held (28 rows): truncated names (iced, c-ada, glut-sted, sadaro, chese, teamable, pasteuri-eese), unbranded tamales, Hatch peppers 400 oz size error, Hot Tamales candy, Tamal De truncated. Need name/brand cleanup or Steve's call.
- Pending Steve's picks: 24 fuzzy pairs (17 Albertsons, 7 Jewel). La Victoria vs Hatch Select 4 oz and Ortega vs Signature Select 4 oz are wrong pairs, treat as new rows.
- Fix upstream: runner recipe truncates product names; clean in mapper before next landing.
- Albertsons runner store 1650 W State St (Boise); older hand pulls were 4700 N Eagle Rd.

## 2026-10-18 10:50 CT: ALBERTSONS + JEWEL-OSCO MERGE COMPLETE (Fable, Steve: "your call")
- Second landing, 45 writes in 2 atomic batches: 27 price/history updates (24 fuzzy pairs confirmed minus 3, plus 3 truncated-name rows that matched old rows at identical price), 18 new rows. Backups _5-full before, _6-full after.
- Calls made: La Victoria 4 oz and 505 Green Chile Salsa Medium were NOT the paired old rows, landed as new. Ortega 4 oz "mild can" was a duplicate of the other Ortega 4 oz runner row, dropped. Truncated names reconstructed and verified by price match and pull_url slug (Signature Select "...iced" = fire roasted diced, Hatch Select "Glut...sted" = gluten free fire roasted, "Ea Guadalupana" = La Guadalupana, Tucson = Tucson Tamale, "Bistro 28" kept as brand).
- Jewel unbranded deli items landed as brand "Deli", is_private_label true, format Refrigerated. "Previously frozen" deli tamales set Refrigerated (sold thawed), not Frozen.
- Dropped as out of category: Hot Tamales candy, Hatch New Mexico peppers 25 lb case (400 oz, $37.99, seasonal produce), Signature Select petite diced tomatoes with green chilies. Dropped duplicate: unbranded chicken tamale 3ct (same as chicken tamales 3ct).
- Still held (2): jewel-osco unbranded White Queso 12 oz $3.99 (brand unknown, could be ReadyMeals), "Tamal De Queso Con Rajas" 6ct (brand unclear).
- GO-FORWARD FIX for mapper.py: Albertsons/Jewel grid truncates long titles with "..." but pull_url slugs carry the full name. When product_name contains "..." or an abbreviation pattern, rebuild it from the pull_url slug. Would have eliminated 20 of the 28 holds. Sonnet job.
- Store context: Albertsons runner = 1650 W State St Boise (hand pulls were 4700 N Eagle Rd). Jewel runner = 6014 S Cottage Grove (hand pulls were 2940 N Ashland). Prices matched across stores on every confirmed pair.

## Mapper truncation fix (2026-10-18, Sonnet)
- tools/mapper.py now repairs names containing "..." : (1) /shop/pd/ URL slug, (2) unique head/tail match to a known full name (client seed rows + untruncated names in the same run), (3) otherwise the row is tagged name_truncated=true and routed to held/ (never guessed).
- Tested on the 2026-10-18 SG data: 5 rows recovered (Guadalupana x2, Tamal de Queso con Rajas, Velveeta x2), 19 held. Scope is about 5, not the 20 first estimated.
- Open (needs a recipe change, not the mapper): Albertsons-platform grids return houses_dom=0 and via="text", so full titles never reach the mapper. Next step is a DOM selector for the product title (aria-label/title attr) in the albertsons/jewel recipe, tested live. Until then, truncated rows need a hand call at landing.

## 2026-10-18 11:05 CT: PURA AMAZON COMPS LANDED (Steve "Ok on Amazon")
- amazon_comps: 26 rows set (11 Pura own listings with ASIN, 15 top organic comps by bought-past-month across natural soda, kids drinks, hydration). est_monthly_units carries the bought-past-month badge with est_monthly_units_basis saying so; est_monthly_revenue stays null. pura_own_soda-4pk marked superseded (Pura is live on Amazon as of this pull), kept for history.
- Backup covering amazon_comps before this write: shelf-architect-backup-2026-10-18_2.zip (Steve holds it).
- SA retail hygiene items (is_own_brand on store brands, storage-class corrections) handed to the other session as a prompt; see mapped/stinkin-good/hygiene_review_2026-10-18.md.

## SOP v80 landed (2026-10-18, Fable, Steve "Yes")
- app_meta/pull_process v80: duplicate rule 17 (Amazon lane) removed; new rules 18 hygiene gate, 19 storage-class cut for multi-case categories only (ketchup never mentions it), 20 temperature states at discovery with unseen-case flag. Repo copy SOP_v80.md.
- Runbook page generator now renders runner_lane rules as a fourth SOP section (DB app_meta/runbook_page_generator v3, Project doc claude/runbook-page-generator.py).
- SG hygiene (65 writes), 2 held Jewel rows, 3 storage-class insights all landed today after backup _7-full. Steve: SG thesis proven, work is forward-looking for future clients now.

## Process sync gap closed (2026-10-19, Fable)
- Steve: the 72 scheduled run reported the new rules were not in its SOP. Cause: the 10-18 runner-lane landings (v78, v79, v80) updated main only; 72Chocolate's copy was frozen at 2026-10-14 and EHC's at 2026-10-02. The transfer rule (main first, then every client instance in the same session) was missed on all three landings, including mine.
- Fixed: main pull_process v81 (v80 + write_cadence folded in from 72, a 10-03 lesson that never reached main) and onboarding_runbook v42 (new section: hygiene gate and the storage-class lens, plus write per retailer). Copied to 72Chocolate (pull_process v62, runbook v34 with EHC scrubbed and the syndicated SOP section added) and EHC (pull_process v27, runbook v18 = main). pull_prompt_template already identical. app_meta/instances v9 carries the sync_log. Runbook page republished at v42/v81.
- Standing fix: every future SOP landing ends with the client-instance copies in the same batch, and the instances sync_log line. Add it to the landing checklist in tools/landing.py docs.

## SOP v82: Amazon checklist and section shape (2026-10-19, Fable, Steve "ok, apply")
- Rule 17 rewritten as the nine-step Amazon checklist (gate and window, control, search terms, floors and reviews, ladder test, ticket ceiling, parity, posture, size of prize), integrating the Pura lane run and the 72Chocolate hand audit. New rule 21 section shape (goal line, four stats, own rows on the leaders' ladder, single-line flags, three moves, what-we-don't-know footer) applies to every client-facing section. conventions.section_shape. Runbook v43 plain-English section.
- Synced key by key to 72Chocolate (pull_process v64, runbook v35) and EHC (pull_process v28, runbook v19); instances sync_log v10; runbook page v43/v82.
- Mock of the redesigned Amazon section built with Pura's live data (artifact RgdVtDTLU5Ea7jVMvTsqEk). App change is a Sonnet job after Steve reviews the mock: amazonaudit section render + amazon_comps/amazon_audits field adds (search_term, parent_asin, seller, fulfillment, inventory_note, is_collision; gate_window, search_terms, control_findings, ticket_ceiling, posture, three_moves, unknowns) + lane mapper to emit them.
- Lane gaps the mock exposed: seller of record and parent ASIN not captured by the Bright Data Amazon scraper output as mapped; "prebiotic soda" and "cane sugar soda" terms never run for Pura (soda leaders are September hand entries with no floors).

## Amazon lane brought to SOP v82 rule 17 (2026-10-19, code and config only, no run, no DB writes)
- Scraper (Bright Data Amazon products, gd_l7q7dkf244hwjntr0) DOES return, per the 2026-10-18 Pura run (187 products): asin, parent_asin (differs from asin on 153, so variation family is real), seller (buybox seller, 175 of 187; null on 12), prime, number_of_sellers, availability text (low stock lines like "Only 9 left in stock"), bought_past_month (+text, 165 of 187), bs_rank/bs_category (181), sponsored (31), badge/amazon_choice, rating, reviews, coupon.
- It does NOT return, as mapped: ships_from or any FBA/FBM flag, brand store yes/no, or exact inventory counts beyond the availability text. Earlier note that seller and parent ASIN were "not captured" was wrong: both were captured in the houses; they just were not carried into amazon_comps. pull.mjs now also passes ships_from, seller_url, brand_store_url, delivery through if the dataset ever returns them (unverified, absent in the 10-18 data).
- Fulfillment rule: ships_from if present; else third-party seller plus Prime = FBA (could be Seller Fulfilled Prime, flagged in notes); Amazon.com as seller = first party, null; otherwise null. Brand store stays a manual finding.
- Mapper: new tools/amazon_comps.py (reads data/amazon only, writes mapped/<client>/amazon_comps_candidates.json, no DB). Emits search_term, est_monthly_units with est_monthly_units_basis amazon_badge_floor (null badge stays null, app renders "<50"), parent_asin, seller, fulfillment, inventory_note, bs_rank, sponsored, is_collision. Own = ASIN in client own_asins or title matches product_terms; brand-string-only match lands is_own_brand false, is_collision true. Comps = top 5 organic per search term by floor.
- Pura config: own_asins (10), product_terms, own_brand_label added. Dry run on the 10-18 data: 10 own, 2 collisions, 15 comps. Finding: B0BSRFPP4K (Pura x Unify Co. diffuser refill, seller Pattern.) was landed 10-18 as an own-brand row (pura_pura-beverage_b0bsrfpp4k); it is a collision and needs retiring or flipping when the next landing happens (Steve OK first, curated). Also B0BY2X7HVZ (Kids Box) shows Amazon.com as seller of record, not Live a Little Pura: a control finding.
- Soda terms queued: Pura natural-soda neighborhood now has amazon_extra_terms "prebiotic soda" and "cane sugar soda" (two new blocks from gen_client_blocks.py, named natural-soda--prebiotic-soda and natural-soda--cane-sugar-soda). NOT RUN. One run per prospect, monthly on retainer; Steve decides when.

## Amazon section live in main (2026-10-19, Fable, Steve "move forward")
- Main app republished as version 142 (label "Amazon section, SOP v82 shape") after backup _9-full. renderAmazonAudit rebuilt to the rule 21 shape; new optional fields on amazon_comps (search_term, seller, fulfillment, parent_asin, is_collision, est_monthly_units_basis) and amazon_audits (gate_window, always_on_sku, ticket_ceiling, posture, three_moves, unknowns, control_findings); modals extended; save handlers now carry over fields the form does not show (old set() replaced whole docs). Old-field-only clients still render. Not yet rolled to 72 or EHC instances: flag to Steve first, per his 2026-10-19 rule.
- amazon_comps pura_pura-beverage_b0bsrfpp4k flipped to is_collision true, is_own_brand false (the home-fragrance Pura diffuser).
- Open: Steve to review the live section on Pura (phone); Pura audit doc needs the v82 fields filled by hand (gate_window, ticket_ceiling, posture, three_moves); Kids Box seller of record is Amazon.com, ask Greig; soda terms run when Steve says.
