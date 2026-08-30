# Artifact S v0.3 Structural and Semantic Reassessment

Status: NOT RATIFIABLE - bounded v0.4 correction required

Date: 2026-08-18

## 1. Scope and method

This reassessment tests `docs/product/local-analytical-handoff.md` v0.3 against:

- all eight blocking findings and seven tightening items in the v0.2 critique;
- the ratified Artifact R v0.2 design and implemented Phase R2 contracts;
- the implemented R-C01 through R-C03 request and result shapes;
- the verified local `LINEAGE@1` inventory;
- the still-unimplemented Artifact R Phase R3 boundary;
- C-001 and CT-1 source semantics;
- package, digest, XLSX, metadata, validation, and operation closure; and
- the rule that S must stop before any React, Excel model, or Power BI model.

The result is mixed. The product boundary is now correct and four major v0.2
problems are closed. Five bounded contract-closure blockers remain. They do not
require a new domain dataset, runtime query, dashboard, financial model, DAX,
TMDL, or paid dependency.

## 2. Structural results

The declared v0.3 inventory is mechanically consistent:

```text
32 rulings                    S-R01 through S-R32
1 package tree                one embedded complete R model
2 path classes                canonical and noncanonical
3 verification claims        canonical bytes, same-build binary, logical
4 representations            R CSV, R Parquet, R DuckDB, S XLSX
8 metadata files              including the validation registry
12 validation checks          S-V01 through S-V12
3 operations                  S-C01 through S-C03
58 acceptance criteria        S-A01 through S-A58
```

All identifier ranges are sequential and unique. The document contains no
non-ASCII content or trailing whitespace. The package tree contains no React,
Power BI, dashboard, report, forecast, valuation, or financial-model output.

The structural count therefore passes. Count correctness does not make the
nested contracts executable; those remaining issues are recorded below.

## 3. Upstream model compatibility

The implemented Phase R2 `LINEAGE@1` evidence remains:

```text
31 tables
189 source rows
388 catalogue columns
57 relationships
12 measures
99 physical files in the verified R2 model directory
```

Artifact S v0.3 correctly requires the complete R directory and exact P-plus-Q
package for R-C02 `FULL_SOURCE_EQUIVALENCE`. It also correctly refuses to copy
isolated CSV, Parquet, or schema subtrees as if they were a verified R model.

The currently executable R service still rejects DUCKDB until Phase R3. The R
`ModelManifest@v1` names `noncanonical_cache_manifest_path`; it does not name a
DuckDB file path. The future R cache manifest is intended to own that path,
engine version, storage-compatibility version, same-build file hash, and logical
table digests, but no strict R3 cache-manifest contract or implementation yet
exists.

S can therefore bind the R2 inventory today, but it cannot yet verify the exact
CSV/PARQUET/DUCKDB source model required by S-R01, S-R05, S-A03, and S-A04.

## 4. v0.2 blocking-finding closure

| v0.2 finding | v0.3 result | Judgment |
|---|---|---|
| S-B01 - R-C02 inputs incomplete | All S operations carry the exact P-plus-Q path/digest and expected model digest; S-C02 resolves the embedded model path. | CLOSED |
| S-B02 - verified R model split apart | `source-model/` is one complete unchanged R directory; no second CSV/Parquet/schema tree remains. | CLOSED |
| S-B03 - competing DuckDB ownership and missing R3 | R is now the sole owner, but R3 has neither an executable cache contract nor an audited implementation. S also names the DuckDB path as if it came from the R manifest rather than the future cache manifest. | PARTIAL |
| S-B04 - recursive/conflicting digest claims | The manifest omits its own digest; canonical bytes, same-build hashes, and logical reproduction are separated. Remaining nested-schema issues do not reopen the core digest ruling. | CLOSED AT DESIGN LEVEL |
| S-B05 - XLSX type fidelity absent | `XlsxTypeMap@v1` is strong, but the writer and renderer are described as future profiles rather than one closed supported profile. Naming, capacity, and visual-evidence rules also remain incomplete. | PARTIAL |
| S-B06 - metadata contracts absent | File names, top-level contracts, payload intent, and ordering now exist, but field-level provenance and several nested item schemas remain open. | PARTIAL |
| S-B07 - no finite validation registry | Twelve IDs and correct source values exist, but the single-coordinate/single-field schema cannot represent seven of the twelve declared checks. | NOT CLOSED |
| S-B08 - operations not closed | Inputs, sequencing, staging, and high-level results improved materially, but serialized contract-version fields, complete result/error models, supported profile literals, nested schemas, and fixture IDs remain open. | PARTIAL |

Four findings are closed or closed at the design level. Four original findings
remain partial or open and resolve into the five bounded blockers below.

## 5. Blocking findings

### S3-B01 - The required R3 source contract does not yet exist

S requires an R model whose `requested_formats` are exactly CSV, PARQUET, and
DUCKDB. It also declares exactly four noncanonical S paths, including the R
DuckDB file and R cache manifest.

The current R implementation rejects DUCKDB. The current R manifest contains
only `noncanonical_cache_manifest_path`; the DuckDB file path belongs in the
future cache manifest. Artifact S line 355 instead says the R manifest declares
the DuckDB path. The six Phase R3 bullets do not yet define a strict cache
manifest, supported engine/storage coordinates, request validation, verifier,
reproducer, or negative fixtures.

Consequences:

- S cannot compute its closed noncanonical path registry from an executable R
  contract;
- S-C01 cannot obtain the required source model;
- S-C02 cannot exercise the promised R DuckDB checks; and
- R3/S sequencing is stated but not yet backed by a ratified implementation
  boundary.

Required repair:

1. design, implement, and audit R3 before S1;
2. define a strict `NoncanonicalCacheManifest` with the DuckDB path, engine and
   storage coordinates, file hash, table logical digests, ordering, and counts;
3. update R-C01 through R-C03 to build, verify, and logically reproduce it; and
4. make S resolve the DuckDB path through the verified R cache manifest, never
   directly from `ModelManifest@v1`.

### S3-B02 - The XLSX writer and renderer are not actually pinned

`XlsxTypeMap@v1` closes the seven R source types, null representation, safe
integer decision, timestamp/date text policy, and logical workbook preimage.
That is a substantial correction.

`XlsxWriterProfile@v1`, however, lists fields that a future profile must fix. It
does not select an implementation, exact version, supported profile ID, profile
hash, Open XML settings, ZIP policy, date system, style values, or document-
property policy. S-C01 accepts any caller-supplied profile reference/hash rather
than one literal supported registry entry. `render_profile_ref/hash` has no
separate finite contract at all.

The canonical S manifest also carries `render_evidence_digest`, which includes
render-image hashes even though images are outside the package. Exact renderer
version alone does not close operating system, fonts, locale, page setup, and
pagination. S-C03 therefore cannot yet know whether render bytes are a canonical
reproduction coordinate or noncanonical audit evidence.

Excel naming and capacity are also incomplete. The contract does not close
reserved sheet names, leading/trailing apostrophes, cell-reference-like table
names, exact 16,384-column and 32,767-character limits, or defined-name
collisions.

Required repair:

1. select one exact supported writer profile with literal implementation,
   version, settings, and hash;
2. define one exact render profile including fonts, locale, operating-system or
   container coordinate, page setup, and deterministic output rules;
3. decide whether render hashes are canonical reproduction inputs or external
   revision-bound audit evidence, and make S-C02/S-C03 match that decision;
4. bind `XlsxTypeMap@v1` and the supported writer/render profiles as literal
   operation coordinates; and
5. close every Excel sheet, table, defined-name, column, row, and cell-string
   validity and capacity rule.

### S3-B03 - Metadata provenance and nested schemas remain open

The eight metadata documents now have names, versions, source digests, payload
intent, and array ordering. They also correctly keep the P-D16/P-D17 graph in R
rather than copying it into `lineage.json`.

The shared envelope nevertheless has one file-level `derivation_class`, while
several files mix R projections and S additions. For example,
`data-dictionary.json` combines R column semantics with S-owned
`xlsx_storage_mode`. A single `R_PROJECTION` or `S_GUIDANCE` value cannot mark
every field as required by the critique.

Several nested types are also not closed:

- `items[] or document-specific payload` permits two shapes;
- `applicable R format_hints[]` has no deterministic applicability rule;
- `directed_join_steps[]` and `evidence_status_field_coordinates[]` have no
  item schema;
- consumer suitability use and path entries have no finite item contract; and
- the `metadata_entries[]` source-payload and derivation binding in the handoff
  manifest has no exact nested shape.

Consequences:

- two valid builders can emit different metadata while claiming the same
  contract;
- S guidance cannot always be separated mechanically from R authority;
- missing, extra, reordered, or changed nested fields cannot be tested
  consistently; and
- S-A17 through S-A19 are not executable as written.

Required repair:

1. replace the file-level provenance shortcut with an exact field or field-set
   provenance map;
2. define every nested object and list item as a strict versioned model;
3. remove `or`, `applicable`, and other open derivation language;
4. provide one deterministic source-field mapping and ordering function per
   metadata contract; and
5. enumerate positive and missing/extra/reordered/changed fixtures by ID.

### S3-B04 - The validation schema cannot encode its own registry

Each `ValidationCheckRegistry@v1` entry permits only one
`source_dataset_coordinate`, one `field_name`, one `measure_id`, one expected
type, and one expected value.

Only S-V01 through S-V05 fit that shape directly. At least seven checks do not:

- S-V06 spans P-D10 readiness, P-D15 bases, and P-D20 limitations;
- S-V07 checks both monthly cost and readiness reference;
- S-V08 checks net movement and bind-before-compare status;
- S-V09 and S-V10 each require debit and credit fields plus R-M07/R-M08;
- S-V11 compares four authored/referenced datasets; and
- S-V12 checks both node and edge populations, endpoint resolution, direction,
  terminals, and evidence status.

`row_selector[]`, `result_columns[]`, `result_order[]`, and
`source_evidence_refs[]` also lack strict item shapes. The SQL can return more
columns, but that does not repair the registry's single-field source contract.

Consequences:

- the verifier cannot derive one unambiguous query for seven registered IDs;
- composite assertions can hide new calculation or governance logic;
- `VALIDATION_RESULTS` cannot be generated from one finite result model; and
- S-A41 through S-A48 remain unimplementable.

Required repair:

1. define each check as an ordered `assertions[]` collection;
2. give every assertion its own dataset coordinate, typed key-value selector,
   source field or structural predicate, measure reference, expected type/value,
   currency, relationship IDs, and evidence refs;
3. close a check-level combiner, initially `ALL_ASSERTIONS_REQUIRED` only;
4. define strict typed result-column and ordering objects;
5. keep all money assertions in integer minor units plus exact currency; and
6. prove that each S-V01 through S-V12 instance validates against the schema.

### S3-B05 - S-C01 through S-C03 are not yet strict serialized contracts

The operation sections now provide the correct source inputs, required format,
staging order, verification sequence, non-overwrite behavior, checked counts,
and reproduction intent. They are much closer to P/Q/R quality.

They still omit fields needed by strict executable models:

- each request/result is named as versioned, but its `contains exactly` list
  omits `request_contract_version` or `result_contract_version`;
- Build and Verify use combined prose entries such as `handoff_ref and
  handoff_path` rather than one exact field per line;
- the S-C03 result is described in prose rather than a complete field list;
- Build has no explicit error/result vocabulary or declared exception contract;
- the supported XLSX type-map/writer/render profile registry is not finite;
- checksum-ledger, sheet-entry, Open XML part-entry, metadata-entry, SQL-entry,
  selector, and result-column nested models are incomplete; and
- negative fixtures are categories without fixture IDs, expected failure codes,
  pre-write/post-write phase, or residual-path expectations.

Consequences:

- an implementation cannot use strict `extra=forbid` models without inventing
  fields;
- failure behavior cannot be asserted uniformly;
- S-C03 has no one canonical result serialization; and
- S-A50 through S-A55 do not yet form an executable acceptance catalogue.

Required repair:

1. define strict immutable request and result models with literal contract-
   version fields and one field per key;
2. define success, failure-code, exception, checked-count, and nullable-result
   rules for every operation;
3. close every nested manifest, ledger, selector, result, and inventory model;
4. bind only supported literal profile coordinates; and
5. create a finite negative-fixture registry mapping each fixture ID to the
   exact operation, failure code, publication state, and cleanup expectation.

## 6. Tightening-item closure

| Item | Result | Judgment |
|---|---|---|
| S-N01 - use `consumer-ready` | The phrase replaces `mart-ready` and the no-mart rule remains explicit. | CLOSED |
| S-N02 - read-only belongs to the adapter | S-R06 places read-only opening on React/direct-SQL adapters and treats mutation as checksum invalidation. | CLOSED |
| S-N03 - Excel naming and capacity | Normalization, collision suffixes, row preflight, and fail-rather-than-split exist; reserved names, exact column/string limits, and cell-reference/defined-name rules remain open. | PARTIAL |
| S-N04 - distinguish data and metadata presence | CSV/Parquet, DuckDB `model_meta`, and XLSX metadata sheets now have distinct physical roles. | CLOSED |
| S-N05 - declared later subsets | S prohibits informal subsets, but endpoint closure and omission reasons are not explicit requirements of the later contract. | PARTIAL |
| S-N06 - bind/remove unpinned demo coordinate | The unbound `R-LINEAGE-DEMO` label is gone; exact source model/package digests are mandatory. | CLOSED |
| S-N07 - ordered query results | Reconciliation and starter queries are required to have exact result schemas and explicit `ORDER BY`. | CLOSED |

Five tightening items are closed and two remain partial.

## 7. Semantic scenario reassessment

### 7.1 C-001

The declared values and authorities are correct:

- P-D06 preserves separate June v1 GBP 0 and June v2 `1000000` minor GBP rows;
- P-D07/R-M02 remains the exact `1000000` minor GBP bridge authority;
- P-D04/R-M03 and P-D08/R-M04 retain their exact difference fields without
  their agreement becoming a finding or approval;
- P-D10 readiness remains purpose, reporting-version, and scope specific and
  travels with P-D15 bases and P-D20 limitations; and
- P-D11/R-M05 retains `650000` minor GBP and the exact readiness reference.

S preserves exception, finding, issue, remediation, readiness, limitation, and
decision as distinct objects. It does not calculate a DCF, three-statement
model, or executive KPI. Semantic intent passes.

Executable proof is incomplete because S-V06 and S-V07 do not fit the current
single-field registry shape.

### 7.2 CT-1

The declared values and populations are also correct:

- P-D13/R-M06 retains zero control-account net movement and
  `BOUND_BEFORE_COMPARE`;
- Q-D04/R-M07/R-M08 retains J-011 and J-012 as separate authored journals with
  `12000000` minor GBP debit and credit totals each;
- Q-D08/Q-D09 retain referenced J-010 outside the authored population; and
- P-D16/P-D17 retain directed trace identities and evidence terminals.

S does not infer closure from balanced journals or verified remediation.
Semantic intent passes.

Executable proof is incomplete because S-V08 through S-V12 need multi-
assertion, multi-dataset registry shapes.

### 7.3 Semantic judgment

No new domain value, truth level, relationship, measure, status, or consumer
calculation has leaked into v0.3. The C-001 and CT-1 prose remains faithful to
P/Q/R. The remaining semantic risk is mechanical: the declared registry cannot
encode all of the exact proofs it promises.

## 8. Required v0.4 correction sequence

The bounded correction order is:

1. complete and audit R3, including the strict noncanonical cache manifest and
   R-C01/R-C02/R-C03 behavior;
2. correct S's R DuckDB path source and bind the exact audited R3 contract;
3. select literal XLSX writer and renderer profiles and settle render-evidence
   canonicality;
4. finish Excel naming, reserved-name, capacity, and defined-name rules;
5. replace file-level metadata provenance with strict field-set provenance and
   close every nested metadata model;
6. replace the single-field validation shape with ordered typed assertions and
   validate all twelve instances;
7. close every S operation, manifest, ledger, result, error, and negative-
   fixture model; and
8. repeat this structural and semantic reassessment before ratification.

After ratification, implementation must still proceed through S1 to S4 and the
mandatory cohesion audit. No handoff, XLSX, React, Excel model, Power BI model,
DAX, TMDL, report, forecast, or valuation is authorised by this assessment.

## 9. Verdict

Artifact S v0.3 is not ratifiable as written.

The product boundary is correct. The exact source-package binding, complete R
embedding, single R ownership of DuckDB, no-mart/no-consumer boundary, core
digest separation, XLSX type map, and C-001/CT-1 intent should survive v0.4.

Five bounded blockers remain:

1. the exact R3 cache contract and implementation do not exist;
2. XLSX writer/render profiles and the visual-evidence role are not closed;
3. metadata provenance and nested schemas are not fully executable;
4. the validation schema cannot represent seven of its twelve checks; and
5. S-C01 through S-C03 still lack complete strict serialized models.

A bounded v0.4 can close all five without expanding Artifact S into consumer
analysis or presentation.
