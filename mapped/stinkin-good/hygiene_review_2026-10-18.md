# SG data hygiene review, 2026-10-18 (Fable). Nothing changed yet; Steve decides.

## A. is_own_brand on retailer private label (39 rows)
is_own_brand in the app means "the client's own product" (star, accent color, bypasses pricing exclusions). 39 store-brand rows carry it as well as is_private_label (Signature SELECT, Kirkland, Great Value, Member's Mark, Hy-Vee, Food Lion, 365, Bowl & Basket, Best Choice, Essential Everyday, First Street, Weis Quality, Aldi/Casa Mamita, Publix, Wegmans, Schnucks, Meijer, Sprouts, Giant Eagle, Hannaford, Stop & Shop/Giant store brand, Raley's, Stew's, Mollie Stones deli, Kroger store-made). Proposed fix: is_own_brand false on all 39, is_private_label true on the one that lacks it. The 12 SG and Pura rows keep true.

## B. Storage class that disagrees with what the brand ships (28 rows, SG)
Clear: 505 Southwestern 16oz/40oz jars flagged Refrigerated at Fry's, H-E-B, Mariano's, Safeway, Smith's, Walmart 3pk, Costco 40oz (7 rows) -> Shelf-stable. Bueno chopped green chile at City Market -> Frozen. Kroger salsa con queso jar at City Market -> Shelf-stable. Bueno red chile pork tamales at King Soopers ("Refrigerated - Appetizer/Entree") -> Frozen.
Likely: Hatch Valley flame-roasted 24oz (CM, KS, Fry's, Safeway: 9 rows, Refrigerated/Shelf-stable) -> Frozen. Santiago's 28oz green chile with pork (CM, KS: 6 rows, Refrigerated) -> Frozen.
Not errors: 505 green chile queso dip 15oz and Roadhouse tomatillo salsa 15oz flagged Refrigerated by Kroger category (CM, KS) are 505's refrigerated deli line, leave.
Steve's call: Schlereth's Stinkin Good Green Chile Sauce 15oz UPC 0089351100272 at CM and KS is Frozen by Kroger category; the 270 and 269 UPCs are Refrigerated. Two Schlereth's rows are two UPCs, not duplicates. Is 272 a frozen SKU? And city-market_stinkin-good_stinkin-good-green-chili_15oz is Shelf-stable with no source; KS twin is Refrigerated -> Refrigerated unless Steve says otherwise.

## C. Pura on Amazon (amazon_comps)
amazon_comps/pura_own_soda-4pk says Pura has no live Amazon listing (2026-09-08). The runner found 11 live Pura listings 2026-10-18 and the pack architecture matches the audit rule (12pk $2.08/can, 24pk $1.46/can). Candidates in mapped/pura/amazon_comps_candidates.json: 11 own, 15 comps (top 5 organic by bought-past-month per neighborhood). The stale own-brand row should be retired or rewritten when these land. The audit recommendation text is Steve's and stays as is.

## Resolution (2026-10-18, Steve OK, landed by Clyde)
- A landed: 38 store-brand rows is_own_brand false; Mollie Stones deli also is_private_label true. SG and Pura rows untouched.
- B landed: 26 format writes, format_source steve-2026-10-18. 8 Shelf-stable (505 jars x7, Kroger salsa con queso CM). 17 Frozen (Bueno hot chopped CM, Hatch Valley 24oz x10 incl. extra-hot, Santiago's 28oz x6). 1 Refrigerated (CM stinkin-good-green-chili 15oz). Bueno tamales KS already Frozen, no write. 505 queso dip and Roadhouse left as is. Safeway Santiago's not named, left as is.
- Schlereth's UPC 0089351100272 (Fable call): KEEP Frozen. Kroger's own taxonomy put it in Frozen while 270 and 269 sit in Refrigerated, and it is a separate UPC with a separate name ("Chile" vs "Chili"). Two UPCs in two cases is the most likely read. Confirm with Schlereth's directly; if it is a mis-shelved listing, flip to Refrigerated with format_source steve.
- Held Jewel rows (Fable call), landed as 2 new rows: unbranded White Queso 12oz $3.99 -> ReadyMeals White Queso Dip Ready2Heat (exact price/size match to the ReadyMeals yellow queso at the same store), private label, Refrigerated, format_source inferred-price-match. "Tamal De Queso Con Rajas" 6ct $6.99 -> Deli private label, Refrigerated, name from the product URL.
- C: already landed by the Fable session (pura_own_soda-4pk superseded v3, 26 pura_* amazon_comps rows live).
- Restore point before all of this: shelf-architect-backup-2026-10-18_7-full.zip.
