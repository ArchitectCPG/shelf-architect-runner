# SOP v88 proposal: scope, registry, gate with memory (2026-11-13, postmortem on v83 to v87)

Status: approved by Steve 2026-11-13 ("go", "yes"). Depth grade added. Lands on main after the backup; client instances at their next session.

## Why
The Vosges update fixed intake, decisions, audit and forecast. Banner selection stayed hand-built per client: 25 banners typed into clients/vosges.json, 19 dispatched runs for 125 blocks, slugs and recipes re-learned mid-run. Pura's file has 6 banners against a 94-retailer MULO list. No way to run the universe or a named subset.

## What is built (sandbox)
- registry/banners.json (tools/build_registry.py): 243 universe banners with channel, distributors, doors, ACV weight, states, and what the runner has proven: lane, slug, last good pull, market pins. Rebuilt from disk any time; source snapshots in registry/source/.
- tools/scope.py: a client file can carry "scope" instead of a typed retailers list. preset universe | mulo | fdmc, narrowed by channels, distributors, states, min_doors, with include and exclude. Prints banners in scope, runner-ready, doors and ACV covered, biggest uncovered, block count, and the gate list. --emit prints the retailers list in the shape gen_client_blocks.py already reads, so the generator is unchanged.
- Gate with memory: a banner with a good pull inside 30 days and a market pin on file skips Stage 0. Only new, stale, failed or family-recipe banners are gated. The in-run store check still runs on every block.

## Rule changes proposed
1. coverage_policy: depth is always full inside the scope (every neighborhood at every banner in scope). Breadth is the scope set at intake: universe, a preset, or a subset. A banner out of scope is a decision written in the client file, not a skip.
2. runner_lane rule 14: the banner list comes from the scope resolved against the registry, never typed by hand. The resolver's uncovered list is the coverage question, asked before the run.
3. stage_0_onboarding.runner_variant: gate only banners the registry marks new, stale (30 days), failed or family. Record the pass back to the registry.
4. run_caps: the 100-block cap is for attended Chrome. Runner cap is 20 blocks per retailer per run, no total cap.
5. Intake v2 line 29 to 30 becomes one scope line: preset or channels, distributor, markets, banners to add, banners to avoid.
6. Every proven route, slug fix and store pin learned in a client run is written to the registry in the same commit (the Woodman's and Fresh Thyme slugs lived only in clients/vosges.json).

## Dry replay, 2026-11-13 (no Bright Data spend)
| shape | in scope | runner-ready | doors covered | blocks | gate |
|---|---|---|---|---|---|
| Vosges: natural + specialty on UNFI, plus Whole Foods (5 nbhds) | 47 | 9 | 61% | 45 | 0 |
| EHC: drug, mass, club, 7 named regionals (8 nbhds) | 14 | 11 | 96% | 88 | 5 |
| Pura: MULO list (4 nbhds) | 74 | 33 | 90% | 132 | 19 |
| Whole universe (4 nbhds) | 193 | 42 (+5 family) | 51% | 168 (+20) | 27 |

## Known gaps the replay shows
- Natural tail: INFRA (360 doors) and NCG (230) are co-op groups with no single storefront; 38 small natural banners never probed. Natural coverage is 9 banners.
- Club: Sam's and BJ's fail on the runner; Costco is online or Instacart pricing.
- Drug: Walgreens good; CVS returns a partial shelf (lazy load). Both count as ready, so an EHC-shape read at CVS is thinner than the number says.
- 'Ready' means at least one priced pull, not full depth. Depth per banner is not scored yet.
- Salsa-era banners (Food Lion, Publix, Hy-Vee, Kroger and others) have a proven route but no market pin on file; they go through the gate once.
- Fareway is on the MULO list but not in the universe.
