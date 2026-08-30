# Milestone 5 Slice A1 - Finance Data Substrate

Status: Implemented and independently verified on 2026-08-24

## 1. Outcome

Slice A1 restores the high-volume Atlas finance-data substrate inside the
Finance & Assurance Platform. It produces deterministic synthetic source-system
records, an explicit intentional-defect registry, generation QA, and a lossless
DuckDB Bronze layer for five years plus current YTD.

The accepted portfolio population is:

- data reference: `ATLAS-FINANCE-PORTFOLIO@v2`;
- actual history: 2021-01 through 2026-06, 66 monthly periods;
- 41 closed source datasets;
- 4,079,677 source rows;
- 139,551 causal business events;
- 315,827 source-system journal lines;
- 274 declared intentional defects;
- 7 source-generation QA checks, all passing; and
- package digest:
  `sha256:b962f39ca04ee25fac1524126b0494f612285a56a1525e3ce9456aa42d813e38`.

The package is physically available at:

`build/finance-data-substrate/ATLAS-FINANCE-PORTFOLIO-V2`

The earlier `ATLAS-FINANCE-PORTFOLIO@v1` scale run is superseded by v2 because
v2 completes the original Atlas-shaped source inventory described below.

## 2. Bounded authority

This slice owns synthetic source generation and Bronze ingestion only.

Bronze preserves source-system truth. It deliberately loads every CSV source
column as text and adds only source-row hash, ingestion time, source file,
source-file hash, and source data-reference metadata. It is not accounting
truth, a typed Silver layer, a governed Gold/Q mart, or a consumer semantic
model.

The generator may produce a source-system journal only from a generated
`BUSINESS_EVENT`. Accounting lifecycle events never enter this posting path.
Every journal is balanced in reporting-currency integer minor units before it
is written, and independent package verification repeats journal, period, and
business-event binding controls from the closed DuckDB database.

## 3. Restored source inventory

The 41 source products cover:

| Domain | Restored source products |
|---|---|
| Reference | fiscal periods, regions, FX rates, departments, products, product price book |
| Customer and revenue | customers, CRM accounts, subscriptions, subscription events, invoices, invoice lines, payments, allocations, daily AR ageing, revenue schedule, deferred-revenue roll-forward |
| Procurement | vendors, vendor invoices, vendor invoice lines, vendor payments, daily AP ageing |
| Workforce | employees, monthly headcount, payroll, compensation components, headcount plan |
| Planning | budget versions and lines, forecast versions and scenarios, variance source extract |
| Accounting | chart of accounts, source GL lines, opening balance sheet, monthly trial balance, financial-statement extract |
| Event and governance | business events, intentional-defect registry, generation QA, source-output inventory |

Largest accepted portfolio sources are:

| Source | Rows |
|---|---:|
| Daily AR ageing | 2,700,542 |
| Daily AP ageing | 587,442 |
| Source GL journal lines | 315,827 |
| Business events | 139,551 |
| Employee compensation components | 51,564 |
| Customer invoice lines | 41,820 |
| Revenue recognition schedule | 41,232 |
| Customer invoices | 36,593 |
| Payments | 34,141 |
| Planning forecast lines | 20,160 |

The population includes GBP, USD, EUR, and SGD source records and preserves
local and reporting-currency integer minor units where translation is needed.

## 4. Messy-data and control value

The portfolio intentionally includes, and separately declares:

- 171 unallocated cash receipts;
- 45 late-recorded billing events;
- 36 duplicate customer-invoice external numbers;
- 12 duplicate vendor-invoice external numbers;
- 8 CRM-to-billing customer-name drifts; and
- 2 HRIS rows with missing departments.

These defects remain source facts for Hermes/Silver tests. The generator does
not silently clean them, and Bronze does not mutate them.

## 5. Implementation map

- `src/finance_assurance/finance_data/definitions.py` closes dataset paths,
  grains, source systems, record classes, and ordered columns.
- `src/finance_assurance/finance_data/generation.py` streams the deterministic
  multi-domain population and constructs causal business-event/source-journal
  pairs.
- `src/finance_assurance/finance_data/bronze.py` creates the lossless DuckDB
  Bronze database and ingestion metadata.
- `src/finance_assurance/finance_data/service.py` stages, verifies, seals, and
  atomically publishes a package.
- `src/finance_assurance/finance_data/runner.py` exposes build and independent
  verify operations.
- `tests/finance_data/test_finance_data_substrate.py` proves package closure,
  causality, balancing, annual revenue/FX treatment, restored-source controls,
  and deterministic rebuilding.

## 6. Package boundary

```text
ATLAS-FINANCE-PORTFOLIO-V2/
|- raw/                         41 source CSV files
|- warehouse/
|  `- atlas-finance.duckdb     lossless Bronze plus load metadata
|- source-manifest.json
|- bronze-manifest.json
|- checksums.json
|- finance-data.digest
`- README.md
```

Raw CSV bytes, the stable source manifest, and README form the reproducible
canonical digest scope. The DuckDB file is verified against its same-build
manifest and by logical table/source controls, but its physical bytes are not
claimed to reproduce across database-engine builds.

## 7. Verification evidence

The accepted build passed:

- independent package digest, physical inventory, file hash, byte-count, CSV
  shape, minor-unit, and currency verification;
- exact raw-to-Bronze table, row-count, source-file hash, and ingestion-metadata
  closure for all 41 datasets;
- journal-level and period-level debit/credit equality;
- complete GL-to-business-event binding and unique causal event identities;
- annual-invoice reporting-revenue reconciliation without FX leakage;
- deferred-revenue roll-forward identities;
- payroll-to-compensation-component reconciliation;
- all generated source QA checks; and
- five focused Python tests, including a second deterministic build;
- the complete 306-test Python regression suite; and
- repository-wide Ruff lint plus focused format verification.

The verified package is approximately 653 MB, including a 243 MB DuckDB
database.

## 8. Deliberate limitations and next gate

Slice A1 does not type, clean, reject, conform, aggregate, or publish analytical
truth. The financial-statement extract and trial balance are source-system
reports, not yet the final three-statement or model-ready feed. No Parquet,
dbt Silver/Gold, Q registry extension, R/S handoff, React dashboard, Excel
model, Power BI semantic model, DAX, valuation, or forecast decision is emitted
by this slice.

Slice A2 is now the next mandatory gate. It adds source-backed banking, fixed
assets, debt, leases, tax, equity, accruals, prepayments, intercompany,
consolidation, three-statement, and monthly-close depth before any Silver/Gold
work begins. Its authority is recorded in
`docs/product/statutory-finance-source-substrate.md`.
