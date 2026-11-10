# Forecast runner (SOP v85 build 4)

One command turns a client's forecast config (Decision Sheet B, lines 9 to 20) into the workbook, the dashboard docs, the download and the write batches.

    python3 forecast/run.py clients/<id>.forecast.json [out_dir]

- build.py: config to workbook (Read Me, Assumptions, Overall with the P&L block, Current State, one detail tab per existing account, Retailer Expansion, SKU Expansion, optional Plan and Vol templates). No client value lives in code.
- extract.py: recalculates in LibreOffice, stops on any formula error, writes dash_doc.json and sheets_doc.json in the shape the page renders. The recalculated file is the download.
- emit.py: write batches under the request ceiling: forecast_sheets/<id>__<file_key>, <id>__<file_key>_sheets, forecast_files/<id>__<file_key>__<n>, and the client_config.forecast block (dashboard, Model tabs, Retail Marketing image tab). A session sends them with db_write; existing docs need ifVersion.

Config (see clients/vosges.forecast.json): frame (start year and month, so fiscal years work), tiers, existing_spend, timing, sku_stairstep, waterfall, ramp, lines (SRP, velocity, COGS per format), existing accounts (doors, SKUs, line, velocity overrides), optional rollout (any number of drops, a first account that skips the review wait, an earliest month for everyone else), retailer_expansion accounts, sku_expansion, optional sanity check and plan templates, dashboard copy. Copy in the config that quotes a figure goes through tools/numbers_audit.py before it is written (numbers_audit_gate).

Proof 2026-11-10: clients/vosges.forecast.json reproduces the live Vosges v1 dashboard exactly (every company figure and revenue sub-tile equal to the cent). forecast/tests: a fiscal-year client with two existing accounts on two lines and no rollout (existing revenue matches hand math), and a three-drop rollout (the third tranche matches hand math month by month). All build with 0 formula errors.

- `love_label` (optional): in-store layer name on the Plan tab. Default "Pack Love". Set "Can Love" only for a canned beverage client (Steve, 2026-11-10).

- Dashboard tiles (Steve, 2026-11-10, every client): the headline tile is gross sales (what the brand invoices), with retail $ at shelf as a sub-line. Trade, marketing and contribution margin tiles show $ and % of gross sales. No spend % tile. extract.py emits company.gross_sales and dashboard.gross_label; the page renders the new tiles when gross_sales is present (patch in docs/page_patches/2026-11-10_forecast_tiles.diff, live on Vosges; main and the other client pages get it at their next session per the sync rule).
- Existing accounts can be "kind": "flat" (no doors or velocity): brand $ per year, brand $ as % of retail, trade and marketing % of brand $. Used for Faire independents on Vosges.
- marketing_return (optional, SA default 1.1, Steve 2026-11-10): marketing $ returns ratio x in retail $ at shelf, incremental on top of the velocity base. Adds a row on Overall (spread with base revenue), runs through the waterfall to gross sales, blended COGS, no trade on top; dashboard gets a Marketing return card. Lower or drop it if the client already runs marketing (the return may sit in the base).
