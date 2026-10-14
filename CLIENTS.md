# Running a client through the runner (sandbox, no DB writes)

1. Copy clients/stinkin-good.json to clients/<client_id>.json. Set: brand_terms, competitor_terms, markets (zip + lat/lng each), neighborhoods (id + search term), retailers (banner, lane, market).
2. Lanes: kroger (any Kroger-family banner via host), instacart (slug; any Instacart storefront incl. whitelabel, zip-pinned via graphql), api (walmart, target prebuilt scrapers), recipe (reuse an existing blocks/<template>-salsa.json recipe: safeway, wholefoods, etc.).
3. python3 tools/gen_client_blocks.py <client_id>  (writes blocks_gen/<client_id>/*.json and prints the dispatch list)
4. gh api -X POST repos/ArchitectCPG/shelf-architect-runner/actions/workflows/pull.yml/dispatches -f ref=main -f 'inputs[blocks]=<list>'
5. After the run: git pull; python3 tools/client_report.py <client_id>  (scored table + SG and competitor hits in data/clients_<id>_report.json)

2026-10-13 Stinkin' Good test: 24 blocks (8 retailers x 3 shelves). 20 usable first pass, 22 of 24 after one retry. Open: Walmart returns 0 at Denver 80202 (crawler error on a Walmart page selector; worked at 60615), Whole Foods green chile landed on Montrose instead of the Denver store.
