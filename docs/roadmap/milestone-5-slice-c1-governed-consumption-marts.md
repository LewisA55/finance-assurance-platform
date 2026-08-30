# Milestone 5 Slice C1 - Governed Consumption Marts

Status: Complete and independently verified on 2026-08-25

## 0. Verdict

C1 passes. The published `Q-FINANCE-C1@v1` package is at
`build/finance-model/Q-FINANCE-C1-V1` and is bound to the exact A2.4 digest
`sha256:f78c55657d82be85539f168d39026843fadb87c82d01504b74d579502e593b4a`.

It contains 70 Silver views, 99 Gold datasets, 20 governance tables, 387
passing dbt tests, and 64 passing independent controls. The 21 new marts contain
55,951 rows; the complete Gold warehouse contains 4,641,980 rows.

The semantic digest is
`sha256:c2469194bb8646f1751e8dc822565579721b323a355083c4cea5c98a8cacd105`
and the sealed package digest is
`sha256:d03f6d5403a056dd0dad105366d81b9a3785f8eaa7be2e0216b2ad5eb2032e51`.

The acceptance tests and readiness replay derive eligible period coverage from
the admitted source domains. The explicit 60-month executive-history threshold
remains unchanged; the contract does not fabricate rows when an admitted domain
has a shorter valid history. The correction passes both the compact smoke
profile and the full portfolio authority.

## 1. Objective

Slice C1 publishes executive, presentation, and model-serving marts over the
ratified `Q-FINANCE-B4@v1` warehouse. It restores the analytical breadth of the
original Atlas product while using the deeper statutory, subledger, operational,
and planning authorities established in B1 through B4.

The release is `Q-FINANCE-C1@v1`, with `Q-FINANCE@v5` as its closed semantic
catalogue.

## 2. Authority boundary

C1 may aggregate, pivot, classify, and present governed B4 Gold records. It must
not create new business events, journals, statutory actuals, planning inputs, or
forecast results. A mart is a consumption projection, not a new source of truth.

Every C1 row must preserve:

- the exact A2.4 source reference and package digest;
- reporting-version identity wherever statutory actuals are used;
- purpose-specific reliability and value authority;
- a direct drill-through relation or evidence reference; and
- integer minor units for monetary values.

## 3. Closed mart inventory

### Executive analytical marts

1. `mart_financial_performance_monthly`
2. `mart_balance_sheet_monthly`
3. `mart_cash_flow_liquidity_monthly`
4. `mart_o2c_customer_collections_monthly`
5. `mart_revenue_waterfall_monthly`
6. `mart_ap_working_capital_monthly`
7. `mart_workforce_cost_monthly`
8. `mart_saas_performance_monthly`
9. `mart_fixed_asset_capex_monthly`
10. `mart_capital_structure_monthly`
11. `mart_tax_equity_monthly`
12. `mart_planning_performance_monthly`

### Presentation marts

13. `mart_cfo_presented_financials`
14. `mart_cfo_presented_operating_metrics`
15. `mart_cfo_metric_readiness`
16. `mart_executive_cfo_command_center`

### Model-serving marts

17. `mart_model_actuals_feed`
18. `mart_model_working_capital_drivers`
19. `mart_model_capital_schedules`
20. `mart_model_planning_inputs`
21. `mart_model_readiness_controls`

## 4. Corrections to original Atlas

- The synthetic opening-balance-sheet mart is retired. C1 serves all 66
  hard-closed monthly balance sheets from B1.
- Operating profit and expenses are never inferred from payroll plus AP spend.
  Financial performance uses published statutory statement lines.
- Readiness is computed from current warehouse populations, reconciliations,
  reporting versions, and scenario bindings. It is not loaded from a readiness
  CSV.
- Executive time ranges are derived from `dim_period`; no calendar window or
  current year is hard-coded.
- Department and operating classifications come from governed dimensions, not
  text matching.
- Planning variance remains a management-source report and is not promoted to
  statutory actual authority.

## 5. Acceptance gates

C1 passes only when:

1. all 21 marts are physically present and registered once in `Q-FINANCE@v5`;
2. every statutory mart reconciles exactly to B1 statement, trial-balance, or
   reconciliation facts;
3. every operational mart reconciles to its B3 atomic facts or governed monthly
   state;
4. capital, tax, and equity marts reconcile to B2 schedules and rollforwards;
5. planning marts preserve B4 truth-class and scenario boundaries;
6. model readiness is validator-produced and exposes failed evidence rather than
   copying expected results;
7. all monetary columns ending in `_minor` remain `BIGINT`;
8. all dbt tests and independent controls pass;
9. the sealed package verifies against the exact A2.4 source digest; and
10. a clean rebuild has the same semantic digest and registry exports.

## 6. Explicit exclusions

C1 does not build React pages, charts, Excel formulas, a three-statement model,
DCF mechanics, DAX, TMDL, Power BI visuals, or Pythia scenario execution. Those
consumer implementations will query these marts in later bounded slices.
