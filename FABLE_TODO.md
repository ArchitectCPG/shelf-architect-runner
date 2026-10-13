# Fable TODO: Shelf Architect runner (sandbox, no DB writes until Steve OKs)

## START HERE (next session)
Read this file top to bottom, then README.md. Repo ArchitectCPG/shelf-architect-runner main is clean. Dispatch: gh api -X POST repos/ArchitectCPG/shelf-architect-runner/actions/workflows/pull.yml/dispatches -f ref=main -f 'inputs[blocks]=all' (or a comma list of blocks/*.json). Wait ~6-10 min, git pull, score data/*/*/<date>.json. Steve wants plain-words, step-by-step help on his own loose ends (section at bottom).

Order of work now:
1. Map remaining banners live in Chrome with Steve (2-3 min each, same pattern as the Kroger/Albertsons/Meijer work: open the store picker, type zip, pick first store, confirm): publix.com, hy-vee, giant eagle, food lion, stop & shop, wegmans, aldi, sprouts.com (own site, not Instacart), fresh thyme. Encode as blocks with store_js.
2. Full rescore of all blocks, score table into README.md.
3. Widen toward the ~241 list (read the DB read-only, bucket by platform, generate blocks per family).
4. Hybrid lanes decision and cost/time estimate, then draft the pull_process change for Steve's OK with a backup zip. Not before.
5. Steve's loose ends (bottom of file), walk him through them.

## 2026-10-13 TARGET: root-caused, deprioritized
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
1. Rotate the Bright Data API token that appeared in chat (Bright Data dashboard, account settings, API tokens: create new, delete old). Check nothing in the repo or connector uses the old one.
2. Delete the redundant Bright Data zone scraping_browser1 (keep mcp_unlocker and mcp_browser).
3. Costco: complete Bright Data identity verification (KYC) so Costco can be scraped. Steve does the ID step himself; Claude only guides and never enters IDs or documents.
4. Send the Ed Lavery email (store-location data ask plus how Steve will use the Placer file). Draft was composed earlier, not sent. Re-draft in Steve's voice (steve-voice skill, no em dashes), show it, and send only after his yes.
5. Clean-up check: Bright Data balance (about $54), $5 consumed alert on, auto-recharge off. Confirm nothing is spending unattended.
6. Ask Bright Data (account manager or support chat in the dashboard) to allow these sites that are currently blocked by robots.txt in the Scraping Browser: publix.com, stopandshop.com, heb.com, bjs.com, walgreens.com. Error text to paste: "Requested URL is restricted in accordance with robots.txt. Ask your account manager to get full access for targeting this site (brob)". Until then those 5 banners are attended-only (Publix also pulls via the Instacart storefront, unpinned).

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
