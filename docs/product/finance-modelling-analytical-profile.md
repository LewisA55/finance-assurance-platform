# Finance Modelling Analytical Profile

Status: Design v0.1 - bounded scope proposal, not yet ratified

## 0. Purpose

This profile expands the governed analytical population so independently
authored React, Excel, and Power BI work can perform credible historical
financial analysis, three-statement modelling, forecasting, and DCF valuation.

It does not turn Artifact S into a calculation engine. The authority flow is:

```text
synthetic business events and source records
-> Atlas accounting and reporting versions
-> Pythia planning assumptions
-> governed P/Q analytical datasets
-> Artifact R FINANCE_MODELLING@1 physical model
-> Artifact S local analytical handoff
-> React, Excel, and Power BI consumer projects
```

Historical actuals, planning assumptions, and market assumptions remain
distinct populations. Consumer formulas, DAX, visualisations, forecasts, and
valuation conclusions remain downstream work.

## 1. Current baseline and why it is insufficient

The current `LINEAGE@1` handoff is physically sound but intentionally narrow.
Its durable DuckDB model currently contains:

- two accounting periods: 2026-06 and 2026-07;
- one legal entity: NEXUS-UK;
- four ledger accounts;
- four statement lines;
- four reporting values across one predecessor and successor reporting
  version; and
- bounded C-001 and CT-1 scenario evidence.

That population supports lineage, restatement, correction, assurance, and
controlled reconciliation demonstrations. It cannot support a historical
trend, complete trial balance, three-statement model, forecast, WACC, DCF, or
peer-comparables claim.

The correction is an upstream population and semantic-profile expansion, not
an Artifact S transformation. Artifact S must continue to distribute exact
verified inputs without inventing missing finance facts.

## 2. Target analytical depth

The first `FINANCE_MODELLING@1` population should use the following bounded
synthetic depth:

| Coordinate | Target |
|---|---|
| Historical frequency | Monthly |
| Historical window | Five completed fiscal years plus current YTD |
| Forecast frequency | Monthly for two years, annual thereafter |
| Explicit forecast window | Ten years |
| Forecast scenarios | BASE, BULL, BEAR |
| Reporting currency | GBP |
| Consolidation | Group plus legal entity |
| Business segmentation | Governed segment dimension, including consolidated |
| Reporting versions | As-was and as-restated where applicable |
| Monetary storage | Signed integer minor units plus currency |
| Rates and ratios | Fixed-point decimal with declared scale |

This is synthetic portfolio depth, not production evidence or a benchmark.

## 3. Truth populations

### 3.1 Historical actuals

Historical actuals originate from Atlas accounting and reporting authority.
They include complete monthly ledger balances and statement values with exact
reporting-version identity. Restated and predecessor values remain
simultaneously available.

### 3.2 Operating metrics

Operating metrics originate from governed business-event or source-system
records. They may explain revenue or cost drivers but never silently replace
accounting values. Examples include customers, seats, units, utilisation,
headcount, and contract metrics.

### 3.3 Forecast assumptions

Forecast assumptions originate from Pythia and carry scenario, owner, basis,
effective period, approval state, source citation, and version. They are inputs
to later models, not forecast results emitted by Artifact S.

### 3.4 Market and valuation assumptions

Risk-free rates, equity risk premium, beta, borrowing rates, peer multiples,
terminal growth, and exit multiples form a separate assumption population.
Every value carries an as-of date, source or synthetic-basis reference,
currency where relevant, unit, and verification status. These values never
masquerade as Atlas actuals.

## 4. Conformed dimensions

| Dataset | Grain | Required purpose |
|---|---|---|
| `dim_period` | one fiscal period | Calendar, fiscal year, quarter, YTD, LTM, actual/forecast classification |
| `dim_entity` | one legal entity | Entity analysis and consolidation |
| `dim_segment` | one business segment | Revenue and margin driver analysis |
| `dim_account` | one chart-of-accounts version and account | Complete trial balance and account semantics |
| `dim_statement_line` | one statement taxonomy line | Income statement, balance sheet, and cash flow presentation |
| `bridge_account_statement` | one account-to-statement mapping | Reproducible statement derivation |
| `dim_reporting_version` | one immutable reporting version | As-was, as-restated, and publication history |
| `dim_scenario` | one planning scenario version | Base, bull, and bear isolation |
| `dim_currency` | one ISO currency | Exact currency and presentation policy |
| `dim_assumption` | one assumption definition | Driver identity, unit, aggregation, and allowed scope |
| `dim_asset_class` | one fixed/intangible asset class | CapEx, depreciation, and amortisation schedules |
| `dim_debt_instrument` | one debt or lease instrument | Debt, interest, maturity, and lease schedules |

Dimensions use stable governed keys. Consumer labels and display ordering stay
separate from business identity.

## 5. Governed facts and schedules

| Dataset | Grain | Core content |
|---|---|---|
| `fact_trial_balance_monthly` | period, entity, account, reporting version, currency | Opening, debit activity, credit activity, closing balance |
| `fact_statement_actual_monthly` | period, entity, segment, statement line, reporting version, currency | Governed income statement, balance sheet, and cash flow values |
| `fact_operating_metric_monthly` | period, entity, segment, metric | Revenue and operational drivers with units |
| `fact_working_capital_monthly` | period, entity, component, currency | Receivables, inventory, payables, deferred revenue, and other operating balances |
| `fact_capex_addition` | acquisition event or monthly asset-class addition | Tangible and intangible investment, life, method, and in-service date |
| `fact_fixed_asset_schedule_monthly` | period, entity, asset class, vintage | Gross book value, additions, disposals, depreciation/amortisation, closing NBV |
| `fact_debt_schedule_monthly` | period, entity, instrument | Opening principal, drawdown, repayment, interest, maturity, and closing principal |
| `fact_lease_schedule_monthly` | period, entity, lease instrument | Lease liability, right-of-use asset, interest, payment, and depreciation |
| `fact_tax_monthly` | period, entity, jurisdiction | Current tax, deferred tax, cash tax, and effective tax rate inputs |
| `fact_equity_monthly` | period, entity, equity component | Share capital, retained earnings, dividends, and diluted shares |
| `fact_forecast_assumption` | scenario, period, entity or segment, assumption | Growth, margin, working-capital, CapEx, tax, debt, and dividend drivers |
| `fact_market_assumption` | as-of date, assumption | Risk-free rate, ERP, beta, cost of debt, terminal growth, and exit multiple |
| `fact_peer_comparable` | as-of date, peer, metric | Revenue growth, margins, EV/revenue, EV/EBITDA, and other declared multiples |

The trial balance is the accounting basis. Statement facts must reconcile to
it through versioned mappings; operating metrics and assumptions must not be
posted into the ledger merely to make modelling convenient.

## 6. Registered analytical measures

The profile should register tool-neutral specifications for at least:

- revenue, COGS, gross profit, and gross margin;
- R&D, SG&A, depreciation, amortisation, and total operating expenses;
- EBITDA, EBIT, operating margin, interest expense, tax, and net income;
- cash from operations, CapEx, change in net working capital, and free cash
  flow;
- cash, gross debt, net debt, shareholders' equity, goodwill, intangibles, and
  lease liabilities;
- DSO, DPO, inventory days, asset turnover, and working-capital intensity;
- EBITDA-to-FCF conversion, ROIC, debt/EBITDA, and interest cover; and
- basic and diluted shares.

Each measure declares its source population, grain, aggregation, currency,
reporting-version policy, scenario policy, sign convention, and failure
behaviour. WACC, terminal value, enterprise value, equity value, per-share
value, and sensitivities remain consumer calculations over registered inputs.

## 7. Consumer delivery

### 7.1 React with DuckDB-Wasm

React should use the profile's Parquet files as the primary browser input.
DuckDB-Wasm registers local or same-origin Parquet and queries it in-browser.
The native `finance-assurance.duckdb` file remains useful for desktop SQL,
testing, and reconciliation, but is not the primary browser payload.

The React adapter should receive:

- partitioned Parquet facts and compact dimension Parquet files;
- a browser catalogue containing paths, hashes, row counts, grains, columns,
  and relationships;
- read-only view SQL for common historical, statement, driver, and lineage
  queries;
- query-result contracts for stable React data hooks;
- source and handoff digests displayed in the application; and
- bounded browser-size and query-latency acceptance checks.

No React view should have to rediscover joins, sign conventions, reporting
version selection, or currency rules.

### 7.2 Excel

Excel should receive model-ready source tables, not a finished financial
model. The data pack should include compact tables for:

- monthly and annual actual statements;
- operating metrics;
- working-capital history;
- CapEx and fixed-asset schedules;
- debt, lease, tax, and equity history;
- forecast assumptions by scenario;
- market and comparable inputs;
- source citations, relationships, measure definitions, limitations, and
  control totals.

The later Excel portfolio workbook may then build the three statements, DCF,
WACC, scenarios, and sensitivities with explicitly authored formulas.

### 7.3 Power BI

Power BI should receive the same typed Parquet facts and dimensions in a
declared star schema, plus relationship, field-role, format, summarisation,
measure, reporting-version, scenario, and lineage metadata.

The later Power BI project owns Power Query, TMDL, DAX, calculation groups,
report pages, and visuals. Every implemented measure must reconcile to the
tool-neutral specification and package digest.

## 8. Read-only query layer

The profile should provide non-authoritative read-only SQL for:

- monthly and annual income statements;
- monthly and annual balance sheets;
- cash flow statements and cash reconciliation;
- actual-versus-prior-period and actual-versus-restated bridges;
- segment revenue and margin trends;
- working-capital days and movements;
- CapEx, depreciation, amortisation, debt, lease, and tax roll-forwards;
- historical inputs required by a three-statement model;
- forecast-assumption matrices by scenario;
- WACC input extraction and peer-comparable checks; and
- full lineage from displayed value to reporting version, ledger population,
  business event, and evidence where available.

These queries expose governed inputs and registered measures. They do not
persist a forecast or valuation conclusion.

## 9. Reconciliation and acceptance

The expanded profile is not analysis-ready until all of the following pass:

1. every monthly trial balance balances by entity, period, version, and
   currency;
2. opening balance plus activity equals closing balance;
3. statement values reconcile to mapped trial-balance accounts;
4. assets equal liabilities plus equity for every balance-sheet date;
5. cash-flow movement reconciles opening to closing cash;
6. net income links consistently between the income statement, cash flow, and
   retained earnings;
7. depreciation and amortisation reconcile to fixed and intangible asset
   schedules;
8. interest and closing debt reconcile to debt schedules;
9. lease expense and liabilities reconcile to lease schedules;
10. tax expense, cash tax, and deferred tax movements reconcile;
11. historical actuals, forecast assumptions, and market assumptions remain
    distinguishable in every format;
12. predecessor and restated reporting versions remain simultaneous;
13. CSV, Parquet, native DuckDB, XLSX, and browser Parquet reconcile to one
    package snapshot and digest;
14. React query results, Excel source tables, and Power BI imports match the
    same registered controls; and
15. limitations continue to disclose synthetic depth and purpose-specific
    reliability.

## 10. Bounded implementation sequence

1. Ratify the finance-modelling population, horizon, entity, segment, and
   currency assumptions.
2. Extend the synthetic generator with monthly business events, opening
   balances, complete accounts, and governed schedules.
3. Extend Atlas and Pythia contracts without allowing assumptions to enter the
   posting engine.
4. Add governed P/Q datasets, relationships, measures, lineage, and controls.
5. Add and independently verify Artifact R `FINANCE_MODELLING@1`.
6. Rebuild Artifact S over that exact profile with CSV, Parquet, DuckDB, XLSX,
   metadata, SQL, and one digest.
7. Build the React DuckDB-Wasm adapter, Excel model, and Power BI model as
   separate consumer workstreams.

No later step may compensate for an unclosed earlier reconciliation by
hardcoding a consumer value.
