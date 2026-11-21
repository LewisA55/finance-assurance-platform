# Consumer Products Workspace

This directory holds the separately authored analytical products that consume
the governed C2 delivery package. It does not own source events, accounting
truth, controls, reporting versions, or the governed semantic definitions.

| Product | Tracked here | Ignored locally | Release delivery |
|---|---|---|---|
| Excel | Model documentation, input map, schedule specifications, validation controls and reusable text assets | `excel/work/` and `excel/exports/` | Tagged XLSX asset when complete |
| [Power BI](power-bi/README.md) | NexusFinance PBIP, TMDL model, PBIR report, custom visuals and validation | `power-bi/work/`, `power-bi/exports/` and Power BI Desktop cache | Current local export at `power-bi/work/R2/NexusFinance.pbix` |

Every consumer product must pin one exact governed delivery manifest and state
its reporting version, purpose, scope, currency basis and reconciliation
controls. Consumer calculations may analyse published facts; they must not
create a second accounting or governed-truth authority.

The Excel three-statement and DCF model is the v0.2 product. NexusFinance is
the Power BI reporting project for v0.3. The workspace keeps reviewable source
and evidence in Git and desktop exports and caches in local directories.

```text
excel/
  specifications/   workbook architecture, schedules and input mapping
  validation/       reconciliations, formula checks and review evidence
power-bi/
  NexusFinance/     editable PBIP, TMDL semantic model and PBIR report
  semantic-model/   semantic-model notes
  report/           report notes
  custom-visuals/   source for the bounded purposeful visuals
  validation/       model, measure, security and rendering checks
```

Before public-release work or material desktop-model changes, create a private,
checksum-bound archive using the
[private backup procedure](../docs/public-release/private-backups.md). The
backup includes ignored authoring workspaces without making those binaries part
of the public repository.
