# Milestone 5 Slice A2.4 - Final Statutory Acceptance

Status: Complete and ratified on 2026-08-24

## 1. Verdict

The complete A2 statutory finance source gate is ratifiable and ratified. All
thirty `A2-A01` through `A2-A30` criteria pass against a sealed portfolio
package and a separately built reproduction. No structural or semantic blocker
remains. Silver/Gold Slice B is authorised to begin over this exact source
authority.

## 2. Ratified package

- data reference: `ATLAS-FINANCE-STATUTORY-A24@v1`;
- source path:
  `build/finance-data-substrate/ATLAS-FINANCE-STATUTORY-A24-V1`;
- reproduction path:
  `build/finance-data-substrate/ATLAS-FINANCE-STATUTORY-A24-V1-REPRODUCED`;
- acceptance report:
  `build/finance-data-substrate/ATLAS-FINANCE-STATUTORY-A24-ACCEPTANCE.json`;
- statutory contract: `A2.4`;
- actual history: 2021-01 through 2026-06;
- 78 closed datasets and 78 lossless Bronze tables;
- 4,227,015 rows;
- 276 declared synthetic defects;
- 82 canonical and seal files reproduced byte-for-byte; and
- package digest:
  `sha256:f78c55657d82be85539f168d39026843fadb87c82d01504b74d579502e593b4a`.

The formal `statutory-acceptance-report@v1` contains thirty passes, zero
failures, and semantic digest
`sha256:daeeb099f5be7feec3de494f7f659776aeaa6c20316692dc30c5c7b3a9999791`.

## 3. Bounded A2.4 corrections

A2.4 preserves the accepted A2.3 bytes and produces a successor package. It
closes four final-proof obligations discovered during the criterion mapping:

1. formation replay now explicitly proves that every first-period statutory
   trial-balance opening is zero and that entity activity reproduces from the
   source GL;
2. every cash-flow statement carries a net-income anchor equal to the income
   statement and retained-earnings bridge without changing the direct-method
   operating, investing, and financing cash identity;
3. every hard-close accounting event cites all five passed Argus prerequisite
   reconciliation records; and
4. statement lineage replays entity GL activity, group entity aggregation,
   elimination activity, chart mappings, registered derivations, reporting
   versions, business events, and emitted source identities.

A2.4 also rejects any untraced non-zero dividend or other reserve movement.
The current population contains none; future activity must enter through an
authorised equity movement before it can affect retained earnings.

## 4. Structural reassessment

| Test | Result |
|---|---|
| Registry and manifest closure | PASS - 78 unique declared and physical paths |
| Ordered CSV schemas | PASS - exact headers and row widths |
| Monetary contract | PASS - integer minor-unit text plus explicit currency |
| Source hash closure | PASS - each raw file binds to manifest, checksum ledger, and Bronze table |
| Physical package closure | PASS - no undeclared file is admitted |
| Truth ownership | PASS - Hermes source/admission, Atlas accounting/reporting, Argus assurance remain distinct |
| Event-origin firewall | PASS - entity posting accepts only business events; consolidation accepts only accounting events |
| Reporting-version closure | PASS - statements resolve to one hard-closed trial-balance version |
| Predecessor immutability | PASS - A1, A2.1, A2.2a, A2.2b, and A2.3 verify at their accepted digests |
| Reproduction boundary | PASS - canonical source and seal bytes reproduce; DuckDB is logically revalidated rather than declared canonically byte-stable |

## 5. Thirty-criterion semantic reassessment

| Criterion | Evidence | Result |
|---|---|---|
| A2-A01 | closed manifest and physical inventory | PASS |
| A2-A02 | zero-opening formation and first-period GL replay | PASS |
| A2-A03 | business-event-to-source-journal trace | PASS |
| A2-A04 | accounting-event origin guard and elimination trace | PASS |
| A2-A05 | monetary schema scan | PASS |
| A2-A06 | raw-to-Bronze hash and logical closure | PASS |
| A2-A07 | GL cash-to-bank transaction join | PASS |
| A2-A08 | bank-statement running-balance replay | PASS |
| A2-A09 | monthly bank reconciliation | PASS |
| A2-A10 | fixed-asset gross and net book value roll-forward | PASS |
| A2-A11 | depreciation, amortisation, impairment, disposal, GL and cash replay | PASS |
| A2-A12 | finite debt principal and headroom roll-forward | PASS |
| A2-A13 | contractual interest recalculation | PASS |
| A2-A14 | prohibited financing-policy scan | PASS |
| A2-A15 | lease liability, ROU, GL and cash reconciliation | PASS |
| A2-A16 | current, deferred, cash and payable tax reconciliation | PASS |
| A2-A17 | tax-loss vintage continuity and utilisation | PASS |
| A2-A18 | authorised equity trace and zero untraced distribution/reserve activity | PASS |
| A2-A19 | retained-earnings bridge | PASS |
| A2-A20 | accrual and prepayment source, schedule and GL replay | PASS |
| A2-A21 | bilateral intercompany confirmation | PASS |
| A2-A22 | accounting-event-derived elimination replay | PASS |
| A2-A23 | monthly entity trial-balance balance and continuity | PASS |
| A2-A24 | consolidated group trial-balance replay and balance | PASS |
| A2-A25 | balance-sheet identity for every period and scope | PASS |
| A2-A26 | income statement, cash flow and retained-earnings net-income agreement | PASS |
| A2-A27 | direct-method cash-flow identity and closing-cash agreement | PASS |
| A2-A28 | five-control hard-close prerequisite binding | PASS |
| A2-A29 | statement-to-TB-to-GL-to-event-to-emitted-source trace | PASS |
| A2-A30 | independent deterministic rebuild | PASS |

## 6. Reproduction evidence

The reproducer reads the sealed source manifest and constructs a fresh request
without using the source database or copying generated outputs. It then:

1. generates every raw dataset in a separate directory;
2. rebuilds DuckDB Bronze from those raw records;
3. runs the complete logical verifier;
4. compares all 80 canonical README, source-manifest, and raw-dataset files;
5. compares the checksum ledger and detached digest bytes; and
6. compares the Bronze manifest after excluding only the explicitly
   non-canonical database byte hash and size.

The two package digests are identical. All 82 canonical and seal files are
byte-identical. Both independently built databases validate as 78 tables and
4,227,015 source rows.

## 7. Adversarial reassessment

Private-copy mutations prove the final controls fail closed:

- changing cash-flow net income by one minor unit fails A2-A26;
- removing the hard-close prerequisite references fails A2-A28; and
- changing one source-GL source identity fails A2-A29.

Ordinary checksum and database-hash mutations remain covered by the package
verifier. Duplicate capital invoices and prepayments remain deliberately
present, quarantined, and excluded from accounting; the ratification does not
silently clean them.

## 8. Product interpretation

A2 ratifies the historical source and accounting substrate, not the finished
analytics product. It proves that five years of operational and statutory
finance can be transformed safely in the next phase. It does not prebuild:

- Silver typing or Gold semantic models;
- React statutory or CFO pages;
- Excel integrated statements, forecasts, WACC, or DCF;
- Power BI models or DAX;
- Pythia scenarios; or
- Aegis findings and remediation workflows.

Those product layers may now consume the ratified A2.4 source authority through
the bounded Slice B transformation contract.

## 9. Next authorised slice

Slice B1 has now restored periods, entities, scopes, accounts, events, source
GL, eliminations, trial balances, statements, controls, and reporting versions
over `ATLAS-FINANCE-STATUTORY-A24@v1`. B2 is authorised to extend that same
model with statutory subledger dimensions and facts before any executive or
modelling mart is rebuilt.
