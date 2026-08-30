# Milestone 5 Slice A2.3 - Multi-Entity Close and Statements

Status: Implemented and independently verified on 2026-08-24

## 1. Gate decision

A2.3 is complete. Atlas now derives a 66-month statutory history for the UK
parent, US subsidiary, and consolidated group from the same event-driven
financial state. Silver/Gold remains blocked only by the final A2.4 package
reproduction and independent assessment gate.

## 2. Accepted package

- data reference: `ATLAS-FINANCE-STATUTORY-A23@v1`;
- path: `build/finance-data-substrate/ATLAS-FINANCE-STATUTORY-A23-V1`;
- actual history: 2021-01 through 2026-06;
- 78 closed source, reference, derived, and control datasets;
- 4,226,817 source rows and 78 lossless Bronze tables;
- 276 declared synthetic defects;
- 15 source-generation QA checks, all passing; and
- digest:
  `sha256:76ab92676bf255f760ab76d55ef662654c14f516e60032bea0677fc9958bb57e`.

## 3. Multi-entity source and accounting boundary

The population contains 120 bilateral intercompany transactions and 120
period/entity-pair confirmations from the US subsidiary's July 2021 start
through June 2026. Each transaction contains independent seller and buyer
source identities. Hermes authenticates and admits both exact-record views
before Atlas derives the two entity business events and balanced journals.

The positions remain open and bilaterally confirmed in this phase. They do not
fabricate cross-currency cash settlement. Seller receivables and buyer payables
roll forward to the same amount for every pair and month.

Atlas creates 60 consolidation accounting events and 480 group-only
elimination journal lines. The elimination interface accepts only
`ACCOUNTING_EVENT`; the entity posting interface accepts only `BUSINESS_EVENT`.
Accounting events never appear in the business-event population or source
posting path.

## 4. Historical close products

For every one of the 66 actual months and each of `NEXUS-UK`, `NEXUS-US`, and
`NEXUS-GROUP`, the package contains:

- 6,732 account-level trial-balance rows with opening, activity, elimination,
  closing, version, and hard-close state;
- 8,316 income-statement, balance-sheet, and cash-flow lines;
- 198 retained-earnings bridges;
- 198 cash-flow reconciliations;
- 198 monthly close and reporting-publication records; and
- 990 Argus statutory reconciliation results, five per period and scope.

The 654 accounting events comprise the 60 consolidation events plus soft
close, hard close, and reporting-version publication for every period and
scope. Consolidated intercompany receivables and payables close to zero.

Every statement, retained-earnings bridge, and cash reconciliation carries the
same digest of its exact source trial balance. A reporting version is published
only after balanced trial balance, balance-sheet equation, retained-earnings
roll-forward, cash-flow identity, and statement-lineage controls pass.

## 5. Successor correction

The A2.3 cumulative successor corrects a transitional A2.2b formation-lease
duplication. The London headquarters lease commencement now reuses the
source-backed `OPEN-LEASE` business event instead of creating a second
commencement journal when its lease schedule is constructed. The accepted
A2.2b package bytes and digest remain unchanged and independently verifiable.

## 6. Independent verification

The verifier recomputes from emitted Bronze rows:

- exact intercompany source hashes and two-sided Hermes admission;
- bilateral balance confirmation and cumulative continuity;
- source-to-entity event binding and journal balance;
- accounting-event isolation and elimination lineage;
- elimination amounts by period, transaction, balance, revenue, and expense;
- trial-balance completeness, arithmetic, continuity, and balance;
- consolidated intercompany balance elimination;
- exact trial-balance digests carried by all published products;
- retained-earnings roll-forward and income-statement agreement;
- balance-sheet equation;
- cash-flow identity and trial-balance cash agreement;
- soft-close, hard-close, and publication event resolution; and
- the exact population and pass state of all 990 Argus results.

The complete finance-data scope has 26 tests, including deterministic package
reproduction, plus a clean Ruff pass. The verifier remains compatible with the
accepted A1, A2.1, A2.2a, and A2.2b package inventories and digests.

## 7. Explicit non-scope

A2.3 does not build Silver/Gold marts, Parquet, React pages, Excel models,
Power BI models, forecasts, scenarios, DCF, Aegis cases, or automated
remediation. A2.4 audits the sealed historical source authority. Analytical
product construction resumes only after that gate passes.
