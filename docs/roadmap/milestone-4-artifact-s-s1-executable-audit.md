# Artifact S Phase S1 Executable Authority Audit

Status: bounded v0.12 correction complete - independent reassessment required

Date: 2026-08-20

## 1. Scope and method

This audit began the authorised Phase S1 private-copy mutation harness and
metadata/provenance constructor. It resolved every one of the forty-one
`negative-mutation-recipes-v1.json` rows against:

- the ratified Artifact S v0.7 package tree and metadata envelope;
- the implemented Artifact R `LINEAGE@1` file and contract shapes;
- the three exact S request models;
- the mutation target/value grammar and operator contracts; and
- the requirement that an implementation must not invent aliases, pointers,
  before-states, or target-resolution rules.

The existing S1 contracts, profiles, authority hashes, digest functions,
failure-admission validator, and schema models remain valid. The executable
mutation and metadata-construction boundary cannot close as written.

## 2. Blocking finding S1-B01 - fourteen recipes do not resolve

Fourteen recipes contain a target, before-state, or capability coordinate that
cannot resolve against the ratified v0.7 contracts.

### 2.1 R and S path mismatches

| Fixture | Recipe defect | Ratified or implemented shape |
|---|---|---|
| S-NF02 | `SOURCE_MODEL::schema/P-D06.schema.json` | R emits `schemas/p-evidence-v1/P-D06.schema.json`. No alias rule exists. |
| S-NF04 | `SOURCE_HANDOFF::manifest.json#/handoff_digest` | S emits `handoff-manifest.json`; the member is intentionally absent and may be added there. |
| S-NF21 | `SOURCE_MODEL::duckdb-cache-manifest.json#/model_profile_version` | R emits `noncanonical-cache.json` with `/profile_coordinate/profile_version`. |
| S-NF22 | `SOURCE_MODEL::manifest.json#/datasets/P-D06/row_count` | R emits `model-manifest.json` with ordered `table_entries[]`; no `datasets` object exists. |
| S-NF39 | `SOURCE_MODEL::manifest.json` and `REQUEST_FIELD:expected_model_manifest_digest` | R emits `model-manifest.json`; S-C01 has no `expected_model_manifest_digest` request field. |

The grammar classifies these values as literal package-relative paths and
request fields. Treating them as aliases would add an unratified resolution
layer.

### 2.2 Metadata-envelope and field mismatches

Every S metadata document has the exact envelope
`{contract_version, handoff_binding, source_documents, source_datasets,
field_provenance, payload}`. Six recipes address payload fields at the document
root or name fields that do not exist:

| Fixture | Recipe defect |
|---|---|
| S-NF09 | `/datasets/0/source_digest` is neither an envelope field nor a data-dictionary payload field. |
| S-NF10 | `/field_provenance/0/source_pointer` uses singular `source_pointer`; the contract owns `source_pointers[]` and requires a pointer object rather than text. |
| S-NF11 | `/checks/0/...` omits the required `/payload` segment. |
| S-NF14 | `/checks/10/...` omits the required `/payload` segment. |
| S-NF15 | `/checks/11/...` omits the required `/payload` segment. |
| S-NF23 | `/checks/0/...` omits the required `/payload` segment. |

S-NF09 and S-NF10 cannot be repaired by prefixing `/payload`; their asserted
before-states require an exact positive metadata projection that v0.7 does not
publish.

### 2.3 Operator, capability, and request mismatches

| Fixture | Recipe defect |
|---|---|
| S-NF26 | The required runtime capability is `openpyxl-3.2.9`, but the pinned writer is `XlsxWriter 3.2.9` and openpyxl is not an S dependency or profile. |
| S-NF27 | `ADD_JSON_ARRAY_ITEM` targets `/limitations/0`, which already exists, while the before-state is `ABSENT`; the operator contract requires appending to the selected array. |
| S-NF38 | S-C01 targets `expected_handoff_digest`, but that request deliberately has no expected handoff digest. |

The current value grammar also has no literal for the verified current file
hash or complete current array needed to express corrected S-NF39 and S-NF27
before-states without inventing semantics.

## 3. Blocking finding S1-B02 - metadata construction is not vector-bound

The v0.7 prose names the eight payload families and many nested models, but it
does not publish one exact positive projection vector for them. In particular,
an implementation must still choose:

- the exact `r_paths` serialized shape;
- the exact source-document and source-dataset binding set for each document;
- field names for the directed join-step endpoint arrays;
- the exact evidence-status field selection;
- the precise source pointer and algorithm reference for every payload leaf
  and array-order claim; and
- the final pointer order and positive object digest used as recipe
  before-state authority.

The general completeness rules do not uniquely derive those serialized bytes.
Two conforming-looking implementations can therefore emit different metadata
and provenance while satisfying the prose. S-NF09 and S-NF10 expose that gap
directly because their targets cannot be fixed until one positive metadata
shape is authoritative.

## 4. Bounded v0.8 correction sequence

The correction need not change the package tree, consumer boundary, R3
ownership, SQL, workbook profiles, finance semantics, or failure-state model.
It should only:

1. publish exact positive logical vectors for all eight metadata documents,
   including full envelope/payload shapes, source binding sets, provenance,
   ordering, and expected object digests;
2. bind exact field names for every currently prose-only nested shape;
3. replace the fourteen unresolved recipe targets and before-states with
   literal coordinates into those vectors or the implemented R/S request
   contracts;
4. add only the minimal current-file/current-array value resolvers required by
   the corrected before-states;
5. machine-prove every target resolves exactly once and every before-state
   equals the positive fixture before mutation; and
6. repeat the executable-authority audit before resuming the mutation harness.

## 5. Boundary result

No caller source, repository authority, R model, handoff, workbook, or DuckDB
was mutated. No output generator or consumer artifact was added.

Phase S1 remains in progress, but executable mutation and metadata/provenance
construction are blocked by S1-B01 and S1-B02. Implementing aliases, guessed
JSON pointers, or locally selected provenance would violate ADR-043 rather than
complete it.

## 6. Bounded v0.8 resolution record

The authorised correction is complete. It does not retrospectively change the
v0.7 audit result. The correction:

1. adds `metadata-construction-vectors-v1.json` with eight exact construction
   tuples, closed nested field names, source-binding sets, literal lineage
   selections, provenance rules, ordering, and canonical tuple digests;
2. replaces `negative-mutation-recipes-v1.json` with versioned v2 authority for
   current use while retaining v1 as historical evidence;
3. fixes all fourteen unresolved R paths, S pointers, capability coordinates,
   request fields, and before-states without introducing aliases;
4. adds only `JSON:CURRENT_TARGET_VALUE` and
   `SHA256:CURRENT_TARGET_BYTES` to the value grammar;
5. versions the matching negative-fixture registry as v3 without changing its
   forty-one fixture semantics; and
6. leaves the implementation pinned to v0.7 authorities until independent
   v0.8 reassessment authorises resumption.

The correction authorities and hashes are bound in
`docs/product/local-analytical-handoff.md`. Independent reassessment must still
machine-prove all target resolutions, before-states, vector digests, reference
closure, and retained v0.7 semantic boundaries. No handoff bytes are authorised
by this resolution record.

The independent reassessment is recorded in
`docs/roadmap/milestone-4-artifact-s-v08-assessment.md`. It confirms the literal
path corrections and retained semantic boundaries but rejects closure because
the plan tuples are not complete positive metadata objects, the machine test
does not execute target/before-state resolution, and the lineage literals
truncate P-RL11/P-RL12 composite keys. The bounded v0.9 sequence in that report
supersedes the claimed v0.8 resolution for current planning.

## 7. Bounded v0.9 resolution record

The correction required by the independent v0.8 reassessment is complete and
recorded in
`docs/roadmap/milestone-4-artifact-s-v09-correction.md`. Eight complete positive
logical metadata objects replace the plan tuples as current authority; one
positive context and private logical resolver exercise all forty-one recipe
targets and before-states; and the full P-RL11/P-RL12 composite endpoints are
restored. Historical authorities remain unchanged and production loaders are
not repointed. Independent v0.9 reassessment was the next gate.

## 8. Independent v0.9 reassessment result

The reassessment is recorded in
`docs/roadmap/milestone-4-artifact-s-v09-assessment.md`. It confirms complete
table/data-dictionary shapes, restored composite lineage fields, reproducible
object/vector digests, and all forty-one target and before-state resolutions.
It rejects closure because relationships, measures, and field roles are not
complete exact R projections; several provenance pointers do not dereference
to their claimed R sources; and mutation returns detached values without
resealing, request mutation, ordered validation, or observed first-failure
execution. The bounded v0.10 sequence supersedes the claimed v0.9 resolution
for current planning.

## 9. Bounded v0.10 correction result

The correction is recorded in
`docs/roadmap/milestone-4-artifact-s-v10-correction.md`. It adds exact complete
R projections for all LINEAGE relationships, R measures, and LINEAGE field
roles; embeds positive source document payloads for dereferenceable provenance;
and replaces detached mutation checks with private-context mutation execution,
reseal and request-mutation actions, ordered checkpoint validation, and observed
first-failure assertions for all forty-one recipes.

This is implementation evidence only. Phase S1 remains paused until independent
v0.10 reassessment passes.

## 10. Independent v0.10 reassessment result

The reassessment is recorded in
`docs/roadmap/milestone-4-artifact-s-v10-assessment.md`. It confirms the exact
R catalogue projections, corrected pointer indices, and private target/request
mutation. It rejects closure on two bounded grounds: the source payloads are
not authenticated by their declared `SourceDocumentBinding` hashes, and the
reseal/checkpoint path logs expected names and returns expected failures without
performing reseal transformations or validator-derived failure observation.
That assessment established the bounded v0.11 sequence as the next gate.

## 11. Bounded v0.11 correction result

The correction is recorded in
`docs/roadmap/milestone-4-artifact-s-v11-correction.md`. It replaces placeholder
document bindings with exact hash-authenticated R source bytes, validates those
bytes under the named R contracts, and restores `model.digest` as exact
LF-terminated text. It also executes all reseal contracts as private digest-
state transformations and derives every first failure from checkpoint rules
over mutated state without reading the expected checkpoint. The adversarial
checkpoint control passes. Phase S1 remains paused until independent v0.11
reassessment passes.

## 12. Independent v0.11 reassessment result

The reassessment is recorded in
`docs/roadmap/milestone-4-artifact-s-v11-assessment.md`. Provenance source
authentication passes. Executable authority remains blocked because positive
seal initialization is not idempotent under five reseal paths and the
checkpoint rules detect target inequality rather than their named semantic
conditions. A lower row count incorrectly reports XLSX capacity overflow.

## 13. Bounded v0.12 correction result

The correction is recorded in
`docs/roadmap/milestone-4-artifact-s-v12-correction.md`. It constructs positive
and mutated seals with shared pure functions, stores them at explicit logical
authority coordinates, separates source and staged cache bindings, and proves
all clean reseals are idempotent. Forty-one named predicates replace generic
baseline inequality, and benign capacity/path controls no longer inherit
negative outcomes. Phase S1 remains paused until independent v0.12
reassessment passes.

## 11. Bounded v0.11 correction result

The correction is recorded in
`docs/roadmap/milestone-4-artifact-s-v11-correction.md`. It replaces placeholder
document bindings with exact hash-authenticated R source bytes, validates those
bytes under the named R contracts, and restores `model.digest` as exact
LF-terminated text. It also executes all reseal contracts as private digest-
state transformations and derives every first failure from checkpoint rules
over mutated state without reading the expected checkpoint. The adversarial
checkpoint control passes. Phase S1 remains paused until independent v0.11
reassessment passes.

## 10. Independent v0.10 reassessment result

The reassessment is recorded in
`docs/roadmap/milestone-4-artifact-s-v10-assessment.md`. It confirms the exact
R catalogue projections, corrected pointer indices, and private target/request
mutation. It rejects closure on two bounded grounds: the source payloads are
not authenticated by their declared `SourceDocumentBinding` hashes, and the
reseal/checkpoint path logs expected names and returns expected failures without
performing reseal transformations or validator-derived failure observation.
The bounded v0.11 sequence in that assessment is the next gate.
