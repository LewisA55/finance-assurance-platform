# Artifact P - Governed Synthetic Output and Analytical Export Contract

Status: Design v0.1 - draft for critique

## 0. Purpose and Closure Rule

Artifact P defines the first reusable governed output boundary above the
ratified public product. It turns exact, synthetic Finance & Assurance Platform
views into one deterministic, tabular package that can later be consumed by
Excel, a Power BI semantic model, portfolio downloads, and other offline
analytical tools without creating a second source of finance logic.

Artifact P is not an Excel workbook, a Power BI model, a new warehouse, or a
larger synthetic-company generator. It freezes the shared output contract those
later products must consume.

Artifact P closes only when:

1. one package is assembled from one revision-pinned Artifact O read boundary;
2. every exported value is a lossless tabular projection of an exact Artifact O
   view or envelope field;
3. reporting history, readiness, evidence state, module ownership, and directed
   traceability survive the tabular boundary;
4. the package is byte-verifiable and reproducible without paid services,
   credentials, runtime network access, or mutable public workflows;
5. C-001 and CT-1 are both representable without canonical-literal branching;
6. Excel and Power BI can consume the same package rather than receiving
   separately authored extracts; and
7. no downstream consumer is authorised to recalculate an accounting,
   assurance, governance, readiness, or decision conclusion.

## 1. Binding Sources

Artifact P is constrained by:

- the five repository invariants in `AGENTS.md`;
- Artifact G v0.2, module ownership and publish/consume contracts;
- Artifact I v0.2.2, the parameterised application boundary;
- Artifact J v0.2, authoritative records and rebuildable projections;
- Artifact L v0.2.1, strict internal runtime messages;
- Artifact N v0.2.1, persisted-contract compatibility;
- Artifact O v0.2, public queries, views, and exact-original read rules;
- C-001, the hard-close restatement reference transaction;
- CT-1, the open-period reversal and replacement reference transaction;
- ADR-033, the ratified public product boundary; and
- ADR-034, the ratified Milestone 3 acceptance and manual browser boundary.

Artifact P may narrow those contracts for analytical delivery. It may not
weaken or reinterpret them.

## 2. Product Outcome and Audience

The immediate product outcome is one downloadable, inspectable output package:

```text
ordinary runtime authority
-> exact Artifact O queries
-> one pinned export snapshot
-> governed tabular package
-> Excel / Power BI / portfolio download
```

The package is intended for:

- a finance professional opening the data in Excel;
- an analyst building a Power BI semantic model;
- a reviewer checking exact values, readiness, provenance, and hashes;
- a recruiter inspecting the project without running the full application; and
- later repository-owned adapters that generate presentation artefacts from the
  same governed source.

The package does not claim that the present C-001 and CT-1 volume resembles a
full enterprise population. It proves the output contract at canonical depth.
Expanded synthetic operations will add governed rows only after their source
processes and module contracts exist.

## 3. Vocabulary

### 3.1 Governed export

A read-only, derived package created from exact, revision-pinned platform views.
It is not an authoritative business, accounting, assurance, governance, or
planning record.

### 3.2 Export snapshot

The immutable read context shared by every query used in one export:

```text
workspace_ref
runtime_revision
query_revision
semantic_as_of
compatibility_mode
scenario_refs
```

### 3.3 Canonical package

The deterministic directory whose files, ordering, encodings, schemas, and
digests are governed by this artifact.

### 3.4 Dataset

One closed tabular contract with a registered identifier, schema version,
fixed column order, deterministic row identity, and declared Artifact O source.

### 3.5 Consumer adapter

A repository-owned, non-authoritative transformation that consumes a verified
canonical package and produces an Excel workbook, Power BI project input, or
download wrapper. It may format, relate, filter, and visualise. It may not
invent a platform conclusion.

### 3.6 Reliance context

The exact product, purpose, period, and scope to which an Aegis readiness
assessment applies. File inclusion alone never implies readiness.

### 3.7 Package digest

The SHA-256 digest of the canonical checksum ledger. It identifies the exact
package bytes without requiring the manifest to hash itself.

## 4. Rulings

### P-R01 - One governed package feeds every analytical channel

Excel, Power BI, portfolio downloads, and later offline analytical adapters
consume the same canonical dataset family. Consumer-specific extracts may not
be separately authored from runtime or database state.

### P-R02 - The export layer is never authoritative

An export package, workbook, semantic model, chart, or downloaded file may not
be consumed as a causal business event, accounting event, posting proposal,
control result, governance decision, readiness assessment, or planning input.

### P-R03 - Artifact O is the only semantic source boundary

The baseline export assembler consumes O-Q01 through O-Q11 through their
in-process application port. It may not import SQLite, runtime repositories,
validation fixtures, web components, HTTP response scraping, or database
tables.

### P-R04 - One package uses one pinned snapshot

Every Artifact O result in one package must share the same workspace,
runtime revision, query revision, semantic-as-of time, compatibility mode, and
scenario scope. A mismatch rejects the whole build.

### P-R05 - Exact-original compatibility remains mandatory

Artifact P version 1 accepts only `EXACT_ORIGINAL` Artifact O responses. A
future `TYPED_TARGET` or adapted input requires a successor Artifact P contract,
visible compatibility labelling, and an append-only architecture decision.

### P-R06 - No unspecified latest lookup exists

The request identifies exact scenario and semantic-time coordinates. Every
reporting version, readiness record, issue version, decision, journal, and
trace subject remains an exact reference supplied by Artifact O.

### P-R07 - Tabularisation is lossless and non-inferential

The assembler may flatten nested closed fields, repeat parent keys, and move
arrays into child tables. It may not calculate, classify, net, rank, score,
reconcile, approve, close, or otherwise infer a semantic result.

### P-R08 - Finance values retain integer minor units

Money is exported as signed base-10 integer minor units plus ISO-4217 currency.
No binary float, display-formatted currency string, implicit currency, or
spreadsheet formula is part of the canonical package.

### P-R09 - Reporting history remains versioned

As-was and as-restated reporting versions remain separate rows. Restatement
bridges retain predecessor, successor, adjustment, currency, statement field,
and restatement-case identity. A consumer may not overwrite v1 with v2.

### P-R10 - Readiness remains purpose-specific

Readiness is exported only as its exact reporting product, period, purpose,
scope, status, basis, limitations, assessor, and readiness reference. No
dataset-level or package-level `approved` flag is derived.

### P-R11 - Controlled use retains its exact readiness binding

A Pythia decision row must retain the exact reporting-version and readiness
references consumed by its frozen planning input. Presence of a readiness row
for another purpose or scope is insufficient.

### P-R12 - Evidence claims remain bounded

Content-verified reporting values retain `VERIFIED`; declaration-only evidence
remains declaration-only or unavailable according to Artifact O. A package
digest proves export bytes, not the truth of an upstream evidence artefact.

### P-R13 - Directed traceability remains directed

Trace nodes and edges are exported separately. Edge direction and relationship
labels are preserved exactly. Consumer joins, diagrams, or graph layouts may
not replace J-P11 authority.

### P-R14 - Module ownership remains visible

Every domain dataset identifies its owning module or shared-substrate role.
Cross-module references remain explicit rather than being flattened into one
generic status table.

### P-R15 - Synthetic status is prominent and machine-readable

The manifest and package context both state that all business data is
synthetic. A consumer adapter must carry the notice into its visible output.

### P-R16 - The canonical package is a directory, not a workbook

The authoritative export representation is the deterministic directory defined
in section 7. An `.xlsx`, `.pbip`, `.pbix`, `.zip`, or dashboard is a derived
consumer artefact and never replaces the directory's schemas and checksums.

### P-R17 - CSV is a typed transport, not the schema authority

Dataset schema files define column types, nullability, enum domains, keys, and
relationships. CSV text is interpreted only with its matching exact schema.

### P-R18 - Rows and files have deterministic order

Columns follow registered order. Rows sort lexically by their stable `row_key`.
Files sort lexically by relative path. An implementation may not rely on
database, map, filesystem, or locale order.

### P-R19 - Empty, null, and absent are distinct

Null is represented by an unquoted empty CSV field. Non-null fields are quoted.
An empty string is prohibited. A variant-inapplicable field is nullable only
where its dataset schema explicitly permits it.

### P-R20 - Package verification is offline and complete

Verification recomputes every schema and data-file hash, validates the checksum
ledger and package digest, parses every row under the exact schema, checks keys
and registered relationships, and confirms one coherent export snapshot.

### P-R21 - Export creation does not mutate platform state

Building, verifying, or reproducing an export may not append authority, update
projections, claim effects, run demo lifecycle commands, or change the source
workspace. Output-directory creation is the only permitted mutation.

### P-R22 - Publication is atomic at filesystem scope

The builder writes and verifies a sibling staging directory before one atomic
promotion to the requested final path. A failed build leaves no directory that
can be mistaken for a valid package.

### P-R23 - The baseline remains local, deterministic, and free to run

Creation and verification require no API key, paid service, hosted database,
external dataset, telemetry account, runtime network access, or generative AI.

### P-R24 - Contract growth is additive only within declared semantics

New rows conforming to an existing dataset may be added when a ratified source
scenario expands. New columns, changed meanings, new enum members, changed
relationships, adapted inputs, or new dataset identifiers require an explicit
contract-version decision.

## 5. Consumer Profiles

The following consumers are in scope as future adapters over the same package.
They do not alter the canonical dataset registry.

| Profile | Intended use | Permitted behaviour | Prohibited behaviour |
|---|---|---|---|
| P-U01 `PORTFOLIO_DOWNLOAD` | Inspectable project artefact | Package or wrap verified canonical files and explanatory material | Drop schemas, hashes, synthetic notice, or reliance context |
| P-U02 `EXCEL_MODEL` | Finance analysis and modelling | Import typed tables, define relationships, add presentation formulas and user-owned scenarios | Rewrite governed actuals, hide version identity, or promote formulas to platform authority |
| P-U03 `POWER_BI_SEMANTIC_MODEL` | Governed interactive analytics | Import typed tables, define explicit measures, dimensions, relationships, and display metadata | Read runtime tables directly, infer readiness, or replace exact source references with labels |

The existing React public product continues to use Artifact O's finite HTTP
boundary for live views. It may expose a package download and manifest summary;
it does not need to ingest its own export package to render existing journeys.

## 6. Export Operations

The export application boundary contains exactly three operations.

### P-C01 - BuildGovernedExport

Input:

```text
export_ref
workspace_ref
scenario_refs[]
semantic_as_of
exported_at
output_path
contract_version = governed-export-package@v1
```

Behaviour:

1. validate the closed request and require a non-empty, sorted, unique scenario
   set;
2. open one read-only export snapshot over the existing Artifact O in-process
   query service;
3. execute the finite query plan in section 10;
4. reject any response whose envelope coordinates differ from the snapshot;
5. tabularise only registered fields;
6. serialize schemas, relationship metadata, data, and package documentation;
7. construct the manifest, checksum ledger, and package digest;
8. run P-C02 against the staging directory; and
9. atomically promote the verified directory.

Output:

```text
export_ref
package_path
package_digest
runtime_revision
query_revision
semantic_as_of
dataset_count
row_count
```

### P-C02 - VerifyGovernedExport

P-C02 accepts one package path and returns a closed verification result. It
performs no platform query and no write. It must distinguish at least:

```text
VERIFIED
MISSING_FILE
UNREGISTERED_FILE
HASH_MISMATCH
PACKAGE_DIGEST_MISMATCH
SCHEMA_INVALID
ROW_INVALID
KEY_VIOLATION
RELATIONSHIP_VIOLATION
SNAPSHOT_MISMATCH
UNSUPPORTED_CONTRACT
UNSUPPORTED_COMPATIBILITY_MODE
```

### P-C03 - ReproduceGovernedExport

P-C03 rebuilds from the exact source workspace and the original manifest basis
into a disposable path, verifies it, and compares its package digest with the
expected digest. It never overwrites the original package.

Reproduction requires the same authoritative runtime revision to remain
available. If the source workspace no longer contains that revision, the
result is `SOURCE_REVISION_UNAVAILABLE`, not a best-effort rebuild from current
state.

## 7. Canonical Package Contract

### 7.1 Directory layout

```text
<export_ref>/
|-- manifest.json
|-- README.txt
|-- relationships.json
|-- schemas/
|   |-- P-D01.schema.json
|   |-- ...
|   `-- P-D20.schema.json
|-- data/
|   |-- P-D01.csv
|   |-- ...
|   `-- P-D20.csv
|-- checksums.sha256
`-- package.digest
```

No additional file is permitted in a version-1 package. All paths use forward
slashes in manifests and checksum material regardless of host operating system.

### 7.2 Manifest

`manifest.json` is strict canonical JSON and contains:

```text
contract_version
export_ref
workspace_ref
runtime_release
runtime_revision
query_revision
semantic_as_of
exported_at
compatibility_mode
synthetic_data
synthetic_data_notice
scenario_refs[]
authoritative_inventory_digest
projection_generation_ref
dataset_entries[]
relationship_contract_version
producer_release
```

Each `dataset_entry` contains:

```text
dataset_id
dataset_version
module_owner
relative_path
schema_path
row_count
data_sha256
schema_sha256
source_query_ids[]
source_view_ids[]
semantic_source_refs[]
```

`semantic_source_refs` are sorted, unique, exact Artifact O envelope references.
They preserve package-level source closure and do not claim that every source
applies to every individual row.

### 7.3 Hash closure

`checksums.sha256` contains the SHA-256 of every canonical file except itself
and `package.digest`, in lexical relative-path order. It includes
`manifest.json`, `README.txt`, `relationships.json`, every schema, and every
dataset.

`package.digest` contains exactly:

```text
sha256:<SHA-256 of the exact checksums.sha256 bytes>\n
```

This avoids a self-referential manifest hash while binding the complete package
content.

### 7.4 Canonical JSON

JSON uses UTF-8 without BOM, LF line endings, lexical object-key ordering,
compact separators, exact array order, and one trailing LF. Numbers are
integers only. Floating-point JSON values are prohibited.

### 7.5 Canonical CSV

CSV uses UTF-8 without BOM and LF line endings. The first row is the exact
registered header. Every non-null header or value is double-quoted; embedded
double quotes are doubled. Null is an unquoted empty field. Empty strings,
tabs, carriage returns, and embedded line breaks are prohibited.

Scalar encodings are:

| Type | Encoding |
|---|---|
| `text` | exact UTF-8 text inside double quotes |
| `integer` | optional `-` followed by base-10 digits, quoted |
| `boolean` | quoted lowercase `true` or `false` |
| `date` | quoted `YYYY-MM-DD` |
| `timestamp` | quoted UTC RFC 3339 ending in `Z` |
| `hash` | quoted lowercase `sha256:` plus 64 hex characters |
| `enum` | quoted registered uppercase token |

Every dataset begins with a non-null `row_key`. Rows sort lexically by that key,
which must be unique within the dataset.

## 8. Dataset Schema Vocabulary

Every `P-D*.schema.json` contains only:

```text
schema_contract_version
dataset_id
dataset_version
module_owner
description
primary_key[]
columns[]
```

Each column contains:

```text
name
type
nullable
description
enum_values[]  # present only for enum
```

Version 1 uses only scalar fields. Arrays from Artifact O are represented as
child rows or P-D17 reference bindings.

## 9. Closed Dataset Registry

Artifact P version 1 contains exactly twenty datasets.

| ID | Dataset | Owner | Artifact O basis | Row grain |
|---|---|---|---|---|
| P-D01 | `package_context` | shared substrate | O-V01 | one package |
| P-D02 | `scenarios` | shared substrate | O-V01 | one scenario |
| P-D03 | `module_lenses` | shared substrate | O-V02 | one module summary |
| P-D04 | `source_reconciliations` | Hermes | O-V03 | one exact reconciliation |
| P-D05 | `reporting_versions` | Atlas | O-V04/O-V05 | one reporting version |
| P-D06 | `reporting_values` | Atlas | O-V04/O-V05 | one statement field per reporting version |
| P-D07 | `restatement_bridges` | Atlas | O-V04 | one statement-field adjustment |
| P-D08 | `assurance_exceptions` | Argus | O-V06 | one machine exception |
| P-D09 | `governance_case_stages` | Aegis | O-V07 | one explicit case stage |
| P-D10 | `readiness_assessments` | Aegis | O-V08 | one product-purpose-scope assessment |
| P-D11 | `governed_decisions` | Pythia/source domain | O-V09 | one governed decision and admission outcome |
| P-D12 | `decision_inputs` | Pythia | O-V09 | one frozen decision input reference |
| P-D13 | `decision_effects` | source business domain | O-V09 | one visible operational effect |
| P-D14 | `correction_cases` | Argus/shared read model | O-V11 | one correction integrity result |
| P-D15 | `correction_journals` | Atlas | O-V11 | one reversal or replacement journal summary |
| P-D16 | `correction_journal_lines` | Atlas | O-V11 plus exact permitted journal detail | one immutable journal line |
| P-D17 | `reference_bindings` | shared substrate | O-V01-O-V11 | one ordered exact reference attached to a parent row |
| P-D18 | `trace_nodes` | shared substrate | O-V10 | one unchanged J-P11 node |
| P-D19 | `trace_edges` | shared substrate | O-V10 | one unchanged directed J-P11 edge |
| P-D20 | `package_sources` | shared substrate | Artifact O success envelopes | one exact semantic source reference per query response |

P-D16 is ratifiable only if the existing O-Q11 application boundary exposes
the exact immutable journal-line fields already used to produce its balance
result. Artifact P does not author a generic journal query. If that mapping
cannot be proved without expanding Artifact O, P-D16 must be removed from
version 1 or Artifact O must receive an explicit successor contract before P is
ratified.

### 9.1 P-D01 `package_context`

```text
row_key
export_ref
workspace_ref
runtime_release
runtime_revision
query_revision
semantic_as_of
exported_at
compatibility_mode
synthetic_data
synthetic_data_notice
authoritative_inventory_digest
projection_generation_ref
producer_release
```

### 9.2 P-D02 `scenarios`

```text
row_key
scenario_ref
canonical_family
status
public_role
entry_point_count
```

### 9.3 P-D03 `module_lenses`

```text
row_key
scenario_ref
module
summary_code
primary_product_ref
```

Presentation routes are excluded because they are transport-specific and not
analytical semantics.

### 9.4 P-D04 `source_reconciliations`

Common columns:

```text
row_key
scenario_ref
module
reconciliation_ref
reconciliation_type
scope_ref
performed_at
reconciliation_status
downstream_exception_ref
period_id
expected_item_count
posted_item_count
submitted_unposted_count
deferred_count
expected_amount_minor
posted_amount_minor
difference_minor
currency
cash_application_ref
receipt_party_ref
application_party_ref
party_mapping_ref
identity_match
```

Only the fields applicable to the exact Artifact O union variant are non-null.
The schema fixes the nullable set; no third variant is admitted.

### 9.5 P-D05 `reporting_versions`

```text
row_key
scenario_ref
module
reporting_version_ref
period_id
version
publication_origin
published_at
currency
content_ref
content_verification_status
source_publication_ref
predecessor_version_ref
restatement_case_ref
manifest_hash
published_by_event_id
import_attestation_ref
original_authority_ref
source_ref
```

Origin-specific fields remain nullable only for the other closed origin variant.

### 9.6 P-D06 `reporting_values`

```text
row_key
scenario_ref
module
reporting_version_ref
period_id
statement_field
label
amount_minor
currency
content_verification_status
trace_available
```

No value is emitted when Artifact O marks the field unavailable.

### 9.7 P-D07 `restatement_bridges`

```text
row_key
scenario_ref
module
period_id
predecessor_version_ref
successor_version_ref
statement_field
adjustment_minor
currency
restatement_case_ref
```

The adjustment is copied from O-V04. It is not recomputed from P-D06.

### 9.8 P-D08 `assurance_exceptions`

```text
row_key
scenario_ref
module
exception_type
test_run_ref
test_definition_ref
exception_ref
assertion
severity
related_governance_case_ref
period_id
expected_amount_minor
actual_amount_minor
difference_minor
receipt_party_ref
application_party_ref
journal_id
amount_minor
currency
```

Variant-specific fields follow the same strict-union rule as P-D04.

### 9.9 P-D09 `governance_case_stages`

```text
row_key
scenario_ref
module
case_ref
stage_ordinal
stage_type
stage_ref
stage_status
owner_ref
predecessor_stage_ref
successor_stage_ref
```

`stage_type` is exactly one of:

```text
EXCEPTION
REVIEW
FINDING
INITIAL_ISSUE
REMEDIATION_DIRECTIVE
CORRECTION
VERIFICATION
PRIOR_ISSUE_VERSION
FINAL_ISSUE_VERSION
```

Stage rows are a structural projection of explicit O-V07 references. They do
not infer a workflow transition or convert `REMEDIATION_VERIFIED` to `CLOSED`.

### 9.10 P-D10 `readiness_assessments`

```text
row_key
scenario_ref
module
readiness_ref
reporting_version_ref
period_id
purpose_ref
scope_ref
status
assessed_by_ref
```

Basis and limitation arrays are emitted through P-D17 with roles
`READINESS_BASIS` and `READINESS_LIMITATION`.

### 9.11 P-D11 `governed_decisions`

```text
row_key
scenario_ref
module
planning_input_ref
reporting_version_ref
readiness_ref
purpose_ref
scope_ref
decision_ref
decision_type
position_ref
original_start_date
recommended_start_date
monthly_cost_minor
currency
reason_code
approval_ref
approval_outcome
candidate_ref
candidate_admission_outcome
```

The approval and admission outcomes remain separate columns.

### 9.12 P-D12 `decision_inputs`

```text
row_key
scenario_ref
module
decision_ref
planning_input_ref
input_ordinal
input_ref
```

Rows preserve the frozen Artifact O order.

### 9.13 P-D13 `decision_effects`

```text
row_key
scenario_ref
module
decision_ref
effect_type
subject_ref
original_date
recommended_date
amount_minor
currency
```

Version 1 admits only the explicit deferred-hire effect already present in
O-V09. It does not generalise a planning-effect taxonomy.

### 9.14 P-D14 `correction_cases`

```text
row_key
scenario_ref
module
source_projection_ref
source_projection_hash
reversal_proposal_ref
reversal_journal_ref
replacement_proposal_ref
replacement_journal_ref
identity_before
identity_after
reversal_binding_status
control_account_net_movement_minor
currency
verification_ref
issue_update_ref
```

The net movement is copied from O-V11 and is not recalculated in the export.

### 9.15 P-D15 `correction_journals`

```text
row_key
scenario_ref
module
correction_row_key
journal_role
journal_ref
debits_minor
credits_minor
currency
balanced
```

`journal_role` is `REVERSAL` or `REPLACEMENT`. Balance values and result are
copied from O-V11.

### 9.16 P-D16 `correction_journal_lines`

```text
row_key
scenario_ref
module
journal_ref
line_ordinal
account_ref
debit_minor
credit_minor
currency
```

P-D16 is intentionally the one open ratification challenge identified above.

### 9.17 P-D17 `reference_bindings`

```text
row_key
scenario_ref
parent_dataset_id
parent_row_key
reference_role
reference_ordinal
reference_ref
```

Version 1 roles are closed to the arrays already published by Artifact O,
including scenario entry points, source refs, subject refs, evidence refs,
correction refs, prior issue refs, readiness refs, readiness bases, and
readiness limitations.

### 9.18 P-D18 `trace_nodes`

```text
row_key
scenario_ref
module
trace_subject_ref
node_ref
role
record_family
record_identity
semantic_hash
```

`semantic_hash` is nullable only under Artifact O's exact J-P11 rule.

### 9.19 P-D19 `trace_edges`

```text
row_key
scenario_ref
module
trace_subject_ref
source_ref
target_ref
relationship
```

No edge is reversed or added for presentation convenience.

### 9.20 P-D20 `package_sources`

```text
row_key
query_id
view_id
scenario_ref
semantic_source_ordinal
semantic_source_ref
runtime_revision
query_revision
semantic_as_of
compatibility_mode
```

P-D20 is the query-envelope provenance index. It is not a replacement for the
domain references carried by the other datasets.

## 10. Finite Query and Tabularisation Plan

The version-1 assembler executes only the queries needed by the requested
scenario set. Every invocation uses the same export snapshot.

| Artifact O query | Output datasets |
|---|---|
| O-Q01 | P-D01, P-D02, P-D17, P-D20 |
| O-Q02 | P-D03, P-D17, P-D20 |
| O-Q03 | P-D04, P-D17, P-D20 |
| O-Q04 | P-D05, P-D06, P-D07, P-D20 |
| O-Q05 | P-D05, P-D06, P-D17, P-D20 |
| O-Q06 | P-D08, P-D17, P-D20 |
| O-Q07 | P-D09, P-D17, P-D20 |
| O-Q08 | P-D10, P-D17, P-D20 |
| O-Q09 | P-D11, P-D12, P-D13, P-D17, P-D20 |
| O-Q10 | P-D18, P-D19, P-D20 |
| O-Q11 | P-D14, P-D15, conditionally P-D16, P-D17, P-D20 |

Duplicate semantic rows returned through both O-Q04 and O-Q05 must be
byte-identical after tabularisation and collapse to one row key. A disagreement
rejects the package; first-writer or last-writer behaviour is prohibited.

## 11. Relationship Registry

`relationships.json` is a closed, canonical JSON array. Each relationship
contains:

```text
relationship_id
from_dataset
from_columns[]
to_dataset
to_columns[]
cardinality
required
```

Version 1 registers at least:

```text
P-D06.reporting_version_ref -> P-D05.reporting_version_ref
P-D07.predecessor_version_ref -> P-D05.reporting_version_ref
P-D07.successor_version_ref -> P-D05.reporting_version_ref
P-D10.reporting_version_ref -> P-D05.reporting_version_ref
P-D11.reporting_version_ref -> P-D05.reporting_version_ref
P-D11.readiness_ref -> P-D10.readiness_ref
P-D12.decision_ref -> P-D11.decision_ref
P-D13.decision_ref -> P-D11.decision_ref
P-D15.correction_row_key -> P-D14.row_key
P-D16.journal_ref -> P-D15.journal_ref
P-D17.parent_dataset_id + parent_row_key -> registered parent row
P-D19.source_ref -> P-D18.node_ref
P-D19.target_ref -> P-D18.node_ref
```

The exact cardinality and required flags must be proven against both reference
transactions before ratification. Consumer adapters import this registry; they
do not infer relationships from matching column names.

## 12. C-001 Proof

A valid C-001 package must make the following simultaneously visible:

1. the synthetic Nexus scenario and exact export snapshot;
2. Hermes' 12 expected, 11 posted, one submitted-unposted, one deferred, and
   GBP 10,000 recognition gap;
3. Atlas June v1 with GBP 0 subscription revenue;
4. Atlas June v2 with GBP 10,000 subscription revenue;
5. the exact GBP 10,000 restatement bridge without client subtraction;
6. the Argus completeness exception as a machine observation;
7. the Aegis review, finding, issue, remediation, verification, and successor
   issue stages without collapsing their meanings;
8. each purpose-specific readiness assessment for its exact version and scope;
9. Pythia's exact frozen input, approved source-domain decision, returned
   candidate, unsupported admission outcome, and GBP 6,500 monthly effect; and
10. the verified GBP 10,000 trace as unchanged directed nodes and edges.

The same package must preserve the business-event/accounting-event firewall.
No exported decision or row is eligible to drive posting-rule evaluation.

## 13. CT-1 Proof

A valid CT-1 package must make the following simultaneously visible:

1. the cash-application identity mismatch;
2. the exact Argus identity exception and Aegis governance chain;
3. J-010 as referenced-only G-13 state with its exact source hash;
4. the bind-before-compare reversal status;
5. separate immutable J-011 reversal and J-012 replacement journals;
6. balanced journal results copied from the governed view;
7. `CUST-VEGA` before and `CUST-ORION` after;
8. the published GBP 0 control-account net movement without export-side
   calculation; and
9. the exact verification and issue-update references.

CT-1 does not require a Pythia row or readiness assessment. Their absence is
scope-correct and must not be filled with synthetic defaults.

## 14. Failure Behaviour

| Failure | Required result |
|---|---|
| Any Artifact O query fails | Reject package build; retain typed cause in local build result only |
| Query envelopes disagree on snapshot | `SNAPSHOT_MISMATCH`; publish nothing |
| Input compatibility is not `EXACT_ORIGINAL` | `UNSUPPORTED_COMPATIBILITY_MODE` |
| A registered source field is unavailable | Omit only where the dataset contract permits unavailable data; otherwise reject |
| Duplicate row key with different bytes | `ROW_COLLISION`; publish nothing |
| Missing required relationship target | `RELATIONSHIP_VIOLATION` |
| Unknown field, enum, dataset, file, or schema | Reject |
| Hash or package digest mismatch | Verification fails; package is not trusted |
| Final output path already exists | Reject; do not overwrite |
| Source revision unavailable during reproduction | `SOURCE_REVISION_UNAVAILABLE` |
| Staging failure | Remove or quarantine only the resolved staging path; leave final path absent |
| Consumer adapter cannot represent a field | Adapter fails; canonical package remains valid and unchanged |

No failure authorises fallback to SQLite, current/latest state, a less exact
reporting version, a different readiness purpose, or a consumer-side formula.

## 15. Milestone 4 Build Sequence

### Phase 0 - Critique and ratify Artifact P

- verify every P-D field against exact Artifact O contracts and implementation;
- resolve P-D16 without creating a generic journal export;
- prove the relationship registry and snapshot semantics;
- close all contradictions with Artifact N exact-original rules; and
- ratify the final contract through an append-only ADR.

### Phase 1 - Canonical package contracts

- implement strict export request/result, manifest, schema, relationship, and
  verification models;
- implement canonical JSON and CSV serializers independently of validation
  library field order;
- implement deterministic row keys and closed dataset registry; and
- prove positive and negative serialization fixtures.

### Phase 2 - Revision-pinned export assembler

- add one read-only export snapshot over the existing in-process Artifact O
  service;
- implement O-Q to P-D tabularisation with no database access;
- enforce exact-original, snapshot, deduplication, and source-closure rules; and
- build C-001 and CT-1 packages through P-C01.

### Mandatory post-Phase-2 cohesion audit

Before any Excel or Power BI work, audit:

- every exported field against its Artifact O source;
- absence of new finance, assurance, governance, readiness, or planning logic;
- exact reporting history and purpose-specific readiness;
- evidence wording and directed trace preservation;
- deterministic package bytes, relationship integrity, and offline operation;
- dependency direction and absence of SQLite/fixture access; and
- C-001/CT-1 parity with the live public product.

### Phase 3 - Verification and reproducibility

- implement P-C02 and P-C03;
- prove clean build, failure atomicity, tamper detection, and exact
  reproducibility;
- publish one machine-readable Milestone 4 report; and
- retain all Milestone 1 through 3 acceptance gates unchanged.

### Phase 4 - Excel consumer

Only after the governed package passes the cohesion audit:

- define a separate Excel consumer artifact;
- import P-D datasets and registered relationships;
- preserve actuals, versions, readiness, provenance, and synthetic disclosure;
- add finance modelling as clearly consumer-owned assumptions and formulas; and
- prove refresh from a newly generated package without manual table repair.

### Phase 5 - Power BI consumer

Only after the same package boundary is proven:

- define a separate semantic-model artifact;
- import the same P-D datasets and registered relationships;
- classify columns and measures as governed source, display measure, or
  consumer-owned analytical calculation;
- preserve exact version, readiness, evidence, and module filters; and
- prove parity with Excel for shared governed values.

Expanded synthetic operations follow only after this boundary works at
canonical depth. Volume must not arrive before semantics.

## 16. Explicit Non-Goals

Artifact P does not include:

- an `.xlsx`, `.xlsm`, `.pbix`, or `.pbip` implementation;
- DAX, M, Power Query, VBA, Office Scripts, or workbook formulas;
- a generic BI semantic layer, report builder, or arbitrary SQL endpoint;
- a new warehouse, mart layer, database, or module repository;
- direct exports from SQLite or runtime persistence tables;
- an expanded ERP/CRM/bank/payroll generator or event taxonomy;
- authentication, uploads, scheduling, cloud storage, email delivery, or public
  mutation routes;
- paid APIs, hosted services, external datasets, AI commentary, or telemetry;
- global readiness, evidence-content invention, latest-version inference, or
  client-side accounting; or
- replacement of Artifact O's live browser API.

## 17. Acceptance Criteria

Artifact P may be ratified only when the following requirements are
unambiguous. Milestone 4 may close only when its implementation proves that:

- P-A01: one canonical package is the shared governed source for every
  analytical consumer;
- P-A02: no package or consumer artefact becomes authoritative platform input;
- P-A03: the assembler consumes only the in-process Artifact O boundary;
- P-A04: every dataset row belongs to one coherent export snapshot;
- P-A05: every input response is `EXACT_ORIGINAL`;
- P-A06: no unspecified latest lookup or silent version substitution occurs;
- P-A07: tabularisation is limited to lossless reshape and explicit copying;
- P-A08: all finance values remain integer minor units plus currency;
- P-A09: June v1 and v2 remain exact, immutable, and simultaneous;
- P-A10: restatement bridges are copied from Artifact O rather than recalculated;
- P-A11: readiness remains exact by product, purpose, period, and scope;
- P-A12: Pythia controlled use retains its exact readiness binding;
- P-A13: evidence and content-verification claims are not strengthened;
- P-A14: J-P11 node identity, semantic hash, edge direction, and relationship
  remain unchanged;
- P-A15: module ownership and cross-module references remain visible;
- P-A16: synthetic status is machine-readable and visible to every consumer;
- P-A17: the canonical directory, not a workbook or BI model, is the governed
  export representation;
- P-A18: schema files close types, nullability, enums, keys, and relationships;
- P-A19: canonical JSON and CSV are independent of model declaration, database,
  filesystem, and locale ordering;
- P-A20: null, empty, absent, and variant-inapplicable states cannot collapse;
- P-A21: P-C02 detects missing, extra, malformed, and tampered content;
- P-A22: P-C01, P-C02, and P-C03 do not mutate platform authority or
  projections;
- P-A23: final-path publication is atomic and never overwrites an existing
  package;
- P-A24: package creation, verification, and reproduction require no paid
  service, credential, or runtime network access;
- P-A25: contract growth follows P-R24 and never silently changes a version-1
  field;
- P-A26: the package contains exactly P-D01 through P-D20;
- P-A27: every P-D dataset has one proved Artifact O source mapping;
- P-A28: duplicate semantic rows from multiple permitted queries must be
  byte-identical;
- P-A29: the relationship registry validates all required targets and both
  directed trace endpoints;
- P-A30: C-001 proves the complete source-to-decision loop and verified GBP
  10,000 reporting trace;
- P-A31: CT-1 proves referenced-only source state, bind-before-compare reversal,
  separate correction journals, corrected identity, and GBP 0 net movement;
- P-A32: absence of CT-1 readiness or Pythia rows is preserved rather than
  defaulted;
- P-A33: a clean rebuild from the same source revision produces the same package
  digest;
- P-A34: tampering with one byte changes verification outcome;
- P-A35: a failed build leaves no apparently valid final package;
- P-A36: an Excel or Power BI adapter can consume only a P-C02-verified package;
- P-A37: every Artifact O field not exported is explicitly documented as
  presentation-only, redundant, or deferred rather than silently lost;
- P-A38: all Milestone 1 through 3 acceptance gates remain unchanged and
  passing; and
- P-A39: one clean-checkout Milestone 4 command verifies build, schema, hashes,
  relationships, C-001/CT-1 parity, offline operation, and reproducibility.

## 18. Structural Inventory

Artifact P v0.1 contains:

- 24 rulings: P-R01 through P-R24;
- 3 consumer profiles: P-U01 through P-U03;
- 3 export operations: P-C01 through P-C03;
- 20 datasets: P-D01 through P-D20; and
- 39 acceptance criteria: P-A01 through P-A39.

These counts are structural checks, not evidence of correctness.

## 19. Ratification Challenges and Next Move

The critique should focus first on four questions:

1. Can P-D16 journal lines be obtained through O-Q11's already-permitted exact
   application reads without widening Artifact O or creating a generic journal
   export?
2. Is one package-wide pinned query session implementable without weakening
   Artifact O's one-session-per-response rule or duplicating its assemblers?
3. Are P-D09 case-stage rows a demonstrably lossless reshape of O-V07, or do
   predecessor/successor columns imply workflow edges that Artifact O does not
   publish?
4. Does P-D13 remain a faithful one-row projection of O-V09, or should it be
   omitted until a genuine multi-effect planning contract exists?

The recommended next action is a hard cross-artifact critique of those four
questions plus a field-by-field implementation mapping. Artifact P remains a
draft until every dataset can be traced to an exact current source and no
consumer convenience has become a platform claim.
