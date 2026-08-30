# Milestone 5 Slice C2 - Consumer Materialisation

Status: Implementation authorised on 2026-08-25

## 0. Objective

Slice C2 materialises the verified `Q-FINANCE-C1@v1` consumption marts for
three deliberately different consumers. It changes physical delivery, not
financial meaning.

The release is `Q-FINANCE-C2@v1`. It must bind:

- C1 physical package digest
  `sha256:d03f6d5403a056dd0dad105366d81b9a3785f8eaa7be2e0216b2ad5eb2032e51`;
- C1 semantic digest
  `sha256:c2469194bb8646f1751e8dc822565579721b323a355083c4cea5c98a8cacd105`;
- A2.4 source digest
  `sha256:f78c55657d82be85539f168d39026843fadb87c82d01504b74d579502e593b4a`;
- all 21 Q-FINANCE v5 mart datasets plus eight conformed dimensions already
  present in C1; and
- the exact C1 schemas, row populations, values, nulls and integer-minor-unit
  money contract.

## 1. Consumer boundary

### React

React receives one directory per mart and one Parquet file per eligible period
year. Marts without `period_id` and the eight conformed dimensions receive one
unpartitioned file. The delivery includes a query catalogue and starter SQL but
no route, component, chart or dashboard.

### Excel

Excel receives schema-bound UTF-8 CSV for all 21 marts and eight conformed
dimensions. Nulls use the explicit
`\\N` token and the metadata publishes the exact DuckDB type for every column.

The XLSX data pack includes documentation, catalogue, controls, dictionary,
relationships, measure specifications, all eight conformed dimensions and
these eight typed mart sheets:

1. `mart_model_actuals_feed`
2. `mart_model_working_capital_drivers`
3. `mart_model_capital_schedules`
4. `mart_model_planning_inputs`
5. `mart_model_readiness_controls`
6. `mart_financial_performance_monthly`
7. `mart_balance_sheet_monthly`
8. `mart_cash_flow_liquidity_monthly`

The workbook is a data pack, not a three-statement model. It contains no
forecast formula, DCF, assumption, chart, external link, query connection,
macro or Data Model.

### Power BI

Power BI receives one ZSTD-compressed typed Parquet file per C1 mart and
conformed dimension plus:

- the C1 table catalogue and grains;
- column types, field roles, visibility and summarisation guidance;
- all v5 relationships touching a C1 mart, with endpoint delivery status;
- all 82 C1 measure specifications; and
- modelling instructions and reconciliation totals.

C2 emits no PBIX, PBIP, TMDL, Power Query M, DAX, calculation group, report
page, theme or visual.

## 2. Package shape

```text
Q-FINANCE-C2-V1/
|-- README.md
|-- delivery-manifest.json
|-- checksums.json
|-- finance-delivery.digest
|-- csv/
|   `-- <21 mart + 8 dimension>.csv
|-- parquet/
|   |-- react/<mart>/period_year=<yyyy>/part-00000.parquet
|   `-- powerbi/<mart>.parquet
|-- excel/
|   `-- finance-assurance-c1-data-pack.xlsx
|-- metadata/
|   |-- table-catalogue.json
|   |-- data-dictionary.json
|   |-- reconciliation.json
|   `-- workbook-logical-manifest.json
|-- react/
|   |-- query-catalogue.json
|   `-- starter-queries.sql
`-- powerbi/
    |-- tables.json
    |-- field-roles.json
    |-- relationships.json
    |-- measures.json
    `-- modelling-instructions.md
```

## 3. Invariants

1. C1 verifies before any mart is read.
2. C2 reads the C1 DuckDB warehouse in read-only mode.
3. Every mart is exported in deterministic first-key order.
4. Every format retains source columns in source order.
5. React and Power BI Parquet retain exact Arrow logical types.
6. CSV uses LF line endings, UTF-8 without BOM and `\\N` for null.
7. C2 metadata never enters a governed mart row.
8. Raw monetary values remain `BIGINT` minor units.
9. Workbook source sheets are formula-free and typed.
10. All per-format row counts and logical digests replay to C1.
11. Publication is atomic and never overwrites an existing target.
12. A resealed consumer-file mutation must be rejected by source replay.

## 4. Acceptance

- all 21 C1 marts and eight conformed dimensions are non-empty and materialised
  in all applicable formats;
- source mart rows total 55,951;
- 82 C1 measure specifications are delivered;
- 59 executable v5 relationships between delivered tables are supplied, with
  the one assurance-lineage relationship retained as documented external
  guidance;
- all 15 model-readiness controls pass;
- all balance-sheet, cash-flow, revenue-waterfall and tax/equity controls pass;
- the workbook is visually inspected sheet by sheet;
- no formula error, external link, macro or consumer model is present;
- checksum and detached digest scopes are closed; and
- independent verification returns `VERIFIED`.

React implementation, the Power BI semantic model, Excel forecast formulas and
Pythia scenario execution remain later consumer gates.
