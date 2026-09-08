# Excel Product Workspace

## Intended product

The v0.2 Excel product will be an authored integrated three-statement and DCF
model. It will consume one exact C2 data delivery package, not raw source
events or a private warehouse.

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
