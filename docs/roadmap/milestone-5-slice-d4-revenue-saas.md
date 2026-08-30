# Milestone 5 Slice D4 - Revenue and SaaS Economics

Status: Implementation authorised on 2026-08-26

## 0. Objective

Slice D4 extends the browser-local CFO product with a governed `/revenue-saas`
experience over the published `Q-FINANCE-C2@v1` delivery. It connects the
revenue subledger to subscription-state economics without treating ARR,
billings, collections and statutory revenue as interchangeable measures.

D4 answers six management questions:

1. How do opening deferred revenue, billings and recognised revenue explain the
   closing contract liability?
2. What new, expansion, contraction, churn and FX movements explain MRR?
3. What are current ARR, gross retention, net retention and customer scale?
4. Which products, regions and customer segments drive ARR concentration?
5. How do billings and collections compare with recognised revenue?
6. Do the revenue schedule, subscription state and executive presentation bind
   to the same period, reporting version and source package?

## 1. Product boundary

D4 provides:

- a `/revenue-saas` route within the existing finance shell;
- a 66-month recognised-revenue, billings and deferred-revenue history;
- deferred-revenue and monthly recurring-revenue bridges;
- ARR, MRR, retention, customer and subscription indicators;
- product, region and customer-segment portfolio composition;
- an explicit acquisition, expansion and churn signal;
- visible authority, reliability, reporting-version and package state; and
- exact runtime population replay for every admitted D4 table.

D4 does not provide:

- revenue forecasts, bookings targets, pipeline or sales recommendations;
- cohort lifetime value, CAC payback or unit economics without governed cost
  and acquisition attribution;
- transaction editing, remediation or workflow actuation;
- an assurance conclusion over revenue beyond the source reliability labels;
- Pythia scenarios, DCF or valuation results; or
- Excel formulas, DAX, a semantic model or Power BI visuals.

## 2. Data authority

D4 adds three C2 marts to the D1-D3 browser runtime:

1. `mart_revenue_waterfall_monthly` - 66 revenue-subledger period rows;
2. `mart_saas_performance_monthly` - 3,720 product-region-segment-period
   subscription-state rows; and
3. `mart_cfo_presented_operating_metrics` - 726 period-metric executive
   presentation rows.

The revenue waterfall is authoritative for deferred revenue and recognised
revenue. The SaaS mart is authoritative for MRR, ARR, retention, customer and
subscription state. Executive metrics provide a presentation-level
cross-check. Operational collections admitted in D3 remain a distinct O2C
authority and are not relabelled as revenue.

## 3. Analytical rules

1. Revenue waterfall rows bind to one exact group reporting version per period.
2. Opening deferred revenue plus new billings less recognised revenue must
   equal closing deferred revenue.
3. Scheduled and recognised revenue must retain their published reconciliation
   differences; D4 never plugs a difference.
4. Ending MRR equals beginning MRR plus new, expansion, contraction, churn and
   FX movements across the selected subscription cohorts.
5. ARR and customer counts aggregate only the selected period's published
   product-region-segment rows.
6. Gross and net retention are beginning-MRR-weighted ratios, not averages of
   cohort percentages.
7. Product, region and segment shares use ending ARR as the common denominator.
8. Revenue, billings, collections and ARR remain separately labelled measures
   with their original value authorities.
9. Missing movement categories remain zero or unavailable; they are not
   inferred from ending balances.
10. UI selections filter loaded rows and never become SQL identifiers or
    unvalidated SQL literals.
11. Money remains integer minor units until the presentation boundary.
12. Missing comparison or runtime rows produce a visible unavailable state.

## 4. Acceptance

- D1-D3 routes remain buildable and behaviourally intact;
- the Revenue & SaaS navigation item and route are active;
- all nineteen D1-D4 runtime tables replay to their C2 row counts;
- the latest D4 state is June 2026 and binds to
  `RV-NEXUS-GROUP-2026-06@v1`;
- every revenue waterfall equation and MRR movement equation reconciles;
- weighted retention and ARR composition use governed numerators;
- the page never labels billings, collections, ARR or deferred revenue as
  statutory revenue;
- unsupported forecasting and acquisition-cost measures remain absent;
- loading, empty and runtime-error states remain explicit; and
- focused D1-D4 tests, full application tests, typecheck, lint and build pass.
