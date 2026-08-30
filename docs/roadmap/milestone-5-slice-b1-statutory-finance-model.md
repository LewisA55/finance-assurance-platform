# Milestone 5 Slice B1 - Statutory Finance Model

Status: Complete and verified on 2026-08-24

## 1. Verdict

The first bounded Silver and Gold gate passes. The original Atlas dbt pattern
has been restored over the exact A2.4 authority without restoring its synthetic
opening balance sheet or presentation proxies. B1 is a usable statutory
analytical spine and authorises B2 subledger modelling. It does not ratify the
whole of Slice B.

## 2. Verified package

- model reference: `Q-FINANCE-B1@v1`;
- package path: `build/finance-model/Q-FINANCE-B1-V1`;
- analytical warehouse: `warehouse/finance-analytics.duckdb`;
- source reference: `ATLAS-FINANCE-STATUTORY-A24@v1`;
- source digest:
  `sha256:f78c55657d82be85539f168d39026843fadb87c82d01504b74d579502e593b4a`;
- 13 Silver views;
- 15 governed Gold datasets containing 480,059 rows;
- 4 governance catalogue tables;
- 71 passing dbt tests;
- 16 passing independent semantic controls;
- model semantic digest:
  `sha256:26a0b5bee480cdeb3ed4848375226c1c232aad95e4a298ea053715e0717bfff4`;
  and
- sealed package digest:
  `sha256:afdca9179fd2a92e7cd2d2257dc421737ab0094a9552bb7b8febc4637794c7df`.

## 3. B1 acceptance results

| Criterion | Evidence | Result |
|---|---|---|
| B1-A01 | A2.4 package verifier before and during B1 verification | PASS |
| B1-A02 | DuckDB attachment declared and executed read-only | PASS |
| B1-A03 | thirteen strict Silver type projections | PASS |
| B1-A04 | all Gold monetary columns remain `BIGINT` minor units | PASS |
| B1-A05 | Gold row populations reconcile exactly to Silver | PASS |
| B1-A06 | business events remain the only source-journal causal class | PASS |
| B1-A07 | accounting events remain separate lifecycle and consolidation records | PASS |
| B1-A08 | 320,033 source journal lines balance and resolve to business events | PASS |
| B1-A09 | entity trial-balance activity replays from source GL | PASS |
| B1-A10 | group activity and eliminations replay independently | PASS |
| B1-A11 | every trial-balance row rolls opening to closing | PASS |
| B1-A12 | retained earnings and cash flow reconcile for all 198 versions | PASS |
| B1-A13 | income statement, cash flow, and retained earnings agree on net income | PASS |
| B1-A14 | every balance sheet satisfies the accounting equation | PASS |
| B1-A15 | all 990 Argus statutory reconciliation results pass | PASS |
| B1-A16 | fifteen Q-FINANCE datasets, relationships, measures, lineage, and source references close | PASS |

## 4. Build and mutation evidence

The dbt build completed 103 nodes: 32 models and 71 tests, with zero errors,
warnings, skips, or no-op nodes. The Python acceptance boundary then reopened
the output warehouse, attached A2.4 read-only, reproduced model schemas and row
counts, compared physical catalogue exports, and reran 16 semantic controls.

Five isolated service tests pass. A private package copy was mutated by adding
one minor unit to a posted journal debit and then resealed. The package
verifier rejected it at `SOURCE_JOURNALS_BALANCE`; a valid checksum could not
promote invalid accounting state.

## 5. Physical contents

```text
Q-FINANCE-B1-V1/
|-- warehouse/
|   `-- finance-analytics.duckdb
|-- metadata/
|   |-- model-manifest.json
|   |-- dbt-manifest.json
|   |-- dbt-run-results.json
|   |-- q_finance_dataset_registry.json
|   |-- q_finance_relationship_registry.json
|   |-- q_finance_measure_registry.json
|   `-- q_finance_lineage_registry.json
|-- README.md
|-- checksums.json
`-- finance-model.digest
```

## 6. Next bounded gate

B2 should add analytical dimensions and atomic facts for fixed assets,
treasury and debt, leases, tax and tax losses, accruals, prepayments, equity,
intercompany, bank statements, and bank reconciliations. Each must retain its
event, legal entity, period, currency, reporting version, control, evidence,
and source coordinates and reconcile back to the B1 statutory spine.
