# Artifact S v0.2 Hard Critique

Status: NOT RATIFIABLE - bounded v0.3 correction required

Date: 2026-08-17

## 1. Scope

This critique tests Artifact S v0.2 against the ratified and implemented
Artifact R boundary rather than only against S's internal prose and counts.

The review covers:

- the exact R-C01 build, R-C02 verification, and R-C03 reproduction
  contracts;
- the implemented Phase R2 canonical file inventory and detached digest;
- the complete `LINEAGE@v1` inventory of thirty-one tables, 189 rows, and 388
  catalogue columns;
- the sixteen R-owned technical relationship-key placements in LINEAGE;
- all fifty-seven LINEAGE relationship entries and twelve R measures;
- CSV, Parquet, DuckDB, and XLSX ownership and reproduction claims;
- the seven proposed S metadata files and two SQL example files;
- Excel/Open XML storage limits relevant to exact typed-value delivery;
- C-001 and CT-1 validation claims; and
- separation between governed handoff data and independently authored React,
  Excel, and Power BI analysis.

Artifact S's product direction is correct. The blockers are package closure,
materializer ownership, executable contract, and cross-format fidelity gaps.
None requires reopening Artifact P, Artifact Q, the runtime, the accounting
model, or the product thesis.

## 2. Structural and Implementation Audit

S's stated structural inventory is internally correct:

```text
26 rulings                 S-R01 through S-R26
1 profile                  LINEAGE@v1
4 delivery formats         CSV, PARQUET, DUCKDB, XLSX
7 metadata files           exact stated package tree
2 SQL files                starter and reconciliation
3 operations               S-C01 through S-C03
4 implementation phases    S0 through S3
36 acceptance criteria     S-A01 through S-A36
```

Identifiers are sequential. The document contains no non-ASCII bytes, tabs,
or trailing whitespace.

The implemented LINEAGE boundary is also exact:

```text
tables                         31
source rows                   189
catalogue columns             388
  governed source columns     372
  R technical projections     16
relationships                  57
  active                       30
  inactive role-playing         1
  navigation-only              18
  validation-only               8
measures                       12
```

The current CSV-plus-Parquet demonstration contains ninety-seven files inside
R's canonical checksum ledger plus `checksums.json` and `model.digest`, for
ninety-nine physical files in the verified model directory. DuckDB remains
rejected by the executable R service until Phase R3.

LINEAGE's 388 catalogue columns use these source-type families:

```text
text          258
integer        40
hash           38
enum           25
date           12
timestamp      10
boolean         5
nullable       58
```

These checks establish coverage and hygiene only. They do not close the eight
blocking findings below.

## 3. Strengths That Should Survive v0.3

The following decisions are sound and should not be reopened:

- S ends at a local handoff instead of generating finished consumers;
- React receives local query inputs, Excel receives a data pack, and Power BI
  receives typed files plus modelling instructions;
- the package uses complete LINEAGE rather than an undeclared subset;
- S creates no new fact, dimension, aggregate, forecast, valuation, or
  governed decision;
- canonical R files remain authoritative while DuckDB and XLSX are
  conveniences;
- money remains integer minor units and raw numerics retain no-summarization
  guidance;
- authored/referenced journals, reporting versions, readiness, evidence
  status, and trace direction remain distinct;
- the package states honestly that C-001 and CT-1 do not support a DCF,
  three-statement model, trends, budgeting, or broad KPIs; and
- later consumer work must reconcile to an exact handoff.

This is the right portfolio boundary. The correction pass should make it
executable without widening it.

## 4. Blocking Findings

### S-B01 - S cannot execute the R-C02 verification it requires

S-R01 requires R-C02 before S reads a table. S-C01 and S-C02 carry a source
model path and digest but omit the exact P-plus-Q source-package path.

The implemented `VerifyConsumerModel` requires:

```text
model_path
source_package_path
expected_model_digest
expected_source_package_digest
verification_scope = FULL_SOURCE_EQUIVALENCE
```

R-C02 first reruns P-C02 and deliberately refuses to infer source equivalence
from an R model alone.

Consequences:

- S-C01 cannot perform its first promised verification step;
- S-C02 can degrade to checksum-only trust in the R directory; and
- S-A01, S-A02, S-A09, and S-A36 are not executable.

Recommended repair:

- add `source_package_path` and `expected_source_package_digest` to S build,
  verify, and reproduce requests;
- require equality with the R manifest's source-package digest;
- retain `FULL_SOURCE_EQUIVALENCE` as the only v1 scope; and
- reject an unavailable, substituted, or merely resealed source package.

### S-B02 - The package breaks the verified R model into unverifiable pieces

The S tree copies R's `csv/`, `parquet/`, and `schemas/` directories but omits
R's canonical README, manifest, semantic catalogue, relationship catalogue,
checksum ledger, and detached digest. It then proposes S metadata with
overlapping meanings.

R-C02 verifies one closed directory and rejects missing or unknown files. The
three copied subtrees are not a model that R-C02 can verify.

Consequences:

- copied files lose their closed R directory context;
- common origin cannot be proved from individual file equality alone;
- R metadata can drift from renamed S projections; and
- `exact Artifact R tree` overstates what S preserves.

Recommended repair:

- embed the complete unchanged R model beneath `source-model/`;
- run R-C02 against that exact directory and the exact P-plus-Q package;
- let conveniences reference the embedded R paths; and
- if top-level copies remain, classify them as redundant S copies with their
  own parity proofs, not as the verified R model.

### S-B03 - DuckDB has competing owners and is not implemented yet

Artifact R already owns optional DuckDB materialization, including schemas,
Parquet loading, metadata, storage versions, cache checksum, logical parity,
read-only adapter rules, and canonical-digest exclusion.

The Phase R2 service explicitly reports `DUCKDB remains blocked until Phase
R3`. S-C01 nevertheless introduces an S DuckDB writer profile and says S builds
the database from its own inventory.

Consequences:

- S can diverge from the ratified R DuckDB contract;
- two builders can claim the same physical role;
- S cannot currently produce its mandatory package; and
- the R3/S phase order is undefined.

Recommended repair:

- implement and audit Phase R3 before S requires DuckDB;
- require the R source model to include CSV, Parquet, and DuckDB;
- copy/reference R's DuckDB and noncanonical cache manifest;
- remove the S-owned DuckDB writer profile; and
- reopen R through an ADR if S genuinely needs a different database.

### S-B04 - Digest and logical-reproduction rules contradict each other

S says the manifest records the handoff digest, checksums and digest are
written last, all files have closed scope, and DuckDB/XLSX reproduce logically
rather than byte-for-byte.

No single digest construction satisfies those statements:

- a checksummed manifest containing its own final digest is recursive;
- including DuckDB/XLSX bytes makes logical reproduction change the digest;
  and
- excluding them requires separate stable manifests and tamper rules that S
  does not define.

Consequences:

- S-R23 through S-R25 cannot all pass;
- S-C03 has no objective success test; and
- S-A10, S-A31, and S-A32 are ambiguous.

Recommended repair:

- omit `handoff_digest` from the manifest body;
- define `handoff.digest` as the hash of canonical checksum-ledger bytes;
- close the canonical path scope and ordering;
- exclude non-byte-reproduced binaries from canonical reproduction;
- add finite DuckDB/XLSX noncanonical manifests with writer coordinates,
  same-build file hashes, and logical digests; and
- separate canonical reproduction, tamper detection, and logical parity.

### S-B05 - XLSX type fidelity has no executable adapter map

S requires exact values and types but does not map R's seven source types into
SpreadsheetML cells. LINEAGE includes forty integers, ten timestamps, twelve
dates, five booleans, fifty-eight nullable columns, and many text/hash/enum
columns.

Excel has fifteen digits of numeric precision. Open XML cells also represent
numeric/date, shared-string, and Boolean storage differently rather than
retaining R's type vocabulary automatically.

Official references:

- [Excel specifications and limits](https://support.microsoft.com/en-US/Excel/excel-specifications-and-limits)
- [Microsoft Learn: Open XML cell values](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/how-to-retrieve-the-values-of-cells-in-a-spreadsheet)

Consequences:

- a signed 64-bit integer can lose digits as an Excel number;
- UTC timestamp representation can drift as a serial date/time;
- blank cells have no self-describing R null/type meaning;
- hashes, enums, dates, and timestamps can be inferred or reformatted; and
- exact typed equality cannot be tested from displayed text.

Recommended repair:

- define `XlsxTypeMap@v1` for every R type;
- store hashes, enums, UTC timestamps, and unsafe integers as explicit text;
- define the safe numeric range for integer minor units;
- close the date system, timestamp format, Boolean type, null representation,
  and no-inference rule;
- include source type/nullability in the table map;
- close sheet, table, column, style, visibility, and ordering rules; and
- verify by reopening Open XML and reconstructing exact typed R rows.

### S-B06 - The metadata files lack contracts and derivation rules

S names seven metadata files but defines no exact fields, versions, ordering,
serialization, source R fields, or permitted S additions. Several overlap R's
manifest, semantic catalogue, and relationship catalogue.

`lineage.json` is ambiguous: it could mean model lineage metadata, pointers to
P-D16/P-D17, or duplicated governed trace rows. Only the first two are within
S's authority.

Consequences:

- metadata can become a second semantic catalogue;
- relationships or measures can drift during renaming;
- consumers cannot distinguish R authority from S guidance; and
- S-R06, S-R10, S-R11, S-R16, and S-A05 through S-A07 are open.

Recommended repair:

- define a strict versioned schema for each file;
- mark every field `R_COPY`, `R_PROJECTION`, or `S_GUIDANCE`;
- use byte copies where R already has the required shape;
- make projections canonical and reversible to exact source coordinates;
- prohibit `lineage.json` from duplicating/synthesizing trace edges; and
- add missing/extra/reordered/changed metadata fixtures.

### S-B07 - Controls and SQL are not a finite validation registry

S lists useful outcomes but does not bind them to check IDs, dataset rows, R
measures, selectors, typed minor-unit expectations, or failure semantics. The
prose uses GBP major units even though S-R09 makes major-unit display
consumer-owned.

The bridge must come from P-D07/R-M02, correction movement from P-D13/R-M06,
journal balance from exact R-M07/R-M08 rows, and readiness from one exact
purpose/scope. Their agreement cannot create a finding or approval.

Consequences:

- SQL can recompute a conclusion under the label of validation;
- workbook controls can be plausible but untraceable;
- major-unit conversion can appear governed; and
- S-A21 and S-A31 are not executable.

Recommended repair:

- define `ValidationCheckRegistry@v1` with finite check IDs;
- bind dataset coordinates, row selectors, source fields/R measures, typed
  minor-unit expectations, and currency;
- classify structural, source, measure, and relationship checks;
- prohibit validation queries from creating conclusions;
- separate non-authoritative starter SQL from verifier SQL;
- close permitted relationship dispositions and query ordering; and
- generate workbook controls from executed registry results.

### S-B08 - S-C01 through S-C03 are not closed operations

Unlike P/Q/R, S defines no strict request/results, status vocabulary, failure
semantics, exact file registry, or machine-testable negative cases. Writer
profiles are named but have no contracts or hashes.

Missing boundaries include source-package inputs, required R formats,
canonical/noncanonical counts, writer hashes, workbook logical digest,
verification checked counts, reproduction statuses, path firewall,
unknown-file behavior, workbook hazard detection, and visual-evidence binding.

Consequences:

- Phase S1 has no finite executable target;
- atomicity/non-overwrite remain prose-only;
- failure can leave unclear outputs; and
- S-A01 through S-A36 cannot become one acceptance catalogue.

Recommended repair:

- define strict S-C01/S-C02/S-C03 request and result models;
- close the canonical/noncanonical file registry before writing;
- bind exact writer profiles and dependency versions;
- add finite fail-closed status values;
- reuse R's path firewall and same-parent staging rules;
- bind workbook inspection and visual evidence to the exact revision; and
- add tamper, missing, unknown, collision, type-loss, formula, macro, link,
  stale-source, and atomicity fixtures.

## 5. Non-Blocking Tightening Items

### S-N01 - Replace `mart-ready` with `consumer-ready`

S prohibits replacement marts. `Consumer-ready governed analytical inputs` is
more exact and avoids implying a dimensional mart already exists.

### S-N02 - DuckDB read-only status belongs to the adapter

The file is not intrinsically immutable. Require adapters to open it read-only;
any write invalidates its cache checksum and verified-handoff claim.

### S-N03 - Close Excel naming and capacity rules

Define sheet/table normalization, reserved names, collision suffixes, row/cell
capacity gates, and failure rather than silent truncation.

### S-N04 - Distinguish data presence from metadata presence

CSV/Parquet carry data tables; XLSX and DuckDB also carry metadata structures.
Acceptance criteria should state exactly where relationships and measures
appear rather than saying every inventory exists in every format.

### S-N05 - Later subsets remain declared contracts

A consumer subset must prove endpoint closure and explain every omission. It
cannot call an undeclared CORE-plus-selected-LINEAGE hybrid an R profile.

### S-N06 - Bind the illustrative demo coordinate to a fixture

`R-LINEAGE-DEMO` is caller-defined. Bind S's first package to the exact model
manifest and digest produced by its fixture.

### S-N07 - Query results require explicit ordering

SQL result order is undefined without `ORDER BY`. Every reproducible example or
validation result needs an exact ordering and typed result schema.

## 6. Answers to S's Eight Critique Questions

### 6.1 Does S duplicate files that should remain in R?

Yes. Embed one complete verified R model and derive only S-specific
conveniences.

### 6.2 Can DuckDB remain rebuildable acceleration?

Yes, under Phase R3 ownership and R's noncanonical cache contract. S must not
create a second materializer.

### 6.3 Can XLSX preserve R types and nulls logically?

Not under v0.2. A strict type map, writer profile, and Open XML round-trip
verifier can make the claim testable.

### 6.4 Is the metadata sufficient for later adapters?

Conceptually yes, mechanically no. It needs closed schemas and deterministic R
derivation.

### 6.5 Does suitability prevent C-001/CT-1 overclaiming?

Yes. Retain it prominently and express controls in governed minor units and
exact scope.

### 6.6 Can example SQL avoid becoming an ungoverned mart?

Yes, if it is read-only, ordered, finite, source-bound, and never persists new
facts or joined views.

### 6.7 Can every format reconcile to one snapshot digest?

Not yet. Canonical digest, binary checksums, logical digests, and the complete R
source model must first be separated.

### 6.8 Has consumer implementation leaked into S?

The large v0.1 leak is closed. S-owned DuckDB materialization and GBP major-unit
controls are the two remaining smaller leaks.

## 7. Required v0.3 Correction Sequence

1. Make the exact P-plus-Q package and complete R model mandatory S inputs.
2. Replace split canonical subtrees with one embedded unchanged R model.
3. Complete R3 and make R the sole DuckDB materializer.
4. Separate canonical digest, binary checksums, and logical reproduction.
5. Define the XLSX type map, writer profile, digest, and verifier.
6. Close all seven metadata contracts and provenance.
7. Define finite validation-check and SQL registries in minor units.
8. Close S-C01 through S-C03 and all negative fixtures.

Then rerun R-C02, the 31/388/57/12 inventory proofs, cross-format parity,
DuckDB R3 checks, Open XML inspection, every C-001/CT-1 validation check,
reproduction, the complete negative suite, and all prior milestone gates.

## 8. Verdict

Artifact S v0.2 is not ratifiable as written.

Eight blocking issues remain:

1. S cannot invoke mandatory R-C02 verification.
2. The package splits the closed R model into unverifiable pieces.
3. DuckDB has competing R/S ownership and R3 is incomplete.
4. Digest and logical-reproduction rules conflict.
5. XLSX type/null fidelity is unspecified.
6. The seven metadata files have no executable contracts.
7. Controls and SQL lack a finite source-bound registry.
8. S-C01 through S-C03 are not closed executable operations.

A bounded v0.3 can close all eight without adding a dashboard, DCF,
three-statement model, DAX, TMDL, new runtime query, new domain dataset, or paid
dependency.
