# Nexus Financial Comparison

The comparison package has two independently sourced pages.

| Page | Grain and anchors | Evidence |
| --- | --- | --- |
| Planning Variance | June 2026, GBP, seven accounts across eight departments. Published C2 budget, synthetic May forecast vintage, published management actual. Account selection changes the two-stage bridge and the department drivers. | Budget line, management row, June 2025 baseline row, versioned forecast factor and sealed C2 delivery. Revenue treats higher positive values as favourable. Costs treat lower positive values as favourable. |
| Restatement Comparator | June 2026, GBP, two lines from the C-001 accounting replay. Original `RV-2026-06@v1` and republished `RV-2026-06@v2`. | Snapshot hashes, `RC-001`, republication `AE-C001-011`, `J-560` line, July ledger period and approved June presentation adjustment. |

The May scenario is a synthetic retrospective forecast vintage for the
showcase. It uses the prior June's management actuals and the registered
account factors in `forecast-policy.json`. The C2 budget and the management
actuals keep their original authority. C-001's figures and reporting versions
belong to the canonical replay. The C2 statutory actuals, reporting versions
and seal are unchanged.

Run `python build-integration.py` in the repository Python environment with the
pinned C2 delivery present under `build/finance-delivery/Q-FINANCE-C2-V1`.
It checks the physical C2 seal, runs H0 through H7, verifies both content
hashes and ties each restatement delta to its approved adjustment before it
emits the two inlined semantic adapter tables and the PBIR pages.

Run `npm ci`, `npm run typecheck`, `npm test`, `npm run package`, then
`python stage-package.py` to stage the private visual. The renderer uses
Power BI table roles for amounts in integer minor units and publishes a
visible unavailable state when rows, anchors or evidence are incomplete.
