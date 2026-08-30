# Artifact R v0.2 Ratification Assessment

Status: RATIFIED - ADR-038 accepted 2026-08-13

Date: 2026-08-13

## 1. Scope

This assessment re-tests Artifact R v0.2 against:

- all eight blocking and seven non-blocking findings from the v0.1 hard
  critique;
- all thirty-seven implemented P/Q dataset schemas;
- all 427 source columns and seven physical source types;
- all sixty-four relationship-contract-v2 entries;
- the 706-row verified P-plus-Q canonical package;
- Excel Data Model and Power BI import-model relationship constraints;
- C-001 and CT-1 consumer journeys; and
- the repository's authority, readiness, evidence, compatibility, and local-
  reproducibility invariants.

The result is positive. No unresolved design-level blocker remains. Artifact R
v0.2 is ratifiable but is not yet ratified because no ADR has been appended.

## 2. Structural Results

The revised inventory is internally consistent and mechanically verified:

```text
28 rulings                    R-R01 through R-R28
3 cumulative profiles        CORE, LINEAGE, DIAGNOSTIC
37 dataset classifications   26 CORE, 5 LINEAGE, 6 DIAGNOSTIC
427 source columns            exact implemented P/Q inventory
7 physical source types      boolean, date, enum, hash, integer, text, timestamp
8 composite relationships    exact P relationship-v2 inventory
33 active relationships       exact finite activation plan
1 inactive role relationship P-RL04 successor reporting-version role
12 measures                   R-M01 through R-M12
3 operations                 R-C01 through R-C03
48 acceptance criteria       R-A01 through R-A48
```

Identifiers are sequential. The document contains no non-ASCII bytes, tabs,
or trailing whitespace.

## 3. Dataset and Profile Closure

All P-D01 through P-D21 and Q-D01 through Q-D16 are classified exactly once.
The cumulative profile sizes are exact:

```text
CORE         26 datasets
LINEAGE      31 datasets
DIAGNOSTIC   37 datasets
```

Every profile is closed over every required upstream consumer-relationship
endpoint. The complete relationship disposition is also closed:

| Profile | Relevant | Active | Inactive role | Navigation | Validation | Total |
|---|---:|---:|---:|---:|---:|---:|
| CORE | 49 | 27 | 1 | 17 | 4 | 49 |
| LINEAGE | 57 | 30 | 1 | 18 | 8 | 57 |
| DIAGNOSTIC | 64 | 33 | 1 | 18 | 12 | 64 |

The active plan contains only registered relationship identities, has no
cycle, and has zero pairs connected by more than one directed active-filter
path. Every active edge preserves many-to-one cardinality and single filtering
from the registered one side to the many side.

## 4. Blocking-Finding Closure

| Finding | Resolution | Result |
|---|---|---|
| R-B01 | `ColumnRoleRegistry@v1` retains source origin/transformation and applies one ordered role plus visibility and summarization disposition to every source/R column. | CLOSED |
| R-B02 | `enum` is physically mapped as a string with the exact source set; empty CSV fields are null only for nullable columns and non-null empty text is prohibited. | CLOSED |
| R-B03 | All eight composite consumer relationships receive one exact relationship-specific SHA-256 technical-key projection shared by Parquet, DuckDB, CSV import adapters, Excel, and Power BI. | CLOSED |
| R-B04 | Every in-profile relationship receives a finite disposition; the exact thirty-three-edge active plan is acyclic, single-directional, and free of duplicate directed paths. | CLOSED |
| R-B05 | CORE is now the minimum business-analysis profile; LINEAGE is required for full trace/evidence journeys and for the first flagship Excel contract. Undeclared subsets are prohibited. | CLOSED |
| R-B06 | R-C02 now has strict request/result contracts, requires the exact source package, reruns P-C02, and verifies source equivalence. Selected schemas are always copied. | CLOSED |
| R-B07 | Parquet uses a complete versioned writer-profile contract plus logical table digests. DuckDB is a separately checksummed, logically reproduced, non-canonical cache. | CLOSED |
| R-B08 | All fifty raw integers default to no summarization; every measure closes grain, grouping, currency, version, population, multi-row behavior, and incompatibilities. | CLOSED |

## 5. Non-Blocking-Finding Closure

- R-N01: `formats[]` is explicitly non-empty and ordered without duplicates.
- R-N02: physical source row order is exactly `row_key ASC`.
- R-N03: staging is beneath the final parent; writers are closed and no
  temporary/WAL file remains before verification and same-filesystem publish.
- R-N04: consumer adapters open DuckDB read-only; a write invalidates its cache
  checksum.
- R-N05: physical aliases use one deterministic `r_` normalization, length,
  hash-suffix, and collision-rejection rule.
- R-N06: only source `enum` fields receive enum enforcement; Q text fields
  remain text.
- R-N07: direct SQL and saved views remain consumer analysis and cannot inherit
  the verified R-output claim after mutation.

## 6. Additional Second-Pass Corrections

The v0.2 re-audit found and corrected five internal tensions beyond the
original critique.

First, R-R04 now permits only the eight explicit R technical key fields rather
than contradicting their existence with a blanket prohibition on added fields.

Second, byte-identical CSV remains unchanged while CSV adapters derive the
same R-owned technical keys during import. Parquet and DuckDB materialize the
keys after all source columns. Source-row and technical-projection digests
remain separate.

Third, `row_key` and all diagnostic execution columns receive
`SOURCE_TECHNICAL` before business-key classification, preventing a structural
package key from becoming a domain identifier merely because it is unique.

Fourth, the canonical digest and checksum ledger exclude both the DuckDB file
and its noncanonical-cache manifest. The stable canonical manifest names only
the cache-manifest path; each regenerated cache verifies against its own hash,
and cross-build DuckDB hashes are never compared.

Fifth, portable physical aliases always receive the `r_` prefix. This removes
an undefined reserved-word set while retaining deterministic truncation and
collision rejection.

## 7. Physical Reproducibility Judgment

Artifact R now separates three different claims correctly:

```text
source equivalence
  -> exact verified P/Q bytes, schemas, typed rows, and logical table digests

canonical physical reproduction
  -> exact CSV/Parquet/metadata bytes under one exact writer profile

local query acceleration
  -> DuckDB logical equality plus same-build tamper checksum
```

The exact Parquet library version and setting values are deliberately selected
and dependency-locked in Phase R1 before any canonical fixture is admitted.
That is an implementation binding under the already closed writer-profile
contract, not an open semantic decision. Phase R2 cannot start without it.

## 8. Consumer-Safety Judgment

R v0.2 does not claim that Excel, Power BI, React, or SQL can be prevented from
creating formulas. It enforces the honest boundary: a consumer-owned formula
cannot be presented as a governed platform value.

The shared semantic contract now provides:

- default no-summarization for every raw numeric field;
- exact-value single-row behavior;
- explicit reporting-version and currency context;
- separate authored and referenced journal populations;
- gross-activity labels for journal-line sums;
- one technical-key implementation for composite relationships; and
- one active relationship topology shared by Excel and Power BI.

No derived business mart is required for the first consumers. The technical
key projection is model mechanics, not a new business fact.

## 9. Canonical Proof Result

The LINEAGE profile retains every dataset needed to prove C-001 and CT-1
without runtime access.

C-001 retains source reconciliation, Argus exception, Aegis lifecycle,
purpose-specific readiness, simultaneous reporting versions, exact P-D07
restatement bridge, J-560 drill-through, directed trace, governed decision, and
frozen inputs. The reporting bridge is not recalculated from ledger lines.

CT-1 retains P-D13's bind-before-compare conclusion, referenced J-010,
authored J-011/J-012, separate reversal/replacement totals, exact evidence, and
the governed zero-net-movement conclusion. No measure or relationship unions
authored and referenced journal populations.

## 10. Ratification Judgment

Artifact R v0.2 is ratifiable and was subsequently ratified through ADR-038.

Ratification should append the next ADR and authorize only:

- Phase R1 strict contracts, column/profile registries, relationship-key and
  activation registries, writer-profile selection, and negative fixtures;
- Phase R2 deterministic schema/CSV/Parquet and semantic materialization;
- the mandatory post-Phase-R2 cohesion audit; and
- Phase R3 optional non-canonical DuckDB acceleration after that audit.

It should not yet authorize an `.xlsx`, `.pbix`, `.pbip`, TMDL project,
analytical React expansion, wider synthetic population, public download route,
paid API, credential, hosted dependency, generic SQL API, or new domain mart.
The first Excel consumer remains behind R implementation and cohesion closure.
