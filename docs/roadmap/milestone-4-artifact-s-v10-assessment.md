# Artifact S v0.10 Structural and Semantic Reassessment

Status: NOT RATIFIABLE - two bounded blockers

Date: 2026-08-20

## 1. Scope and method

This independent reassessment tests the bounded Artifact S v0.10 correction
against:

- all six steps in the v0.10 correction sequence from the independent v0.9
  reassessment;
- both new v0.10 authorities and all eight complete positive metadata vectors;
- the exact Artifact R `LINEAGE@1` table, column, relationship, measure, and
  semantic-role registries;
- every R-derived provenance pointer and its claimed source document binding;
- all forty-one private-copy mutation recipes, reseal contracts, request
  mutations, operation checkpoints, and claimed first failures; and
- the retained R3, fixed-SQL, C-001, CT-1, ownership, product, and consumer
  boundaries.

The audit distinguishes a pointer that dereferences inside a construction
sidecar from a source document authenticated by its declared hash. It also
distinguishes iteration over checkpoint names from execution of validators
whose result is derived from mutated state.

## 2. Evidence that passes

Both v0.10 authority files reproduce their documented ASCII/LF bytes, file
hashes, and parsed-object hashes. All eight output documents validate as strict
`MetadataDocument` objects, all object and vector digests reproduce, and all
16,971 payload-provenance entries are complete, lexical, unique, and included
in their vector preimages.

The exact R catalogue projections now pass:

```text
LINEAGE tables                  31
LINEAGE columns               388
LINEAGE relationships          57 / 57 exact and ordered
R measures                     12 / 12 exact and ordered
LINEAGE field roles           388 / 388 exact and ordered
```

R-M01 and P-D06 `amount_minor` now retain their exact R semantics. The
construction-sidecar JSON pointers all dereference and compare equal to their
projected scalar or ordered-array values. P-D06 `amount_minor` resolves through
semantic-column index 79, while P-RL11 and P-RL12 resolve through relationship
indices 25 and 26.

All forty-one primary mutation targets are now changed in a deep private
context, and all fifteen declared request mutations change their request
targets. The original checked-in authority context remains unchanged. These
are material improvements over v0.9.

A fresh R-owned `LINEAGE@1` model and DuckDB cache were built for this
reassessment. The five starter queries returned 4, 1, 1, 2, and 58 rows. All
twelve reconciliation queries returned `PASS`, and all twenty-nine assertion
columns were true. R remains the only CSV, Parquet, and DuckDB materializer.

Ruff passes for `src` and `tests`. The complete repository regression passes:

```text
289 passed
```

The production authority loader remains pinned to the nine ratified S1
authorities and does not load either v0.10 authority. S contains no handoff
builder, DuckDB writer, XLSX writer, dashboard, financial model, DAX, TMDL,
PBIX, PBIP, or consumer implementation.

## 3. Blocking finding S10-B01 - provenance inputs are not source-authenticated

The new `source_document_payloads` maps make JSON pointers locally
dereferenceable, but the maps are not authenticated as the source documents
named by each output `SourceDocumentBinding`.

Across the eight vectors there are fifteen source-document binding
occurrences. Fourteen bind JSON documents. Every one of those fourteen
declares one of the repeated placeholder hashes `sha256:111...` through
`sha256:666...`; none equals the canonical-byte SHA-256 of the corresponding
embedded JSON payload. The remaining `source-model/model.digest` input is
represented as a JSON object even though R defines that source as an
LF-terminated detached-digest text file.

The v0.10 test checks only that the payload-map keys equal the declared source
paths. It does not require a binding hash to authenticate the bytes from which
the dereferenced object was parsed, nor does it validate these sidecars as the
R contracts named by their `contract_version` values.

The vector digest protects the sidecar map as part of the test vector, but it
does not prove that the sidecar is the R file identified by the metadata
document's path and SHA-256. A pointer into an unauthenticated parallel object
does not close exact source provenance under the platform traceability
invariant. The pointer-coordinate corrections pass; the source binding needed
to make those coordinates authoritative remains open.

## 4. Blocking finding S10-B02 - reseals and validators are still declarative

Private target mutation and request mutation now execute. Resealing and
first-failure observation do not.

`_execute_reseal` reads the list of declared step names and appends it under
`executed_reseals`. Independent state comparison for
`RESEAL_R_CACHE_AND_S_NONCANONICAL_MANIFEST` changes only that audit-log key.
It changes no JSON root, direct target, derived digest, manifest binding, cache
binding, or handoff seal. The test treats the presence of returned step names
as proof that resealing occurred.

`execute_recipe` contains no checkpoint validator calls. It iterates the
operation's checkpoint registry, compares each checkpoint name with
`recipe[9]`, and then returns `recipe[9]` as the first failure and `fixture[4]`
as the failure code. Both observed values therefore come directly from the
expected authorities rather than from the mutated context.

An adversarial check changed the first recipe's expected checkpoint from
`C01_SOURCE_PACKAGE_VERIFIED` to `C01_ENTRY` without changing its mutation.
The harness immediately reported `C01_ENTRY` as the first failure while still
returning `SOURCE_PACKAGE_VERIFICATION_FAILED`. This result could not be
produced by real ordered validation and demonstrates that the expected answer
drives the claimed observation.

The v0.10 test then compares those returned authority values with the same
recipe and fixture values. It proves checkpoint ordering and authority
agreement, not that earlier validators passed or that the expected validator
failed because of mutated state. The forty-one claimed observed first failures
and seventeen claimed reseals are therefore not executable evidence.

## 5. Bounded v0.11 correction sequence

No package-tree, consumer-boundary, R3-ownership, SQL, workbook-profile,
finance-semantic, failure-code, checkpoint, admission, or operator-vocabulary
change is required. The next correction should only:

1. replace the parallel logical source payloads with exact deterministic R
   source bytes, or an exact byte-construction preimage, for every bound source
   document;
2. require each `SourceDocumentBinding.sha256` to equal those exact source
   bytes, parse and validate each JSON source under its named R contract, and
   retain `model.digest` as its exact LF-terminated text body;
3. dereference every R-derived JSON pointer only from those hash-authenticated
   parsed source bytes and retain the already-correct 79, 25, and 26 mappings;
4. implement each reseal step as a real deterministic state transformation
   that recomputes the affected model, cache, workbook, or handoff binding in
   the private context;
5. implement checkpoint validators as functions of the mutated context and
   request, stop on the first returned public failure, and use the recipe and
   fixture values only as post-observation assertions; and
6. add adversarial controls proving that changing an expected checkpoint does
   not change the observed result, then repeat independent reassessment.

Historical v0.7 through v0.10 authorities must remain available as evidence.
Production loaders must not be repointed merely because a new test authority
reproduces its hash.

## 6. Verdict

Artifact S v0.10 is not ratifiable. It closes the complete R catalogue
projection defect, corrects the concrete provenance coordinates, and performs
real private target and request mutation. It does not bind those provenance
objects to the declared R source-document hashes, execute reseal state
transformations, or derive first failures from validators.

No handoff, workbook, DuckDB copy, consumer artifact, Phase S1 resumption,
production-loader repointing, or ratification ADR is authorised. A bounded
v0.11 correction followed by a new independent reassessment is required.

## 7. Subsequent bounded resolution

The required correction is recorded in
`docs/roadmap/milestone-4-artifact-s-v11-correction.md`. It adds exact
hash-authenticated source bytes and typed R validation, deterministic private
reseal state transformations, state-derived ordered checkpoint validators, and
an adversarial expected-checkpoint control. This does not change the v0.10
verdict. Independent v0.11 reassessment remains required before Phase S1
resumes.

## 7. Subsequent bounded resolution

The required correction is recorded in
`docs/roadmap/milestone-4-artifact-s-v11-correction.md`. It adds exact
hash-authenticated source bytes and typed R validation, deterministic private
reseal state transformations, state-derived ordered checkpoint validators, and
an adversarial expected-checkpoint control. This does not change the v0.10
verdict. Independent v0.11 reassessment remains required before Phase S1
resumes.
