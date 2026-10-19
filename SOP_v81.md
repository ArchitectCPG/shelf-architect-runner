# Shelf Architect pull SOP v81, runner lane (2026-10-19)

v81 (2026-10-19): write_cadence folded in from the 72Chocolate instance (Steve 2026-10-03, never reached main). Synced wholesale to the 72Chocolate and Easy Healthcare instances the same session. v80 (Steve 'Yes', 2026-10-18): runner_lane rules 18 hygiene gate, 19 storage-class cut for multi-case categories only, 20 temperature states at discovery with unseen-case flag; duplicate rule 17 (Amazon lane) removed. Proven on Stinkin' Good; storage class is a conditional lens, not a standing section.

Summary: Bright Data + GitHub Actions runner is the primary pull route; attended Chrome is plan B. Kroger developer API primary for Kroger banners (Steve 2026-10-18). Rules below are the v78 one-page SOP as approved. v79 (2026-10-18, Steve): rule 8 amended (runner fills format only where blank); 13 storage class on every row; 14 standard banner set for a new client; 15 competitive pulls follow the competitors; 16 intake lists competitive markets; 17 Amazon lane separate from retail and temperature-gated.

Benchmark: 72 Chocolate attended process: 25 retailers, 135 blocks walked. Coverage measured in ACV (doors as proxy), not banner count.

1. **Primary route is the runner..** Bright Data plus GitHub Actions, unattended, one domain per browser session. Attended Chrome is plan B only: mapping a new banner, bot-walled sites, the Costco warehouse tag, a broken recipe.

2. **Cadence..** One run per new prospect. Monthly at most on retainer. No scheduled or daily pulls. The runner never writes to the database on its own; every landing goes through the mapper, a backup zip, and Steve's OK.

3. **Kroger developer API is the primary route for Kroger banners.** (Steve, 2026-10-18, reversing 2026-10-14). The reading on record: Shelf Architect is a category-wide view across banners, and Kroger is one column in it. Kroger-specific cuts are made only when building a pitch to a Kroger buyer, which serves Kroger. Terms 4a (analysis targeting Kroger) is read as not applying to that use. Stored rows (Terms 5e) are a known exposure, accepted for small per-client datasets. If the key is ever revoked, the browser recipe is the fallback and nothing else in the process changes. Rows from this route carry the UPC and route runner-kroger-api.

4. **Row identity..** One retailer table in the runner (slug, display name, id prefix) is the only source for retailer names and id prefixes, matched to what already exists in the database. Price history appends on an exact id match only. Anything looser is a merge plan that a person reviews; code never merges on a guess.

5. **No size, no landing..** A row the runner cannot size is held, counted in the report, and never lands under a size-less id.

6. **A card must name its product..** On text-scraped banners a card is kept only if its own text contains the product name. Cards that fail are dropped and counted, because they were pairing one product's name with its neighbor's price.

7. **Absence is not a delist..** Rows the runner did not see keep their last_pulled date and age. A run never deletes a row. Hand-pulled items outside the search terms stay as they are.

8. **Curated fields stay curated..** (amended v79). flavor, protein, priority and channel are never written by the runner. `format` is the one exception: the runner fills it only where it is blank, and never overwrites a value a person set. Category comes from the client department.

9. **Coverage marker.** (Steve, 2026-10-17). Every Stage 2 report ends with one coverage line: in-scope banners pulled, not found, attended pending; doors and ACV share covered; the biggest uncovered ACV named. Then one question: search more banners, or move on to the read. The run is not done until Steve answers. Never auto-expand.

10. **Costco via Instacart..** Warehouse-local assortment, price_basis instacart_quote, roughly 15 percent over the warehouse tag. Pricing intel, not shelf price, and labeled that way on the row.

11. **Instacart under the runner..** The v77 Instacart exception covered Steve's signed-in attended account. The runner uses no login: zip-pinned public storefront, lightest touch, no same-run retries, a verification wall ends that retailer for the run.

12. **Landing order..** Backup zip to archives first, then one approval from Steve, then the SOP update and the rows land in the same sitting. The SOP will keep growing; a new rule is added here with a date and who set it. Coverage benchmark on record: 72 Chocolate's attended process, 25 retailers, 135 blocks walked. Coverage is measured in ACV, doors as the proxy until the per-banner ACV field exists, not in banner count.

13. **Storage class on every row.** (Steve, 2026-10-18). The runner sets `format` to Frozen, Refrigerated or Shelf-stable wherever the source says so, with `format_source` recording how: kroger-category (Kroger API department tags, most reliable), name (the product title or card says frozen, shelf-stable, canned, jar, fresh, refrigerated), or same-product-elsewhere (same brand and product already classified at another banner or by hand). If none of those apply the field stays blank. It never guesses. Every report states how many rows are classified and how many are blank, and analysis that compares price across storage classes (price per oz, price ladders, the thesis) is read within a class, or flagged where blanks could change the answer.

14. **Standard banner set for a new client.** (Steve, 2026-10-18). Every new client's config starts from the full in-scope banner list for its markets, not just the banners that were easy last time. Albertsons (zip-pinned recipe) is part of the standard set wherever the client's markets have one, alongside the Kroger API banners, Walmart, Target, Sprouts, Safeway, Whole Foods, Costco and the regional chains that fit. A banner is left out only with a reason written in the client config.

15. **Competitive pulls follow the competitors, not only the client's markets.** (Steve, 2026-10-18). Each client has home markets and competitive markets. A banner is pulled in a market where it has doors: Albertsons in Boise, Jewel-Osco in Chicago, Safeway and King Soopers in Denver. Competitive markets are labeled on the config and on every row's region. After every pull the runner compares the store it landed on with the market zip; a mismatch is reported as "wrong market" and not landed (found 2026-10-18: Albertsons at a Denver zip pinned to an Idaho store).

16. **Amazon lane, separate and temperature-gated.** (Steve, 2026-10-18). Amazon comps come from the Bright Data Amazon products scraper by keyword, national, one run per prospect and monthly on retainer, same as retail. The lane is a separate channel: its own blocks, its own output folder, its own report, and its rows never enter retail_entries or the 40/15/20 retail waterfall; their only home is amazon_comps, which stays a manual audit. The lane runs only for a client whose product is shelf-stable, per neighborhood; refrigerated and frozen products get no Amazon blocks and the report says why. The report shows price, pack count, $/unit, Amazon's own bought-past-month figure labeled as a floor, category rank, and sponsored vs organic. No revenue or size-of-prize number is ever derived from rank; a sized prize comes from Helium 10 bought by the month and is entered by hand.

17. **Hygiene gate before any thesis.** (Steve, 2026-10-18). After a landing and before Stage 3 runs: is_own_brand is true only on the client's own rows; every retailer store brand carries is_private_label true; truncated product names are held, not guessed. When rule 19 applies, format is set on every row, with hand values recorded as format_source steve-<date>, never guessed. Fable proposes the fix batch, Steve OKs, backup zip first.

18. **Storage-class cut, only for multi-case categories.** (Steve, 2026-10-18). At Stage 1 ask one question: does this category sell in more than one temperature state? If yes (green chile, queso, dips, entrees), the storage-class cut is the first thesis output: cut the home-banner set by Refrigerated, Frozen, Shelf-stable and write three insights sourced 'Shelf Architect retail tracker': where the fight is by case; the like-for-like benchmark ($/oz by class, pack optics); and the band on the second shelf. Judge premiums against the platform's refrigerated-equivalent rule, never a blended $/oz. If no (ketchup, crackers, soda), skip format and never mention storage class in anything the client sees.

19. **Temperature states at discovery, multi-case only.** (Steve, 2026-10-18). For a multi-case category, Steve names each competitor's temperature states in discovery. The pull flags any competitor SKU found in a case he did not name as an 'unseen case' line in the run status; it never joins the competitive set or the thesis until Steve decides. If nothing unseen turns up, the run says nothing about it.

## write_cadence (from 72Chocolate, Steve 2026-10-03)

Write per retailer, never at the end of the run. When a retailer's blocks for the current phase are finished, write that retailer's retail_entries rows and update only those blocks' last_walked and last_result on pull_matrix, each pinned to a fresh read, and refresh the lease heartbeat in the same beat, before navigating to the next retailer. Never carry more than one retailer's unwritten results. A run that dies mid-walk then loses at most one retailer instead of everything it has gathered.

Before writing a block's rows, query retail_entries by retailer and neighborhood and match the live products against what comes back by brand, product name and size. Do not construct a doc_id and assume it is new. Size slugs exist in both dotted and dashed spellings (2.1oz and 2-1oz), so a constructed id can miss an existing row for the same real product and create a duplicate, and an unpinned set against an existing id fails the whole batch.
