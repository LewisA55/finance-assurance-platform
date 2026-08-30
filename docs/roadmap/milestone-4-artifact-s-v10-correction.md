# Artifact S v0.10 Bounded Correction

Status: COMPLETE - rejected by reassessment; bounded v0.11 correction required

Date: 2026-08-20

## 1. Scope

This bounded correction addresses only the three blockers from the independent
v0.9 reassessment:

- complete exact R projection for relationships, measures, and field roles;
- dereferenceable R-derived provenance pointers; and
- private-copy mutation execution with reseal, request-mutation, ordered
  validators, and observed first failure.

No production handoff loader is repointed. Historical v0.7 through v0.9
authorities remain available. No S handoff, DuckDB copy, workbook, semantic
model, dashboard, report, or consumer artifact is emitted.

## 2. New Authorities

The correction adds versioned test authorities:

- `tests/fixtures/local-analytical-handoff/metadata-positive-logical-vectors-v3.json`
- `tests/fixtures/local-analytical-handoff/mutation-positive-context-v2.json`

The v0.10 metadata authority has eight logical metadata vectors, all with
construction inputs, source document payloads, validated documents, object
digests, and vector digests.

Pinned hashes:

```text
metadata-positive-logical-vectors-v3.json file
sha256:e5ba39351cad07ffd077ba26ed96b704c7f21d69f38cba9751096714be5c2cd7

metadata-positive-logical-vectors-v3.json object
sha256:23e12948afa1676c9eb2f4a3e91ef223ddd2b05d9fba65911452e9d37e80863f

mutation-positive-context-v2.json file
sha256:c32461aa324f71a6ef9a23a6035afe6198edd523af47f7d3e062b4a1b7a3488d

mutation-positive-context-v2.json object
sha256:4b25e5332ab2b3a7fafa7cc7aab5175efb01c360ef744ec06a8b1ab727748517
```

## 3. Projection Closure

v0.10 derives the three previously incomplete projections from the R registries:

```text
LINEAGE relationships     57 / 57
R measures                12 / 12
LINEAGE field roles      388 / 388
```

The emitted relationship payload equals `relationship_plan("LINEAGE")`. The
measure payload equals `MEASURE_REGISTRY`. The field-role payload equals the
selected LINEAGE slice of `COLUMN_ROLE_REGISTRY`, with S-owned `format_hints`
classified separately.

The prior R-M01 and P-D06 contradictions are closed:

- R-M01 is `Reporting Value Minor`;
- R-M01 keeps the scenario/version/statement-field required grouping;
- R-M01 keeps `INTEGER_MINOR_UNITS`;
- P-D06 `amount_minor` is hidden; and
- P-D06 `amount_minor` has no display folder.

## 4. Provenance Closure

v0.10 embeds the positive source document payloads used by every R-derived
metadata vector. The test harness dereferences every JSON pointer and requires
scalar equality or exact array-order derivation.

The previously wrong coordinates now resolve to the intended R positions:

- P-D06 `amount_minor` resolves through semantic column index 79;
- P-RL11 resolves through relationship index 25; and
- P-RL12 resolves through relationship index 26.

Validation-check and consumer-suitability payloads are classified as S guidance
for this bounded correction. Data-dictionary XLSX storage modes and field-role
format hints are also S guidance, not R-owned facts.

## 5. Mutation Execution Closure

v0.10 replaces detached mutation return checks with a private mutable execution
context. For all forty-one mutation recipes, the harness:

- resolves the target and before-state;
- mutates the private context target;
- executes declared reseal contracts;
- applies declared request mutations;
- runs operation checkpoints in order; and
- asserts the first observed public failure equals the admitted fixture state.

Observed execution counts:

```text
recipes                         41
private target mutations         41
reseal recipes executed          17
request mutations executed       15
first failures observed          41
```

## 6. Verification

Focused v0.10 verification passes:

```text
python -m pytest tests/handoff/test_v10_authority_correction.py -q
4 passed
```

Lint passes:

```text
python -m ruff check src tests
All checks passed
```

The correction is ready for independent v0.10 structural and semantic
reassessment. Ratification, Phase S1 resumption, and any production loader
repointing remain blocked until that reassessment passes.

## 7. Subsequent independent reassessment

The independent result is recorded in
`docs/roadmap/milestone-4-artifact-s-v10-assessment.md`. It confirms the exact
complete R projections, corrected provenance coordinates, real private target
and request mutation, retained R3/SQL evidence, and unchanged consumer
boundary. It rejects ratifiability because the dereferenceable source payloads
are not authenticated by their declared source-document hashes, reseals only
log step names, and checkpoint outcomes are copied from expected authorities
rather than derived by validators. A bounded v0.11 correction is required.

## 7. Subsequent independent reassessment

The independent result is recorded in
`docs/roadmap/milestone-4-artifact-s-v10-assessment.md`. It confirms the exact
complete R projections, corrected provenance coordinates, real private target
and request mutation, retained R3/SQL evidence, and unchanged consumer
boundary. It rejects ratifiability because the dereferenceable source payloads
are not authenticated by their declared source-document hashes, reseals only
log step names, and checkpoint outcomes are copied from expected authorities
rather than derived by validators. A bounded v0.11 correction is required.
