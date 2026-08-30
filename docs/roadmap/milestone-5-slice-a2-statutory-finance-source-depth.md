# Milestone 5 Slice A2 - Statutory Finance Source Depth

Status: Complete and ratified through Phase A2.4 on 2026-08-24

## 1. Gate decision

Slice A2 has passed. The operational A1 foundation has been extended through
source-backed statutory subledgers, multi-entity close, complete historical
statements, deterministic reproduction, and independent acceptance. Slice B
Silver/Gold is now authorised over the ratified A2.4 package.

## 2. Completed Phase A2.0

Phase A2.0 provides:

- a zero-opening formation policy from 2021-01-01;
- two legal entities and one group scope;
- an initial closed 26-dataset statutory source and control registry;
- exact ordered columns, grains, owners, and record classes;
- explicit business-event versus accounting-event journal origins;
- forbidden unlimited-revolver and minimum-cash-plug policies;
- a closed `A2-A01` through `A2-A30` acceptance catalogue;
- executable gate validation on import; and
- four passing structural tests.

The normative design is
`docs/product/statutory-finance-source-substrate.md`. The executable registry
and acceptance catalogue are
`src/finance_assurance/finance_data/statutory_gate.py`.

## 3. Implementation order

| Phase | Scope | Exit condition |
|---|---|---|
| A2.1 | formation, entities, banking, finite debt facilities | Complete - cash and bank statements reconcile monthly; formation derives from source transactions |
| A2.2a | fixed assets | Complete - independent sources pass through Hermes admission, Atlas rules and movements, and Argus controls |
| A2.2b | leases, tax, accruals, prepayments | Complete - source-backed schedules roll forward and reconcile to event-driven GL activity |
| A2.3 | intercompany, eliminations, entity/group TB, three statements, close | Complete - 66 months of entity/group statutory accounts reconcile with exact lineage |
| A2.4 | sealed package, portfolio build, reproduction, independent audit | Complete - all thirty A2 acceptance criteria pass from emitted bytes |

## 4. Non-authorised work

This gate does not yet author:

- typed or cleaned Silver models;
- Gold/Q dimensions, facts, measures, or marts;
- Parquet or Artifact R/S finance-modelling profiles;
- React statutory pages;
- Excel three-statement, forecast, WACC, or DCF formulas;
- Power BI models or DAX; or
- forecast financing decisions.

Those remain downstream of a passed A2 statutory source gate.

## 5. Completed Phase A2.1

The accepted physical package is:

- data reference: `ATLAS-FINANCE-STATUTORY-A21@v1`;
- path: `build/finance-data-substrate/ATLAS-FINANCE-STATUTORY-A21-V1`;
- actual history: 2021-01 through 2026-06;
- 49 closed source datasets and lossless Bronze tables;
- 4,192,604 source rows;
- 274 declared defects;
- 11 source-generation QA checks, all passing; and
- digest:
  `sha256:39effe6a0171376ba3563da8b90d6f66b6c0a9cebddab30dd979b9af2d4b405f`.

A2.1 adds eight source products to A1: legal entities, bank accounts, bank
transactions, bank statement lines, monthly bank reconciliations, debt
instruments, monthly debt schedules, and authorised equity movements.

Formation and funding are fixed source transactions rather than a cash plug:

- GBP 50.0m formation equity on 2021-01-01;
- GBP 15.0m term debt on 2021-01-01;
- GBP 20.0m Series B equity on 2024-01-02;
- GBP 25.0m growth equity on 2025-04-01; and
- a finite GBP 20.0m revolver that remains completely undrawn.

The portfolio emits 56,321 bank transactions and matched statement lines. All
126 required entity-bank months reconcile with zero difference. Independent
statement replay gives a minimum historical cash balance of GBP 5,795,788.10;
no financing event is generated from that balance. At 2026-06 the term loan is
GBP 4.5m, with GBP 10.5m repaid, while the revolver remains zero drawn.

The verifier recalculates cash-to-GL binding, one-to-one statement binding,
running balances, monthly reconciliation coverage and identities, debt
roll-forwards, prior-period continuity, contractual interest, facility
headroom, the zero-draw revolver policy, and equity event/journal/authorisation
binding from Bronze rows. It does not accept generator status flags as proof.
The same current verifier also reverified the unchanged 41-table A1 package at
its accepted digest.

Focused closure evidence is 12 passing finance-data tests, including a second
deterministic smoke build, plus repository-policy Ruff checks over the complete
finance-data implementation and tests.

## 6. Completed Phase A2.2a

The fixed-asset vertical is accepted as
`ATLAS-FINANCE-STATUTORY-A22-FA@v1`. It expands the executable A2 registry to 32
datasets and the physical package to 57 datasets by adding capital purchase
orders, goods receipts, capital invoices, asset lifecycle events, asset
register and movement records, Hermes admission results, and Argus controls.

The accepted package contains 4,199,209 rows and has digest
`sha256:24f4fdca761ad07cc1849bb3e6cf4a9752fbfe163ecc98c34bfb31c69c19c01c`.
Its exact implementation and evidence are recorded in
`docs/roadmap/milestone-5-slice-a22-fixed-asset-vertical.md`.

## 7. Completed Phase A2.2b

The statutory-subledger package is accepted as
`ATLAS-FINANCE-STATUTORY-A22B@v1`. It expands the physical package to 68
datasets and 4,207,578 rows. Leases, tax and tax losses, accruals, and
prepayments now have independent source records, Hermes admission, Atlas
posting rules and monthly schedules, and Argus controls. Its exact evidence is
recorded in
`docs/roadmap/milestone-5-slice-a22b-statutory-subledgers.md`.

## 8. Completed Phase A2.3

Phase A2.3 adds bilateral intercompany source records and confirmations,
entity business-event journals, accounting-event-derived consolidation
eliminations, entity/group trial balances, three historical statements,
retained-earnings and cash-flow reconciliations, and immutable monthly close
and publication events. Exact physical package evidence is recorded in
`docs/roadmap/milestone-5-slice-a23-multi-entity-close.md`.

The accepted `ATLAS-FINANCE-STATUTORY-A23@v1` package contains 78 datasets,
4,226,817 rows, and digest
`sha256:76ab92676bf255f760ab76d55ef662654c14f516e60032bea0677fc9958bb57e`.

## 9. Completed Phase A2.4

The ratified `ATLAS-FINANCE-STATUTORY-A24@v1` package contains 78 datasets,
4,227,015 rows, and digest
`sha256:f78c55657d82be85539f168d39026843fadb87c82d01504b74d579502e593b4a`.
An independent build reproduced all 82 canonical and seal files byte-for-byte.
The formal acceptance report contains thirty passes, zero failures, and digest
`sha256:daeeb099f5be7feec3de494f7f659776aeaa6c20316692dc30c5c7b3a9999791`.
Exact evidence is recorded in
`docs/roadmap/milestone-5-slice-a24-final-statutory-acceptance.md`.

## 10. Immediate next bounded slice

Slice B1 has now restored the typed statutory Silver and governed Gold spine
over the ratified A2.4 package. B2 is authorised to add the statutory
subledger analytical facts. Consumer models and experiences remain later
slices.
