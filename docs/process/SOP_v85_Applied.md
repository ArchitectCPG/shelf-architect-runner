# SOP v85, applied 2026-11-10

Pressure test of the 2026-11-07 change proposal (C1 to C9), run on Fable, approved by Steve ("go"). This file is the record of what landed and the build list that follows.

## Where it landed
- Main instance: app_meta/pull_process (SOP version 85), app_meta/onboarding_runbook (new section "Process v2"), app_meta/pull_process_core (new, read first).
- Vosges instance: same three docs, level with main.
- Not touched: every other client instance. Each is brought level at its next session (sync_rule).

## What changed against the proposal
| Change | Verdict | Amendment |
|---|---|---|
| C1 intake v2 | amended | Two modes (client, prospect). A blank defaults and is flagged, never blocks. Current SKUs are seeded as expected doors, never as retail_entries rows. |
| C2 seed | decided | The instance seeds itself from reference files served with the page. Proof pending. Fallback: script emits write batches, Sonnet sends them. |
| C3 Stage 0 gate | amended | Enforced in runner code. store_expect mandatory on every block. New check: term precision under 50 percent stops the full pull. |
| C4 hygiene | amended | Rules live in clients/<id>.json, mapper is generic, no category words in tool code. 10 percent target is unproven until the Vosges replay. |
| C5 decision sheets | held | Steve answers by line number, changes only. Intake answers are pre-filled, not asked twice. |
| C6 forecast | amended | Review-wait skip is a Sheet B default for approved-vendor accounts only. Spend default tied to the margin standard. Existing items use real velocity. COGS named as cost target. |
| C7 numbers audit | held | A script gate that blocks the write; covers forecast copy. |
| C8 model routing | amended | models.routing supersedes older lines naming Fable. Search terms and relevance rules sit in Stage 1. |
| C9 answer and stop | held | step_handoff.ask_then_wait. |
| new: core doc | added | pull_process_core, one page, read first. |
| new: sync rule | added | Main is the source; a client copy is refreshed at its next session. |

## Build list, in order
| # | Build | Owner | Spec |
|---|---|---|---|
| 1 | Stage 0 gate checks (BUILT 2026-11-10, tools/gate.py) | Sonnet | gen_client_blocks.py writes store_expect from the market on every block and refuses to emit one without it; client_report.py prints term precision per neighborhood and fails under 50 percent; config check for relevance and hard_exclude. |
| 2 | Generic hygiene in the mapper (BUILT 2026-11-10, tools/hygiene.py) | Sonnet | Move the Vosges patterns from pouch_filter.py and stage2_hygiene.py into clients/vosges.json; mapper applies config rules; replay the Vosges landing and report the share sent to review. |
| 3 | Seed proof | Opus | Export the reference set from main to served files; add a Seed reference data action to the page; prove on a scratch instance. If it fails, write the batch emitter for Sonnet. |
| 4 | Forecast runner | Opus | Make forecast/build.py and extract.py generic, driven by forecast.json from Sheet B; one command emits workbook, dashboard docs and download. |
| 5 | Numbers audit script | Sonnet | Recompute every figure in a copy block from retail_entries or the workbook; non-zero exit on a mismatch. |
| 6 | Shared assets at setup | Sonnet | Copy files/retail-marketing-framework.jpg and its forecast_images doc into every new instance as part of the seed. |
| 7 | Slim the SOP | Fable, one pass | Move browser-era sections of pull_process and the runbook into an archive doc once core has been used on one client without a miss. |

## Open
- Trade and marketing default when Sheet B is blank: 20 percent of gross sales, confirmed by Steve 2026-11-10.
- Seed by page is decided but unproven.
- Hygiene review share measured on the Vosges replay (8.1 percent); a held-out test needs the next client.

## Build 1 result (2026-11-10, Sonnet)
Built: tools/gate.py (config, store, brand, precision checks, plus a `stamp` retrofit), wired into gen_client_blocks.py (refuses to generate on a config failure), client_report.py (flags WRONG MARKET and UNPINNED, prints the gate table, `--gate` exits non-zero) and mapper.py (does not land a block that fails the store check). pull.mjs store_expect is now case-insensitive to match.
Configs: store_expect added to every market in vosges, pura and stinkin-good (city plus 3-digit zip prefix); four Vosges retailer pins where the recipe returns only a street address or store name (jewel-osco, albertsons, safeway, heb); explicit empty hard_exclude where the key was missing (Vosges refrigerated shelf, Pura and Stinkin' Good non-brand shelves).
Replay on the Vosges data: caught H-E-B landing on Victoria, Meijer landing on a Michigan store (Alpine), Fresh Thyme unpinned, Whole Foods blocks with no pinned store, and no brand block with data at Albertsons, Safeway and Meijer. Mapper dry run: 12 blocks not landed. Four bad configs refused by the generator; a rule set that matches nothing scores 0 percent and fails.
Not done: dispatch-time refusal in the workflow (the generator, report and mapper enforce it); Pura and Stinkin' Good blocks not regenerated or stamped; hand-added blocks (the refrigerated scout shelf, extra Amazon terms) are wiped by gen_client_blocks.py on regeneration, so use `gate.py <client> stamp` on existing clients.

## Build 2 result (2026-11-10, Sonnet)
Built: tools/hygiene.py (client-agnostic engine: exclude brands, fragment brands held, brand canon, private label brands, per-shelf format rule, matrix suffix) and tools/shelf_filter.py (generic pre-landing filter, replaces the Vosges-only pouch_filter.py, which is deleted). The mapper applies the rules inline and writes mapped/<client>/hygiene_log.json for every row a rule removes. tools/stage2_hygiene.py now reads the same config. All Vosges patterns moved to clients/vosges.json (hygiene, neighborhood format_rule, retailers[].matrix_suffix). No category word is left in tool code. gate.py now compile-checks the new config sections.
Equivalence: stage2_hygiene.py on config gives byte-identical output to the hard-coded version on all seven output files.
Replay on the Vosges data (mapper run into a temp folder, nothing landed or changed in mapped/):
- Rows: 4,510 before, 4,281 after. The 229 rows removed are all in hygiene_log.json (matched by rule and reason); nothing dropped silently; no row id changed.
- Sent to a person: 348 of 4,281 = 8.1 percent (235 no size parsed, 104 name truncated, 9 fragment or Unbranded brand). Target was under 10 percent. Caveat: 339 of the 348 are the mapper's existing size and title holds, unchanged; the engine's own review queue is the 9 fragment rows.
- Against the hand process: 27 of the 30 brands excluded by hand in Stage 2 are also excluded by rule. Of the 1,371 rows landed by hand, 1,115 land clean again, 240 are not produced by the current pull data (older pulls), and 16 are removed by rule.
- Those 16 landed rows are findings for Steve: 10 are brands the rules exclude as not this shelf (Barnana, Snack Factory, Mitica, The Gfb, Nassau Candy, Woodstock) and 6 are bars (Unreal, Hu at Whole Foods) the rules route to the bars shelf. They sit on the pouch shelf in the DB today. Not changed.
- The old pouch filter kept 21 rows that the config rules drop (Barnana, Snack Factory, Mitica, Belvita, Simple Mills), which Stage 2 then handled by hand.
Not done: the rules were tuned on this same data, so the 8.1 percent is a replay, not a held-out test; the next client's first landing is the real measure. brand canon is stored on the row, ids keep the raw brand so price history still matches.
