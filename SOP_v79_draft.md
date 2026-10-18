# Pull process SOP v79 (DRAFT, not landed): amendments to v78
Set by Steve, 2026-10-18. Rules 1-12 of v78 stand except where noted. Goal: these apply to every client, not just Stinkin' Good.

8. **Curated fields stay curated (amended).** flavor, protein, priority and channel are never written by the runner. `format` (Frozen / Refrigerated / Shelf-stable) is the one exception: the runner fills it only where it is blank, never over a value Steve or a hand pull set, and records where it came from in `format_source`. Category still comes from the client department.

13. **Storage class on every row, wherever the source says it.** Order of evidence: (a) the retailer's own category (Kroger API categories), (b) explicit words in the product name or card (frozen, shelf-stable, can, jar, refrigerated, fresh), (c) the same brand and product already classified at another retailer, labeled same-product-elsewhere. If none of these speak, the field stays blank. The runner never guesses; a blank is a visible gap, a wrong flag poisons the price-per-oz read. Every report states how many rows are flagged, how many blank, by retailer. Price comparisons and the thesis are always cut by storage class first.

14. **A banner must have doors in the market.** Before a banner is added to a client, confirm it operates in that market (Denver is Safeway and King Soopers, not Albertsons). After every pull the runner compares the store it landed on with the requested zip. A mismatch is reported as "wrong market" and is not mapped or landed. Found 2026-10-18: Albertsons at a Denver zip pinned to a store in Idaho.

15. **New-client intake adds one step:** list which banners have doors in each client market before building blocks.
