# Milestone 5 Slice D3 - Cash, Working Capital and Capital Structure

Status: Implementation authorised on 2026-08-26

## 0. Objective

Slice D3 extends the browser-local CFO product with a governed `/cash-capital`
experience over the published `Q-FINANCE-C2@v1` delivery. It explains how
operating performance converts into cash, where liquidity is held or consumed,
and how working capital, debt, leases and fixed assets shape the balance sheet.

D3 answers six management questions:

1. What cash and available liquidity are held at the selected close?
2. Which operating, investing and financing movements explain the monthly cash
   change?
3. How much cash is tied up in receivables, payables and deferred revenue?
4. Which regions and customer segments drive overdue receivables and DSO?
5. What debt, lease and fixed-asset positions support the capital structure?
6. Do the cash-flow, balance-sheet and subledger positions reconcile to the
   exact hard-closed reporting version?

## 1. Product boundary

D3 provides:

- a `/cash-capital` route within the existing finance shell;
- group, UK and US statutory cash, balance-sheet and liquidity positions;
- monthly cash-flow bridge and a 66-month cash, debt and liquidity trend;
- receivables, payables, deferred-revenue and operating-working-capital views;
- DSO, DPO, overdue exposure and regional/segment collections analysis;
- debt and lease movements, capacity and capital-structure composition;
- fixed-asset net book value, additions, depreciation and class composition;
- visible reconciliation, reporting-version, reliability and package state; and
- exact runtime population replay for every admitted D3 table.

D3 does not provide:

- treasury forecasts, covenant forecasts or refinancing recommendations;
- a generated cash forecast, scenario, DCF or valuation result;
- invoice- or bank-transaction editing, remediation or workflow actuation;
- revenue-cohort and SaaS economics reserved for D4;
- control-case and end-to-end lineage exploration reserved for D5; or
- Excel formulas, DAX, a semantic model or Power BI visuals.

## 2. Data authority

D3 adds eight C2 marts to the D1-D2 browser runtime:

1. `mart_balance_sheet_monthly` - 198 scope-period statutory positions;
2. `mart_cash_flow_liquidity_monthly` - 198 reconciled scope-period cash rows;
3. `mart_ap_working_capital_monthly` - 66 group monthly working-capital rows;
4. `mart_model_working_capital_drivers` - 66 model-ready driver rows;
5. `mart_o2c_customer_collections_monthly` - 784 region-segment-period rows;
6. `mart_capital_structure_monthly` - 132 group and UK capital rows;
7. `mart_fixed_asset_capex_monthly` - 330 entity-asset-class-period rows; and
8. `mart_tax_equity_monthly` - 198 scope-period tax and equity rollforwards.

The statutory cash-flow and balance-sheet marts remain the authority for
published positions. Operational working-capital and collections marts explain
the drivers but do not replace statutory balances. The model driver mart is
labelled as a governed modelling feed and is not a forecast.

## 3. Analytical rules

1. Closing positions bind to one exact scope-period reporting version.
2. Cash bridge components are copied from the reconciled statutory cash-flow
   mart and must sum to the governed net change in cash.
3. Closing cash must equal opening cash plus net change in cash.
4. Available liquidity equals governed closing cash plus undrawn facility;
   D3 does not invent additional liquidity sources.
5. Net debt is a governed position and is never inferred from an unsigned debt
   label in the presentation layer.
6. Group working-capital metrics retain their source-provided operational and
   modelling authority labels; differences from statutory balance-sheet
   presentation are shown rather than plugged.
7. Regional collection values aggregate only rows for the selected period and
   retain their operational O2C reliability purpose.
8. Fixed-asset totals aggregate governed asset-class rows for the selected
   period; additions are not presented as cash expenditure unless a governed
   cash-flow row identifies them as such.
9. UI selections filter loaded rows and never become SQL identifiers or
   unvalidated SQL literals.
10. Money remains integer minor units until the presentation boundary.
11. Missing scope, comparison or runtime rows produce a visible unavailable
    state rather than an invented value.

## 4. Acceptance

- D1 and D2 routes remain buildable and behaviourally intact;
- the Cash & Capital navigation item and route are active;
- all sixteen D1-D3 runtime tables replay to their C2 row counts;
- the latest group cash row is June 2026 and binds to
  `RV-NEXUS-GROUP-2026-06@v1`;
- cash bridge components reconcile to net cash movement and closing cash;
- statutory balance-sheet difference and cash-flow unreconciled difference are
  zero for every admitted row;
- group, UK and US scope selection never fabricates unsupported capital rows;
- working-capital and collections views retain their distinct authority labels;
- fixed-asset composition reconciles to the selected asset-class rows;
- loading, empty and runtime-error states remain explicit; and
- focused D1-D3 tests, full application tests, typecheck, lint and build pass.
