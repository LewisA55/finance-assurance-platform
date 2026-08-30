# Artifact S v0.6 Structural and Semantic Reassessment

Status: NOT RATIFIABLE - bounded v0.7 correction required

Date: 2026-08-20

## 1. Scope and method

This independent reassessment tests
`docs/product/local-analytical-handoff.md` v0.6 against:

- the three blockers in the v0.5 reassessment;
- all checked-in canonical, validation, workbook-vector, and failure fixtures;
- the implemented Artifact R Phase R3 boundary;
- a fresh P-plus-Q and `LINEAGE@1` build;
- all five starter queries, twelve reconciliation queries, and twenty-nine
  validation assertions;
- the complete failure admission matrix and negative-fixture registry; and
- C-001, CT-1, R3 ownership, and the no-consumer-implementation boundary.

Artifact S v0.6 closes the canonical-byte and workbook-vector blockers. Its
fixed SQL authorities execute correctly against a fresh verified model. One
bounded failure-state blocker remains.

## 2. Independent mechanical and execution evidence

The v0.6 structure is internally consistent:

```text
32 rulings                    S-R01 through S-R32
58 acceptance criteria       S-A01 through S-A58
7 checked-in authorities     all declared file hashes reproduce
8 workbook digests           2 positive plus 6 mutation vectors
19 selectors                 lexical and unique
12 checks                    S-V01 through S-V12
29 assertions                all independently pass
20 failure codes             all have direct fixture coverage
41 negative fixtures         S-NF01 through S-NF41
```

The seven checked-in file hashes, three parsed-object hashes, and three profile
hashes reproduce exactly. The external Arial audit asset exists at the declared
ratification-environment path and reproduces its pinned hash:

```text
sha256:b3658eadae55e682b5f69eb64c439c1ecc8f196c0bb8d4756d145d13bc86476a
```

The typed-row positive vector reproduces:

```text
sha256:45e5d4a173227f850d5e667c8fefa9df3ce571ba2a48a4a11705a4b25e6a0504
```

The logical-workbook positive vector reproduces:

```text
sha256:bbc933e97173a78b4e63f73c7552c42170cced257f76a2d6473eb59a9f3cf199
```

All six value, type, order, count, source-digest, and storage-mode mutation
digests also reproduce and differ from their positive base.

A fresh governed P-plus-Q package and 31-table `LINEAGE@1` model were built
through the ordinary runtime. R-C02 `FULL_SOURCE_EQUIVALENCE` returned
`VERIFIED`. The model contains 99 canonical files and two noncanonical cache
files, preserving the exact 112-ledger-path and 118-physical-file S arithmetic.

Every validation assertion was separately resolved from the fresh Parquet
tables. All twenty-nine field, set, population, and graph assertions passed.
The fixed SQL authorities then executed read-only against the fresh R-owned
DuckDB:

```text
S-QS01 rows  4
S-QS02 rows  1
S-QS03 rows  1
S-QS04 rows  2
S-QS05 rows 58

S-QV01 through S-QV12  exact registered schemas
29 SQL assertion columns       true
12 check_status values         PASS
```

The complete R2/R3 service test file also passed: 19 tests in 53.99 seconds.

## 3. v0.5 blocker closure

| v0.5 blocker | v0.6 result | Judgment |
|---|---|---|
| S5-B01 - canonical S-owned bytes underdetermined | Exact checked-in README, limitations, starter-SQL, and reconciliation-SQL authorities now bind the four previously open paths. `source_model_path` is the unambiguous package-relative literal `source-model`. All hashes reproduce and all SQL executes. | CLOSED |
| S5-B02 - workbook vectors and renderer dependency absent | Two positive and six mutation digests reproduce. The renderer profile now has one explicit external regular-file input contract, and the declared Arial bytes match the pinned hash. | CLOSED |
| S5-B03 - failure matrix and records not exhaustive | Late source loss, `SEAL`, every admitted `BUILD_FAILED` phase, all twenty failure codes, and complete fields for forty-one fixtures now exist. The fixtures do not bind the complete admission matrix, and mutation references are not executable recipes. | PARTIAL |

## 4. Blocking finding

### S6-B01 - Failure states are closed for fixtures, not for the admission matrix

The code/phase admission matrix contains 80 distinct
`(failure_code, operation, failure_phase)` triples. The forty-one fixture rows
cover 34 distinct triples. The remaining 46 admitted triples have no exact
claim-status, path-state, output-state, or cleanup-state record.

Examples include:

- `INVALID_REQUEST` at S-C02/S-C03 `PRECHECK`;
- `DIGEST_MISMATCH` at S-C01/S-C02 `VERIFY` and S-C03 `VERIFY`;
- S-C01 metadata, validation, and SQL mismatches at `DERIVE` or `VERIFY`;
- S-C03 inventory, metadata, SQL, XLSX, and binary failures at both `VERIFY`
  and `REPRODUCE`; and
- S-C03 `ATOMIC_PUBLICATION_FAILED` and `SOURCE_CHANGED_DURING_COPY` at
  `REPRODUCE`.

The general rule that a claim is verified only after the complete claim passes
does not uniquely derive every missing state. Multiple checks occur inside
`VERIFY` and `REPRODUCE`; a failure near phase entry and a failure after an
earlier claim passed can share the same code/phase while requiring different
claim statuses. An implementation must therefore invent a sub-phase checkpoint
or serialize one of several plausible state combinations.

The mutation layer is also not reproducible yet. `mutation_asset_ref` values
such as `RESEALED_SOURCE_REGISTRY_TAMPER` and
`RESEALED_DUCKDB_DOMAIN_DIVERGENCE` are closed names, but no strict recipe binds
the target path/cell, original value or digest, replacement, resealing steps,
request-field changes, and expected first failing checkpoint. The instruction
to apply a mutation immediately before its checkpoint cannot be executed from
the fixture alone.

This is one bounded blocker because the public failure model, vocabulary,
phase list, rollback rule, and tested edge cases are otherwise sound.

Required repair:

1. introduce an exact operation-checkpoint registry finer than the current
   phases;
2. bind every admitted code/operation/checkpoint to the three claim statuses,
   three source path states, output state, and cleanup state;
3. either cover every admission with a fixture or explicitly define fixtures
   as a tested subset of a complete state registry;
4. define each mutation recipe with exact target, before state, mutation,
   resealing, request change, and expected earliest failure; and
5. machine-prove that every admission has one state vector, every fixture and
   recipe resolves, and no non-admitted serialization validates.

The existing forty-one fixtures should remain unless a stricter checkpoint
model proves one redundant.

## 5. Semantic scenario reassessment

### 5.1 C-001

C-001 passes. June v1 remains `0` minor GBP; June v2, the bridge,
reconciliation, and machine exception remain `1000000` minor GBP; readiness
retains its exact version, purpose, scope, approved status, basis, and empty
limitation set; and the decision retains its `650000` minor GBP monthly effect
and readiness reference. Reporting versions remain simultaneous and no result
is upgraded into a new governance conclusion.

### 5.2 CT-1

CT-1 passes. The control-account movement remains `0` minor GBP with
`BOUND_BEFORE_COMPARE`; J-011 and J-012 remain distinct authored journals,
balanced at `12000000` minor GBP debit and credit each; J-010 remains
referenced-only; and the 42-node, 58-edge directed trace retains exact endpoint
resolution and evidence status. Verified remediation is not treated as issue
closure.

### 5.3 Consumer and authority boundary

The boundary passes. R remains the sole CSV, Parquet, and DuckDB materializer.
XLSX remains a data-only S projection. SQL is fixed, read-only, and
non-authoritative. Measures remain specifications. No React dashboard, Excel
financial model, Power BI semantic model, DAX, TMDL, report, forecast, or
valuation enters the handoff.

## 6. Bounded v0.7 correction sequence

The correction order is:

1. define the exact operation-checkpoint and full state-vector registry;
2. bind strict executable mutation recipes and first-failure precedence;
3. reconcile all admissions, state vectors, fixtures, and recipes by machine;
4. retain and rerun all v0.6 canonical, workbook, SQL, C-001, and CT-1 proofs;
   and
5. repeat independent reassessment before ratification.

The package tree, exact canonical authorities, workbook vectors, renderer
contract, SQL bytes, R3 ownership, validation registry, and consumer boundary
must remain unchanged.

## 7. Verdict

Artifact S v0.6 is not ratifiable as written.

The canonical handoff boundary is now exact, workbook reproduction is
vector-bound, all SQL and source assertions execute correctly, and the finance
and assurance semantics pass. One bounded blocker remains: the failure
admission matrix is larger than its exact state and mutation authority.

No Artifact S implementation, handoff, XLSX data pack, or ratification ADR is
authorised until a bounded v0.7 closes S6-B01 and passes another independent
reassessment.
