# Milestone 4 Post-R3 Cohesion Audit

Status: PASSED - Artifact R Phase R3 complete

Date: 2026-08-19

## 1. Scope

This audit tests the completed Artifact R Phase R3 implementation against the
ratified R v0.2 boundary, implemented R-C01 through R-C03 contracts, all R-A01
through R-A48 acceptance criteria, the exact P-plus-Q package, C-001, CT-1, and
the prerequisite needed by Artifact S.

The audited change is bounded to optional local DuckDB acceleration. It adds no
new dataset, source query, domain value, relationship, measure, readiness
conclusion, accounting record, consumer model, dashboard, formula, DAX, TMDL,
or runtime authority.

## 2. Exact R3 contract

R3 dependency-locks DuckDB 1.5.5 in `pyproject.toml` and `uv.lock`. The build
request accepts only `storage_compatibility_version = v1.5.0`; a completed
database must report storage tag `v1.5.0+`.

`NoncanonicalCacheManifest@v1` is a strict immutable contract containing:

- source model, package, and profile coordinates;
- database path, byte count, and same-build SHA-256;
- engine, engine version, requested compatibility, and observed storage tag;
- exact source and metadata schema inventory;
- exact metadata-table inventory;
- one ordered cache-table binding per R manifest table;
- Parquet paths and hashes, row counts, column order, and logical and technical
  digests; and
- the mandatory read-only consumer flag.

The database path is exactly `warehouse/finance-assurance.duckdb`. The cache
manifest path is exactly `noncanonical-cache.json`. Both files remain outside
R's canonical checksum ledger and detached model digest.

## 3. Build and publication result

R-C01 now admits `CSV, PARQUET, DUCKDB` in canonical format order and requires
Parquet plus the exact DuckDB storage coordinate. The builder:

1. verifies the complete P-plus-Q source package before parsing;
2. writes deterministic R Parquet under `PYARROW-25@v1`;
3. records DuckDB schema/object coordinates in every model table binding;
4. constructs DuckDB only from those emitted Parquet files;
5. creates `p_evidence_v1`, `q_analytics_v1`, and `model_meta`;
6. creates exactly `cache_profile`, `documents`, and `table_bindings` in
   `model_meta`;
7. checkpoints and closes the database and rejects a retained WAL;
8. writes the strict cache manifest after the database is closed;
9. invokes R-C02 against staging; and
10. atomically publishes only after every canonical and noncanonical check
    passes.

The exact LINEAGE build required by Artifact S contains 31 source tables, 189
source rows, 99 canonical files including the R ledger and detached digest, two
noncanonical cache files, and 101 physical files in total.

## 4. Verification and reproduction

R-C02 retains complete source equivalence and adds independent cache checks. It
recomputes the closed physical inventory, canonical digest, cache-manifest
serialization, database checksum, and byte count. It opens the database with
DuckDB's read-only connection mode and verifies:

- one non-internal database with the exact storage tag;
- the exact three non-internal schemas;
- all expected R tables and the exact three metadata tables;
- no unregistered view, macro, or index;
- exact column order and row count for every source table;
- bidirectional `EXCEPT ALL` equality between each DuckDB table and its bound
  Parquet file;
- exact embedded cache-profile row;
- exact embedded canonical R documents and document hashes; and
- exact embedded table bindings.

R-C03 still reproduces every canonical byte exactly. For DuckDB, it reads the
verified source cache coordinate, rebuilds through ordinary R-C01, and requires
same-build R-C02 verification and logical equality rather than database-byte
equality. This preserves the distinction between canonical reproduction and a
rebuildable acceleration cache.

## 5. Adversarial and semantic audit

The R3 tests prove that verification rejects:

- a cache file changed without updating its manifest;
- an unknown field added to the strict cache manifest;
- a domain value changed in DuckDB after the cache manifest is resealed;
- an unknown DuckDB table added after the cache manifest is resealed;
- an unsupported storage-compatibility request;
- an unavailable writer connection; and
- any partially staged output after a DuckDB failure.

The consumer read-only test proves a write statement fails. The reproduction
test proves exact canonical bytes for the complete CSV/Parquet/DuckDB LINEAGE
request and fresh logical verification of the rebuilt cache.

C-001 and CT-1 retain the same 31-table LINEAGE population. DuckDB contains no
new calculation or conclusion: the June reporting versions, bridge,
reconciliation, exception, readiness, limitations, J-010 reference population,
J-011/J-012 authored population, correction binding, and directed trace remain
the exact R Parquet values. Cache presence or successful verification implies
neither readiness nor closure.

## 6. Findings and remediation

### R3-F01 - Python Arrow conversion introduced an undeclared timezone package

The first verifier fetched DuckDB results through a Python Arrow conversion.
TIMESTAMPTZ conversion attempted to import `pytz`, which is not part of the R
contract.

Resolution: logical equality now executes inside DuckDB with bidirectional
`EXCEPT ALL`, while Python receives only counts and schema metadata. R3 adds no
undeclared timezone dependency and retains exact timestamp comparison.

### R3-F02 - Object closure needed schemas and indexes as well as tables

The first object-inventory check closed tables, views, and macros but did not
explicitly reject an empty unregistered schema or user-created index.

Resolution: R-C02 now compares the complete non-internal schema set and rejects
every index. R-owned metadata tables use no primary-key or unique index.

### R3-F03 - Cache order and manifest format dependence needed direct guards

The initial strict cache models closed uniqueness but did not directly require
cache-table order to equal R manifest order, and `ModelManifest@v1` relied on a
later request reconstruction to reject DUCKDB without PARQUET.

Resolution: cache verification compares ordered coordinates, and the R
manifest validator now directly requires Parquet whenever DuckDB is declared.

### R3-F04 - Acceptance evidence still named the pre-R3 rejection test

R-A18, R-A19, R-A45, and R-A46 still pointed to the Phase R2 test that rejected
DuckDB.

Resolution: those criteria now point to the R3 build/read-only and logical
reproduction tests.

All findings are closed. None changes P, Q, or R domain semantics.

## 7. Evidence

```text
DuckDB runtime                         1.5.5
requested storage compatibility       v1.5.0
observed database storage tag         v1.5.0+
R3 focused tests                      6 passed
Artifact R tests                      47 passed
complete Python inventory             269 passed
Ruff                                  PASS
frontend lint                         PASS
frontend typecheck                    PASS
frontend deterministic build          PASS
frontend rendered-route tests         10 passed
LINEAGE source tables                 31
LINEAGE source rows                   189
LINEAGE catalogue columns             388
LINEAGE relationships                 57
LINEAGE measures                      12
LINEAGE canonical files               99
LINEAGE noncanonical cache files      2
LINEAGE physical files                101
LINEAGE canonical model digest        sha256:2297a1a83a58cc8064f4e03b176d10cc8f074b4725a09255b12f6ec08c22bbc1
```

The storage-compatibility setting and read-only connection behavior align with
DuckDB's published storage and Python client contracts:
`https://duckdb.org/docs/current/internals/storage` and
`https://duckdb.org/docs/stable/clients/python/overview`.

## 8. Judgment

Artifact R Phase R3 passes its cohesion audit with no unresolved blocker.

R now owns one exact optional DuckDB cache contract and implementation without
turning the cache into canonical authority. The complete LINEAGE model required
by Artifact S can be built, verified, copied unchanged, and reproduced with
canonical byte equality plus noncanonical logical equality.

This closes the R3 prerequisite. It authorises the bounded Artifact S v0.4
design correction and reassessment, not an S handoff implementation, XLSX data
pack, React experience, Excel model, Power BI model, DAX, TMDL, report,
forecast, or valuation.
