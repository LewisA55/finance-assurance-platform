# Artifact S Production Implementation

Status: implemented and locally verified

Date: 2026-08-24

## Outcome

Artifact S is no longer only a mutation-harness or logical-authority exercise.
The repository now contains an executable local analytical handoff builder and
an independent verifier.

## Production entry points

- `src/finance_assurance/handoff/service.py` owns staged build, seal, verify,
  and atomic publication.
- `src/finance_assurance/handoff/metadata_builder.py` derives the eight S
  metadata documents from authenticated R source documents and datasets.
- `src/finance_assurance/handoff/workbook.py` creates and reproduces the
  data-only XLSX pack and its logical and Open XML inventories.
- `src/finance_assurance/handoff/runner.py` exposes the
  `finance-assurance-handoff build|verify` command.

## Executed boundary

The production path:

1. verifies the exact source P/Q package and R model through R-C02;
2. copies the complete R directory without changing its owned bytes;
3. writes fixed limitations, SQL, and README authorities;
4. derives and authenticates all eight metadata documents;
5. executes S-QV01 through S-QV12 against copied DuckDB and requires every
   registered assertion to pass;
6. creates five metadata worksheets followed by all thirty-one R tables;
7. records workbook typed-row, logical, binary, and Open XML digests;
8. seals every canonical file in lexical order and writes `handoff.digest`;
9. independently verifies the staged output; and
10. publishes the verified directory atomically.

The verifier repeats R-C02, reconstructs metadata and workbook output from the
embedded R authorities, compares the same-build XLSX bytes, validates every
canonical checksum and detached digest, and closes the physical file inventory.

## Boundary retained

This is a governed analytical handoff, not another accounting or assurance
pipeline. It consumes completed upstream controls and evidence and only checks
that their exact published result survived copying and projection. It adds no
dashboard, DCF, three-statement model, forecast, Power BI semantic model, DAX,
TMDL, report page, production benchmark, or statistical claim.

## Verification evidence

The real-filesystem integration test constructs the demo P/Q package, builds a
31-table R `LINEAGE@1` model with CSV, Parquet, and DuckDB, publishes S, verifies
all 36 worksheets, and proves that an XLSX binary mutation is rejected. The
focused S contract and service tests and the broader R service regression suite
pass together. Independent spreadsheet inspection confirms 36 sheets and no
formulas, defined names, or drawings.
