# Running a client through the runner (sandbox, no DB writes)

1. Copy clients/stinkin-good.json to clients/<client_id>.json. Set: brand_terms, competitor_terms, markets (zip + lat/lng each), neighborhoods (id + search term), retailers (banner, lane, market).
2. Lanes: kroger (any Kroger-family banner via host), instacart (slug; any Instacart storefront incl. whitelabel, zip-pinned via graphql), api (walmart, target prebuilt scrapers), recipe (reuse an existing blocks/<template>-salsa.json recipe: safeway, wholefoods, etc.).
3. python3 tools/gen_client_blocks.py <client_id>  (writes blocks_gen/<client_id>/*.json and prints the dispatch list)
4. gh api -X POST repos/ArchitectCPG/shelf-architect-runner/actions/workflows/pull.yml/dispatches -f ref=main -f 'inputs[blocks]=<list>'
5. After the run: git pull; python3 tools/client_report.py <client_id>  (scored table + SG and competitor hits in data/clients_<id>_report.json)

2026-10-13 Stinkin' Good test: 24 blocks (8 retailers x 3 shelves). 20 usable first pass, 22 of 24 after one retry. Open: Walmart returns 0 at Denver 80202 (crawler error on a Walmart page selector; worked at 60615), Whole Foods green chile landed on Montrose instead of the Denver store.

## Amazon lane (added 2026-10-18, sandbox)
Separate from retail by construction: blocks in blocks_gen/<client>/amazon/, results in data/amazon/, scored by tools/amazon_report.py. client_report, mapper and landing never read that folder; Amazon rows never go to retail_entries or the 40/15/20 waterfall (target home later: amazon_comps, which stays a manual audit).
Config: top-level "amazon": {enabled, temperature (shelf_stable | refrigerated | frozen), zip (blank = national), limit, brand_check}. The lane runs only when temperature is shelf_stable; a neighborhood can carry its own "temperature" to override. Otherwise the generator writes SKIPPED.txt and no blocks.
Dispatch the AMAZON: line that gen_client_blocks.py prints. Report: python3 tools/amazon_report.py <client> (pack count, $/unit, bought-past-month as Amazon's own floor, category BSR, sponsored vs organic). No revenue estimate is derived from BSR; a sized prize still means Helium 10 by the month, entered by hand.
First run 2026-10-18 (Pura): 4 of 4 blocks, 46 to 48 listings each, 80 to 98% relevant. Stinkin' Good gated off (refrigerated).
