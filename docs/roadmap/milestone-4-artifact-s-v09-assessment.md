# Artifact S v0.9 Structural and Semantic Reassessment

Status: NOT RATIFIABLE - three bounded blockers

Date: 2026-08-20

## 1. Scope and method

This independent reassessment tests the bounded Artifact S v0.9 correction
against:

- every step in the v0.9 correction sequence from the independent v0.8
  reassessment;
- all eight positive metadata input/output vectors and both new authority
  hashes;
- the strict implemented S metadata models;
- the exact Artifact R `LINEAGE@1` table, column, relationship, measure, and
  semantic-role registries;
- every one of the forty-one target, before-state, operator, reseal, request-
  mutation, and expected-checkpoint recipes; and
- the retained R3, fixed-SQL, C-001, CT-1, product-boundary, and consumer-
  boundary proofs.

The audit distinguishes Pydantic shape validity from semantic equality with R,
syntactic pointer validity from dereferenceable provenance, and a detached
changed return value from mutation of a private execution context followed by
ordered failure observation.

## 2. Mechanical and retained evidence that passes

The two v0.9 authorities reproduce their documented ASCII/LF bytes and hashes:

| Authority | LF-terminated file SHA-256 | Parsed-object `canonical_sha256` |
|---|---|---|
| `metadata-positive-logical-vectors-v2.json` | `sha256:193b315987c0de728b2f65baa3d4acb7bf6d58430def24f44c997ee30706103c` | `sha256:62d6b623e0bad9b42eade36da81765dd4c4891c3cdebeda82e5d146e6604bec7` |
| `mutation-positive-context-v1.json` | `sha256:a44d58028a0fa0db7f5c7ff9d549ab42abc731bac54e078a74782d4a67b39ae6` | `sha256:8f56e97f27e8668eeb2d1614d1527a79fb2653fe5bd6eab3faefa91e19406ca4b` |

All eight output documents validate as strict `MetadataDocument` objects. All
eight object digests and input/output-vector digests reproduce. The positive
source binding and data dictionary contain all thirty-one LINEAGE tables and
all 388 selected R source/technical columns. The 10,663 payload-provenance
entries are lexical, unique, shape-complete, and included in their vector
preimages.

The P-RL11 and P-RL12 relationship values now retain the correct four ordered
endpoint fields. All forty-one target references and declared before-states
resolve, all nineteen operator branches return a value different from their
input, and every recipe remains bound to one fixture and admitted failure.

Ruff passes for all `src` and `tests`, and the full repository suite passes:

```text
285 passed
```

A fresh R-owned `LINEAGE@1` model and DuckDB cache reproduce model digest
`sha256:2297a1a83a58cc8064f4e03b176d10cc8f074b4725a09255b12f6ec08c22bbc1`.
The five starter queries return 4, 1, 1, 2, and 58 rows. S-QV01 through S-QV12
each return `PASS`; all twenty-nine assertion columns are true.

C-001, CT-1, R3 ownership, and the consumer boundary remain unchanged. S still
contains no DuckDB writer, dashboard, financial model, DAX, TMDL, PBIX, PBIP,
or consumer semantic-model implementation.

## 3. Blocking finding S9-B01 - positive projections are incomplete and contradict R

The v0.9 source-model and data-dictionary vectors are complete for their
declared LINEAGE shapes. Three other vectors are not complete projections of
the same R snapshot:

```text
projection        exact LINEAGE count   v0.9 positive count
relationships                         57                    2
measures                              12                    1
field roles                          388                    1
```

The two relationship rows are exact P-RL11/P-RL12 values, but the other fifty-
five R relationship rows are absent. The lone measure and field-role rows are
also not exact copies of their corresponding R values. For R-M01:

```text
field                 exact R value                 v0.9 value
measure_name          Reporting Value Minor         June v2 revenue
required_grouping     scenario/version/field        empty
default_format        INTEGER_MINOR_UNITS           GBP_MINOR
```

For P-D06 `amount_minor`, R specifies `default_visibility = HIDDEN` and
`display_folder = null`; v0.9 specifies `VISIBLE` and `Reporting`.

Strict Pydantic validation cannot detect these differences because the payload
models close field shapes and enums, not equality to the selected R catalogue.
The v0.9 test asserts only the thirty-one table and 388 data-dictionary-column
counts. It does not compare relationships, measures, or field roles with R.

This contradicts the exact-projection rules in Section 7 and fails S-A17,
S-A20, and the claim that all eight vectors are complete objects for one exact
LINEAGE model.

## 4. Blocking finding S9-B02 - provenance is shape-complete but not dereferenceable

The v0.9 test checks that each JSON pointer starts with `/`, is not `/`, and
names a bound source document. It never loads the positive R source document,
dereferences the pointer, or compares the source value or array order with the
target projection.

Independent dereference comparison finds concrete wrong coordinates:

- P-D06 `amount_minor` is semantic-catalogue column index 79; every positive
  field-role pointer is hard-coded to `/columns/6/...`;
- P-RL11 and P-RL12 are LINEAGE relationship indices 25 and 26; the
  relationship and lineage vectors point to `/0/...` and `/1/...`; and
- the field-role array-order entry points to `/fields`, which is not a member
  of R `SemanticCatalogue`; its source array is `/columns`.

The two lineage endpoint values themselves are now correct, but their claimed
source coordinates are not. A source-document path plus a syntactically valid
JSON pointer is not exact provenance when it resolves to a different object or
does not resolve.

S8-B01's demand for complete ordered provenance arrays is satisfied only at the
shape and digest level. Exact addressability remains open, violating S-A18.

## 5. Blocking finding S9-B03 - mutation and earliest-failure execution remain unproved

The v0.9 resolver materially improves the v0.8 string-only test: it resolves
all forty-one positive targets and before-states. Its mutation method then
returns a new detached `LogicalValue`; it does not apply the mutation to a
private copy of the context.

Machine inspection gives:

```text
recipes                                      41
detached return values changed               41
context targets unchanged after apply        41
recipes requiring reseal                     17
recipes requiring request mutation           15
reseal actions executed                       0
request-mutation actions executed             0
ordered validators executed                   0
observed first public failures                 0
```

The test proves only that the application checkpoint ordinal is lower than the
declared failure checkpoint ordinal and that the declared failure tuple exists
in the admission registry. It does not prove that no earlier invariant fails,
that the expected validator detects the changed private object, or that the
first public failure occurs at the declared checkpoint. It also cannot prove
that exactly one target changed because no context is mutated.

S8-B02 is therefore partially closed for target and before-state resolution but
the explicit v0.9 correction requirement for private-copy mutation, ordered
resealing/request steps, and earliest-failure proof is not closed.

## 6. Bounded v0.10 correction sequence

No package-tree, consumer-boundary, R3-ownership, SQL, workbook-profile,
finance-semantic, failure-code, checkpoint, admission, or operator-vocabulary
change is required. The next correction should only:

1. construct the relationship, measure, and field-role vectors from the exact
   selected R registries, preserving all 57 relationships, all twelve measures,
   and all 388 field roles in their required order;
2. machine-compare every projected R-owned table, column, relationship,
   measure, and field-role field with the positive R input objects, while
   keeping S-only XLSX modes and format hints explicitly classified;
3. include dereferenceable positive R manifest, semantic-catalogue,
   relationship-catalogue, and cache-manifest logical inputs in the vectors;
4. resolve every R-derived provenance pointer against those inputs and require
   exact scalar equality or exact array-order derivation, including indices 79,
   25, and 26 above;
5. mutate an actual deep private copy for all forty-one recipes, execute the
   ordered reseal and request-mutation contracts, run checkpoint validators in
   operation order, and assert the first observed public failure equals the
   recipe and admission authority; and
6. repeat independent structural and semantic reassessment before Phase S1
   resumes.

Historical v0.7 through v0.9 authorities must remain available as evidence.
Current production loaders must not be repointed merely because new authority
files reproduce their hashes.

## 7. Verdict

Artifact S v0.9 is not ratifiable. It closes the truncated composite-field
finding and materially improves positive object shape, digest closure, target
resolution, and before-state proof. It does not provide complete exact R
projections for three metadata documents, dereferenceable exact provenance, or
private-context mutation with observed earliest failure.

No new handoff, workbook, DuckDB copy, consumer artifact, Phase S1 resumption,
or ratification ADR is authorised. A bounded v0.10 correction followed by a
new independent reassessment is required.
