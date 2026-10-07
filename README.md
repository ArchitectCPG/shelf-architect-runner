# Shelf Architect runner (Bright Data Scraping Browser via GitHub Actions)

STATUS 2026-10-07 1:00 PM CT (supersedes older status): FIRST FULL SALSA SWEEP SCORED. 9 of 11 banners return products. Sandbox only, nothing in the Shelf Architect DB. Sweep paused here by Steve; next step is a Fable session for the hard parts, Sonnet for mechanical fixes.

SWEEP RESULT (run 2026-10-07 17:5x UTC, neighborhood = salsa, requested store zip 60615)
| banner | houses | store it landed on | note |
|---|---|---|---|
| kroger | 38 | none captured | works in browser now; names show "Price Cut" (parser picks promo badge) |
| walmart | 42 | none captured | works; names show "Now$397" and a "Spanish / Espanol" banner row (parser) |
| publix (Instacart) | 30 | 1640 Publix Way | good |
| safeway (Instacart) | 21 | zip 44035 (Ohio) | zip drifts to exit IP |
| sprouts | 33 | store 505 | good names and prices after junk filter v3 |
| target | 39 | zip 65401 (Missouri) | drifts to exit IP |
| meijer | 45 | Alpine (Michigan) | drifts to exit IP |
| albertsons | 1 | 4700 N Eagle Rd (Idaho) | lazy load, only 1 card; needs HTML route or card_selector |
| jewel-osco | 1 | none | same as Albertsons |
| whole-foods | 0 | Ashburn | REGRESSED: passed twice with 60615 and 23-27 houses, this run store did not set and 0 houses. Flaky, re-run and check the Update Location step |
| heb | 0 | none | goto blocked (Bright Data restricted or rate limit); keep attended |

KEY FINDINGS
1. STORE DRIFT is the core problem. Only Whole Foods (when it works) pins a store. Every other banner lands on whatever store matches the random US exit IP. Access is proven, store-comparable pricing is not. Fixes to try: (a) Bright Data geo suffix on the browser username beyond -country-us (try state or city targeting for Illinois), (b) per-banner set-store steps (Target Ship to / store picker, Meijer store picker, Instacart Pickup zip, Kroger and Albertsons store locator), (c) Walmart Scraper API zipcode param from the runner.
2. BUG FIXED: each job uploaded the whole checked-out data/ tree and merge-multiple let stale copies overwrite fresh results. Fix: pull job runs `rm -rf data` before the walk.
3. BUG FIXED: Bright Data "global adaptive rate limit (bucket_rate_limit)" killed goto on Walmart, Publix, H-E-B at max-parallel 4. Fix: goto retries up to 4x with backoff on that error, max-parallel 2. H-E-B still failed, may be a restricted domain.
4. Browser cost note: free credits first, then $8/GB; sweep of 11 pages is a few MB each.

RESUME STEPS
- Dispatch: gh api -X POST repos/ArchitectCPG/shelf-architect-runner/actions/workflows/pull.yml/dispatches -f ref=main -f 'inputs[blocks]=all' (gh workflow run is blocked). Then wait ~6 min, git pull, score data/*/*/<date>.json (retailer, store_set, houses, error). Job logs and artifact downloads are blocked from Claude, read the committed JSON.
- TODO Sonnet-level: fix parser name picker for Kroger/Walmart (skip badges like Price Cut, Now$xxx, language banners), Albertsons/Jewel HTML route or card_selector, rerun Whole Foods.
- TODO Fable-level: store pinning per banner (above), then extend beyond salsa neighborhood, decide hybrid lanes (Bright Data prebuilt scrapers with zipcode where they exist, runner for the rest), then draft a pull_process change for Steve's OK with a backup zip. Not before.
- Open: Costco needs Bright Data KYC. Rotate the Bright Data API token that appeared in chat. Delete redundant zone scraping_browser1. Ed email draft composed, not sent.

RUNNER DESIGN, ACCOUNTS, LANES: unchanged from earlier notes below.

RUNNER DESIGN (pushed to main):
- src/pull.mjs: recipe-driven. Steps: goto (retry on rate limit), wait, dismiss (loose, never fails), click / click_any (EXACT whole-label match; loose "Select" opened a promo panel), fill {placeholder|label|role, value, enter}, search {placeholder, term} (Escape then force-fill, no click), press, scroll. Variables {{store_zip}} {{term}}. Username gets -country-us. Captcha.waitForSolve after each goto. captureStore(store_patterns). extractProducts: price-leaf walk-up, name = longest clean line, junk filter v3. Writes data/<retailer>/<block>/<date>.{json,txt,png}, JSON always written. Exit 1 on error.
- pull.yml: inputs.blocks = comma list or "all"; plan job validates every blocks/*.json then builds matrix; pull jobs (max-parallel 2) clear stale data, walk, upload artifacts; collect job commits ONCE. Cron off.
- Blocks: 11 salsa recipes in blocks/ (all valid JSON now).
WHY: Claude's cloud cannot reach Bright Data (egress allowlist) and the hosted MCP has no browser tools, so browser pulls run in GitHub Actions.
LANES (2026-10-06): Walmart MCP structured tool works (url only; zipcode in Scraper API). Kroger family MCP scrape_as_html works. Albertsons scrape_as_markdown works. Instacart scrape_as_html works (zip drifts). Whole Foods and store-set banners: runner.
ACCOUNTS: GitHub ArchitectCPG, repo shelf-architect-runner (private), secret BRD_BROWSER_PASSWORD set, Claude GitHub App installed. Bright Data zones mcp_unlocker, mcp_browser (runner), scraping_browser1 (redundant). About $54 balance, free credits first, $5 alert on, auto-recharge off.
