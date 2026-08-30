# Milestone 5 Slice B3 - Operational Finance Model

Status: Complete and independently verified on 2026-08-24

## 1. Verdict

B3 passes. The governed finance warehouse now combines the B1 statutory spine,
the B2 balance-sheet subledgers, and the high-volume operating evidence that
made the original Atlas product analytically rich. B3 is an additive successor:
the sealed B1 and B2 packages and their registries remain unchanged.

Operational records do not acquire accounting authority merely by entering
Gold. Posting-driving invoices, receipts, recognised-revenue rows, payments,
payroll lines, and admitted capital invoices resolve to exact B1 business
events and journals. Lifecycle events, allocations, invoice lines, and daily
snapshots retain parent lineage as operational evidence.

## 2. Verified package

- model reference: `Q-FINANCE-B3@v1`;
- predecessor model reference: `Q-FINANCE-B2@v1`;
- package path: `build/finance-model/Q-FINANCE-B3-V1`;
- analytical warehouse: `warehouse/finance-analytics.duckdb`;
- source reference: `ATLAS-FINANCE-STATUTORY-A24@v1`;
- source digest:
  `sha256:f78c55657d82be85539f168d39026843fadb87c82d01504b74d579502e593b4a`;
- 64 Silver views;
- 72 governed Gold datasets containing 4,551,697 rows;
- 12 governance tables preserving the v1 and v2 catalogues and adding v3;
- 289 passing dbt tests;
- 42 passing independent semantic controls;
- model semantic digest:
  `sha256:bac36745e9516412468929d226d98e4d3de911b603a98f43b0802694c85637f4`;
  and
- sealed package digest:
  `sha256:0e2dceb70b6916b0202210198a280b21f15dc717a8cc15a4009884f7fd6374bc`.

## 3. B3 analytical contract

| Domain | Conformed state | Atomic and derived facts |
|---|---|---|
| Commercial | region, product, effective price, customer, subscription | lifecycle movements, invoices, lines, receipts and allocations |
| Revenue | customer, subscription and product | monthly recognition schedule and deferred-revenue rollforward |
| Procurement | vendor, department and GL account | vendor invoices, lines, payments, capital orders, receipts and invoices |
| Workforce | employee, department and region | payroll lines, compensation components and monthly headcount |
| SaaS | subscription month-end replay | MRR/ARR, new, expansion, contraction, churn, FX remeasurement and retention |
| Working capital | customer, vendor, period and reporting currency | full daily AR/AP and integrated monthly AR, trade AP, capital AP, deferred revenue, DSO and DPO |

The 30 B3 additions contain 3,890,317 rows. The largest governed facts retain
their original useful grain: 2,700,542 daily AR rows and 587,442 daily AP rows.
They are not replaced by monthly summaries. Monthly SaaS and working-capital
facts are additional replayable states for analytical consumption.

## 4. Accounting and defect boundary

`fct_operational_event_links` contains 139,294 causal links. Its journal totals
replay B1 in reporting currency and every link resolves to a reliable hard-
closed entity version.

The source contains 22 capital invoices but only 21 admitted posting chains.
B3 preserves all 22 records. The declared duplicate remains visible with no
business-event or journal authority, zero GL lines, `is_posted_to_gl = false`,
and reliability `SOURCE_RECORD_UNPOSTED`. The 21 admitted invoices resolve
through purchase order, goods receipt, business events, journals, payment and
fixed-asset identity.

Two employee-master rows contain blank department identifiers. They remain in
`dim_employee`; payroll and headcount use their actual period-level department
coordinates. B3 therefore preserves source defects without dropping valid
transactions or silently repairing the master.

## 5. Acceptance evidence

| Criterion | Evidence | Result |
|---|---|---|
| B3-A01 | exact A2.4 authority verified and attached read-only | PASS |
| B3-A02 | 26 new strict Silver views preserve full source populations | PASS |
| B3-A03 | 30 additive Gold datasets close at declared grains | PASS |
| B3-A04 | all 139,294 posting objects resolve to B1 events, journals and closes | PASS |
| B3-A05 | billing lines equal invoice net amounts | PASS |
| B3-A06 | allocations equal receipts and gross invoice amounts | PASS |
| B3-A07 | revenue schedules never over-recognise and completed service periods close | PASS |
| B3-A08 | deferred revenue formula and currency continuity replay | PASS |
| B3-A09 | vendor lines, invoices and payments reconcile | PASS |
| B3-A10 | capital three-way match preserves 21 posted plus one unposted record | PASS |
| B3-A11 | payroll components and total payroll cost reconcile | PASS |
| B3-A12 | month-end subscription state replays lifecycle events | PASS |
| B3-A13 | MRR bridge closes through new, expansion, contraction, churn and FX | PASS |
| B3-A14 | AR, total AP and deferred revenue agree to B1 group trial balance | PASS |
| B3-A15 | Q-FINANCE v3 closes at 72 datasets, 109 relationships and 94 measures | PASS |

A clean execution completed all 148 models and 289 tests. A separate process
then independently verified the sealed portfolio package and all 42 controls
at the published digest.

## 6. Consumer boundary and next gate

B3 is analysis-ready substrate, not a prebuilt dashboard, spreadsheet model,
Power BI semantic model, or Pythia forecast. React/DuckDB-WASM, Excel, and Power
BI can later consume the same facts and tool-neutral catalogues.

B4 is the remaining Slice B gate: planning facts, final Q-FINANCE closure,
deterministic logical rebuild, independent reassessment, and Slice B
ratification. Executive and model-serving marts remain Slice C.
