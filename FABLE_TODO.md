# Fable TODO: Shelf Architect runner (sandbox, no DB writes until Steve OKs)

Context: claude/runner/README.md has the sweep table and design. Repo ArchitectCPG/shelf-architect-runner. Dispatch: gh api -X POST repos/ArchitectCPG/shelf-architect-runner/actions/workflows/pull.yml/dispatches -f ref=main -f 'inputs[blocks]=all'. Results are committed to data/<retailer>/<block>/<date>.json (job logs and artifacts are not readable from Claude).

## 1. Store pinning (the core problem)
Only Whole Foods pins a store. Others land on the exit IP's store (Idaho Albertsons, Ohio Safeway, Missouri Target, Michigan Meijer).
- Test Bright Data geo targeting on the browser username beyond -country-us (state or city suffix for Illinois). If supported this fixes most banners at once.
- Otherwise per-banner set-store recipes: Target (Ship to / store picker), Meijer, Instacart banners (Pickup zip), Kroger family and Albertsons family (store locator by zip), Sprouts (store 505 vs Chicago store).
- Walmart: zipcode via Bright Data Scraper API from the runner.
- Acceptance: store_set equals a Chicago-area store for every banner, or the banner is flagged "store drift, not comparable".

## 2. Reliability
- Whole Foods regressed (store did not set, 0 houses). Find the flaky step, add a retry or verify-and-redo loop on the Update Location flow.
- H-E-B goto blocked: test with Unlocker lane or leave attended.
- Add per-block retry (re-run whole block once if houses < threshold or store_set empty).

## 3. Extraction quality
- Kroger and Walmart names pick badges ("Price Cut", "Now$397", language banner). Prefer a name from the product link text or an h-tag/aria-label, fall back to longest clean line.
- Albertsons and Jewel-Osco return 1 card (lazy load). Try HTML route (Bright Data scrape_as_html) or a card_selector plus scroll-until-stable.
- Instacart banners (Safeway, Publix): names garbled by promo lines. Add explicit card selector.
- Score every banner: houses >= 20, clean names >= 90%, store_set present.

## 4. Universe growth (sandbox)
- Sweep now covers about 37 banners on the salsa neighborhood. Score the new 26, mark each: works / needs recipe / blocked (Costco needs Bright Data KYC).
- Pull the full ~241 banner list from the DB (read only) and bucket by platform (Kroger, Albertsons, Instacart, Ahold, Walmart, Hy-Vee, independents) so one recipe covers a whole family.
- Extend beyond salsa to the other neighborhoods in a client matrix, using search term and collection routes.

## 5. Hybrid lanes decision
- Compare per banner: Bright Data prebuilt scraper with zipcode vs runner vs Claude in Chrome. Pick one lane per banner, record in the retailer docs.
- Cost per full sweep (credits used vs $8/GB), time saved vs current process, what is lost (member pricing, logged-in assortment, attended-only banners).

## 6. Only after the above scores well
- Draft a pull_process change (app_meta/pull_process, onboarding_runbook, pull_prompt_template) for Steve's OK, with a backup zip for the Drive folder. Do not write to the DB before his OK.

## Housekeeping
- Rotate the Bright Data API token that appeared in chat. Delete redundant zone scraping_browser1. Costco KYC. Ed email draft composed, not sent.

## Sweep 2 result (2026-10-07 ~2 PM CT, 37 banners, salsa)
Got products: whole-foods 23 (Chicago 60615 pinned, recovered), sprouts 40, target 40, hyvee 132 (suspect: returns site-wide items like ground chuck, not salsa), foodlion 33 (names are search-suggestion junk), publix 37 (some non-salsa items), fredmeyer 23, walmart 26, safeway 12, acmemarkets 8, randalls 9, tomthumb 9, shaws 6, jewel 5, albertsons 1.
Zero products, no error (page loaded, extractor found nothing; need recipe/selector): aldi, amazon-fresh, freshthyme, giant-eagle, meijer (regressed from 45), naturalgrocers, ralphs, shoprite, smiths, thefreshmarket, vons, wegmans, schnucks (store Rockford Pl set, 0 houses).
Errors: bjs, heb, stopandshop, walgreens (goto blocked or restricted), cvs (tunnel failed), dollargeneral (timeout), harristeeter (CDP websocket error, transient), kroger (execution context destroyed on evaluate, page redirect, add retry), samsclub (context closed).
Patterns: Albertsons family (acmemarkets, randalls, tomthumb, shaws, vons, jewel) all render a few cards, so one Albertsons-family fix (scroll until stable or HTML route) unlocks 6 banners. Kroger family (kroger, fredmeyer, ralphs, smiths, harristeeter) same: one fix, 5 banners. Zero-product pages are probably bot walls or shells, check the saved png/txt in data/<retailer>/ before writing recipes.

## More banners to add (after the family fixes)
Club/value: Costco (KYC first), Grocery Outlet, Lidl, WinCo, Smart & Final, Save A Lot. Regional: Stater Bros, Raley's, Price Chopper, Weis, Harps, Brookshire's, Ingles, Lowes Foods, Piggly Wiggly, Bashas', Fareway, Dierbergs, Mariano's/Pick 'n Save, Big Y. Specialty: Erewhon, Earth Fare, Fairway, Gelson's. Mass/dollar/c-store: Dollar Tree, Family Dollar, Five Below, 7-Eleven, Casey's. Online: Thrive Market, Amazon main, FreshDirect. Best source: read-only pull of the ~241 banner list from the Shelf Architect DB, bucket by platform, generate blocks per family.

## HANDOFF (2026-10-07 2 PM CT)
State: repo ArchitectCPG/shelf-architect-runner main is clean and pushed, 37 salsa blocks, workflow works end to end (validate, clear stale data, 3 parallel, single collector commit). Latest data committed under data/. No Shelf Architect DB writes happened, so no backup zip is due. Start with section 1 (geo suffix test) and the two family fixes (Albertsons, Kroger). Sonnet can run sweeps and score; Fable for store pinning design and the hybrid decision.
