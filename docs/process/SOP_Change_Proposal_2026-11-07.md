# SOP and runbook change proposal (from the Vosges postmortem)

Drafted by Opus 2026-11-07. For Fable review and apply on Tue 2026-11-10. Source: claude/Vosges_Postmortem_2026-11-07.md in the Vosges project (copy at docs/process/ in this repo).

Targets: app_meta/pull_process and app_meta/onboarding_runbook in the main instance (454bdece-8633-4012-9d01-0f0ba50117f5), then the Vosges instance copies. 72Chocolate and EHC copies need Steve's approval (writes outside the session instance were refused before).

## Changes

### C1. Intake v2 replaces the current intake
Runbook new_client_setup step 1 points to docs/process/Intake_v2.md. Current retail (accounts, doors, SKUs, SRP, velocity), fiscal year, COGS, launch staging and private label are required fields. Existing SKUs are seeded as brand rows before Stage 0.

### C2. Seed by script, not by session
new_client_setup steps 1 and 2 (reference copy) become a runner script. Model: Sonnet. No Fable.
OPEN: no bulk cross-instance copy exists in the tools. Fable to decide: script that emits db_write op files Sonnet sends in batches, or keep a manual copy on Sonnet.

### C3. Stage 0 gate additions
Gate fails unless: brand term walked at every banner; each banner's pinned store matches the target market (address check); clients/<id>.json has relevance and hard_exclude for every neighborhood. Filter before cap.

### C4. Rule-based hygiene
Mapper applies classifier rules built from held.json patterns (snack and protein bars, bulk, baking, deli, cookies, wafers, toys, fragments). Clean rows land; exceptions only go to review. Target: under 10 percent of rows reviewed.

### C5. Decision sheets
Runbook adds Decision Sheet A (after Stage 3 thesis, before judgment sections) and Decision Sheet B (before Go-to-Market and forecast). Opus pre-fills defaults; Steve edits once. No judgment section is built before its sheet is back.

### C6. Forecast standards (platform default, set by Steve 2026-11-07)
- Calendar year unless the client says otherwise
- Trade and marketing percent on gross sales, never retail at shelf
- P&L block on Overall ending in contribution margin; dashboard net tile = Contribution Margin, percent tile = Contribution Margin percent of gross sales
- COGS from margin_scenarios, flagged as ceiling until real
- Existing-account expansions skip the review wait
- Forecast section always has: dashboard, Model tabs, Retail Marketing (shared slide, no customization)
- Built by the forecast runner from forecast.json (Sheet B)

### C7. Numbers audit before copy
Any figure quoted in DB copy is recomputed from retail_entries in code first (extends conventions.audit_the_numbers_not_the_code). Applies to launch plan notes, thesis and synopsis.

### C8. Model routing
| Model | Use for |
|---|---|
| Sonnet | Stage 0, pulls, retries, landings, hygiene exceptions, attended walks, reconciliation, seed, dashboard refresh |
| Opus | Intake, decision sheets, judgment sections, page edits, forecast build |
| Fable | Stage 1 matrix, Stage 3 thesis, final verification before client delivery, plan pressure-tests |

### C9. Working rule
When Steve asks a question, answer and stop. No edits until he says go.

## Fable: what to decide Tuesday
1. Pressure-test C1 to C9; cut or change anything that will not hold for a non-chocolate client.
2. Decide C2 (seed path).
3. Apply the accepted changes to main pull_process and onboarding_runbook (bump versions), then to the Vosges copies.
4. List the runner builds in order (seed, gate checks, hygiene rules, forecast runner, numbers audit, shared assets) with a Sonnet or Opus owner each.
5. Report DONE / NEXT. No em dashes.
