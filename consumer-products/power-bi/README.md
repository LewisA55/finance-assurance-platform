# Power BI Product Workspace

## Intended product

The v0.3 Power BI product will demonstrate a governed semantic model and a
small number of purposeful report experiences over the same C2 delivery
package consumed by Excel and React.

## Working boundary

- Keep model design, field roles, measure specifications, security design,
  TMDL/PBIP text source and validation specifications in this tracked
  directory when they are authored.
- Keep active `.pbix` files, imported delivery copies, desktop cache and
  rendered exports in `work/` or `exports/`; both are ignored.
- Publish the reviewed PBIX/PBIP as a tagged release asset with the exact C2
  manifest reference and reconciliation evidence.

The current `work/` directory is for private authoring only. It is deliberately
outside the v0.1 source boundary. The active Desktop file is kept locally as
`work/finance-assurance-platform.pbix` so future authoring has one stable home.
