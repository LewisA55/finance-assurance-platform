# Artifact S v0.5 Structural and Semantic Reassessment

Status: NOT RATIFIABLE - bounded v0.6 correction required

Date: 2026-08-19

## 1. Scope and method

This independent reassessment tests
`docs/product/local-analytical-handoff.md` v0.5 against:

- the four blockers in the v0.4 reassessment;
- the implemented and audited Artifact R Phase R3 boundary;
- the checked-in validation-registry fixture and its declared hashes;
- canonical-path, XLSX, metadata, SQL, operation, failure, and fixture closure;
- a fresh P-plus-Q and R `LINEAGE@1` build; and
- the C-001, CT-1, and no-consumer-implementation invariants.

Artifact S v0.5 closes row-addressable provenance and the missing validation
authority. It also makes the workbook digest model materially more precise and
unifies public failure signaling. Three bounded executable-contract blockers
remain. No blocker requires more domain data or any React, Excel-model, Power
BI, DAX, TMDL, report, forecast, or valuation work.

## 2. Independent mechanical and execution evidence

The declared v0.5 structure is mechanically consistent:

```text
32 rulings                    S-R01 through S-R32
58 acceptance criteria       S-A01 through S-A58
28 negative-fixture rows     S-NF01 through S-NF28
19 selectors                 lexical and unique
12 checks                    S-V01 through S-V12
29 assertions                lexical and gap-free within each check
3 operations                 S-C01 through S-C03
20 failure codes             one closed lexical list
```

The design and registry fixture are ASCII/LF documents. The registry's exact
LF-terminated file hash and parsed-object no-LF canonical hash reproduce:

```text
file SHA-256
sha256:60ca04f300039da6c575fe77c25f69a440bb7c413e53674911b4db740f38b633

S-CANONICAL-JSON@v1 object SHA-256
sha256:36255992b12b0176f290ec2fa033e5655d8ca4b3a2e4cbd3a522a1de295f7cb8
```

All three literal profile bodies parse and reproduce their declared object
hashes:

```text
XLSX-TYPE-MAP@v1
sha256:41b42f86d6620e042e1137b352fee44018ecfa34b980fb4bca4f33eeb71e48dd

XLSXWRITER-3.2.9@v1
sha256:1a7dc795c0f09c22db462051c1190cf8b86dea7f03c6e79b4990fa1637c15f76

S-GRID-RENDERER-PILLOW-12.3.0@v1
sha256:fb2c4d41ea4ec9baa0c0eae9abe69cdb5ab606123b1ff3249a949c928e9c0fd6
```

A fresh governed P-plus-Q package and `LINEAGE@1` model were then built from the
ordinary runtime. R-C02 `FULL_SOURCE_EQUIVALENCE` returned `VERIFIED` for 31
tables, 99 canonical R files, and two noncanonical cache files. This confirms
the S path arithmetic:

```text
99 complete R files, including R checksums.json and model.digest
+ 13 S-owned canonical payload files
= 112 S canonical-ledger paths
+ 4 noncanonical paths
+ 2 S detached-integrity files
= 118 physical files
```

Every selector was resolved from the fresh model's Parquet files. All 29 typed
field, set, population, and graph assertions passed. The graph preimages also
reproduced through DuckDB 1.5.5 `to_json(struct_pack(...))` SQL:

```text
42 trace nodes
sha256:9f4cff10f2689171c44139e00b1f5fd33bfbbb36a102c85396451a166490bc37

58 directed trace edges
sha256:f70c2c84b33d66fb48f51f65e0d77a906b3907f24ed59f7a1b9ed3f33d608db1
```

The complete R2/R3 service test file passed: 19 tests in 58.62 seconds. The
first invocation could not access pytest's user-temp directory under the
workspace sandbox; rerunning with a workspace-local `--basetemp` produced the
clean result above.

## 3. v0.4 blocker closure

| v0.4 blocker | v0.5 result | Judgment |
|---|---|---|
| S4-B01 - profile and workbook digest preimages open | Exact no-LF canonical JSON, three profile bodies, typed cells, typed rows, logical workbook sheet variants, ordering, null counts, and exclusions are now stated. Required positive and mutation vectors are asserted but not supplied, and the renderer's hashed font asset is unavailable. | PARTIAL |
| S4-B02 - governed row provenance unavailable | `DatasetCellPointer@v1`, source-dataset bindings, one-row/set resolution, strict leaf/array coverage, the full consumer-suitability registry, and the remaining named nested payload shapes are present. | CLOSED |
| S4-B03 - twenty-nine validation instances absent | A checked-in design authority now contains all 19 selectors, 12 checks, and 29 assertions. Both declared hashes reproduce and every assertion independently passes a fresh verified LINEAGE model. | CLOSED |
| S4-B04 - competing operation failures | All three operations now expose success-only results and one `HandoffOperationFailure@v1`. The code/phase table is not exhaustive across the operation timelines, and the negative-fixture rows do not contain all fields claimed for their future records. | PARTIAL |

## 4. Blocking findings

### S5-B01 - Canonical S-owned bytes are not fully determined

S-R08 requires every canonical path to reproduce byte-for-byte, and S-C02 must
regenerate canonical metadata and SQL. Several S-owned canonical paths still
have no unique body:

- `README.md` has no exact template, field order, escaping rule, or checked-in
  authority;
- `limitations.json` has no contract model or exact payload registry;
- `starter-queries.sql` has no finite query-ID registry, exact query bodies, or
  result schemas; and
- `S-SQL-GENERATOR@v1` constrains keywords and broad assertion strategies but
  does not select exact CTE names, aliases, casts, line layout, or the complete
  emitted text for each reconciliation assertion.

The latter matters because two read-only queries can implement the same
registry and formatting rules while producing different canonical bytes. The
contract also does not settle whether `HandoffManifest@v1.source_model_path`
copies the external S-C01 request path or records the embedded relative
`source-model/` path. The R manifest has no `source_model_path` field from which
it can be copied.

Consequently, the closed path count is correct but not every path has one
deterministic byte representation. `checksums.json`, `handoff.digest`, S-C02,
and S-C03 cannot yet have one implementation-independent expected result.

Required repair:

1. define an exact README template and a strict `limitations.json` contract;
2. publish a finite starter-query registry and exact result contracts;
3. check in golden SQL bytes, or fully specify and vector-test the byte-level
   generator for both SQL files; and
4. define `source_model_path = source-model` as a normalized package-relative
   literal, or replace the field with an unambiguous embedded-path field.

### S5-B02 - Workbook conformance vectors and the render dependency are absent

The profile bodies and logical preimage shapes are now precise, and their three
printed hashes are correct. Section 6.4 nevertheless says positive vectors
cover the typed value families and that mutations change the logical digest,
but no vector object, expected digest, or mutation fixture exists. The only
checked-in Artifact S design fixture is the validation registry.

The external renderer profile also requires `Vera.ttf` with a literal hash.
That asset is not present in the repository or installed environment, and the
contract gives no governed source or audit-dependency path. The render PNGs
correctly remain outside the handoff, but the profile cannot currently be
executed from the declared repository boundary.

This does not reopen the XLSX model. It leaves interoperability and the S4
visual-audit prerequisite unproved.

Required repair:

1. check in exact typed-cell, typed-row, and logical-workbook positive vectors
   with expected digests;
2. add one exact mutation vector for value, type, order, count, source digest,
   and storage mode; and
3. provide the hash-verified font as a governed audit dependency, or define an
   explicit reproducible acquisition/input contract without placing render
   evidence in the handoff.

### S5-B03 - The failure matrix is not exhaustive over operation time

S-C03 first runs S-C02 and then invokes R-C03 and a private S-C01. If the
external P-plus-Q package becomes unavailable after the initial S-C02 succeeds,
R-C03 detects `SOURCE_PACKAGE_UNAVAILABLE` during `REPRODUCE`. The matrix admits
that code for S-C03 only in `SOURCE_VERIFY`, while its own explanation says an
R-C03 failure belongs to `REPRODUCE`. No valid failure serialization exists for
that reachable state.

Similarly, S-C01 admits generic `BUILD_FAILED` only in `STAGE`, even though
canonical writing, metadata/SQL derivation, and workbook writing occur later.
The contract neither assigns every unexpected local write failure to a more
specific code nor admits `BUILD_FAILED` in those phases.

The negative-fixture table does not resolve the gap. Section 10 says each
fixture record contains a mutation asset and three exact claim statuses, but
the table supplies only a mutation description and no claim-status values.
For example, S-NF23 does not say how the canonical registry mutation is resealed
or which expected handoff digest is sent, so the earliest failure can be digest
verification rather than `VALIDATION_REGISTRY_MISMATCH`.

Required repair:

1. enumerate code/phase pairs for failures before, during, and after source
   verification, including late source loss in S-C03;
2. define the code for unexpected copy, derivation, SQL, XLSX, verification,
   ledger-write, and publication failures;
3. publish complete fixture records with exact request changes, mutation
   assets, all three claim statuses, path states, cleanup state, and message
   fragment; and
4. prove that each fixture reaches its intended failure before any earlier
   inventory or digest check.

## 5. Semantic scenario reassessment

### 5.1 C-001

C-001 passes independently. The registry resolves and proves June v1 revenue
at `0` minor GBP, June v2 at `1000000`, the exact `1000000` bridge,
reconciliation, and exception values, purpose/version/scope-specific approved
readiness with its exact basis and empty limitation set, and the `650000` minor
GBP deferred-hire decision effect. Reporting versions remain simultaneous and
no S assertion upgrades an exception, readiness state, or decision.

### 5.2 CT-1

CT-1 passes independently. The registry preserves the `0` minor GBP control-
account movement and `BOUND_BEFORE_COMPARE`; J-011 and J-012 remain separate
authored, balanced `12000000` minor GBP journals; J-010 remains referenced-only;
and all 42 nodes and 58 source-to-target edges retain exact identity and endpoint
resolution. Verified remediation is not converted into issue closure.

### 5.3 Consumer and authority boundary

The product boundary passes. R remains the sole owner of CSV, Parquet, and
DuckDB materialization. XLSX remains a data-only S projection. Measures remain
specifications, consumer metadata remains guidance or traced projection, and
the package emits no dashboard, financial model, semantic model, DAX, TMDL,
report, forecast, or valuation.

## 6. Bounded v0.6 correction sequence

The correction order is:

1. close every S-owned canonical payload, including README, limitations, and
   both SQL files;
2. publish the workbook logical-digest vectors and the reproducible renderer
   font dependency;
3. make the operation failure matrix temporally exhaustive and publish complete
   negative-fixture records;
4. rerun all 29 registry assertions and the exact SQL digest proof against a
   fresh verified LINEAGE build; and
5. repeat structural and semantic reassessment before ratification.

R3, the dataset-cell provenance model, validation registry, product boundary,
consumer-suitability registry, C-001/CT-1 values, and no-consumer-output rule
must survive unchanged.

## 7. Verdict

Artifact S v0.5 is not ratifiable as written.

The correction closes two v0.4 blockers outright and substantially closes the
other two. Its structure, path arithmetic, profile hashes, R3 ownership,
metadata authority, validation registry, source semantics, and consumer
boundary are sound. Independent execution proves all 29 assertions and both
graph digests.

Three bounded blockers remain:

1. not every canonical S-owned path has one exact reproducible body;
2. workbook digest vectors and the renderer font dependency are missing; and
3. the operation failure matrix and negative-fixture records are not exhaustive.

No Artifact S implementation, handoff, XLSX data pack, or ratification ADR is
authorised until a bounded v0.6 closes these findings and passes another
independent reassessment.
