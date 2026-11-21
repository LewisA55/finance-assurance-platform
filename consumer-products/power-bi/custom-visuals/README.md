# Power BI custom visuals

The [NexusFinance report](../NexusFinance/NexusFinance.pbip) uses nine private
custom visual packages from this directory.

The [original custom visual specification](specification-v0.1.md) records
the eight reusable primitives, their data roles, Power BI capability mappings,
source adapters, evidence boundaries and acceptance criteria.

[P5 implementation](reliability-tile/README.md) records the semantic adapter,
local package workflow and Desktop acceptance of Governed KPI Review. The
source project also includes the statement matrix, rollforward bridge, tie-out
panel, close grid, lineage DAG and metric card packages. The report-detail
package restyles legacy grids and trends using their original Power BI query
fields. It forwards the reporting-version row identity to the host evidence menu.

The specification records the input requirements for the Two-Stage Variance
Bridge (P7) and Restatement Comparator (P8). The
[comparison implementation](comparison/README.md) provides both review
surfaces using the synthetic forecast and C-001 replay.

## Build and stage

From each package directory, run `npm ci`, `npm run typecheck`, `npm test`,
`npm run package` and `python stage-package.py`. The nine directories are
`close-grid`, `comparison`, `lineage-dag`, `metric-card`, `reliability-tile`,
`report-detail`, `rollforward-bridge`, `statement-matrix` and `tie-out-panel`.
Staging installs the private visual in the source PBIP and creates a local QA
copy under `work/`. The checked-in PBIR and TMDL can be used directly.
See the package notes when regenerating semantic adapters or page definitions.

Compiled packages and local development outputs must remain outside Git or be
published as deliberate release assets.
