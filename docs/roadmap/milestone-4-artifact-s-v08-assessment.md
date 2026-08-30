# Artifact S v0.8 Structural and Semantic Reassessment

Status: NOT RATIFIABLE - three bounded blockers

Date: 2026-08-20

## 1. Scope and method

This independent reassessment tests
`docs/product/local-analytical-handoff.md` v0.8 against:

- S1-B01, S1-B02, and every step in the bounded v0.8 correction sequence;
- `metadata-construction-vectors-v1.json`, mutation-recipe v2, and negative-
  fixture v3 as parsed objects and exact ASCII/LF files;
- the strict implemented S metadata and request models;
- every corrected recipe coordinate and asserted before-state;
- the implemented Artifact R `LINEAGE@1` paths, relationship catalogues, and
  R-owned DuckDB cache; and
- the retained SQL, C-001, CT-1, ownership, and consumer boundaries.

The reassessment distinguishes a checked construction-plan description from a
positive metadata output vector. It does not treat a test that compares target
strings as proof that a resolver reached one positive object value.

## 2. Mechanical evidence that passes

The three v0.8 authority files reproduce their contract and documented hashes:

```text
metadata construction vectors     8 plan tuples, all tuple digests reproduce
mutation recipes                  41 unique recipes, 19 closed operators
negative fixtures                 41 unique fixtures, all recipe refs closed
```

The nested field lists equal the current strict Pydantic model fields. P-D06 is
the sixth R manifest table entry, so index 5 is correct. P-D16 and P-D17 contain
no enum source columns, so an empty lineage `evidence_status_fields[]` selection
is consistent with those two datasets. The fourteen corrected target and
before-state strings match the implemented R/S names, including:

- `schemas/p-evidence-v1/P-D06.schema.json`;
- `handoff-manifest.json`;
- `/payload/checks/...`;
- `noncanonical-cache.json#/profile_coordinate/profile_version`;
- `model-manifest.json#/table_entries/5/row_count`;
- `XlsxWriter-3.2.9`;
- `REQUEST::expected_model_digest`; and
- `SHA256:CURRENT_TARGET_BYTES`.

The focused R2/R3 plus S authority regression passes 31 tests. A fresh R-owned
cache has 31 tables and 189 source rows. All fixed SQL remains valid:

```text
S-QS01 rows  4
S-QS02 rows  1
S-QS03 rows  1
S-QS04 rows  2
S-QS05 rows 58

S-QV01 through S-QV12       PASS
registered assertion columns 29
true assertion columns        29
```

C-001 and CT-1 therefore retain the v0.7 values and distinctions. R remains
the only CSV, Parquet, and DuckDB materializer. S still contains no DuckDB
writer or consumer implementation.

## 3. Blocking finding S8-B01 - plan tuples are not positive metadata vectors

The correction gate required exact positive logical vectors for all eight
complete `MetadataDocument@v1` objects, including their envelopes, payloads,
source bindings, provenance arrays, ordering, and expected object digests.

`metadata-construction-vectors-v1.json` instead contains eight ten-field plan
tuples. Mechanical inspection finds:

```text
complete MetadataDocument objects       0
concrete field_provenance arrays         0
expected emitted-object digests          0
expected_plan_digest values              8
```

Each `expected_plan_digest` covers only the first nine fields of its local plan
tuple. It does not cover `construction_rules`, `lineage_literal_selection`, or
`provenance_projection_rules`. The file-level authority hash detects registry
byte changes, but it is not the required per-document output-object vector and
cannot prove that two constructors emit one identical metadata object.

The provenance rules remain prose templates such as "recursively copies" and
"appends". They do not enumerate the exact derivation class, source pointer,
and algorithm for every payload scalar leaf and array-order claim. For example,
the data-dictionary rule does not decide the exact provenance entry for each
derived ordinal or XLSX storage mode. The validation rule likewise names broad
categories rather than producing the complete ordered pointer array.

S1-B02 is therefore not closed. An implementation must still choose metadata
bytes and provenance entries that the correction was required to authorise.

## 4. Blocking finding S8-B02 - the machine proof does not resolve targets

The correction gate required every recipe target to resolve exactly once in a
positive fixture and every before-state to equal that resolved value.

`test_v08_authority_correction.py` proves the fourteen corrected strings equal
another literal dictionary. It does not construct any `MetadataDocument`, run
a target resolver, compare a JSON value or file hash to a recipe before-state,
apply an operator, or prove the expected first failing checkpoint. There is no
`MetadataDocument` or target-resolution call in that test.

This is material for S-NF10. Its corrected target is
`/field_provenance/0/source_pointers` and its mutation sets the selected value
to `[]`. Without one positive lineage document, the authority does not prove
that index 0 exists, that its source-pointer array is non-empty, or that the
declared mutation changes a value. S-NF09 also lacks the required concrete
positive data-dictionary object even though its P-D06 ordinal is derivable.

S1-B01's literal-coordinate defects are improved, but correction-sequence step
5 is not complete and executable closure is not established.

## 5. Blocking finding S8-B03 - lineage join fields truncate composite identity

The v0.8 lineage literal selection states:

```text
P-RL11  source_ref -> node_ref
P-RL12  target_ref -> node_ref
```

The verified R relationship catalogue defines four-column composite joins:

```text
P-RL11 from [scenario_ref, reporting_version_ref, statement_field, source_ref]
        to [scenario_ref, reporting_version_ref, statement_field, node_ref]

P-RL12 from [scenario_ref, reporting_version_ref, statement_field, target_ref]
        to [scenario_ref, reporting_version_ref, statement_field, node_ref]
```

`DirectedJoinStep@v1` is required to retain the exact ordered from/to fields.
The two-field `step_endpoint_fields` literals and the contract's shortened
arrow description omit scenario, reporting-version, and statement-field
identity. A consumer following that guide could join equal node references
across distinct contexts. This contradicts R rather than merely leaving the
constructor open.

## 6. Bounded v0.9 correction sequence

No package-tree, consumer-boundary, R3-ownership, SQL, workbook-profile,
finance-semantic, failure-state, or operator-vocabulary change is required.
The next correction should only:

1. replace or supplement the eight plan tuples with eight executable positive
   input/output vectors containing complete metadata logical objects, complete
   ordered provenance arrays, and expected `canonical_sha256` object digests;
2. place every construction input that can affect an output, including exact
   provenance mapping and lineage selection, inside the applicable vector
   digest preimage;
3. bind every payload scalar and array to one exact derivation class, ordered
   source-pointer list, and algorithm reference without prose-only recursion;
4. restore the complete ordered P-RL11 and P-RL12 composite from/to fields;
5. run the private-copy resolver against the positive objects for all forty-one
   recipes, assert every before-state, prove every mutation changes exactly its
   declared target, and prove the expected earliest failure checkpoint; and
6. repeat independent structural and semantic reassessment before Phase S1
   resumes.

Historical v0.7/v0.8 authorities should remain available as evidence. Current
implementation loaders must not be repointed to v0.8 merely because its file
hashes reproduce.

## 7. Verdict

Artifact S v0.8 is not ratifiable. The correction preserves the product,
finance, R3 ownership, SQL, workbook, and consumer boundaries, and most of the
fourteen literal recipe corrections are sound. It does not close the exact
positive metadata construction or executable-target proof required by its own
gate, and it introduces one lineage-key truncation.

No new handoff, workbook, DuckDB copy, consumer artifact, implementation phase,
or ratification ADR is authorised. A bounded v0.9 correction followed by a new
independent reassessment is required.

## 8. Subsequent bounded resolution

The required v0.9 correction is now recorded in
`docs/roadmap/milestone-4-artifact-s-v09-correction.md`. It adds complete
positive logical metadata objects and object digests, executable logical target
and before-state resolution for all forty-one recipes, and the complete
P-RL11/P-RL12 endpoint fields. This does not alter the v0.8 verdict. Independent
v0.9 reassessment remains required before Phase S1 resumes.
