# Artifact S v0.9 Bounded Correction Record

Status: COMPLETE - rejected by reassessment; superseded by bounded v0.10 correction

## 1. Scope

This record closes only S8-B01, S8-B02, and S8-B03 from the independent v0.8
reassessment. It does not change the ratified v0.7 package tree, consumer
boundary, R3 ownership, SQL, workbook profiles, finance semantics, failure
codes, checkpoints, admissions, operator vocabulary, C-001, or CT-1.

No production authority loader is repointed by this correction. The v0.7 and
v0.8 authorities remain available as historical evidence. No R model, S
handoff, DuckDB copy, XLSX data pack, or consumer artifact is emitted.

## 2. Finding resolution

| Finding | Bounded v0.9 resolution |
|---|---|
| `S8-B01` | Replace the eight construction-plan tuples as current authority with eight complete, strict `MetadataDocument` logical objects. Each object includes its complete envelope, payload, source bindings, ordered provenance, and expected object digest. |
| `S8-B02` | Add one positive logical mutation context and a test-only private resolver. Resolve all forty-one targets, derive and compare every before-state, apply all nineteen operator kinds, prove every mutation changes its target, and check the declared failure checkpoint follows the application boundary and matches the closed fixture/failure authorities. |
| `S8-B03` | Restore the complete ordered four-column P-RL11 and P-RL12 endpoint fields in both the relationship and lineage positive objects. |

## 3. Positive metadata authority

Current authority:

```text
tests/fixtures/local-analytical-handoff/metadata-positive-logical-vectors-v2.json
```

- LF-terminated file SHA-256:
  `sha256:193b315987c0de728b2f65baa3d4acb7bf6d58430def24f44c997ee30706103c`
- parsed-object `canonical_sha256`:
  `sha256:62d6b623e0bad9b42eade36da81765dd4c4891c3cdebeda82e5d146e6604bec7`
- eight complete metadata objects;
- thirty-one `LINEAGE@1` table entries;
- 388 governed source and R-technical columns; and
- 10,663 exact payload provenance entries.

Expected complete-object and input/output-vector digests:

| Vector | Object digest | Vector digest |
|---|---|---|
| `S-MV09-01` | `sha256:68c5ce2d837f8e1f22f0f458259503c861e21173d2ac0afbb97270d8332b9305` | `sha256:c020e76d35cb40c867e7bd2f1f99d9cc11785979345b74f2bb13996082c9a2c4` |
| `S-MV09-02` | `sha256:6e91d5490d3ca571bead778dcdc1ace6eea090dec05709386737681faf4b9cff` | `sha256:9fc11911420074d0d6556f0e95e61db9390178606e5942941e8e48fdfc7f2829` |
| `S-MV09-03` | `sha256:8fd5a8fb7892bee5ac8277fd79b0e37ff6b6a66c1df1b4162b39634914281ac2` | `sha256:4bcef1b1d5281e961298df1720dc5cf9f7708dd58d1014bd0c6faa37268287f0` |
| `S-MV09-04` | `sha256:83b874b5e0a2a6413cb24a00bf927296cfe08793039593f44658fb497c07d224` | `sha256:223bc65af3aca701af445f97f25a40758f34bebd764126ef3ea324722480cbe4` |
| `S-MV09-05` | `sha256:42e2837d77ee1cdb2595f9e9bbe975957b6e44c96b523e2a89e21cda5c859d45` | `sha256:b3376cc0864a71015fd09b602ffff2b0afef823af1fbf391e8b1629e1c900c3a` |
| `S-MV09-06` | `sha256:6eb8c50db02065602c574417978488d1c57f82221240d8bb51c26d9451634ec9` | `sha256:616fc513abc64da09e98c9621397533fe870da5bf69b01044766b41fe090c81c` |
| `S-MV09-07` | `sha256:686d051655920874c7a618cbd50cabd75ae511e24873311416cbad670cc297f8` | `sha256:144c338261569b016241f97d8fac5bfb4cb02e4375341adbe31191fb7e2b4d90` |
| `S-MV09-08` | `sha256:69df8db7a69a4ff1345d4aab5f320a4207995517d35b58ffd82865b065645645` | `sha256:868c84f339f0cc752fc217fc37dfc7be846f07450b09f6aa903fea2f7da68c87` |

The deterministic test builder derives the table and column shapes from the
existing R registries. The fixture values, row counts, file hashes, and object
digests are bounded logical test values; they are not claims about a generated
handoff snapshot.

Each vector carries a complete construction-input preimage: the source R
registry contract hash, exact metadata contract, handoff binding, source-
document bindings, source-dataset bindings, payload projection, and complete
provenance mapping. `expected_vector_digest` covers that preimage and the
complete output document. `expected_object_digest` independently covers the
output document alone.

Every scalar payload path has exactly one `VALUE` provenance entry. Every
array path has exactly one `ARRAY_ORDER` entry. R-derived entries contain
document or dataset-cell pointers bound by the same metadata envelope;
S-guidance entries contain no upstream pointer. All entries are lexical and
unique and are included in the complete-object digest preimage.

## 4. Mutation resolution authority

Positive context:

```text
tests/fixtures/local-analytical-handoff/mutation-positive-context-v1.json
```

- LF-terminated file SHA-256:
  `sha256:a44d58028a0fa0db7f5c7ff9d549ab42abc731bac54e078a74782d4a67b39ae6`
- parsed-object `canonical_sha256`:
  `sha256:8f56e97f27e8668eeb2d1614d1527a79fb2653fe5bd6eab3faefa91e19406ca4b`

The context binds metadata vector roots, the complete logical model-manifest
table list, dataset, DuckDB, XLSX, SQL, request, runtime, and file targets, and
the derived before-state values used by the v2 recipe authority. The resolver
operates on copied logical values only. It cannot address another target and
does not write any source or output path.

The executable proof establishes for every one of the forty-one recipes:

1. the target reference resolves once;
2. the declared before-state resolves and equals the target;
3. the declared operator and operand produce a different logical value;
4. the application boundary precedes the expected first-failure checkpoint;
5. the operation and expected checkpoint agree with the closed negative
   fixture and failure-admission authorities; and
6. all target/source authority files remain ASCII, LF-terminated, and
   reproducible from the deterministic builder.

This proof closes the design-authority defect. Actual operation execution and
first-runtime-failure observation remain Phase S1 implementation and cohesion-
audit obligations; this correction does not claim an emitted handoff exists.

## 5. Composite lineage correction

The positive relationship and lineage objects now retain:

```text
P-RL11
  from [scenario_ref, reporting_version_ref, statement_field, source_ref]
  to   [scenario_ref, reporting_version_ref, statement_field, node_ref]

P-RL12
  from [scenario_ref, reporting_version_ref, statement_field, target_ref]
  to   [scenario_ref, reporting_version_ref, statement_field, node_ref]
```

No shortened consumer join is authorised.

## 6. Executable evidence

The bounded correction test is:

```text
tests/handoff/test_v09_authority_correction.py
```

Supporting deterministic, test-only code is:

```text
tests/handoff/v09_authority_builder.py
tests/handoff/v09_logical_resolver.py
```

The focused v0.9 suite passes four tests. The complete handoff slice passes all
sixteen tests, Ruff passes for the handoff implementation and tests, and the
full repository regression passes all 285 tests.

## 7. Gate

The bounded v0.9 correction is complete, not ratified. Independent structural
and semantic reassessment must reproduce the hashes, model validation,
provenance coverage, all forty-one resolutions/mutations, retained R3 and SQL
proofs, composite lineage fields, and unchanged product boundary before Phase
S1 resumes. ADR-043 remains the latest ratification authority.

## 8. Subsequent independent reassessment

The independent result is recorded in
`docs/roadmap/milestone-4-artifact-s-v09-assessment.md`. It preserves this
correction record but rejects ratifiability on three bounded grounds: the
relationship, measure, and field-role vectors are incomplete and partly
R-inconsistent; provenance arrays are shape-complete but include wrong or
non-resolving R pointers; and the resolver changes only detached return values
without executing private-context mutation and first-failure observation. A
bounded v0.10 correction is required.
