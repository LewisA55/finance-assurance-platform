# Milestone 5 Slice B2 - Statutory Subledger Model

Status: Complete and verified on 2026-08-24

## 1. Verdict

B2 passes. The nine authorised statutory domains are now typed and analytical
without creating a second accounting authority. Every published rollforward
binds to the B1 period, legal entity, causal business event, posted journal,
reporting version, close state, reliability purpose, and exact A2.4 digest.

B2 is a successor to the sealed B1 contract. It preserves the B1 package and
`Q-FINANCE@v1` registry unchanged and publishes the additive
`Q-FINANCE@v2` registry.

## 2. Verified package

- model reference: `Q-FINANCE-B2@v1`;
- predecessor model reference: `Q-FINANCE-B1@v1`;
- package path: `build/finance-model/Q-FINANCE-B2-V1`;
- analytical warehouse: `warehouse/finance-analytics.duckdb`;
- source reference: `ATLAS-FINANCE-STATUTORY-A24@v1`;
- source digest:
  `sha256:f78c55657d82be85539f168d39026843fadb87c82d01504b74d579502e593b4a`;
- 38 Silver views;
- 42 governed Gold datasets containing 661,380 rows;
- 8 governance tables, including preserved v1 and successor v2 registries;
- 175 passing dbt tests;
- 27 passing independent semantic controls;
- model semantic digest:
  `sha256:411771535dc261c18f3f065f33ba2869407fbb2d2c70039721bc88970b3209b7`;
  and
- sealed package digest:
  `sha256:8feea0056e2a0f545ff4411860027e6f927d09b892ee32e09913e0877d59900b`.

## 3. B2 analytical contract

| Domain | Dimensions | Facts and evidence |
|---|---|---|
| Fixed assets | asset master | lifecycle events, monthly gross/accumulated depreciation/NBV movements, Argus controls |
| Banking | bank account | transactions, statement lines, monthly bank-to-GL reconciliation |
| Debt | debt instrument | principal, interest, repayment, facility and undrawn schedules |
| Leases | lease contract | lifecycle events, liability and ROU-asset schedules |
| Tax | entity jurisdiction | approved inputs, current/deferred tax schedule, loss vintages |
| Equity | B1 entity and period | authorised movements resolved to causal events and journals |
| Accruals | B1 account, entity and period | source estimates/settlements and monthly schedules |
| Prepayments | B1 account, entity and period | source cash/consumption events, quarantine state and schedules |
| Intercompany | B1 seller and buyer entities | bilateral transactions, confirmations and elimination lineage |

`fct_subledger_event_links` supplies the common navigation path from every B2
posting object to B1. It contains 59,061 resolved object-to-business-event
links. Every link has at least one posted B1 journal line and an exact reliable
hard-close reporting version.

## 4. Acceptance evidence

| Criterion | Evidence | Result |
|---|---|---|
| B2-A01 | A2.4 verified before build and source attached read-only | PASS |
| B2-A02 | twenty-five new strict Silver projections preserve technical lineage | PASS |
| B2-A03 | five conformed dimensions and twenty-two new facts close at declared grains | PASS |
| B2-A04 | all Gold monetary fields remain `BIGINT` minor units | PASS |
| B2-A05 | all source and Gold populations reconcile without dropped records | PASS |
| B2-A06 | asset, debt, lease, tax, accrual and prepayment rollforwards replay | PASS |
| B2-A07 | bank statement running balances and monthly GL reconciliations replay | PASS |
| B2-A08 | source accrual and prepayment events reproduce Atlas schedules | PASS |
| B2-A09 | every event link resolves to B1 event semantics, journal totals and close | PASS |
| B2-A10 | dual intercompany admission, cumulative balance and four-line elimination replay | PASS |
| B2-A11 | Argus pass results and the one expected prepayment exception are preserved | PASS |
| B2-A12 | Hermes late-arrival warnings and quarantine outcomes remain analytically visible | PASS |
| B2-A13 | Q-FINANCE v2 closes at 42 datasets, 58 relationships and 50 measures | PASS |
| B2-A14 | sealed B1 package remains independently verifiable at its original digest | PASS |

Eight finance-model service tests pass. A private B2 package copy was mutated
by adding one minor unit to a debt closing principal and then resealed. The
independent verifier rejected it at `B2_ROLLFORWARDS_RECONCILE`; regenerated
checksums could not promote an invalid subledger state.

## 5. Authority and consumer boundary

B2 derives analytics from A2.4 and B1 state. It does not post journals, amend
hard-closed periods, alter source admissions, convert Argus observations into
Aegis issues, or publish forecasts. React, Excel, and Power BI may consume the
facts and registry guidance later, but no dashboard, financial model, DAX,
TMDL, or report visual is generated here.

## 6. Next bounded gate

B3 may add the operational-finance domains: billing, revenue, procurement,
workforce, customer, product, vendor, employee, SaaS state, and detailed
working capital. Those facts must reuse the same B1/B2 dimensions, event
bridge, reporting versions, reliability purposes, and source authority.
