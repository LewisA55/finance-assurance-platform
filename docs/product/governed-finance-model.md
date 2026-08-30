# Governed Finance Model

Status: Slice C1 governed consumption marts complete and verified on 2026-08-25

## 0. Purpose

The governed finance model restores the data-engineering and analytical spine
between the ratified A2.4 source authority and later consumer implementations.
It is a dbt and DuckDB transformation product, not a second ledger and not a
consumer dashboard.

Slice B1 covers the statutory accounting spine. Slice B2 extends that spine
with fixed assets, banking, debt, leases, tax, equity, accruals, prepayments,
intercompany, Hermes admission outcomes, and Argus subledger controls. Together
they prove that typed Silver models and governed Gold datasets can consume the
exact A2.4 population while
preserving causality, reporting versions, reliability, evidence, integer
minor units, and source lineage.

Slice B3 restores the original Atlas operational-finance depth over that
statutory foundation. It adds billing, recognised revenue, procurement,
workforce, SaaS-state, daily AR/AP, and integrated working-capital analytics
without treating operational snapshots or allocations as new posting causes.

Slice B4 closes the atomic model with governed budget, forecast, variance-
source, and headcount-plan inputs. It binds scenarios to an exact reliable
Atlas actuals cutover without claiming a governed Pythia G-11 snapshot or
turning plans into accounting events.

Slice C1 adds 21 executive, presentation, and model-serving marts. These are
governed projections over B1 through B4, not new sources of actuals or plans.
They replace the original Atlas synthetic opening balance, proxy opex, and
source-file readiness logic with versioned statutory history and validators.

Slice B4 closes the atomic model with governed budget, forecast, variance-
source, and headcount-plan inputs. It binds scenarios to an exact reliable
Atlas actuals cutover without claiming a governed Pythia G-11 snapshot or
turning plans into accounting events.

## 1. Authority boundary

Every governed finance-model build must bind:

- data reference `ATLAS-FINANCE-STATUTORY-A24@v1`;
- source package digest
  `sha256:39af66f379d5497399f89e3956e601b6fb99a070146d8c6d378bb684f288b7e5`;
- statutory contract `A2.4`;
- a closed finance-model profile (`Q-FINANCE-B1@v1`,
  `Q-FINANCE-B2@v1`, `Q-FINANCE-B3@v1`, `Q-FINANCE-B4@v1`, or
  `Q-FINANCE-C1@v1`); and
- the read-only source attachment mode.

The build verifies A2.4 before transformation and again during package
verification. dbt writes only to the separate analytical warehouse. Silver
views may read the attached Bronze authority; no Silver or Gold operation can
update it.

```text
sealed A2.4 Bronze DuckDB (read-only)
-> strict Silver views
-> conformed Gold dimensions and atomic facts
-> Q-FINANCE registries
-> sealed B1, B2, B3, B4, or C1 analytical warehouse
```

## 2. Original Atlas migration decisions

| Original Atlas asset | B1 disposition | Current treatment |
|---|---|---|
| dbt and DuckDB transformation pattern | Adapt | Restored with pinned dbt-core 1.11.11 and dbt-duckdb 1.10.1 |
| accounting GL staging | Adapt | Rebound to A2.4 business-event journal lines and strict minor-unit types |
| chart-of-accounts dimension | Adapt | Retains governed A2.4 statement, normal-balance, and cash-flow semantics |
| date dimension | Adapt | Rebuilt from the complete 186-period finance calendar |
| GL actuals fact | Adapt | Adds legal entity, causal business event, posting rule, source record, and reliability coordinates |
| trial-balance staging | Supersede | Uses 66 months of entity and consolidated versioned statutory trial balances |
| financial-statement extract | Supersede | Uses the complete A2.4 three-statement population and trial-balance digest |
| opening-balance-sheet model | Retire | Formation is replayed from zero; no synthetic opening anchor enters Gold |
| presentation-basis opex proxy | Quarantine for later review | It cannot substitute for statutory actuals in B1 |
| executive and modelling marts | Restore | C1 publishes 21 governed marts over the ratified atomic model |

The original repository remains a migration source only. B1 has no runtime
path dependency on it.

## 3. Silver contract

Silver contains thirteen strict views:

- periods and legal entities;
- chart of accounts;
- causal business events and accounting lifecycle events;
- source GL and consolidation elimination journal lines;
- statutory trial balances and statement lines;
- retained-earnings and cash-flow reconciliations;
- monthly close status; and
- statutory reconciliation results.

Dates, timestamps, integers, booleans, and currencies are typed explicitly.
Invalid values fail model execution instead of becoming silent nulls. Source
row hashes, file hashes, ingestion time, source file, and source data reference
remain visible technical lineage fields.

## 4. Q-FINANCE Gold registry

`Q-FINANCE@v1` registers fifteen datasets:

| ID | Gold relation | Grain |
|---|---|---|
| QF-D01 | `dim_period` | one row per fiscal month |
| QF-D02 | `dim_legal_entity` | one row per legal entity |
| QF-D03 | `dim_reporting_scope` | one row per entity or group scope |
| QF-D04 | `dim_gl_account` | one row per governed GL account |
| QF-D05 | `dim_reporting_version` | one row per period, scope, and reporting version |
| QF-D06 | `fct_business_events` | one row per causal business event |
| QF-D07 | `fct_accounting_events` | one row per accounting lifecycle event |
| QF-D08 | `fct_gl_journal_lines` | one row per posted source journal line |
| QF-D09 | `fct_elimination_journal_lines` | one row per consolidation elimination line |
| QF-D10 | `fct_statutory_trial_balance` | one row per period, scope, entity, account, and version |
| QF-D11 | `fct_statutory_statement_lines` | one row per period, scope, statement line, and version |
| QF-D12 | `fct_retained_earnings_bridge` | one row per period, scope, and version |
| QF-D13 | `fct_cash_flow_reconciliation` | one row per period, scope, and version |
| QF-D14 | `fct_monthly_close_status` | one row per period, scope, and version |
| QF-D15 | `fct_statutory_reconciliations` | one row per period, scope, control, and version |

Gold contains 480,059 rows for the portfolio A2.4 authority. It does not
persist major-unit display values. All governed monetary fields remain signed
64-bit minor units and retain currency.

## 5. Tool-neutral governance

Four physical catalogues accompany the warehouse:

- dataset registry: identity, grain, owner, model class, consumption class,
  reliability purpose, source authority, and money contract;
- relationship registry: eighteen exact endpoints, cardinalities, filter
  dispositions, and enforcement purposes;
- measure registry: fifteen exact or additive minor-unit measure
  specifications with required grain and reporting-version policy; and
- lineage registry: Gold model, direct Silver dependencies, A2.4 Bronze
  sources, and transformation class.

These catalogues guide later React, Excel, and Power BI implementations. They
do not prebuild dashboards, workbook formulas, DAX, or a semantic model.

## 5.1 B2 successor registry

`Q-FINANCE@v2` preserves all fifteen B1 dataset identities and adds twenty-
seven governed Gold datasets. The additions comprise five dimensions, twenty-
one domain facts, and one reusable subledger-event bridge. The closed B2
registry therefore contains 42 datasets, 58 relationships, 50 measures, and
42 lineage entries.

The bridge `fct_subledger_event_links` resolves every posting-driving B2 object
to its causal business event, B1 journal-line totals, legal entity, accounting
period, exact reporting version, close status, and purpose-specific reliability
state. Accounting lifecycle events remain separate and are used only for
elimination, close, reversal, restatement, and publication lineage.

The B2 portfolio warehouse contains 661,380 Gold rows. Atomic source facts
retain admitted, admitted-with-warning, and quarantined outcomes. In
particular, the declared duplicate prepayment remains visible but is not
posting eligible; B2 does not silently clean or delete it.

## 5.2 B3 successor registry

`Q-FINANCE@v3` preserves all 42 B2 dataset identities and adds 30 operational-
finance datasets: eight conformed dimensions, a reusable operational-event
bridge, atomic billing/revenue/procurement/workforce facts, full daily AR and
AP snapshots, monthly subscription state, a SaaS movement bridge, and
integrated monthly working capital. The v3 catalogues contain 72 datasets,
109 relationships, 94 measures, and 72 lineage entries.

`fct_operational_event_links` contains 139,294 exact links for customer
invoices, cash receipts, recognised-revenue rows, vendor invoices, vendor
payments, payroll lines, and posted capital invoices. Each link resolves to
the causal B1 business event, reporting-currency journal totals, legal entity,
hard-close version, reliability purpose, and A2.4 digest. Invoice lines,
payment allocations, subscription lifecycle records, and ageing snapshots
retain parent lineage but do not pretend to be independent posting causes.

The B3 portfolio warehouse contains 4,551,697 Gold rows. This includes
2,700,542 daily AR snapshots, 587,442 daily AP snapshots, 156,056 monthly
subscription states, 10,920 product-region-segment SaaS movement rows, and 66
integrated monthly working-capital rows. Total AP is explicitly separated into
trade and capital AP before reconciling to B1. The one quarantined duplicate
capital invoice remains visible as `SOURCE_RECORD_UNPOSTED` and cannot acquire
ledger authority through analytical transformation.

## 5.3 B4 final registry

`Q-FINANCE@v4` preserves all 72 B3 dataset identities and adds six planning
datasets: budget version, forecast-version scenario, atomic budget lines,
atomic forecast lines, a management variance source report, and planned
positions. The final catalogues contain 78 datasets, 127 relationships, 107
measures, and 78 lineage entries.

The portfolio contains one approved and locked BASE scenario plus draft BULL
and BEAR scenarios. All three start from the exact hard-closed
`RV-NEXUS-GROUP-2026-06@v1` Atlas actuals version and contain 120 forecast
months. Approval differences remain visible; B4 does not promote draft
scenarios or create forecast conclusions.

The management variance extract remains explicitly non-statutory. Its 10,416
rows preserve source-system actual, budget, and BASE forecast values and exact
lineage to their source plan lines. Statutory actuals continue to come only
from the Atlas reporting-version facts.

## 6. Reliability

Reliability is purpose-specific. A reporting version is
`RELIABLE_FOR_STATUTORY_ACTUALS` only when it is hard closed and its subledger,
bank, intercompany, trial-balance, and statement states have their exact
accepted domain values. Every versioned Gold fact inherits that status, the
`STATUTORY_ACTUALS` purpose, and the A2.4 package digest.

An operational metric may later have a different valid purpose and status.
B1 does not promote statutory reliability into a universal quality label.

## 7. Executable controls

dbt executes 71 tests. A separate package verifier independently executes 16
logical controls covering:

- Gold-to-Silver population closure;
- integer minor-unit typing;
- journal balance and business-event lineage;
- entity GL to trial-balance replay;
- group entity plus elimination replay;
- trial-balance roll-forward;
- cash-flow, retained-earnings, net-income, and balance-sheet identities;
- statutory reconciliation status;
- reporting-version reliability and source digest;
- Q-FINANCE registry and relationship closure; and
- exact A2.4 source references across all fifteen Gold datasets.

The package verifier also checks every file checksum, physical inventory,
model schema, row count, catalogue export, and semantic digest.

B2 executes 175 dbt tests and 27 independent semantic controls. In addition to
all applicable B1 controls, they replay subledger populations, monthly
rollforwards, prior-period continuity, bank-statement running balances,
source-event-to-schedule movement, event-to-B1-GL totals, reporting-version
bindings, dual intercompany admissions, eliminations, Argus exceptions, Hermes
quarantines, and Q-FINANCE v2 registry closure.

B3 executes 289 dbt tests and 42 independent semantic controls. The successor
controls prove complete operational populations, event-to-B1 journal replay,
billing-line and cash-allocation identities, closed-horizon revenue coverage,
deferred-revenue continuity, procurement and payroll reconciliation, the
capital posting/quarantine boundary, temporal SaaS-state replay, MRR movement
including FX remeasurement, AR/AP/deferred-revenue agreement to the B1 trial
balance, and Q-FINANCE v3 registry closure.

B4 executes 327 dbt tests and 53 independent semantic controls. The final
controls add plan population closure, horizon and scenario isolation, exact
Atlas cutover binding, variance replay, source-line resolution, headcount
governance, truth-class separation, and Q-FINANCE v4 closure.

## 8. Slice B ratification

The sealed B4 package was rebuilt from the same A2.4 authority in a separate
path and at a different build time. Both builds produced identical model
signatures, byte-identical v4 registry exports, and semantic digest
`sha256:2694d3ae0b23fda844fd8b9b1a876aa7e77f4654c1727ca9851111242b948365`.
The different physical package digests correctly preserve their different
build manifests. Slice B is ratified.

## 9. Slice C1 acceptance

The verified `Q-FINANCE-C1@v1` package contains 70 Silver views, 99 Gold
datasets with 4,641,980 rows, and 20 governance tables. The 21 C1 marts add
55,951 rows across executive financial and operating analysis, presentation,
command-centre, model actuals, working-capital drivers, capital schedules,
planning inputs, and validator-produced readiness controls.

`Q-FINANCE@v5` contains 99 datasets, 187 relationships, 189 measures, and 99
lineage entries. All 387 dbt tests and 64 independent controls pass. A resealed
revenue mutation was rejected by `C1_STATUTORY_MARTS_RECONCILE`.

A separate full build at a different timestamp produced identical 189 model
signatures, byte-identical v5 registry exports, and semantic digest
`sha256:c2469194bb8646f1751e8dc822565579721b323a355083c4cea5c98a8cacd105`.
The published physical package digest is
`sha256:16b7795117b7bba57f9d7f7fcb0b72dcdd36f346668611dddad4400a15ad5d8a`.

The corrected acceptance logic is scale-portable: domain coverage is derived
from eligible admitted source periods while the executive readiness gate still
requires at least 60 months. The smoke profile and full portfolio both pass.

React pages, DuckDB-Wasm/Parquet delivery, Excel formulas and valuation,
Power BI semantic implementation, and Pythia forecast execution remain later
bounded consumer gates.
