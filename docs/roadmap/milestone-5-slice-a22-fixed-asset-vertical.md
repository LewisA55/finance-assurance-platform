# Milestone 5 Slice A2.2a - Fixed-Asset Vertical

Status: Implemented and independently verified on 2026-08-24

## 1. Bounded outcome

A2.2a introduces the module operating model through one complete historical
fixed-asset domain without rewriting accepted A1 or A2.1 bytes.

It adds independent capital-procurement, fixed-asset, Hermes-admission,
Atlas-subledger, and Argus-control records to the source/Bronze package.

## 2. Required records

The vertical adds:

- capital purchase orders;
- capital goods receipts;
- capital supplier invoices and settlements;
- fixed-asset lifecycle events;
- fixed-asset register records;
- Hermes source-admission results;
- Atlas-derived monthly fixed-asset movements; and
- Argus fixed-asset control results.

## 3. Accounting treatment

The source generator supplies source facts, not journal lines. An Atlas-owned
fixed-asset posting-rule component derives capitalisation, settlement,
depreciation, impairment, and disposal postings from admitted facts.

Formation assets retain their existing A2.1 formation event identities and are
expanded into source-register detail without creating a second formation
journal.

## 4. Exit conditions

A2.2a passes only when:

1. every capitalised asset has a complete or explicitly formation-scoped
   source chain;
2. every posting-causing source record has one Hermes admission result;
3. quarantined duplicates create no business event or journal;
4. gross book value and accumulated depreciation roll forward by asset;
5. depreciation, amortisation, impairment, disposal, and capital additions
   reconcile to independently queried GL activity;
6. capital invoice settlements reconcile to bank and AP activity;
7. Argus results identify their frozen population, exact evidence, and first
   exception; and
8. current code continues to verify the accepted A1 and A2.1 packages.

## 5. Deferred work

This slice does not implement Aegis cases, Pythia CapEx forecasts, group close,
complete statements, Silver/Gold, React, Excel, or Power BI.

## 6. Accepted package

- data reference: `ATLAS-FINANCE-STATUTORY-A22-FA@v1`;
- path: `build/finance-data-substrate/ATLAS-FINANCE-STATUTORY-A22-FA-V1`;
- 57 closed source, reference, derived, and control datasets;
- 4,199,209 rows across 66 actual months;
- 275 declared defects;
- 13 generated QA results, all passing; and
- digest:
  `sha256:24f4fdca761ad07cc1849bb3e6cf4a9752fbfe163ecc98c34bfb31c69c19c01c`.

The portfolio contains 26 assets and 1,011 monthly asset movements. Independent
source populations contain 21 capital purchase orders, 21 receipts, and 22
invoices: 21 admitted chains plus one preserved duplicate. Hermes publishes
960 ordinary admissions, 6 late-arrival admissions with warnings, and 1
quarantine. The quarantined row creates no business event or journal.

Asset activity contains GBP 29.7m gross additions, GBP 13.19m depreciation,
GBP 3.61m amortisation, GBP 1.0m impairment, one GBP 2.0m gross disposal, and
GBP 0.15m disposal proceeds. Argus publishes 1,037 passing results and one
machine exception for the quarantined duplicate.

The independent verifier recalculates source-chain completeness, admission
source hashes, event binding, quarantine isolation, monthly movement identities
and continuity, asset-to-GL reconciliation, capital invoice AP and cash
settlement, and Argus result integrity from Bronze rows. Seventeen focused tests,
including deterministic rebuilding and negative posting/admission paths, pass.
Ruff passes across the implementation and tests. The accepted A1 and A2.1
packages also reverify at their original digests with the current code.
