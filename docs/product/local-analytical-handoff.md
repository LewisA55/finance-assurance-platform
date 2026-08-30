# Artifact S - Local Analytical Handoff Package

Status: Design v0.3 - bounded correction draft for reassessment

## 0. Purpose and hard constraint

Artifact S defines one portable, local, consumer-ready handoff over one exact,
fully verified Artifact R `LINEAGE@1` model. It supplies governed analytical
inputs for later React, Excel, Power BI, and direct-SQL work without generating
any of those consumer experiences.

The first handoff contains:

1. the complete, unchanged Artifact R source model with CSV, Parquet, and the
   R-owned rebuildable DuckDB cache;
2. a data-only XLSX projection of that model;
3. finite, tool-neutral metadata projections and modelling guidance;
4. source-bound starter and reconciliation SQL; and
5. one manifest, checksum ledger, and detached digest that close the handoff.

> Artifact S packages governed, consumer-ready analytical inputs. It does not
> build analysis, presentation, or a new semantic truth.

No S implementation is authorised until Artifact R Phase R3 has implemented
and audited the optional DuckDB materialization required by this contract.
Artifact S never substitutes for R3 and never owns a DuckDB writer.

## 1. Binding authority and prerequisite

Artifact S is bound, in order, by:

1. the exact P-plus-Q governed package and detached package digest;
2. successful P-C02 full offline verification of that package;
3. the ratified Artifact R v0.2 contract and its implemented R3 extension;
4. successful R-C02 `FULL_SOURCE_EQUIVALENCE` verification of the source model
   against the exact P-plus-Q package;
5. the complete R `ModelManifest@v1`, semantic catalogue, relationship
   catalogue, checksums, and detached model digest; and
6. this Artifact S contract.

Where S conflicts with the verified P/Q package or R model, P/Q and R win. S
may add delivery metadata and a reversible XLSX projection. It may not change a
row, source type, null state, key, grain, relationship disposition, measure
classification, readiness conclusion, limitation, evidence status, or lineage
direction.

The build source is valid only when the R manifest has exactly:

```text
profile_id              LINEAGE
profile_version         1
requested_formats       CSV, PARQUET, DUCKDB
source_compatibility    EXACT_ORIGINAL
source_verification     VERIFIED
```

R3 completion and its post-implementation cohesion audit are external
prerequisites to S1. Ratification of this design alone does not satisfy them.

## 2. Product boundary

```text
ordinary runtime authority
-> exact P-plus-Q governed package
-> P-C02 full offline verification
-> exact R LINEAGE@1 model with CSV, Parquet, and R-owned DuckDB
-> R-C02 full source-equivalence verification
-> Artifact S local analytical handoff
   |- unchanged source-model/
   |- data-only XLSX projection
   |- deterministic metadata projections
   `- source-bound SQL examples
-> independently governed consumer projects
```

Artifact S does not emit:

- React source, routes, components, dashboards, charts, or drill-through;
- Excel formulas, financial models, forecasts, valuations, assumptions, or
  executive dashboards;
- Power BI `.pbix`, `.pbip`, TMDL, semantic models, DAX, report pages, or
  visuals;
- replacement facts, conformed marts, aggregates, latest-only views, or
  consumer-owned conclusions; or
- any paid, cloud, credentialed, or network runtime dependency.

The consumer projects begin only after the S handoff. Their presentation and
consumer-owned calculations may differ, but their governed source values must
reconcile to the same handoff digest.

## 3. Settled rulings

### S-R01 - Both upstream artifacts are mandatory inputs

S-C01, S-C02, and S-C03 require the exact P-plus-Q package path and digest as
well as the exact R model path and digest. R-C02 passes in
`FULL_SOURCE_EQUIVALENCE` scope before S reads or copies any model file.

### S-R02 - The complete R model is embedded unchanged

The handoff contains one byte-for-byte `source-model/` copy of the fully
verified R model directory. R's README, manifest, semantic catalogue,
relationship catalogue, canonical table files, schemas, checksums, detached
digest, DuckDB cache, and noncanonical cache manifest retain their exact paths
relative to that directory.

### S-R03 - S does not split or republish R authority

S creates no second top-level `csv/`, `parquet/`, `schemas/`, or `warehouse/`
copy. Consumers resolve canonical data through `source-model/` and its R
manifest. S metadata is either a byte copy, a deterministic projection, or
explicit S guidance; it is never a replacement semantic authority.

### S-R04 - LINEAGE remains whole

The first handoff admits the complete R `LINEAGE@1` table and relationship
inventory. A later consumer may select a declared subset in its own governed
contract. S publishes no informal subset and no consumer-specific mart.

### S-R05 - R is the sole DuckDB materializer

Artifact R Phase R3 alone builds, versions, checksums, and logically verifies
DuckDB from R Parquet. S copies the verified R cache inside `source-model/`,
records its R-owned cache-manifest path, and supplies no DuckDB writer profile
or database-writing code.

### S-R06 - DuckDB is read-only at the consumer adapter

The database file itself is a rebuildable cache. React and direct-SQL adapters
must open it read-only. Any write invalidates the R same-build checksum and
requires R-C02 reverification or R-C03 reproduction.

### S-R07 - Delivery formats are not truth levels

CSV and Parquet are R canonical table files. DuckDB is an R noncanonical cache.
XLSX is an S noncanonical projection. These physical roles do not create
different business, accounting, assurance, or governed truth.

### S-R08 - Canonical reproduction is byte-exact

Every path in the S canonical checksum ledger must reproduce byte-for-byte
from the exact inputs and pinned profiles. Canonical JSON and SQL are UTF-8,
ASCII-content, LF-terminated files. Canonical JSON uses lexical object-key
ordering, declared array order, no insignificant whitespace, and no floats.

### S-R09 - Noncanonical binaries reproduce logically

DuckDB and XLSX bytes are excluded from the S canonical digest. Each has a
finite noncanonical manifest carrying a same-build SHA-256 and typed logical
digests. Reproduction must match logical digests; it need not match binary
bytes across engine or ZIP rebuilds.

### S-R10 - Digest roles remain distinct

`checksums.json` detects canonical-file byte changes. `handoff.digest` binds the
canonical checksum-ledger bytes. A noncanonical manifest detects same-build
binary tampering. Typed logical digests prove cross-build parity. None of these
claims substitutes for the others.

### S-R11 - The handoff manifest is not self-referential

`handoff-manifest.json` must not contain `handoff_digest`. `checksums.json` and
`handoff.digest` are written after all canonical payload files and are outside
their own ledger. The detached digest is exactly the lowercase SHA-256 of the
canonical `checksums.json` bytes, prefixed by `sha256:`.

### S-R12 - Consumer metadata stays outside domain rows

Worksheet names, XLSX storage modes, display labels, suggested folders,
formatting hints, and suitability notes live only in S metadata. No source row
or R canonical file is modified to carry consumer concerns.

### S-R13 - Source types and nulls survive logically

Every XLSX cell reconstructs to the exact R logical value and source type under
`XlsxTypeMap@v1`. SQL examples read the R physical types. Missing cells never
become zero, false, empty string, or a display placeholder.

### S-R14 - Empty text cannot masquerade as null

The verified R source contracts prohibit non-null empty strings. In the XLSX
projection an absent cell therefore represents null unambiguously. A present
text cell must contain at least one character.

### S-R15 - Raw numerics are not automatically aggregated

All raw integer fields retain `SummarizeBy = None` guidance. Only registered R
measures may be suggested for governed aggregation. S creates no formula, DAX,
SQL view, or persisted aggregate.

### S-R16 - Major-unit display is consumer-owned

Governed money remains signed integer minor units plus exact currency. S
metadata may carry display-format guidance. S files and validation SQL never
replace governed values with decimal major-unit facts.

### S-R17 - Relationship topology is copied exactly

Active, inactive role-playing, navigation-only, and validation-only
dispositions retain their R identities, directions, keys, cardinalities, and
reasons. S creates no Power BI relationship, Excel Data Model relationship, or
alternative join path.

### S-R18 - Measures remain specifications

R measure definitions, grains, classifications, source coordinates, and
aggregation rules are delivered as metadata. S implements no Excel formula,
DAX expression, React calculation, or materialized SQL measure.

### S-R19 - Authored and referenced accounting remain separate

Q-D04/Q-D05 authored journals remain distinct from Q-D08/Q-D09 referenced
source projections. Referenced J-010 never enters the authored journal
population or acquires authored status.

### S-R20 - Reporting history remains simultaneous

As-was and as-restated reporting versions remain separate rows in every
format. S supplies no hidden latest default and never derives the P-D07 bridge
from journals or reporting-value subtraction.

### S-R21 - Readiness and limitations travel together

Any controlled-use guidance points to exact P-D10 readiness, P-D20
limitations, and P-D15 evidence references. A checksum, balanced journal,
populated value, or successful S verification never implies readiness.

### S-R22 - Evidence status remains exact

`CONTENT_BYTES_VERIFIED` and `DECLARED_HASH_ONLY` remain distinct. S validation
may check the stored classification but may not strengthen a declared hash into
content verification.

### S-R23 - Trace identity and direction remain exact

P-D16 nodes and P-D17 directed edges retain exact identities, source/target
direction, and evidence terminals. No undirected convenience edge is emitted.

### S-R24 - React receives query inputs only

React receives the R-owned DuckDB cache, Parquet, schemas, relationship
metadata, and bounded SQL. No UI implementation is part of S.

### S-R25 - Excel receives a data pack only

Excel receives canonical CSV through `source-model/` and one data-only XLSX
projection with documentation and static validation results. It receives no
financial model, forecast, valuation, dashboard, formula, macro, connection,
query, or Data Model.

### S-R26 - Power BI receives import inputs only

Power BI receives canonical Parquet through `source-model/`, exact modelling
metadata, and measure specifications. It receives no semantic model, DAX,
TMDL, report page, or visual.

### S-R27 - SQL is read-only and non-authoritative

SQL may select source rows, counts, types, nulls, relationships, and registered
validation results. It may not create or persist data, invent a conclusion, or
recompute an upstream governed measure under a new label.

### S-R28 - Consumer suitability is stated honestly

The handoff is sufficient for lineage demonstrations, restatement inspection,
correction assurance, controlled KPI use, and local query prototypes over the
bounded C-001/CT-1 population. It is not sufficient for a credible DCF,
three-statement model, enterprise forecast, statistical claim, or production
benchmark.

### S-R29 - One source snapshot binds every representation

Every S file binds the same R model digest and P-plus-Q package digest. A
changed upstream digest always creates a different handoff; there is no partial
refresh or mixed-snapshot package.

### S-R30 - Publication is atomic and non-overwriting

S builds in a unique same-parent staging directory, verifies the complete
staged package, closes all handles, and atomically renames to a previously
absent final directory. Failure removes staging and never alters an existing
handoff.

### S-R31 - Paths are package-relative and firewalled

Every declared file path is POSIX-style, relative, normalized, non-empty, and
unique. Absolute paths, drive prefixes, `..`, empty segments, backslashes,
symlinks, hard links, FIFOs, sockets, devices, and paths outside the package
root reject the operation.

### S-R32 - Consumer work is independently governed

Every later React, Excel, or Power BI project must declare the S handoff digest
it consumes, its own calculations and display decisions, and its own
verification. Consumer output cannot silently flow back into P, Q, R, or S.

## 4. Exact first handoff package

```text
analytical-handoff/
|- README.md
|- handoff-manifest.json
|- limitations.json
|- source-model/
|  `- complete unchanged R LINEAGE@1 model directory
|- excel/
|  |- finance-assurance-data-pack.xlsx
|  `- noncanonical-workbook.json
|- metadata/
|  |- source-model.json
|  |- data-dictionary.json
|  |- relationships.json
|  |- measures.json
|  |- field-roles.json
|  |- lineage.json
|  |- consumer-suitability.json
|  `- validation-checks.json
|- examples/
|  |- starter-queries.sql
|  `- reconciliation-queries.sql
|- checksums.json
`- handoff.digest
```

The R directory is copied without renaming any child. Its exact internal file
inventory is governed by the verified R manifest and R-C02, not duplicated in
this contract. S adds no `react/`, `powerbi/`, `models/`, `dashboards/`, or
`reports/` path.

## 5. Closed file and digest contract

### 5.1 Canonical S scope

The canonical S checksum ledger contains, in lexical path order:

1. `README.md`;
2. `handoff-manifest.json`;
3. `limitations.json`;
4. all eight `metadata/*.json` files;
5. both `examples/*.sql` files;
6. every path listed by the embedded R manifest's
   `canonical_digest_scope`, prefixed with `source-model/`;
7. `source-model/checksums.json`; and
8. `source-model/model.digest`.

No other path may enter `checksums.json`. Each ledger entry is exactly
`{path, sha256, byte_count}`. Paths are lexical ascending, unique, and closed
before payload writing. The ledger contract version is
`handoff-checksum-ledger@v1`.

### 5.2 Noncanonical S scope

The allowed noncanonical paths are exactly:

1. the R DuckDB path declared by the embedded R manifest;
2. the R `noncanonical_cache_manifest_path`;
3. `excel/finance-assurance-data-pack.xlsx`; and
4. `excel/noncanonical-workbook.json`.

The first two are prefixed with `source-model/`. They remain wholly R-owned.
The workbook manifest uses `NoncanonicalWorkbookManifest@v1` and contains:

```text
contract_version
handoff_ref
source_model_ref
source_model_digest
source_package_digest
workbook_path
workbook_sha256
workbook_byte_count
writer_profile_ref
writer_profile_hash
logical_workbook_digest
sheet_entries[]
openxml_part_inventory[]
render_profile_ref
render_evidence_digest
```

Each sheet entry contains the source dataset coordinate or metadata-sheet ID,
sheet name, table name where applicable, ordered columns, typed-row digest, row
count, column count, null counts, and storage modes. The manifest itself is
excluded from the canonical ledger because it contains the workbook's
same-build binary hash.

### 5.3 Closed physical inventory

The actual file inventory must equal the disjoint union of:

- the canonical ledger paths;
- `checksums.json` and `handoff.digest`; and
- the four allowed noncanonical paths.

Missing, extra, duplicated, unregistered, or wrong-kind paths reject S-C01 and
S-C02. The S manifest records both path sets and their expected counts, but not
the detached handoff digest.

### 5.4 Three verification claims

```text
CANONICAL_BYTE_EQUIVALENCE
  checksums.json entries and handoff.digest reproduce exactly

SAME_BUILD_BINARY_INTEGRITY
  R DuckDB and S XLSX match their noncanonical-manifest SHA-256 values

LOGICAL_REPRODUCTION
  reproduced DuckDB and XLSX typed logical digests match their source contracts
```

No operation may report one claim under the name of another.

## 6. Format contracts

### 6.1 CSV and Parquet

CSV and Parquet are consumed only from `source-model/`. S performs no schema
inference, rewrite, repartition, rename, recompression, or second checksum.
Source columns, R technical projections, types, order, and logical digests are
read from the R manifest and semantic catalogue.

CSV carries the R source columns defined for canonical CSV. Parquet carries
typed source columns plus applicable R technical projections. A consumer that
requires the technical projections must use Parquet or the R-owned DuckDB, not
infer that CSV physically contains them.

### 6.2 DuckDB

The embedded DuckDB is exactly the R3 output. It contains the R-declared P and Q
schemas plus `model_meta`, is loaded from R Parquet, and is covered by R's
noncanonical cache manifest. S-C01 checks it only by invoking R-C02 and copying
the verified model directory. S-C02 invokes R-C02 again. S-C03 delegates its
reproduction to R-C03 and compares the R logical cache contract.

S defines no SQL that writes the database and no alternative database schema.

### 6.3 `XlsxTypeMap@v1`

XLSX is projected from verified R Parquet in exact R table and `row_key ASC`
order. Source columns appear first in R order; R technical columns follow in R
order. A preflight scan chooses one storage mode per column before any cell is
written:

| R logical type | XLSX storage mode | Cell representation |
|---|---|---|
| `text`, `hash`, `enum` | `TEXT_EXACT` | explicit text cell |
| `date` | `TEXT_DATE_ISO` | exact `YYYY-MM-DD` text |
| `timestamp` | `TEXT_TIMESTAMP_UTC` | canonical UTC ISO-8601 text with microseconds and `Z` |
| `boolean` | `BOOLEAN_NATIVE` | Open XML Boolean `0` or `1` |
| `integer` | `NUMBER_EXACT` | numeric only if every non-null value has at most 15 significant decimal digits |
| `integer` | `TEXT_INT64` | canonical signed base-10 text otherwise |
| null of any type | `ABSENT_CELL` | cell element absent; never empty text |

`NUMBER_EXACT` is rejected if any value is outside Excel's exact 15-digit
decimal precision. Mixed numeric/text storage inside one logical integer column
is forbidden. The selected mode is recorded per column in the workbook
manifest and the `DATA_DICTIONARY` sheet. Verifiers reconstruct typed values
from the recorded mode and compare them to R Parquet; display formatting is not
accepted as evidence of type fidelity.

The mapping never writes Excel serial dates, locale-formatted timestamps,
floating money, error cells, or formula results.

### 6.4 `XlsxWriterProfile@v1`

Before S1, one exact writer profile fixes and hashes:

```text
profile_id and version
implementation and exact implementation version
Open XML conformance and workbook calculation mode
ZIP entry order, compression method, and timestamp policy
string storage policy
date system
default font, sizes, styles, widths, panes, filters, and table style
document-property policy
formula, macro, connection, external-link, query, and Data Model prohibition
renderer implementation and exact version
profile_hash
```

The profile is an executable dependency lock, not prose. Changing a
byte-affecting or logical setting requires a new writer profile. XLSX bytes are
still noncanonical; the lock provides bounded production and same-build
verification.

### 6.5 Workbook layout, names, and capacity

The workbook contains exactly:

| Sheet class | Content |
|---|---|
| `README` | synthetic notice, source refs/digests, limitations, navigation |
| `DATA_DICTIONARY` | exact S dictionary projection and XLSX storage modes |
| `RELATIONSHIPS` | exact R relationship projection |
| `MEASURES` | measure specifications only; no formulas |
| `VALIDATION_RESULTS` | static expected and observed registry results |
| one sheet per R table | exact data-only typed projection |

Source-table worksheet names derive from the R physical alias after removing
the leading `r_`, replacing invalid Excel characters with `_`, and truncating
to 24 characters. If truncation or normalization collides, append `_` plus the
first six lowercase hex characters of the registry-qualified identity hash
after truncating the base to 24 characters. Final names must be case-insensitive
unique and at most 31 characters.

Excel table names use `t_` plus the same normalized alias, allow only letters,
digits, and underscores, must start with a letter or underscore, and append the
same identity suffix on collision. The workbook manifest records every source
coordinate, worksheet name, and table name.

Before writing, S rejects any table exceeding 1,048,575 data rows or the
workbook's fixed column capacity after the header, any total worksheet count
beyond the pinned writer's tested limit, or any string beyond Excel's cell
character limit. S never splits a governed table across sheets.

### 6.6 Workbook prohibitions and inspection

The governed workbook contains no formulas, defined-name formulas, macros,
external links, data connections, Power Query, pivot cache, chart, image,
embedded object, threaded comment, scenario, what-if table, or Data Model.
Open XML verification inspects content types, relationships, workbook parts,
worksheet cells, formulas, calc chain, external-link parts, connections,
custom XML, VBA, embeddings, and model-related extensions.

Every sheet is rendered under the pinned renderer profile after build. Render
evidence binds `logical_workbook_digest`, sheet name, page count, render-image
hashes, and renderer coordinates. Publication requires structural inspection,
typed logical parity, and revision-bound visual review of every sheet. Render
images remain audit evidence outside the portable handoff; their canonical
summary digest is stored in the S manifest and the workbook manifest.
