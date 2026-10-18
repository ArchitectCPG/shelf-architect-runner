# Pull process SOP v79 (DRAFT, not landed): amendments to v78
Set by Steve, 2026-10-18. Rules 1-12 of v78 stand except where noted. Goal: these apply to every client, not just Stinkin' Good.

8. **Curated fields stay curated (amended).** flavor, protein, priority and channel are never written by the runner. `format` (Frozen / Refrigerated / Shelf-stable) is the one exception: the runner fills it only where it is blank, never over a value Steve or a hand pull set, and records where it came from in `format_source`. Category still comes from the client department.

13. **Storage class on every row, wherever the source says it.** Order of evidence: (a) the retailer's own category (Kroger API categories), (b) explicit words in the product name or card (frozen, shelf-stable, can, jar, refrigerated, fresh), (c) the same brand and product already classified at another retailer, labeled same-product-elsewhere. If none of these speak, the field stays blank. The runner never guesses; a blank is a visible gap, a wrong flag poisons the price-per-oz read. Every report states how many rows are flagged, how many blank, by retailer. Price comparisons and the thesis are always cut by storage class first.

14. **Competitive pulls follow the competitors, not only the client's markets** (Steve, 2026-10-18). Each client has home markets and competitive markets. A banner is pulled in a market where it has doors: Albertsons in Boise, Jewel-Osco in Chicago, Safeway and King Soopers in Denver. Competitive markets are labeled on the config and on every row's region. After every pull the runner compares the store it landed on with the market zip; a mismatch is reported as "wrong market" and not landed (found 2026-10-18: Albertsons at a Denver zip pinned to an Idaho store).

15. **New-client intake adds one step:** list the home markets, then the competitive markets where the named competitors have shelf, and which banners have doors in each.
