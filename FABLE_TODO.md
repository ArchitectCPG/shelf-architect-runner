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

## 2026-10-16: KYC APPROVED (Bright Data residential/robots gate lifted; +$5 credit)
- H-E-B: WORKS via homepage -> search box (direct search URL trips H-E-B's own bot page). 60 salsa houses, clean. PINNED unattended: In-store at -> Change store -> #address-input zip -> first 'Select Store'. 77005 = Buffalo Market H-E-B, 65 houses. Added to SG config (houston market).
- CVS: search page loads (Chicago store), parser grabs promo badge "$3 ExtraBucks" as name and results mix in unrelated items; needs CVS card_selector/parser.
- Walgreens: homepage + store finder load, search results page renders empty (second-layer block). Zip typed into store finder did not change store. Parked.
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
