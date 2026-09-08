# Consumer Products Workspace

This directory holds the separately authored analytical products that consume
the governed C2 delivery package. It does not own source events, accounting
truth, controls, reporting versions, or the governed semantic definitions.

| Product | Tracked here | Ignored locally | Release delivery |
|---|---|---|---|
| Excel | Model documentation, input map, schedule specifications, validation controls and reusable text assets | `excel/work/` and `excel/exports/` | Tagged XLSX asset when complete |
| Power BI | Semantic-model source, report design, custom-visual source and validation specifications | `power-bi/work/`, `power-bi/exports/` and Power BI Desktop cache | Tagged PBIX/PBIP asset when complete |

Every consumer product must pin one exact governed delivery manifest and state
its reporting version, purpose, scope, currency basis and reconciliation
controls. Consumer calculations may analyse published facts; they must not
create a second accounting or governed-truth authority.

The current v0.1 repository intentionally provides workspace contracts only.
The Excel three-statement and DCF model is the v0.2 product; the Power BI
semantic and reporting product is v0.3.

The tracked subdirectories are intentionally small at v0.1. They define where
reviewable source and evidence will live without committing proprietary desktop
caches or unfinished binaries:

```text
excel/
  specifications/   workbook architecture, schedules and input mapping
  validation/       reconciliations, formula checks and review evidence
power-bi/
  semantic-model/   PBIP/TMDL source, measures, relationships and security
  report/           page specifications, navigation and visual contracts
  custom-visuals/   source for the bounded purposeful visuals
  validation/       model, measure, security and rendering checks
```

Before public-release work or material desktop-model changes, create a private,
checksum-bound archive using the
[private backup procedure](../docs/public-release/private-backups.md). The
backup includes ignored authoring workspaces without making those binaries part
of the public repository.
