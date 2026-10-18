# Pull process SOP v78: the runner lane
Shelf Architect main instance, app_meta/pull_process. Supersedes the "written for the browser route" caveat on refresh_cadence (v77, 2026-10-14). Set by Steve, 2026-10-18. Everything in v77 not touched here stands.

1. **Primary route is the runner.** Bright Data plus GitHub Actions, unattended, one domain per browser session. Attended Chrome is plan B only: mapping a new banner, bot-walled sites, the Costco warehouse tag, a broken recipe.

2. **Cadence.** One run per new prospect. Monthly at most on retainer. No scheduled or daily pulls. The runner never writes to the database on its own; every landing goes through the mapper, a backup zip, and Steve's OK.

3. **Kroger developer API is the primary route for Kroger banners** (Steve, 2026-10-18, reversing 2026-10-14). The reading on record: Shelf Architect is a category-wide view across banners, and Kroger is one column in it. Kroger-specific cuts are made only when building a pitch to a Kroger buyer, which serves Kroger. Terms 4a (analysis targeting Kroger) is read as not applying to that use. Stored rows (Terms 5e) are a known exposure, accepted for small per-client datasets. If the key is ever revoked, the browser recipe is the fallback and nothing else in the process changes. Rows from this route carry the UPC and route runner-kroger-api.

4. **Row identity.** One retailer table in the runner (slug, display name, id prefix) is the only source for retailer names and id prefixes, matched to what already exists in the database. Price history appends on an exact id match only. Anything looser is a merge plan that a person reviews; code never merges on a guess.

5. **No size, no landing.** A row the runner cannot size is held, counted in the report, and never lands under a size-less id.

6. **A card must name its product.** On text-scraped banners a card is kept only if its own text contains the product name. Cards that fail are dropped and counted, because they were pairing one product's name with its neighbor's price.

7. **Absence is not a delist.** Rows the runner did not see keep their last_pulled date and age. A run never deletes a row. Hand-pulled items outside the search terms stay as they are.

8. **Curated fields stay curated.** flavor, format, protein, priority and channel are never written by the runner: blank on new rows, untouched on existing rows. Category comes from the client department.

9. **Coverage marker** (Steve, 2026-10-17). Every Stage 2 report ends with one coverage line: in-scope banners pulled, not found, attended pending; doors and ACV share covered; the biggest uncovered ACV named. Then one question: search more banners, or move on to the read. The run is not done until Steve answers. Never auto-expand.

10. **Costco via Instacart.** Warehouse-local assortment, price_basis instacart_quote, roughly 15 percent over the warehouse tag. Pricing intel, not shelf price, and labeled that way on the row.

11. **Instacart under the runner.** The v77 Instacart exception covered Steve's signed-in attended account. The runner uses no login: zip-pinned public storefront, lightest touch, no same-run retries, a verification wall ends that retailer for the run.

12. **Landing order.** Backup zip to archives first, then one approval from Steve, then the SOP update and the rows land in the same sitting. The SOP will keep growing; a new rule is added here with a date and who set it.

Coverage benchmark on record: 72 Chocolate's attended process, 25 retailers, 135 blocks walked. Coverage is measured in ACV, doors as the proxy until the per-banner ACV field exists, not in banner count.
