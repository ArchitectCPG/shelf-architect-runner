# Forecast runner (SOP v85 build 4)

One command turns a client's forecast config (Decision Sheet B, lines 9 to 20) into the workbook, the dashboard docs, the download and the write batches.

    python3 forecast/run.py clients/<id>.forecast.json [out_dir]

- build.py: config to workbook (Read Me, Assumptions, Overall with the P&L block, Current State, one detail tab per existing account, Retailer Expansion, SKU Expansion, optional Plan and Vol templates). No client value lives in code.
- extract.py: recalculates in LibreOffice, stops on any formula error, writes dash_doc.json and sheets_doc.json in the shape the page renders. The recalculated file is the download.
- emit.py: write batches under the request ceiling: forecast_sheets/<id>__<file_key>, <id>__<file_key>_sheets, forecast_files/<id>__<file_key>__<n>, and the client_config.forecast block (dashboard, Model tabs, Retail Marketing image tab). A session sends them with db_write; existing docs need ifVersion.

Config (see clients/vosges.forecast.json): frame (start year and month, so fiscal years work), tiers, existing_spend, timing, sku_stairstep, waterfall, ramp, lines (SRP, velocity, COGS per format), existing accounts (doors, SKUs, line, velocity overrides), optional rollout (any number of drops, a first account that skips the review wait, an earliest month for everyone else), retailer_expansion accounts, sku_expansion, optional sanity check and plan templates, dashboard copy. Copy in the config that quotes a figure goes through tools/numbers_audit.py before it is written (numbers_audit_gate).

Proof 2026-11-10: clients/vosges.forecast.json reproduces the live Vosges v1 dashboard exactly (every company figure and revenue sub-tile equal to the cent). forecast/tests: a fiscal-year client with two existing accounts on two lines and no rollout (existing revenue matches hand math), and a three-drop rollout (the third tranche matches hand math month by month). All build with 0 formula errors.
