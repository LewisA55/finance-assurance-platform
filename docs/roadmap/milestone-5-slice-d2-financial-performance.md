# Milestone 5 Slice D2 - Financial Performance

Status: Implementation authorised on 2026-08-25

## 0. Objective

Slice D2 adds the first full analytical page to the D1 browser-local CFO
product. It explains the financial performance summarised by the command
centre without changing, repairing or resealing the published
`Q-FINANCE-C2@v1` delivery.

D2 answers five management questions:

1. What is the current statutory income-statement position?
2. How has that position changed monthly, year to date and over the last twelve
   months?
3. Which income-statement lines explain the movement?
4. How do the UK and US legal entities reconcile to the consolidated group?
5. How does the separate management-source actual compare with its approved
   budget without being promoted to statutory truth?

## 1. Product boundary

D2 provides:

- a `/financial-performance` product route within the existing D1 shell;
- monthly, year-to-date and last-twelve-month statutory performance views;
- revenue, gross profit, EBITDA, operating profit and net-income analysis;
- a full management income statement with prior-year comparison;
- a 66-month revenue, gross-profit and EBITDA trend;
- UK, US, group and calculated consolidation-effect analysis;
- management-source actual-versus-budget variance by statement line;
- visible reporting-version, close, reconciliation and reliability state; and
- exact runtime population replay for every D2 table.

D2 does not provide:

- a new statutory, planning or forecasting calculation authority;
- a generated forecast, scenario or valuation result;
- cash, working-capital or capital-structure analysis reserved for D3;
- revenue-cohort or SaaS analysis reserved for D4;
- control-case and end-to-end lineage exploration reserved for D5; or
- Excel formulas, DAX, a semantic model or Power BI visuals.

## 2. Data authority

D2 adds five C2 tables to the three-table D1 runtime:

1. `mart_financial_performance_monthly` - 198 statutory scope-period rows;
2. `mart_cfo_presented_financials` - 8,514 presented statement-line rows;
3. `mart_planning_performance_monthly` - 10,416 management-source variance
   rows;
4. `dim_reporting_scope` - three reporting scopes; and
5. `dim_reporting_version` - 198 hard-close reporting-version rows.

The management-source planning mart remains explicitly distinct from the
statutory mart. Its actual values are never substituted for statutory actuals,
and its budget comparison is labelled as a management-source report.

## 3. Analytical rules

1. Monthly values are copied from one exact scope-period reporting version.
2. YTD and LTM are consumer-owned sums of published monthly statutory rows.
3. Gross, operating and EBITDA margins are recomputed from the aggregated
   governed numerators and revenue denominator; basis points are not summed.
4. Prior-year comparison uses the corresponding basis ending twelve months
   before the selected period.
5. Consolidation effect equals group less UK less US for the selected basis.
6. Actual-versus-budget uses only the source-provided management variance mart.
7. Revenue variances are favourable when actual exceeds budget; expense
   variances are favourable when actual is below budget.
8. UI selections filter loaded rows and never become SQL identifiers or
   unvalidated SQL literals.
9. Money remains integer minor units until the presentation boundary.
10. A missing comparison, budget or runtime table produces a visible
    unavailable state rather than an invented value.

## 4. Acceptance

- D1 command-centre behaviour and assurance routes remain buildable;
- the Financial Performance navigation item and route are active;
- all eight D1/D2 runtime tables replay to their C2 row counts;
- the latest group row is June 2026 and binds to
  `RV-NEXUS-GROUP-2026-06@v1`;
- monthly, YTD and LTM totals reconcile to the governed monthly rows;
- the statement displays all defined income-statement lines and subtotals;
- group, UK, US and consolidation-effect values reconcile arithmetically;
- management actual and budget are visibly non-statutory source-report values;
- close, reconciliation, reliability and delivery coordinates remain visible;
- loading, empty and runtime-error states remain explicit; and
- focused D1/D2 tests, full application tests, typecheck, lint and build pass.
