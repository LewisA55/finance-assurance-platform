# Consumer Products Workspace

This directory holds the separately authored analytical products that consume
the governed C2 delivery package. It does not own source events, accounting
truth, controls, reporting versions, or the governed semantic definitions.

| Product | Tracked here | Ignored locally | Release delivery |
|---|---|---|---|
| [Excel](excel/README.md) | Workbook preview, three-statement and DCF builder, model specification and validation controls | `excel/work/` and `excel/exports/` | Completed, reviewed workbook in the local authoring workspace |
| [Power BI](power-bi/README.md) | NexusFinance PBIP, TMDL model, PBIR report, custom visuals and validation | `power-bi/work/`, `power-bi/exports/` and Power BI Desktop cache | [Screenshot gallery](../docs/public-release/power-bi/README.md) and local Desktop export |
| [Executive briefing](executive-briefing/README.md) | Deck generator, chart code and print layout | `executive-briefing/exports/` | [June 2026 executive deck (PDF)](../docs/public-release/Nexus-June-2026-Executive-Deck.pdf) |

Every consumer product must pin one exact governed delivery manifest and state
its reporting version, purpose, scope, currency basis and reconciliation
controls. Consumer calculations may analyse published facts; they must not
create a second accounting or governed-truth authority.

The Excel and NexusFinance Power BI products completed the v0.2 and v0.3
milestones. The workspace keeps reviewable source and evidence in Git and
desktop exports and caches in local directories.

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
executive-briefing/  evidence-bound reporting deck and PDF build
```

Before public-release work or material desktop-model changes, create a private,
checksum-bound archive using the
[private backup procedure](../docs/public-release/private-backups.md). The
backup includes ignored authoring workspaces without making those binaries part
of the public repository.
