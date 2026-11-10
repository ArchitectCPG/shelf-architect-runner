# Seed by page (SOP v85 build 3)

refdata.js is the page code added to the main Shelf Architect page on 2026-11-10 (version 1794320633-2685).
- Export reference set (sidebar footer, any instance): reads retailers, review_calendar, category_scan, distributors, general insights and the listed app_meta, forecast_images and pull_matrix/_template docs, saves one JSON bundle through the downloads capability. Client data never enters it.
- Seed reference data: shows only when the page is served with seed/reference_set.json. Writes every doc (set if missing, merge if present, nothing deleted), creates app_meta/pull_conflicts if missing, writes app_meta/seed_log with counts and failures. A banner offers it when retailers is empty.

New instance recipe: publish_files with index.html (main page), seed/reference_set.json (latest export), files/retail-marketing-framework.jpg; declare db and downloads; open the page and tap Seed twice; check app_meta/seed_log against the bundle counts.

Harness: node run.js (playwright, stub db in stub.js) exports from a fake main and seeds a fake empty instance.

Export rows (2026-11-10): rows.js, sidebar button in main (1794323178-b384) and Vosges (1794323216-49ee). Saves every retail_entries doc as one JSON (kind shelf_architect_rows); this is the --rows input for tools/numbers_audit.py. Harness: node run2.js.
