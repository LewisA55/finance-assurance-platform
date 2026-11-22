# Excel Product Workspace

## Review model

The v0.2 Excel review model integrates the three financial statements, scenario
drivers and a DCF over one exact C2 delivery package. See the
[model specification](specifications/v0.2-model.md) for the data binding,
forecast conventions and rebuild command.

## Working boundary

- Keep model design, schedules, named-range conventions, input maps and
  validation specifications in this tracked directory.
- Keep evolving `.xlsx` files, linked copies of delivery data and rendered
  review exports in `work/` or `exports/`; both are ignored.
- Publish a reviewed workbook as a tagged release asset with its input package
  reference, control totals and reconciliation statement.

The C2 data-only Excel inspection pack is an input aid, not the model itself.
Its governed facts, relationships and measure guidance remain the source of
truth for the later workbook.

Tracked workbook specifications belong in `specifications/`; executable review
and reconciliation definitions belong in `validation/`. The private workbook
itself remains in `work/` until a reviewed release asset is published.
