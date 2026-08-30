# Consumer Products Workspace

This directory holds the separately authored analytical products that consume
the governed C2 delivery package. It does not own source events, accounting
truth, controls, reporting versions, or the governed semantic definitions.

| Product | Tracked here | Ignored locally | Release delivery |
|---|---|---|---|
| Excel | Model documentation, input map, validation specifications and reusable text assets | `excel/work/` and `excel/exports/` | Tagged XLSX asset when complete |
| Power BI | Model documentation, TMDL/PBIP text source, measure catalogue and validation specifications | `power-bi/work/`, `power-bi/exports/` and Power BI Desktop cache | Tagged PBIX/PBIP asset when complete |

Every consumer product must pin one exact governed delivery manifest and state
its reporting version, purpose, scope, currency basis and reconciliation
controls. Consumer calculations may analyse published facts; they must not
create a second accounting or governed-truth authority.

The current v0.1 repository intentionally provides workspace contracts only.
The Excel three-statement and DCF model is the v0.2 product; the Power BI
semantic and reporting product is v0.3.
