# Artifact S v0.11 Bounded Correction

Status: COMPLETE - ready for independent reassessment

Date: 2026-08-20

## 1. Scope

This bounded correction addresses only S10-B01 and S10-B02 from the independent
v0.10 reassessment:

- authenticate every dereferenceable provenance source payload with the exact
  `SourceDocumentBinding.sha256`; and
- replace reseal-name logging and expected-answer replay with real private
  digest-state transformations and state-derived checkpoint validators.

No package tree, R3 ownership, consumer boundary, finance semantic, SQL,
workbook profile, failure code, checkpoint, admission, recipe, operator, or
product claim changes. Historical v0.7 through v0.10 authorities remain
available. Production authority loaders are not repointed, and no handoff,
workbook, DuckDB copy, dashboard, report, or consumer artifact is emitted.

## 2. New authorities

The correction adds:

- `tests/fixtures/local-analytical-handoff/metadata-positive-logical-vectors-v4.json`;
- `tests/fixtures/local-analytical-handoff/mutation-positive-context-v3.json`;
- `tests/handoff/v11_authority_builder.py`;
- `tests/handoff/v11_logical_resolver.py`; and
- `tests/handoff/test_v11_authority_correction.py`.

Pinned authority hashes:

```text
metadata-positive-logical-vectors-v4.json file
sha256:bc3a90f5a833c8c45f9de12e780a48a1513f2660b1e705230d2d8b6ad0f59ac0

metadata-positive-logical-vectors-v4.json object
sha256:5dfd0dabb7fbf8d5135f9e045cb55516e4e06489089f5b8087254becd0f34681

mutation-positive-context-v3.json file
sha256:60eb028f3a06a90d8bc29dffa50b619632c7bcdd37ea60ed9e51db2c4e0284a2

mutation-positive-context-v3.json object
sha256:7f529803f4c5b1917628a062587a2cb878da31d4c8adfe0c27909870b7a1d329
```

## 3. Authenticated provenance closure

Each vector now includes the exact ASCII source bytes used for provenance
construction. Every output source-document binding equals the SHA-256 of those
bytes. Repeated paths across vectors carry byte-identical inputs.

The six source documents bind as follows:

| Source document | Exact byte SHA-256 |
|---|---|
| `model-manifest.json` | `sha256:d8df95264937115ed154c23c0afa779e7ea7709f4c9501567f6f173c6abdc6a6` |
| `semantic-model.json` | `sha256:e9dea2e3f0c9c2e5b29cd240b3ecb972f2bcb7b4e6ef4984c4cc58dd230ca037` |
| `relationships.json` | `sha256:b5c6527f2f97fd0cbbb35e31e40a44a4a45e05c6c2c08188fa97da433e51ee5b` |
| `checksums.json` | `sha256:ca656b6f4da7f045697383d1805b7bb9040ba86248828a6e88c7f60de1a0a5c3` |
| `model.digest` | `sha256:5c198e54b274d715d6de2a760813b1d9747406812202c43a2779702969958275` |
| `noncanonical-cache.json` | `sha256:6b10e4a40500ab8501726205b93c094cf0ad09e3cfaff84fe7ecd52ba6ab86e7` |

The JSON bytes validate under `ModelManifest`, `SemanticCatalogue`, the exact
ordered `RelationshipPlanEntry` list, `ChecksumLedger`, and
`NoncanonicalCacheManifest`. `model.digest` is restored to its exact
LF-terminated detached-digest text representation and equals the digest of the
exact checksum-ledger bytes.

The checksum ledger authenticates the manifest, semantic catalogue, and
relationship catalogue and uses the manifest's exact canonical scope. The
manifest, semantic catalogue, cache manifest, and metadata handoff bindings
agree on the model and source-package coordinates.

All prior pointer corrections remain. Two values that are real S projections
rather than literal R fields now use explicit algorithms:

- cache table count is derived from the authenticated cache `table_entries`;
- cache table-binding digest is derived from that exact ordered array; and
- lineage evidence-status selection is derived by filtering authenticated R
  semantic columns for enum fields in P-D16 and P-D17.

Data-dictionary primary and unique keys now point to authenticated manifest
table entries rather than pretending those fields exist on R `SemanticTable`.

## 4. Executable reseal closure

The v0.11 private context carries explicit model, cache, S-canonical, XLSX,
noncanonical-manifest, and staged digest state. Each of the six reseal contracts
executes its lexical steps as deterministic state transformations.

Across the seventeen resealed recipes:

```text
R cache plus S noncanonical reseal     3 digest-state fields changed
S canonical reseal                     3 digest-state fields changed
S XLSX binary/logical reseal           3 digest-state fields changed
R model reseal                         3 digest-state fields changed
R cache-only reseal                    2 digest-state fields changed
staged canonical reseal                3 digest-state fields changed
```

The resealed-mutant request mutation now sets `expected_handoff_digest` to the
actual recomputed private handoff digest. The unsupported-writer request retains
the authorised `XLSXWRITER-UNSUPPORTED@v1` coordinate.

## 5. State-derived validator closure

The resolver no longer loads fixture outcomes and never reads recipe field 9
while executing. It:

1. captures the positive invariant values for the operation;
2. runs checkpoints in operation order;
3. applies the primary mutation only after its declared application checkpoint;
4. performs reseal and request transformations;
5. evaluates checkpoint rules against the mutated private context; and
6. stops at the first state-derived public failure.

All forty-one recipes produce their admitted checkpoint and failure code. The
expected recipe and fixture values are used only by the test after observation.

The adversarial control changes the first recipe's expected checkpoint to
`C01_ENTRY` without changing its state. The observed result remains
`C01_SOURCE_PACKAGE_VERIFIED` with
`SOURCE_PACKAGE_VERIFICATION_FAILED`, proving the expected value cannot drive
execution.

## 6. Verification

```text
focused v0.11 tests       5 passed
complete handoff tests   25 passed
complete repository     294 passed
Ruff                     All checks passed
```

The only warning is the existing inability to create `.pytest_cache`; the
repository-local `--basetemp` paths work and all tests pass.

## 7. Gate

The bounded v0.11 correction is complete and ready for independent structural
and semantic reassessment. It is not ratified. Phase S1 resumption, production
loader repointing, handoff generation, and any consumer work remain blocked
until that reassessment passes.

## 8. Subsequent independent reassessment

The independent result is recorded in
`docs/roadmap/milestone-4-artifact-s-v11-assessment.md`. The authenticated
provenance correction passes. The executable authority is not ratifiable
because clean positive reseals are not idempotent and the checkpoint rules
classify any target delta rather than evaluating their named semantic
predicates. The bounded v0.12 correction is recorded in
`docs/roadmap/milestone-4-artifact-s-v12-correction.md`.

## 8. Subsequent independent reassessment

The independent result is recorded in
`docs/roadmap/milestone-4-artifact-s-v11-assessment.md`. The authenticated
provenance correction passes. The executable authority is not ratifiable
because clean positive reseals are not idempotent and the checkpoint rules
classify any target delta rather than evaluating their named semantic
predicates. The bounded v0.12 correction is recorded in
`docs/roadmap/milestone-4-artifact-s-v12-correction.md`.
