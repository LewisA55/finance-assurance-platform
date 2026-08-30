# Atlas Finance Intelligence Integration

Status: Direction accepted - Slice A2 statutory substrate ratified

## 0. Product correction

The Finance & Assurance Platform must retain and enhance the original Atlas
Finance Intelligence Platform. Assurance is an extension of the finance
product, not a replacement for it.

The current platform has materially stronger event causality, accounting
integrity, evidence, assurance, governance, readiness, and decision contracts.
It currently has materially less historical finance data, analytical
transformation depth, CFO-facing product, financial modelling, and BI output
than the original Atlas repository.

The target is therefore:

> Original Atlas finance intelligence, rebuilt on the Finance & Assurance
> Platform's stronger governed substrate and enhanced by Hermes, Argus, Aegis,
> and Pythia.

## 1. Capability baseline

### 1.1 Original Atlas assets to retain

The original `D:/projects/finance-intelligence-platform` contains reusable
product assets including:

- approximately thirty synthetic source generators across accounting,
  billing, revenue, procurement, workforce, CRM, planning, and governance;
- intentional source defects that exercise data engineering and control
  handling;
- DuckDB raw ingestion and Bronze validation;
- seventy-six dbt SQL models across Silver and Gold;
- one hundred and ninety-five SQL tests;
- conformed finance dimensions and atomic facts;
- finance, SaaS, revenue, O2C, AP, workforce, modelling, presentation, and CFO
  executive marts;
- nine React analytical pages backed by DuckDB-Wasm and Parquet;
- integrated Excel three-statement and DCF models; and
- a Power BI implementation and export layer.

These are candidate implementation assets. They must be migrated under the
current platform invariants rather than copied as unexamined authority.

### 1.2 Current platform assets to retain

The current repository supplies capabilities the original did not establish
as rigorously:

- business-event causality and posting-rule boundaries;
- immutable journals, reversals, restatements, and reporting versions;
- source, accounting, assurance, governed, and decision truth separation;
- purpose-specific reliability and readiness;
- reproducible evidence and exact lineage;
- Hermes reconciliation and source-integrity products;
- Argus machine observations and exceptions;
- Aegis findings, issues, remediation, readiness, and sign-off;
- Pythia governed decision inputs and decisions; and
- verified P/Q/R/S packages with checksums, digests, and local handoff formats.

The integration must preserve both sets.

## 2. One platform, two cooperating planes

```text
FINANCE DATA AND INTELLIGENCE PLANE
synthetic source systems
-> DuckDB Bronze raw records
-> dbt Silver typed and cleaned records
-> Atlas accounting and reporting authority
-> dbt Gold / Q governed dimensions, facts, and marts
-> Parquet, DuckDB, CSV, Excel, Power BI, and React

FINANCE ASSURANCE AND GOVERNANCE PLANE
Hermes source integrity and reconciliation
-> Argus tests, observations, and exceptions
-> Aegis findings, issues, remediation, and readiness
-> Pythia assumptions, scenarios, forecasts, and decisions
-> reliability and evidence returned to governed Gold / Q products
```

These are not separate stacks. Gold models consume declared reliability and
readiness where required, and every public analytical value can drill through
to the relevant source, accounting, assurance, governance, and evidence
records.

## 3. Layer ownership

| Layer | Physical implementation | Product owner | Responsibility |
|---|---|---|---|
| Synthetic sources | Python generators and source CSV/Parquet | Hermes source boundary | Realistic finance-operating records and intentional defects |
| Bronze | DuckDB raw schemas | Hermes | Lossless source ingestion, ingestion metadata, source hashes |
| Silver | dbt views/tables | Hermes plus domain owner | Typing, cleaning, standardisation, rejection and reconciliation |
| Accounting | Event runtime and Atlas ledger | Atlas | Posting, immutable journals, periods, reporting versions, restatements |
| Gold core | dbt dimensions and facts implementing Q contracts | Atlas/domain owner | Conformed governed finance definitions and atomic analytical facts |
| Gold marts | dbt materialised marts implementing Q contracts | Atlas/Pythia with readiness inputs | CFO, domain, planning, and modelling surfaces |
| Assurance | Argus and Aegis records | Argus/Aegis | Observations, exceptions, findings, issues, remediation, readiness |
| Physical handoff | Artifact R and S | Shared delivery boundary | Typed Parquet, local DuckDB, CSV/XLSX, metadata, SQL, manifests and digests |
| Consumer products | React, Excel and Power BI | Independently governed consumers | Presentation, modelling, DAX/formulas, scenarios and decisions |

dbt Gold and Artifact Q must not become competing semantic layers. Gold is the
physical transformation implementation of registered Q analytical datasets.
Artifact R materialises the selected verified Q profile, and Artifact S
distributes it.

## 4. Preserved architecture invariants

Migration of the original Atlas assets is conditional on the following:

1. only `business_event` may drive posting-rule evaluation;
2. dbt never authors or mutates a posted journal;
3. Bronze and Silver preserve source-system truth rather than overwriting it;
4. rejected or corrected source records remain observable;
5. Atlas actuals and Pythia assumptions remain distinct populations;
6. predecessor and restated reporting versions remain simultaneous;
7. monetary values use signed integer minor units plus currency at governed
   boundaries;
8. every Gold/Q model declares grain, owner, lineage, aggregation, currency,
   version, scenario, and reliability policy;
9. intentional synthetic defects are registered test scenarios, not silent
   data-quality failures; and
10. consumer calculations cannot flow back into accounting or governed truth
    without a separately authorised lifecycle.

## 5. Restored Atlas analytical model

### 5.1 Core dimensions

The integrated model should restore and extend:

- date and fiscal period;
- legal entity and consolidation;
- GL account and statement mapping;
- department and business unit;
- region and market;
- customer, product, subscription, and segment;
- vendor;
- employee and position;
- budget version;
- forecast scenario;
- reporting version;
- control, reliability, and readiness classification; and
- evidence and lineage identity.

### 5.2 Atomic facts

The integrated model should restore and extend:

- GL actuals and monthly trial balance;
- budget and forecast lines;
- invoices, invoice lines, payments, and allocations;
- revenue recognition and deferred revenue roll-forward;
- customer and subscription periodic states and movements;
- vendor invoices, payments, and AP ageing;
- payroll, employee compensation, headcount, and workforce plan;
- operating metrics;
- fixed assets, CapEx, depreciation, and amortisation;
- debt, interest, repayments, and maturities;
- leases;
- tax;
- equity, dividends, and diluted shares;
- assurance observations and exceptions; and
- purpose-specific readiness and governed decision inputs.

### 5.3 Domain and executive marts

The first restored mart inventory includes:

- `mart_financial_performance`;
- `mart_o2c_customer_collections`;
- `mart_revenue_waterfall`;
- `mart_deferred_revenue_control`;
- `mart_ap_working_capital_control`;
- `mart_workforce_cost_control`;
- `mart_saas_arr_movement`;
- `mart_saas_retention`;
- `mart_model_actuals_feed`;
- `mart_opening_balance_sheet`;
- `mart_model_readiness_controls`;
- `mart_cfo_presented_financials`;
- `mart_cfo_presented_operating_metrics`;
- `mart_cfo_metric_readiness`; and
- `mart_executive_cfo_command_center`.

They must be upgraded with reporting-version identity, purpose-specific
reliability, evidence references, and drill-through coordinates from the
current platform.

## 6. Atlas product experience

The main product should again be an analytical CFO environment. The current
scenario routes become evidence and workflow drill-through, not the entire
product surface.

The integrated React product should contain:

1. CFO Command Center;
2. Financial Performance;
3. SaaS Performance;
4. Revenue Quality and Recognition;
5. Working Capital;
6. Workforce and Capacity;
7. Forecast and Valuation;
8. Control and Model Readiness;
9. Reporting Versions and Restatements;
10. Hermes Reconciliation;
11. Argus Assurance Exceptions;
12. Aegis Governance and Remediation;
13. Pythia Planning and Decisions; and
14. end-to-end lineage and evidence trace.

Every KPI or financial value should support a path from executive summary to
domain mart, atomic fact, accounting/reporting version, control state, and
evidence where applicable.

## 7. Shared consumer contract

React, Excel, Power BI, and future grounded commentary consume the same
registered Gold/Q profile.

### React

- DuckDB-Wasm queries compact same-origin Parquet;
- stable query-result contracts isolate components from table details;
- views use marts for common reads and atomic facts for drill-through;
- package and source digests remain visible; and
- the experience remains deployable without an application database.

### Excel

- governed actuals, opening balances, schedules, assumptions, and controls are
  loaded from the same profile;
- the integrated three-statement, DCF, WACC, scenario, and sensitivity logic
  is authored and audited in the workbook; and
- workbook outputs reconcile to the handoff digest and registered controls.

### Power BI

- typed Parquet supplies dimensions, facts, and marts;
- the model implements declared relationships and measures;
- DAX remains a consumer implementation of governed specifications; and
- model and report outputs reconcile to the same handoff.

### Commentary

- generated commentary may describe only metrics and reliability states
  present in the shared contract;
- every claim carries metric, period, scope, scenario, version, and evidence
  coordinates; and
- commentary never promotes an exception to a finding or decision.

## 8. Migration policy for original assets

The original Atlas repository is a migration source, not a runtime dependency.
Each migrated asset must be classified as:

- retain unchanged in behaviour;
- adapt to current contracts;
- supersede with a current implementation;
- retire because it duplicates authority; or
- quarantine pending reconciliation.

The migration records source path, destination path, behaviour change, test
coverage, finance owner, and governing dataset or product contract.

High-value candidates are migrated first:

- source generators and intentional-defect scenarios;
- Bronze ingestion and source QA;
- Silver typing and control models;
- Gold dimensions, facts, executive marts, and model-serving feeds;
- Parquet export and DuckDB-Wasm query contracts;
- CFO React pages;
- Excel model and reconciliation feeds; and
- Power BI export and implementation guidance.

No generated data, warehouse binary, dbt target output, dashboard build, or
consumer binary is treated as source code.

## 9. Bounded delivery sequence

### Slice A - Finance data substrate

- migrate source-generation configuration and core accounting, billing,
  revenue, planning, and workforce generators;
- produce five years plus current-YTD monthly synthetic history;
- restore raw DuckDB ingestion, Bronze inventory, source hashes, and deliberate
  defect registry; and
- map generated finance events into current business-event and accounting
  contracts where posting is required.

Implementation status: complete. The verified `ATLAS-FINANCE-PORTFOLIO@v2`
package contains 41 source datasets, 4,079,677 rows, 66 actual periods, a
lossless DuckDB Bronze layer, 274 declared defects, and seven passing generated
source-QA controls. The implementation and evidence are recorded in
`docs/roadmap/milestone-5-slice-a1-finance-data-substrate.md`.

### Slice A2 - Statutory finance source depth

- replace the synthetic opening anchor with zero-opening formation replay;
- add banking and bank reconciliation, fixed assets, debt, leases, tax,
  equity, accruals, prepayments, intercompany, and consolidation sources;
- derive 66 months of entity and group trial balances and three statements;
- require retained-earnings, cash-flow, subledger, and close reconciliations;
  and
- forbid unlimited-revolver, minimum-cash, and unsourced financing plugs.

Implementation status: Phase A2.1 treasury, A2.2 statutory subledgers, A2.3
multi-entity close, and A2.4 reproduction and independent acceptance are
complete. The ratified A2.4 package contains 78 datasets and 4,227,015 rows
across 66 actual months. It publishes UK, US, and group trial balances and all
three statements from the shared Atlas accounting state. Slice B Silver/Gold
is now authorised.
The fixed-asset vertical is the first implementation of independent source
records flowing through Hermes admission, Atlas posting rules and subledger
movements, and Argus machine controls. Its 57-table portfolio package contains
4,199,209 rows. A2 now passes and Silver/Gold Slice B is authorised. The
governing designs are `docs/product/statutory-finance-source-substrate.md` and
`docs/product/module-operating-model-vnext.md`.

### Slice B - Silver and Gold finance model

- restore core Silver typing, cleaning, rejection, and reconciliation;
- restore the conformed dimensions and atomic facts;
- register them as governed Q datasets with relationship, measure, lineage,
  reliability, and evidence contracts; and
- prove complete trial balance and three-statement control identities.

Implementation status: B1 through B4 are complete, independently verified,
and ratified. The pinned dbt/DuckDB project attaches A2.4 read-only and
publishes 70 typed Silver views, 78 `Q-FINANCE@v4` Gold datasets, and complete
dataset, relationship, measure, and lineage catalogues. Its 327 dbt tests and
53 independent controls pass. The Gold warehouse contains 4,586,029 rows and
rebuilds to an identical logical semantic digest. Slice C is now authorised.

### Slice C - Executive and modelling marts

- restore finance, SaaS, O2C, AP, workforce, revenue, presentation, readiness,
  command-centre, and model-serving marts;
- add current reporting-version, assurance, governance, and evidence fields;
  and
- build `FINANCE_MODELLING@1` through Artifact R and S.

Implementation status: C1 is complete and independently verified. The 21 marts
restore financial performance, the full monthly balance sheet and cash flow,
liquidity, O2C, revenue, AP and working capital, workforce, SaaS, fixed assets,
capital structure, tax and equity, management variance, CFO presentation,
command-centre, and model-serving feeds. `Q-FINANCE@v5` closes 99 datasets, 187
relationships, 189 measures, and 99 lineage entries. All 387 dbt tests and 64
independent controls pass, including current-state readiness replay and
private-copy mutation rejection. Artifact S can now package these marts in a
later consumer-delivery gate; C1 itself does not generate dashboards or models.

### Slice D - React finance intelligence

- restore the analytical CFO pages over DuckDB-Wasm and Parquet;
- add Hermes, Argus, Aegis, Pythia, reporting-version, and evidence
  drill-through; and
- retain static/serverless deployment.

### Slice E - Excel and Power BI

- reconnect the integrated Excel model to the new model-serving feed;
- independently audit formulas, statements, DCF, WACC, scenarios, and
  sensitivities;
- recreate the Power BI semantic implementation over the same Parquet profile;
  and
- reconcile both to React and the handoff controls.

## 10. Success condition

The integrated product is successful only when a reviewer can:

1. inspect messy synthetic source records and ingestion controls;
2. follow Bronze, Silver, and Gold transformation logic;
3. analyse five years of finance and operating performance;
4. use the CFO portal without a server-side analytical database;
5. trace a reported number to accounting and source evidence;
6. understand any assurance exception, finding, issue, remediation, and
   readiness effect;
7. build and reconcile a three-statement and DCF model from the same governed
   actuals; and
8. obtain consistent React, Excel, and Power BI answers from one snapshot and
   contract.

That outcome is more product than original Atlas and more usable finance
intelligence than the current assurance-only surface.
