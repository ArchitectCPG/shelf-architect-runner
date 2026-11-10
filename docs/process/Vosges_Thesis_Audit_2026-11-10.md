# Vosges Stage 3 thesis, numbers audit (2026-11-10)

Rows: live export from the Vosges instance (Export rows, 1,210 rows). Thesis-era set rebuilt exactly: live rows less the 32 refrigerated scout rows, plus the 18 rows removed by hygiene today = 1,196, the count the thesis names.

## Pouch, 2.5 to 4.5 oz
The thesis figures reproduce exactly on the thesis-era rows when every row in the band is counted: 121 rows, 15 banners, median 6.99, p75 8.99, 27 percent at 8.99 or above. That set includes the Erewhon premium and Instacart caveat rows the app keeps out of prices, and 18 rows (Barnana, Snack Factory, The Gfb, Mitica and others) removed today as not this shelf.
Live, on the app's price rules: 111 rows, 15 banners, 100 priced, median 6.99, p75 8.64, p90 10.09, 24 percent at 8.99 or above (76 percent below).
Read: the call holds. 8.99 is top quartile, not the median. The line "8.99 is the 75th percentile" overstates it slightly: on clean shelf prices 8.99 sits just above p75.

## Bars, 2.5 to 3.6 oz
Live, on the app's price rules: 311 rows, 22 banners, 306 priced, median 6.19, p75 6.99, p90 8.99, 6.9 percent at 9.99 or above.
The thesis figures (286 rows, median 5.99, p90 8.63) do not reproduce on any definition tested (band edges, caveat rows, cohorts, private label, any single banner dropped). The 5.99 median does reproduce on the rows pulled 2026-11-06 only; the Safeway, Natural Grocers and Fresh Thyme bars landed 2026-11-07 13:30Z, minutes before the thesis was written, so the thesis most likely read a set without them. p75 6.99 and the 7 percent at 9.99 plus reproduce.
Read: the call holds. 9.99 is above p90 either way and only about 7 percent of bars sit there.

## Proposed copy (not applied; Steve's OK needed)
- Section 1: "Cut to the band Vosges actually enters, 2.5 to 4.5 oz (111 rows, 15 banners): median 6.99, p75 8.64. About 24 percent of small pouches sit at 8.99 or above. At 8.99, Vosges is in the top quarter of the band, just above the 75th percentile."
- Section 5: "In the 2.5 to 3.6 oz bar band (311 rows), the median is 6.19, p75 6.99, p90 8.99. Only 7 percent of bars are at 9.99 or above."

## Lesson for the gate
A thesis figure is computed on the app's price set from a DB export taken after the last landing, never on all rows and never mid-landing. numbers_audit.py does that by default.

## Applied (Steve OK, 2026-11-10)
Sections 1 and 5 of the thesis project doc and the pouch and bars price rail reads in client_config/vosges (v29) now carry the audited figures. Audit passed on the new text with the client's own cohorts (--cohorts from pricing_exclude_cohorts): claims in claims_vosges_thesis_v2.json. Not re-audited: other figures in those reads (Hu 7.99 and 8.99 at Whole Foods checked and hold; the conventional small-band top of 6.89 to 8.19 now has one Target row at 8.99).
