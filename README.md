# Shelf Architect runner
Cloud runner for retailer block pulls. GitHub Actions drives Bright Data's Scraping Browser (remote Chromium) with Playwright:
set a store, search a term, capture houses (SKUs) and prices, commit JSON to `data/`.
- Blocks live in `blocks/*.json` (zip/neighborhood@retailer).
- Secret required: `BRD_BROWSER_PASSWORD` (Bright Data zone `mcp_browser`).
- Run: Actions > retailer-pull > Run workflow (pick a block). Schedule is off until the proof passes.
Output per run: `data/<retailer>/<block>/<date>.json` (+ `.txt` raw page text, `.png` screenshot).
