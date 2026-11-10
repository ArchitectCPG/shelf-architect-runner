# Numbers audit (SOP v85, build 5)

Rule: a figure quoted in copy (launch plan note, thesis, synopsis, dashboard text) is recomputed from the rows by script before the copy is written. A mismatch blocks the write.

Run:
    python3 tools/numbers_audit.py <client> --rows <export> --claims <claims.json> --text <copy.txt> --allow 8.99,9.99 --strict
    python3 tools/numbers_audit.py --selftest

- `--rows`: an export of the instance's retail_entries (a folder of row JSON files, or one JSON file). The audit must read what the DB holds, not what a mapper run produced.
- `--claims`: one entry per figure in the copy: the quote, the number as written, and the metric that reproduces it (stat, field, filter, set). See claims_example_vosges_thesis.json.
- `--text`: the copy block. Every figure in it ($ amounts, percents, counts before rows, banners, houses, packs, brands, doors) needs a claim or an --allow entry. With --strict an uncovered figure fails.
- Exit 0 = pass, 1 = mismatch or uncovered, 2 = bad usage. A session does not write the copy to the DB on a non-zero exit.

Price set follows the app: dollar, size-unverified, off-neighborhood and any premium cohort, plus rows whose notes start PRICING CAVEAT, stay out of medians and percentiles; counts, banners and brands keep premium and caveat rows and drop only off-neighborhood. Median on an even set is the average of the two middles.

Known limits: the DB can only be exported through a session with the artifact tools, so the export step is manual until the page gets an Export rows action (queued with the seed build). Percentile method is linear unless a claim says otherwise.

## First real run: the Vosges Stage 3 thesis (2026-11-10)
Rows rebuilt from every landing batch, less the 18 rows removed today (an approximation of the DB). Nine figures checked.
- Pouch band 2.5 to 4.5 oz: median 6.99 and p75 8.99 reproduce; the 121 rows claimed come out at 120 to 128 depending on how the band edges and caveat rows are read; the 27 percent at 8.99 or above comes out 26 to 27.
- Bars band 2.5 to 3.6 oz: 286 rows claimed, 286 to 313 recomputed; the median claimed is 5.99 and recomputes at 6.19 to 6.29; p90 claimed 8.63 recomputes at 8.99; p75 6.99 and the 7 percent at 9.99 plus reproduce.
- One figure in the copy had no claim behind it (15 banners).
Reading: the pouch figures hold; the bars median and p90 do not reproduce from landed data. Either the rebuilt rows differ from the DB or the thesis used a different set. Needs a DB export to settle, and the bars numbers should be rechecked before the deck goes to Andy and Jay.
