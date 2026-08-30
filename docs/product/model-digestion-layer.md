# Artifact R - Model Digestion Layer and Consumer Dataset Contract

Status: Design v0.2 ratified - Phases R1 and R2 implemented and audited 2026-08-13

Resolution basis: all eight blocking findings and seven non-blocking findings
in `docs/roadmap/milestone-4-artifact-r-v01-critique.md` are incorporated
below.

## 0. Purpose and Closure Rule

Artifact R defines how one verified `P-EVIDENCE@v1` plus
`Q-ANALYTICS@v1` package becomes a shared, local, consumer-ready analytical
model for React, Excel, Power BI, and direct SQL exploration.

Artifacts P and Q already decide which values, evidence, keys, and
relationships may leave the governed runtime. Artifact R does not request more
runtime data and does not create a third truth boundary. It defines a finite
offline projection over those thirty-seven ratified datasets so that every
consumer receives the same typed tables, relationship graph, snapshot
coordinates, and semantic labels.

Artifact R closes only when:

1. one successfully verified P-plus-Q package is the sole domain input;
2. all thirty-seven source datasets receive one explicit consumption class;
3. consumer-facing, lineage, and diagnostic profiles are finite and cumulative;
4. CSV, Parquet, semantic metadata, and optional DuckDB materializations have
   distinct and honest roles;
5. domain values remain separate from R-owned transport and model metadata;
6. every emitted row remains traceable to an exact registry-qualified P/Q row;
7. Excel, Power BI, React, and SQL share one executable relationship plan and
   cannot present a competing relationship or calculation as governed;
8. C-001 and CT-1 remain correct at their current bounded depth; and
9. no consumer implementation begins until this artifact is independently
   critiqued and ratified.

## 1. Binding Sources

Artifact R is constrained by:

- the five repository invariants in `AGENTS.md`;
- Artifact N v0.2.1, exact-original persisted compatibility;
- Artifact O v0.2, public product and flagship journey contracts;
- Artifact P v0.2, package, evidence, checksum, and registry contracts;
- Artifact Q v0.2, analytical reads, ledger semantics, and relationship v2;
- ADR-035 through ADR-037;
- the implemented `P-EVIDENCE@v1` and `Q-ANALYTICS@v1` registries;
- the passed post-evidence and post-analytical-registry cohesion audits;
- C-001, the hard-close restatement reference transaction; and
- CT-1, the open-period reversal and replacement reference transaction.

Artifact R may classify, copy, type-preserve, and physically materialize the
ratified datasets. It may not weaken an upstream ownership, snapshot,
compatibility, readiness, evidence, correction, or trace-direction rule.

## 2. Product Outcome

The local analytical path becomes:

```text
ordinary runtime authority
-> one pinned P-plus-Q governed package
-> offline P-C02 verification
-> Artifact R model plan
-> deterministic consumer materialization
   |- canonical CSV source copies
   |- typed Parquet projections
   |- shared semantic metadata
   `- optional rebuildable DuckDB
-> Excel / Power BI / React / SQL adapters
```

Artifact R is the last shared boundary before presentation-specific products.
It ensures that a workbook, a BI report, and an analytical web page can differ
in interaction and presentation without disagreeing about source rows,
relationships, money, readiness, or evidence.

## 3. Vocabulary

### 3.1 Model digestion layer

A deterministic, read-only, offline projection of one verified P-plus-Q
package into consumer-efficient physical formats. It owns neither business nor
accounting truth.

### 3.2 Source dataset

One registry-qualified Artifact P or Q dataset, identified by
`(registry_id, registry_version, dataset_id, dataset_version)`.

### 3.3 Model profile

A closed, cumulative selection of source datasets and relationships for one
bounded class of consumption. Profiles select existing source datasets; they
do not define replacement marts.

### 3.4 Consumer-facing dataset

A source dataset admitted to the `CORE` profile because its grain directly
supports a ratified product, accounting, assurance, governance, or planning
journey.

### 3.5 Lineage dataset

A source dataset admitted to the `LINEAGE` profile because it supports exact
evidence, provenance, reference, or trace navigation without becoming a
business fact.

### 3.6 Diagnostic dataset

A source dataset admitted only to the `DIAGNOSTIC` profile because it explains
query execution, source closure, package structure, or discovery state.

### 3.7 Domain value

A P/Q value owned by a platform module or the shared substrate. Artifact R may
copy it and apply its declared physical type but may not reinterpret it.

### 3.8 Model metadata

R-owned information about materialization, profile membership, physical type,
relationship loading, measure classification, source binding, or build status.
It cannot be stored as if it were a domain column.

### 3.9 Column role

One exact R classification applied to every source or R-added column:

```text
DOMAIN_KEY
DOMAIN_ATTRIBUTE
DOMAIN_MEASURE_INPUT
EVIDENCE_ATTRIBUTE
SOURCE_TECHNICAL
R_TECHNICAL
```

Column role is separate from `VISIBLE`, `HIDDEN`, or `NOT_LOADED` consumer
disposition. Artifact R retains the exact P/Q `value_origin` and
`transformation` beside its own role.

### 3.10 Governed measure

A measure that exposes an exact governed source value or an additive total of
exact rows at the same declared grain. Its definition and source field are
registered by R.

### 3.11 Consumer calculation

A labelled, non-authoritative formula calculated by a downstream tool. It may
format, aggregate, compare, or ratio governed values but cannot replace a P/Q
conclusion.

## 4. Binding Rulings

### R-R01 - Artifact R is a projection, not an authority

R consumes a verified package and emits rebuildable consumer artifacts. No R
file may become an authoritative source for the runtime, Artifact O, Artifact
P, or Artifact Q.

### R-R02 - One build consumes one immutable package snapshot

Every R build binds the exact source package digest, export reference, query
revision, semantic-as-of time, scenario-set digest, compatibility mode,
registry versions, and relationship-contract version before reading a data
file. Values from two package snapshots may not be combined.

### R-R03 - Verification precedes deserialization

The R builder must obtain `VERIFIED` from Artifact P's offline verifier for the
complete P-plus-Q package before it parses a source CSV. A checksum pass alone
is insufficient. Verification failure emits no final R model.

### R-R04 - The source registry remains closed

Artifact R version 1 consumes exactly `P-EVIDENCE@v1` and
`Q-ANALYTICS@v1`. It cannot add a governed dataset, governed field, domain row,
relationship meaning, or semantic source not present in those registries. The
only added row-level fields are the eight finite hidden `R_TECHNICAL`
relationship-key projections defined in section 7.5.

### R-R05 - Dataset identity is preserved

Every physical table retains the source registry and dataset coordinate in its
model catalogue. Friendly names are aliases only. They never replace
registry-qualified identity.

### R-R06 - No replacement mart may duplicate a governed fact

R v1 does not author separate `dim_*`, `fct_*`, or aggregate tables. The
ratified P/Q datasets already provide the finite business and analytical
grains. A later derived mart requires a contract revision defining its exact
grain, source rows, formula, reconciliation, and non-authoritative status.

### R-R07 - Profiles are cumulative and finite

The profiles are:

```text
CORE       = the 26 consumer-facing datasets
LINEAGE    = CORE plus 5 lineage datasets
DIAGNOSTIC = LINEAGE plus 6 diagnostic datasets
```

Consumers import one whole profile. A consumer may hide an admitted table from
navigation but cannot silently replace the profile with an undeclared subset
or import a diagnostic table without its lower profiles. `CORE plus selected
LINEAGE tables` is not a valid profile.

### R-R08 - Every dataset has one primary consumption class

Each of the thirty-seven P/Q datasets is classified exactly once as
`CORE`, `LINEAGE`, or `DIAGNOSTIC`. Classification says how the table may be
consumed; it does not alter semantic ownership.

### R-R09 - Canonical CSV remains the portable source copy

Artifact P's verified UTF-8 CSV files remain the canonical tabular bytes.
Artifact R copies them byte-for-byte only when a self-contained model bundle
requests `CSV`. R does not rewrite CSV headers, null tokens, integers, dates,
timestamps, or row ordering.

### R-R10 - Parquet is the typed analytical projection

R emits one Parquet file per selected dataset when `PARQUET` is requested.
Columns follow the exact P/Q schema order and R's physical type map. The
Parquet row order equals canonical CSV row order. Parquet is rebuildable and is
never evidence of a value absent from the source CSV.

### R-R11 - DuckDB is optional acceleration

When `DUCKDB` is requested, R creates one local database containing one schema
per source registry and read-only analytical views. It is an ephemeral
consumer cache. It may be deleted and rebuilt from the same verified package
without semantic loss, and it may never be read by the authoritative runtime.

### R-R12 - Semantic metadata is tool-neutral

R emits one tool-neutral semantic catalogue describing table identity, column
types and roles, relationship load rules, measures, display labels, hidden
fields, source value origins and transformations, R column roles, default
ordering, and profile membership. Excel, Power BI, and React adapters translate
this catalogue; none owns a competing semantic definition.

### R-R13 - Domain values and model metadata stay separate

R may not append export path, worksheet, Power BI, React route, display format,
profile, refresh, or model-build fields to a domain dataset. Such values belong
only in R manifests, table bindings, semantic metadata, build reports, or
reserved hidden R technical-key projections. Every R-added column uses an
`_r_` prefix and role `R_TECHNICAL`; it can never become a governed source
field or business identifier.

### R-R14 - Money remains integer minor units

Every source amount remains a signed or non-negative 64-bit integer as allowed
by its P/Q schema and retains its exact ISO-4217 currency column. Major-unit
display values are consumer calculations and are never persisted as governed
facts by R v1.

### R-R15 - Dates and timestamps remain semantically distinct

Schema type `date` becomes a date logical type. Schema type `timestamp`
becomes a UTC timestamp with microsecond precision. Text identifiers that look
like periods or dates remain text unless P/Q typed them otherwise.

Source type `enum` remains a UTF-8 physical string paired with the exact P/Q
`enum_values[]`. Artifact R cannot strengthen a Q `text` discriminator into an
enum merely because the current canonical rows use a finite observed set.

### R-R16 - Empty, null, and absent remain distinct

An empty canonical CSV field on a nullable column becomes a physical null. An
empty field on a required column is invalid. Non-null empty text is prohibited
by Artifact P's canonical CSV contract. An absent field is a contract failure.
R may not coalesce, default, or fill null domain values to satisfy a consumer.

### R-R17 - Relationships are imported, not inferred

Only Artifact Q relationship contract v2 entries classified
`CONSUMER_RELATIONSHIP` may become model relationships. `INTEGRITY_ONLY` and
`POLYMORPHIC_PARENT` relations remain validation or lineage metadata. Matching
field names do not create a relationship.

### R-R18 - Relationship adaptation is explicit

Artifact R owns one finite relationship-key projection and activation plan.
Every composite `CONSUMER_RELATIONSHIP` receives a deterministic hidden
technical key. Every relationship relevant to a selected profile receives
exactly one disposition:

```text
ACTIVE
INACTIVE_ROLE_PLAYING
NAVIGATION_ONLY
VALIDATION_ONLY
```

Adapters may not invent keys, activate another path, use bidirectional
filtering, or weaken cardinality. Polymorphic and `INTEGRITY_ONLY`
relationships are always `VALIDATION_ONLY`.

### R-R19 - Readiness travels with controlled use

Any reporting value or planning input presented as usable for a purpose must
retain the exact relationship to P-D10 readiness, P-D20 limitations, and P-D15
references. A posted journal, balanced entry, verified hash, or populated field
never implies readiness.

### R-R20 - Reporting history remains simultaneous

P-D05, P-D06, and P-D07 retain as-was and as-restated versions as separate
rows. R must not overwrite, flatten to a latest-only table, or calculate the
restatement bridge as a substitute for P-D07.

### R-R21 - Authored and referenced journals remain separate

Q-D04/Q-D05 and Q-D08/Q-D09 remain separate tables and semantic classes.
J-010 cannot be unioned into the authored journal fact or acquire authored
status for model convenience.

### R-R22 - Trace direction and evidence status remain exact

P-D16/P-D17 edges preserve direction. P-D15 and Q-D12 evidence bindings retain
`CONTENT_BYTES_VERIFIED` versus `DECLARED_HASH_ONLY` exactly. R may provide
navigation but cannot strengthen either claim.

### R-R23 - Measures have a closed classification

Every registered measure is exactly one of:

```text
EXACT_VALUE
ADDITIVE_GOVERNED_TOTAL
CONSUMER_CALCULATION
```

An `EXACT_VALUE` selects one exact source field at its registered grain. An
`ADDITIVE_GOVERNED_TOTAL` may sum a registered integer-minor field only where
the measure contract declares the grouping and avoids double counting.
Everything else is a `CONSUMER_CALCULATION` and must be visibly labelled.

Every raw integer column has default summarization `NONE`, including amount,
count, ordinal, version, and revision fields. A consumer may aggregate a raw
integer only through a registered measure. Exact-value measures require one
exact source row in filter context; otherwise they return blank or an explicit
multi-row error as declared by the consumer adapter.

### R-R24 - Consumer aliases are presentational only

Friendly table names, worksheet names, display folders, and React route labels
may vary by adapter. R defines one portable physical alias by prefixing `r_`,
lowercasing the registered dataset name, replacing every non-alphanumeric run
with one underscore, and trimming trailing underscores. A result longer than
63 characters appends the first twelve hex characters of the registry-
qualified identity hash after deterministic truncation to 50 characters. Any
remaining collision rejects the model. Consumer display aliases may differ,
but the semantic catalogue retains the physical alias, source dataset ID, and
column name so an alias can never obscure provenance.

### R-R25 - The model is local, deterministic, and free to run

The baseline requires no paid API, credential, cloud warehouse, online BI
service, identity provider, LLM, or runtime network access. Optional Power BI
Desktop use does not make Power BI Service a dependency.

### R-R26 - Canonical depth remains disclosed

Every R model and later consumer states that v1 contains the bounded C-001 and
CT-1 reference cases. Physical efficiency and semantic breadth do not imply
enterprise data volume or statistical coverage.

### R-R27 - Build publication is atomic

R builds into a unique staging directory, verifies all emitted files and
relationships, then atomically publishes a previously absent final directory.
Overwrite is rejected. Failure removes staging and leaves no partial final
model.

### R-R28 - Reproduction is digest-exact

Rebuilding from the exact source package digest, R contract version, profile,
format set, producer release, caller-supplied build time, and exact Parquet
writer profile must reproduce the same canonical R manifest, semantic
catalogue, CSV/Parquet bytes, checksums, and detached model digest.

DuckDB is excluded from the canonical model digest and byte-equivalence claim.
It is checksummed for same-build tamper detection and must reproduce logical
table equality from the canonical Parquet files under its declared engine and
storage-compatibility versions.

## 5. Consumption Profiles

### 5.1 `CORE@v1`

`CORE` is the minimum governed business-analysis profile for Excel, Power BI,
and analytical React pages. It contains the twenty-six datasets whose rows
support the five module lenses, governed values, and module summaries. It does
not by itself reproduce the complete directed trace or evidence journey.

| Class | Dataset | Consumer role |
|---|---|---|
| Context | P-D01 `package_context` | Snapshot, synthetic notice, and product context |
| Context | P-D02 `scenarios` | Scenario selection and disclosure |
| Context | P-D03 `module_lenses` | Five-lens navigation |
| Hermes | P-D04 `source_reconciliations` | Completeness and identity reconciliation |
| Atlas | P-D05 `reporting_versions` | Reporting history and publication identity |
| Atlas | P-D06 `reporting_values` | Exact statement values |
| Atlas | P-D07 `restatement_bridges` | Exact as-was to as-restated adjustment |
| Argus | P-D08 `assurance_exceptions` | Machine observations and assertions |
| Aegis | P-D09 `governance_cases` | Review, finding, issue, remediation, verification |
| Aegis | P-D10 `readiness_assessments` | Purpose-specific reliance status |
| Pythia | P-D11 `governed_decisions` | Governed planning decision and approval |
| Pythia | P-D12 `decision_inputs` | Frozen decision input membership |
| Atlas/Aegis | P-D13 `correction_cases` | Correction-integrity conclusion |
| Atlas | P-D14 `correction_journals` | Correction journal totals and balance |
| Shared substrate | P-D15 `reference_bindings` | Required readiness and exact parent-reference binding |
| Aegis | P-D20 `readiness_limitations` | Exact limitations by readiness assessment |
| Atlas | Q-D01 `accounts` | Account semantics |
| Atlas | Q-D02 `statement_lines` | Statement semantics and display order |
| Atlas | Q-D03 `account_statement_mappings` | Governed account-to-statement mapping |
| Atlas | Q-D15 `ledger_semantics_catalogues` | Required catalogue version and evidence basis |
| Atlas | Q-D04 `journal_headers` | Authored journal grain |
| Atlas | Q-D05 `journal_lines` | Immutable authored journal-line grain |
| Source domain | Q-D07 `business_events` | Causal business-event context |
| Atlas read boundary | Q-D08 `referenced_journals` | Referenced pre-scope journal identity |
| Atlas read boundary | Q-D09 `referenced_journal_lines` | Referenced pre-scope journal lines |
| Atlas | Q-D10 `accounting_periods` | Exact period state and close basis |

### 5.2 `LINEAGE@v1`

`LINEAGE` contains all `CORE` datasets plus these five datasets:

| Dataset | Consumer role |
|---|---|
| P-D16 `trace_nodes` | Directed reporting-value trace nodes |
| P-D17 `trace_edges` | Directed reporting-value trace edges |
| Q-D06 `journal_input_hashes` | Ordered journal derivation inputs |
| Q-D11 `posting_rules` | Exact posting-rule and content basis |
| Q-D12 `analytical_evidence_bindings` | Exact Q evidence and verification status |

`LINEAGE` is the default for an audit workpaper export, a trace explorer, and a
portfolio evidence walkthrough. It is the minimum profile for the complete
C-001 and CT-1 proofs in sections 11 and 12. It is not required for ordinary
summary pages.

### 5.3 `DIAGNOSTIC@v1`

`DIAGNOSTIC` contains all `LINEAGE` datasets plus these six datasets:

| Dataset | Diagnostic role |
|---|---|
| P-D18 `query_executions` | Public query execution coordinates |
| P-D19 `query_sources` | Public invocation-local source closure |
| P-D21 `scenario_entry_points` | Journey discovery and availability |
| Q-D13 `analytical_query_executions` | Analytical query execution coordinates |
| Q-D14 `analytical_query_sources` | Analytical invocation-local source closure |
| Q-D16 `analytical_context` | Multi-registry discovery and snapshot binding |

`DIAGNOSTIC` is intended for developer inspection, reproducibility, and model
debugging. It is excluded from the default business-facing field list.

### 5.4 Classification proof

The profile registry must prove exact set equality:

```text
CORE primary class        = 26 datasets
LINEAGE primary class     = 5 datasets
DIAGNOSTIC primary class  = 6 datasets
total                     = 37 datasets
```

No dataset may be unclassified or multiply classified.

## 6. Physical Materialization Contract

### 6.1 Source package remains unchanged

Artifact R never writes into the governed package. Its output is a sibling
directory bound to the source package by digest.

```text
build/model-digestion/<model_ref>/
|- model-manifest.json
|- semantic-model.json
|- relationships.json
|- checksums.json
|- model.digest
|- README.txt
|- noncanonical-cache.json      # only when DUCKDB is requested
|- csv/                         # optional byte-identical source copies
|  |- p-evidence-v1/
|  `- q-analytics-v1/
|- schemas/                     # byte-identical selected source schemas
|  |- p-evidence-v1/
|  `- q-analytics-v1/
|- parquet/
|  |- p-evidence-v1/
|  `- q-analytics-v1/
`- warehouse/                   # optional, non-canonical
   `- finance-assurance.duckdb
```

Only the formats requested by the closed build request appear. Unknown files
reject offline verification.

### 6.2 Physical type map

| P/Q schema type | Parquet logical type | DuckDB type | Consumer requirement |
|---|---|---|---|
| `text` | UTF-8 string | `VARCHAR` | Exact text |
| `enum` | UTF-8 string | `VARCHAR` | Exact source `enum_values[]` |
| `integer` | signed 64-bit integer | `BIGINT` | No float conversion |
| `boolean` | boolean | `BOOLEAN` | Exact boolean |
| `date` | date32 | `DATE` | No timezone |
| `timestamp` | timestamp microseconds, UTC | `TIMESTAMPTZ` | Preserve instant |
| `hash` | UTF-8 string | `VARCHAR` | Retain complete `sha256:` value |

R rejects an integer that does not fit signed 64-bit storage. A later need for
larger monetary values requires a physical-contract revision, not silent
decimal or float promotion.

Only a source column typed `enum` receives enum enforcement. An observed finite
set in a source `text` column remains text. The exact enum set participates in
the physical-schema fingerprint and is checked during build and verification.

### 6.3 CSV materialization

`CSV` copies the selected canonical source files without modification. Every
R model, including a model that does not request `CSV`, copies the selected
source schema files byte-for-byte into `schemas/`. Their bytes remain governed-
package bytes; the R manifest stores both the original P/Q checksum and the R
bundle checksum.

### 6.4 Parquet materialization

Each selected source dataset produces exactly one Parquet file. R records:

- source registry and dataset coordinates;
- source CSV and schema hashes;
- Parquet path and hash;
- physical schema fingerprint;
- logical table digest over canonical typed rows;
- row count;
- exact `row_key ASC` physical row order; and
- profile membership.

Parquet file metadata may contain the R contract version and source coordinate.
It may not contain a second copy of domain values or an inferred domain label.
Source columns appear first in exact P/Q schema order. Applicable `_r_hk_*`
columns follow in lexical relationship-ID order. Logical source-table digests
cover source columns only; a separate technical-projection digest covers the
ordered key columns and their preimages.

### 6.5 Parquet writer profile

`ParquetWriterProfile@v1` fixes every byte-affecting setting:

```text
profile_id
profile_version
implementation
implementation_version
compression_codec
compression_level
row_group_size
dictionary_encoding
statistics_mode
data_page_version
timestamp_unit
timestamp_timezone
schema_metadata_policy
writer_version
profile_hash
```

Artifact R v0.2 fixes `timestamp_unit = MICROSECOND` and
`timestamp_timezone = UTC`. The exact library, version, and remaining values
are selected and dependency-locked during Phase R1 before any canonical
Parquet fixture is accepted. A writer-profile change requires an R contract
revision or a separately versioned writer profile; `producer_release` alone is
not a writer contract.

Phase R1 selects this exact profile:

```text
profile_id             PYARROW-25@v1
implementation         PYARROW
implementation_version 25.0.0
compression_codec      ZSTD
compression_level      3
row_group_size          65536
dictionary_encoding    true
statistics_mode        ALL
data_page_version       1.0
timestamp_unit          MICROSECOND
timestamp_timezone      UTC
schema_metadata_policy  R_CONTRACT_AND_SOURCE_COORDINATE_ONLY
writer_version          finance-assurance-pyarrow-writer@v1
profile_hash            sha256:2702aa8812844e508d5b303c50b52e30ab9f20cf7b65c42c2d59f39171b85cb1
writer_options_hash     sha256:2642b3ea3f71badfff44760005b01ed1f80f9a571d823dc99fa6ef78f432b862
```

The profile hash includes the complete writer-options hash in its preimage.
The dependency is exact in `pyproject.toml` and `uv.lock`. Phase R1 validates
the installed version and writer signature but emits no Parquet bytes.

### 6.6 DuckDB materialization

The optional R3 database contains exactly:

```text
schema p_evidence_v1
schema q_analytics_v1
schema model_meta
```

P/Q tables keep the same stable `r_*` aliases as the semantic catalogue.
`model_meta` contains exactly `cache_profile`, `documents`, and
`table_bindings`. The three canonical JSON documents embedded by value are the
model manifest, relationship catalogue, and semantic catalogue; no source
domain row is duplicated there. Database tables are loaded from the emitted
Parquet files, not independently from the source CSVs.

No mutable application table, command path, macro with domain logic, or hidden
latest-view is permitted.

R3 fixes DuckDB `1.5.5`, requested
`storage_compatibility_version = v1.5.0`, and observed database storage tag
`v1.5.0+`. `NoncanonicalCacheManifest@v1` records those coordinates, the
database path, byte count and checksum, exact schema and object inventory,
Parquet bindings, row counts, column order, and logical and technical digests.
The builder closes every connection and rejects a retained WAL before
same-build verification. R-C02 reopens the database read-only and checks exact
schema, table, view, and macro closure plus bidirectional DuckDB-to-Parquet set
equality. A write invalidates its cache checksum; the cache must then be
rebuilt or reverified. Neither the DuckDB file nor its cache manifest enters
the detached canonical model digest.

## 7. Model Manifest and Catalogue

### 7.1 `ModelManifest@v1`

The manifest contains exactly:

```text
contract_version
model_ref
source_package_ref
source_package_digest
source_export_ref
source_query_revision
source_semantic_as_of
source_scenario_set_digest
source_compatibility_mode
source_registry_coordinates[]
source_relationship_contract_version
source_verification_status
source_verification_contract
profile_id
profile_version
requested_formats[]
producer_release
built_at
parquet_writer_profile_ref?
parquet_writer_profile_hash?
synthetic_data
synthetic_data_notice
table_entries[]
semantic_catalogue_path
relationship_catalogue_path
checksum_ledger_path
canonical_digest_scope[]
noncanonical_cache_manifest_path?
```

`built_at` is caller-supplied and participates in reproducibility coordinates;
the builder may not read the wall clock.

`checksums.json`, `model.digest`, and `canonical_digest_scope[]` exclude the
DuckDB file and `noncanonical-cache.json`. The canonical manifest may name the
stable cache-manifest path and requested DUCKDB format, but it cannot contain a
DuckDB file hash. `noncanonical-cache.json` owns the engine version, storage-
compatibility version, file checksum, and logical table digests and is verified
separately.

### 7.2 `ModelTableBinding@v1`

Each table entry contains:

```text
source_registry_id
source_registry_version
source_dataset_id
source_dataset_version
source_dataset_name
primary_consumption_class
included_by_profile
semantic_owners[]
source_schema_path
source_schema_hash
source_data_hash
row_count
primary_key[]
unique_keys[][]
default_sort[]
logical_table_digest
technical_projection_digest
relationship_key_projections[]
csv_path?
csv_hash?
parquet_path?
parquet_hash?
physical_schema_fingerprint?
duckdb_schema?
duckdb_object?
```

The binding contains model metadata only. Source columns stay in the dataset
file and are not repeated here. `logical_table_digest` is SHA-256 over Artifact
P canonical JSON bytes for the array of source-column row objects ordered by
`row_key ASC`. `technical_projection_digest` uses the same construction for an
array containing `row_key` plus applicable `_r_hk_*` fields in lexical
relationship-ID order. Both are independent of Parquet or DuckDB bytes.

### 7.3 `SemanticCatalogue@v1`

The catalogue contains:

```text
catalogue_contract_version
model_ref
profile_coordinate
source_package_digest
tables[]
relationships[]
measures[]
format_hints[]
consumer_capabilities[]
```

Each table retains its source coordinate. Each column retains source name,
source type, physical type, nullability, exact enum set, P/Q `value_origin`,
P/Q `transformation`, R column role, default visibility, default
summarization, display label, and optional display folder. The catalogue cannot
override a P/Q type, enum, owner, key, or relationship.

### 7.4 Column-role registry

`ColumnRoleRegistry@v1` covers all 427 source columns plus the finite R-added
relationship keys. Classification is deterministic in this priority order:

1. an R-added `_r_*` column is `R_TECHNICAL`;
2. every source `row_key` and every column in P-D18, P-D19, P-D21, Q-D13,
   Q-D14, or Q-D16 is `SOURCE_TECHNICAL`;
3. a hash, evidence reference, verification status, verification proof, or
   content-evidence coordinate is `EVIDENCE_ATTRIBUTE`;
4. an amount-minor or governed count field admitted by the measure registry is
   `DOMAIN_MEASURE_INPUT`;
5. a field participating in an exact business-facing natural key or
   or `CONSUMER_RELATIONSHIP` endpoint is `DOMAIN_KEY`;
6. a remaining field whose exact upstream origin is
   `P_TRANSPORT_METADATA`, `P_STRUCTURAL_METADATA`, `O_QUERY_FIELD`,
   `O_ENVELOPE_FIELD`, or `PACKAGE_STRUCTURAL_METADATA` is
   `SOURCE_TECHNICAL`; and
7. every remaining governed source field is `DOMAIN_ATTRIBUTE`.

The registry has a finite override table for fields where a more specific
upstream meaning wins over a general naming rule. It is generated and committed
as semantic metadata. The builder rejects an unclassified or multiply
classified column. Source technical, evidence, R technical, ordinal, version,
revision, and raw numeric fields are hidden by default unless an exact consumer
artifact deliberately exposes them.

All source columns in an included dataset are present in R Parquet. The shared
v1 model therefore uses only `VISIBLE` or `HIDDEN`; `NOT_LOADED` is reserved for
a later consumer-specific contract and cannot be used to evade source parity.

### 7.5 Composite relationship-key projection

The eight composite consumer relationships are:

```text
P-RL02 P-RL03 P-RL04 P-RL05
P-RL06 P-RL07 P-RL08 P-RL10
```

Each receives one hidden R column named from its normalized identity, for
example `_r_hk_p_rl02`, on both endpoints. Parquet and DuckDB materialize those
columns. Byte-identical CSV cannot carry added columns, so a CSV consumer
adapter derives them during import from this same R-owned contract and proves
the resulting technical-projection digest before loading relationships. The key
is:

```text
sha256(canonical_json({
  "relationship_id": <exact relationship id>,
  "values": [
    {"type": <exact source type>, "value": <exact typed value>},
    ... in registered column order
  ]
}))
```

Canonical JSON uses Artifact P's exact UTF-8, lexical-key, no-float encoding,
including its terminating LF. A required null or absent component rejects the
projection. The verifier retains the original tuple and proves that one hash
never identifies two different tuples within either endpoint. A collision
rejects the model. The original governed columns remain unchanged.

These keys exist only to implement the exact upstream relationship in a
single-column consumer engine. They are `R_TECHNICAL`, hidden, and prohibited
from display, grouping, business lookup, or authoritative reference.

### 7.6 Relationship catalogue and activation plan

The R relationship catalogue copies every source relationship entry relevant
to the selected profile and adds:

```text
load_disposition
relationship_role
projected_key_ref?
cross_filter_direction
consumer_reason
```

The exact active set, when both endpoints exist in the selected profile, is:

```text
P-RL01-P-D03  P-RL01-P-D04  P-RL01-P-D05  P-RL01-P-D08
P-RL01-P-D09  P-RL01-P-D13  P-RL01-P-D15  P-RL01-P-D16
P-RL01-P-D17  P-RL01-P-D21  P-RL02          P-RL03
P-RL05         P-RL07         P-RL08          P-RL09
P-RL10         P-RL13

Q-RL03         Q-RL04         Q-RL05          Q-RL06
Q-RL07         Q-RL08         Q-RL09          Q-RL10
Q-RL11         Q-RL13         Q-RL14          Q-RL15
Q-RL24-Q-D04  Q-RL24-Q-D07  Q-RL24-Q-D08
```

`P-RL04` is `INACTIVE_ROLE_PLAYING` for the successor reporting-version role.
Every other upstream `CONSUMER_RELATIONSHIP` whose endpoints exist in the
profile is `NAVIGATION_ONLY`. Every `INTEGRITY_ONLY` or
`POLYMORPHIC_PARENT` entry is `VALIDATION_ONLY`. A relationship whose endpoint
is outside the selected profile is omitted rather than reclassified.

All active relationships retain upstream many-to-one cardinality and use
single filtering from the `to`/one side to the `from`/many side. Bidirectional
filtering is prohibited. R-C02 proves that the directed active-filter graph is
acyclic, exposes no two active paths between the same filter source and target,
and uses a projected key for every active composite relationship.

### 7.7 Measure registry

R v1 defines only these shared measures:

| Measure ID | Source | Class | Rule |
|---|---|---|---|
| R-M01 `reporting_value_minor` | P-D06 `amount_minor` | EXACT_VALUE | One source row, no aggregation |
| R-M02 `restatement_adjustment_minor` | P-D07 `adjustment_minor` | EXACT_VALUE | One bridge row, no recomputation |
| R-M03 `reconciliation_difference_minor` | P-D04 `difference_minor` | EXACT_VALUE | Nullable by reconciliation variant |
| R-M04 `exception_difference_minor` | P-D08 `difference_minor` | EXACT_VALUE | Nullable by exception variant |
| R-M05 `decision_monthly_cost_minor` | P-D11 `monthly_cost_minor` | EXACT_VALUE | One governed decision row |
| R-M06 `correction_net_movement_minor` | P-D13 `control_account_net_movement_minor` | EXACT_VALUE | One correction case row |
| R-M07 `journal_debits_minor` | Q-D04 `total_debit_minor` | EXACT_VALUE | One authored journal row |
| R-M08 `journal_credits_minor` | Q-D04 `total_credit_minor` | EXACT_VALUE | One authored journal row |
| R-M09 `journal_line_debits_minor` | Q-D05 `debit_minor` | ADDITIVE_GOVERNED_TOTAL | Sum by selected authored-line grain |
| R-M10 `journal_line_credits_minor` | Q-D05 `credit_minor` | ADDITIVE_GOVERNED_TOTAL | Sum by selected authored-line grain |
| R-M11 `referenced_line_debits_minor` | Q-D09 `debit_minor` | ADDITIVE_GOVERNED_TOTAL | Sum only referenced lines; never union with Q-D05 |
| R-M12 `referenced_line_credits_minor` | Q-D09 `credit_minor` | ADDITIVE_GOVERNED_TOTAL | Sum only referenced lines; never union with Q-D05 |

Each measure record contains:

```text
measure_id
source_registry_id
source_dataset_id
source_field
classification
aggregation
required_grain[]
required_grouping[]
currency_policy
reporting_version_policy
population_class
multirow_behavior
non_combinable_with[]
default_format
```

R-M01 through R-M08 use `SELECT_EXACT`, their source dataset's exact unique
business key as `required_grain`, `SINGLE_EXACT_CURRENCY`, and
`BLANK_OR_ERROR` when more than one source row remains in context. R-M01 also
requires one exact `reporting_version_ref`; R-M02 requires one exact
predecessor/successor pair. They are not summable.

R-M09 and R-M10 use `SUM`, population class `AUTHORED_JOURNAL_LINE`, and
required grouping at least by `scenario_ref` and `currency`. R-M11 and R-M12
use the same rules with population class `REFERENCED_JOURNAL_LINE`. Each
authored measure lists both referenced measures as non-combinable, and each
referenced measure lists both authored measures. Their display label includes
`gross activity`; none is labelled balance, revenue, expense, or statement
value.

Every one of the fifty raw P/Q integer columns has `default_summarization =
NONE`. Ordinals, versions, revisions, and display order are never measure
inputs. A future multi-currency aggregation requires a separately governed FX
basis and is outside R v1.

Major-unit display, signed debit-minus-credit values, ratios, exception counts,
trend comparisons, and KPIs remain labelled consumer calculations in v1.

## 8. Build, Verify, and Reproduce Operations

### R-C01 - `BuildConsumerModel`

Request:

```text
request_contract_version = build-consumer-model-request@v1
model_ref
source_package_path
expected_source_package_digest
profile_id = CORE | LINEAGE | DIAGNOSTIC
profile_version = 1
formats[] = CSV | PARQUET | DUCKDB
parquet_writer_profile_ref?
parquet_writer_profile_hash?
duckdb_storage_compatibility_version?
output_path
producer_release
built_at
```

Rules:

1. `formats[]` is non-empty, ordered canonically as CSV, PARQUET, DUCKDB, and
   has no duplicates.
2. DUCKDB requires PARQUET in the same request.
3. PARQUET requires one exact supported writer-profile reference and hash.
4. DUCKDB requires one exact storage-compatibility version.
5. P-C02 verifies the complete source package before any table is parsed.
6. The source package must contain exactly P and Q at version 1 and relationship
   contract v2.
7. The profile registry selects the exact datasets and relationships.
8. Source schemas drive strict parsing and physical typing.
9. All files are written to a unique staging directory under the final output
   parent so publication is one same-filesystem rename.
10. Every writer and DuckDB handle is closed and every temporary/WAL file is
    absent before R-C02 begins.
11. R-C02 verifies the staged model before atomic publication.
12. An existing final directory is never overwritten.

Result:

```text
result_contract_version = build-consumer-model-result@v1
model_ref
model_path
model_digest
source_package_digest
profile_id
profile_version
canonical_file_count
noncanonical_cache_file_count
table_count
source_row_count
technical_projection_count
```

### R-C02 - `VerifyConsumerModel`

Request:

```text
request_contract_version = verify-consumer-model-request@v1
model_path
source_package_path
expected_model_digest
expected_source_package_digest
verification_scope = FULL_SOURCE_EQUIVALENCE
```

`FULL_SOURCE_EQUIVALENCE` is the only v1 verification scope and returns:

```text
result_contract_version = verify-consumer-model-result@v1
status = VERIFIED | FAILED
model_digest?
source_package_digest?
checked_file_count
checked_table_count
checked_column_count
checked_relationship_count
message
```

Offline verification requires no runtime, source database, or network. The
exact P-plus-Q package is nevertheless mandatory because source equivalence
cannot be proven from an R package alone. R-C02 first reruns P-C02 and requires
`VERIFIED`, then verifies:

- detached model digest and checksum closure;
- exact file inventory;
- source package coordinate and package-digest binding;
- closed profile membership and dataset classification;
- all source and R-added column roles, visibility, and summarization settings;
- exact source-to-model row counts and source row keys;
- source CSV byte equality where CSV is emitted;
- selected source schema byte equality in every R model;
- exact physical types, column order, nulls, and row order in Parquet;
- exact enum sets and logical table digests;
- all eight composite-key preimages, endpoint equality, and collision absence;
- exact relationship disposition and the unambiguous active filter graph;
- DuckDB table-to-Parquet equality where DuckDB is emitted;
- table, relationship, measure, and format-hint catalogue closure;
- no consumer relationship absent from Artifact Q relationship v2;
- evidence and readiness relationship retention; and
- prominent synthetic-data disclosure.

Verification does not prove upstream domain correctness again. It proves exact
materialization from an already verified source package.

### R-C03 - `ReproduceConsumerModel`

Request:

```text
request_contract_version = reproduce-consumer-model-request@v1
source_model_path
source_package_path
reproduction_output_path
expected_model_digest
expected_source_package_digest
```

Reproduction recovers the exact R-C01 coordinates from the source model,
rebuilds through R-C01 using the exact source package digest, producer release,
caller-supplied `built_at`, and writer profile, and compares the detached model
digest and every canonical file byte. DuckDB is excluded from that byte
comparison and instead receives logical table-parity verification. Its
regenerated file is checked against its own regenerated noncanonical-cache
manifest for same-build tamper detection; original and reproduced DuckDB file
hashes are never compared.

Result:

```text
result_contract_version = reproduce-consumer-model-result@v1
status = REPRODUCED | DIGEST_MISMATCH | SOURCE_PACKAGE_UNAVAILABLE |
         WRITER_PROFILE_UNAVAILABLE | BUILD_FAILED
expected_model_digest
actual_model_digest?
source_package_digest?
message
```

R-C03 does not substitute a newer package or writer.

## 9. Consumer Adapter Boundary

### 9.1 Shared rule

Every consumer adapter must:

1. accept one R model that passes R-C02;
2. declare its supported R contract, profile, and physical formats;
3. import the exact registered tables, technical relationship keys, and
   relationship dispositions;
4. retain source coordinates in hidden technical metadata;
5. label every consumer-owned formula;
6. preserve synthetic-data and canonical-depth notices; and
7. remain disposable and rebuildable.

### 9.2 Excel

The first flagship Excel consumer should use the complete `LINEAGE@v1`
profile because its portfolio purpose includes evidence and trace
drill-through. A later management-summary workbook may declare `CORE@v1`.
Power Query may load CSV or Parquet depending on local library support.
Workbook formulas, assumptions, scenarios, and presentation are workbook-owned
and must remain separate from governed values.

An `.xlsx` file is not part of Artifact R.

### 9.3 Power BI

The first Power BI model should consume Parquet and the shared semantic and
relationship catalogues. TMDL/PBIP generation may translate R metadata into
tables, hidden technical keys, active and inactive relationships, display
folders, formatting, `SummarizeBy = None`, and measures. DAX remains consumer-
owned unless the exact measure appears in R's registry.

A `.pbix`, `.pbip`, or TMDL project is not part of Artifact R.

### 9.4 React

The existing Artifact O public interface continues to use its finite read-only
HTTP contract. A future analytical React surface may consume R through a local
read-only DuckDB/Parquet adapter, but it must not replace Artifact O's live
journey contract or expose diagnostic tables as generic APIs.

### 9.5 Direct SQL

Local DuckDB exploration is authorised only over an R-verified model. Queries
are analysis, not governed publications. Saved analytical views that make
domain claims require a later contract revision or consumer artifact. A saved
view or database write is not the exact verified R output even when its source
remains governed.

## 10. Module Consumption Map

| Module lens | Primary CORE datasets | LINEAGE support | First consumer outcomes |
|---|---|---|---|
| Hermes | P-D04 | P-D15 | Reconciliation status, source-to-ledger explanation |
| Atlas | P-D05, P-D06, P-D07, P-D14, Q-D01-D05, Q-D10 | P-D16, P-D17, Q-D06, Q-D12 | Statements, journals, restatement history, value trace |
| Argus | P-D08 | P-D15, Q-D12 | Exception worklist, assertion and evidence drill-through |
| Aegis | P-D09, P-D10, P-D20 | P-D15, Q-D12 | Issue lifecycle, remediation, purpose-specific readiness |
| Pythia | P-D11, P-D12 | P-D15 | Governed decision, frozen inputs, planning-use basis |

Module placement is a presentation lens. It never changes the semantic owners
recorded by P and Q.

## 11. C-001 Proof

A `LINEAGE@v1` R model built from the canonical package must allow a consumer
to perform these steps without querying the runtime:

1. select the C-001 scenario through P-D02;
2. inspect the failed contract-to-recognition reconciliation in P-D04;
3. inspect the Argus completeness exception in P-D08;
4. follow P-D09 into Aegis review, issue, remediation, and verification;
5. compare June reporting versions in P-D05;
6. read the exact as-was and as-restated values in P-D06;
7. read the GBP 10,000 bridge directly from P-D07;
8. inspect J-560 and its immutable lines through Q-D04/Q-D05;
9. resolve account and statement semantics through Q-D01-D03;
10. retain June hard-close state through Q-D10;
11. retain the exact directed trace through P-D16/P-D17;
12. retain purpose-specific readiness and limitations through P-D10/P-D20;
13. inspect the governed decision and frozen inputs through P-D11/P-D12; and
14. reproduce the same values, keys, and relationships in Excel, Power BI, or
    React without a consumer-specific source extract.

R does not recalculate the GBP 10,000 reporting bridge from journal lines. The
ledger is supporting drill-through; P-D07 remains the bridge authority.

## 12. CT-1 Proof

A `LINEAGE@v1` R model must allow a consumer to:

1. inspect P-D13's exact bind-before-compare correction conclusion;
2. inspect J-010 only in Q-D08/Q-D09 as referenced pre-scope state;
3. inspect J-011 and J-012 only in Q-D04/Q-D05 as authored journals;
4. retain reversal and replacement totals separately in P-D14;
5. follow exact evidence through P-D15, Q-D06, and Q-D12;
6. preserve zero control-account net movement from P-D13 as the governed
   conclusion; and
7. prevent a consumer from unioning the three journal classes into one
   authoritative journal population.

## 13. Failure Semantics

R-C01 fails closed for:

- source verification other than `VERIFIED`;
- a package digest other than the expected digest;
- missing, additional, or unsupported registries;
- compatibility mode other than `EXACT_ORIGINAL`;
- relationship contract other than version 2;
- unknown profile, format, dataset, column, type, or relationship;
- profile classification gaps or duplicates;
- source schema/data mismatch;
- an unclassified or multiply classified source column;
- an enum value outside its exact P/Q source set;
- integer overflow or invalid typed values;
- a consumer relationship whose endpoints are unavailable;
- an incomplete composite key, key mismatch, or detected hash collision;
- any relationship disposition outside the closed plan;
- an active cycle, duplicate directed filter path, bidirectional filter, or
  cardinality change;
- an absent or unsupported Parquet writer profile;
- Parquet row, null, type, key, or order divergence;
- DuckDB-to-Parquet divergence;
- R model metadata written into a source domain column;
- a measure outside the closed measure registry;
- a raw integer with default summarization other than `NONE`;
- a partial or existing output path; or
- loss of synthetic-data or canonical-depth disclosure.

No failure may produce a partially published model or mutate the governed
source package.

## 14. Implementation Sequence

### Phase R0 - Critique, correction, and ratification

- v0.1 field-by-field critique against all thirty-seven P/Q schemas: complete;
- v0.2 correction of all eight blockers and seven non-blocking findings:
  complete;
- independent v0.2 structural and semantic assessment: complete and passed;
- ratification through append-only ADR-038: complete.

### Phase R1 - Contracts and profile registry

- strict build, verification, reproduction, manifest, table-binding, semantic,
  relationship, and measure contracts: complete;
- closed dataset-classification and cumulative-profile registries: complete;
- complete 427-column role and visibility registry: complete;
- eight composite relationship-key projections and finite activation plan:
  complete;
- exact P/Q schema-to-physical-type mapping: complete;
- exact PyArrow implementation and all `ParquetWriterProfile@v1` values:
  dependency-locked and complete;
- positive and negative fixtures: complete;
- post-R1 cohesion audit: passed and recorded in
  `docs/roadmap/milestone-4-post-r1-cohesion-audit.md`;
- Phase R1 itself emitted no Parquet or consumer file; Phase R2 now owns the
  separately verified materialization described below.

### Phase R2 - Parquet and semantic materialization

- status: complete and audited in
  `docs/roadmap/milestone-4-post-r2-cohesion-audit.md`;
- source-package verification and binding: complete;
- strict CSV parsing through P/Q schemas: complete;
- deterministic Parquet writer: complete;
- byte-identical selected schemas and optional CSV: complete;
- logical table digests independent of physical writer bytes: complete;
- semantic and relationship catalogues: complete;
- atomic staged publication: complete;
- CORE, LINEAGE, and DIAGNOSTIC builds: complete.

### Mandatory post-Phase-R2 cohesion audit

Audit:

- exact source-package and snapshot binding;
- no new domain values, inferred statuses, or copied conclusions;
- all thirty-seven source classifications;
- all 427 column roles and visibility dispositions;
- row, technical key, enum, null, type, order, and relationship parity;
- active-filter graph acyclicity and unique directed paths;
- raw numeric summarization, measure grain, currency, version, and population
  safety;
- reporting history and purpose-specific readiness;
- authored-versus-referenced journal separation;
- directed trace and evidence-status preservation;
- C-001 and CT-1 parity;
- deterministic offline reproduction;
- byte-exact Parquet reproduction under the pinned writer profile;
- logical rather than byte-level DuckDB reproduction;
- unchanged P/Q verification and Milestone 1 through 4 tests.

### Phase R3 - Optional DuckDB acceleration

- status: complete and audited in
  `docs/roadmap/milestone-4-post-r3-cohesion-audit.md`;
- strict `NoncanonicalCacheManifest@v1`: complete;
- exact DuckDB 1.5.5 and v1.5.0 storage-compatibility dependency lock:
  complete;
- build only from verified emitted Parquet: complete;
- registry-separated source schemas plus closed metadata schema: complete;
- read-only consumer and verifier access: complete;
- database-to-Parquet equality and adversarial divergence checks: complete;
- engine, requested storage compatibility, and observed storage tag recording:
  complete;
- canonical digest exclusion with logical reproduction: complete;
- atomic failure and no-WAL publication checks: complete;
- no application runtime authority assigned to DuckDB.

### Phase R4 - First consumer artifact

Draft and ratify the Excel consumer contract over the exact R boundary. Power
BI follows from the same model contract. Analytical React expansion remains a
separate decision because Artifact O already owns the public live journeys.

## 15. Explicit Non-Goals

Artifact R does not define:

- a new P/Q dataset or runtime query;
- a data warehouse, lakehouse, dbt project, or generic SQL API;
- a star schema created by copying governed facts into new marts;
- an enterprise-volume synthetic generator;
- an `.xlsx`, `.pbix`, `.pbip`, TMDL, or React implementation;
- dashboard layouts, colours, chart selection, or storytelling copy;
- planning assumptions, forecasts, budgets, or model formulas;
- an authoritative trial balance beyond ratified journal records;
- a latest-only reporting table;
- adapted Artifact N reads;
- direct SQLite or authoritative-repository access;
- public download hosting;
- paid APIs, credentials, cloud services, or runtime network calls; or
- production-scale performance, security, or deployment claims.

## 16. Acceptance Criteria

Artifact R may be ratified only when:

- R-A01: R is explicitly a non-authoritative projection over one verified
  P-plus-Q package.
- R-A02: the exact source package digest and all snapshot coordinates bind
  before source deserialization.
- R-A03: P-C02 `VERIFIED` is mandatory and a checksum-only pass is rejected.
- R-A04: the accepted registry set is exactly P v1 plus Q v1.
- R-A05: all thirty-seven source datasets retain registry-qualified identity.
- R-A06: no R v1 replacement fact, dimension, aggregate, or source query exists.
- R-A07: the profile registry classifies exactly 26 CORE, 5 LINEAGE, and 6
  DIAGNOSTIC datasets with no gap or duplicate.
- R-A08: the three profiles are cumulative and exact.
- R-A09: every model contains byte-identical schemas for every selected source
  dataset.
- R-A10: CSV emission, when selected, is byte-identical to canonical source
  files.
- R-A11: `enum`, text, integer, boolean, date, UTC timestamp, hash, null, and
  absent-field semantics exactly match P/Q.
- R-A12: exact enum sets survive physical and semantic materialization, while Q
  text columns are not strengthened into enums.
- R-A13: all 427 source columns retain exact source origin/transformation and
  receive one R role and one visibility disposition.
- R-A14: every R-added field is reserved, hidden `R_TECHNICAL` metadata and no
  source field is overwritten.
- R-A15: all money remains signed 64-bit integer minor units with exact
  currency.
- R-A16: every Parquet table matches source schema order, `row_key ASC` rows,
  nulls, values, enums, and logical table digest.
- R-A17: the exact supported Parquet writer profile closes every byte-affecting
  setting and is dependency-locked before canonical fixtures exist.
- R-A18: DuckDB is optional, built only from Parquet, opened read-only by
  adapters, and has no authoritative runtime edge.
- R-A19: DuckDB is excluded from canonical byte reproduction and instead proves
  engine-versioned logical parity with Parquet.
- R-A20: all eight composite relationships receive the exact deterministic
  technical-key projection on both endpoints.
- R-A21: incomplete composite values, endpoint mismatch, or a detected hash
  collision rejects the model.
- R-A22: every in-profile relationship receives exactly one closed disposition.
- R-A23: the exact thirty-three-entry active set exists only when both endpoints
  are present, retains many-to-one cardinality, and filters one-side to
  many-side.
- R-A24: the active filter graph is acyclic and has no two directed paths from
  the same filter source to the same target.
- R-A25: `P-RL04` is the only v1 inactive role-playing relationship; all other
  non-active consumer relationships are navigation-only.
- R-A26: integrity and polymorphic relationships are always validation-only.
- R-A27: purpose-specific readiness, limitations, and P-D15 references remain
  required for controlled use.
- R-A28: reporting versions and restatement bridges remain simultaneous and
  immutable.
- R-A29: authored and referenced journal populations remain separate.
- R-A30: trace direction and evidence verification status remain exact.
- R-A31: all fifty raw integer fields default to summarization `NONE`.
- R-A32: the twelve-measure registry closes source, class, aggregation, grain,
  grouping, currency, version, population, multi-row, and incompatibility
  behavior.
- R-A33: exact-value measures return a value only for one exact source row.
- R-A34: additive journal measures require scenario/currency grouping, remain
  gross activity, and cannot combine authored and referenced populations.
- R-A35: portable physical aliases are deterministic, source-bound, and reject
  unresolved collisions.
- R-A36: CORE is the minimum business-analysis profile and LINEAGE is mandatory
  for the complete canonical evidence journeys.
- R-A37: the first flagship Excel contract consumes complete LINEAGE rather
  than an undeclared subset.
- R-A38: the baseline requires no paid, hosted, credentialed, or network
  dependency.
- R-A39: canonical C-001/CT-1 depth and synthetic status remain prominent.
- R-A40: build publication uses a unique same-parent staging directory, closes
  all handles, leaves no temporary/WAL file, and rejects overwrite.
- R-A41: R-C02 has one strict full-source-equivalence request/result contract and
  requires the exact source package.
- R-A42: R-C02 reruns P-C02 before verifying all files, profiles, fields, rows,
  schemas, technical keys, relationships, measures, and source bindings.
- R-A43: exact reproduction requires the exact source package and writer
  profile and reproduces every canonical model byte.
- R-A44: DuckDB reproduction compares logical tables, verifies each regenerated
  cache against its own checksum, and never compares canonical or cross-build
  DuckDB file bytes.
- R-A45: adapters import one complete profile and cannot mutate R or its source
  package.
- R-A46: a consumer-owned formula may not be presented as a governed platform
  value.
- R-A47: C-001 and CT-1 remain consumable through LINEAGE without runtime
  access, bridge recomputation, or authored/referenced blending.
- R-A48: existing P/Q verification, reproduction, and acceptance gates remain
  green, and no consumer implementation begins before R ratification.

## 17. Structural Inventory and Ratification Gate

Artifact R v0.2 contains exactly:

- twenty-eight rulings, R-R01 through R-R28;
- three cumulative profiles;
- thirty-seven source-dataset classifications: 26 CORE, 5 LINEAGE, and 6
  DIAGNOSTIC;
- three physical formats: CSV, Parquet, and optional DuckDB;
- one shared semantic catalogue;
- one complete 427-source-column role registry;
- eight composite relationship-key projections;
- thirty-three conditionally present active relationships and one inactive
  role-playing relationship;
- one versioned Parquet writer-profile contract;
- twelve finite shared measures, R-M01 through R-M12;
- three operations, R-C01 through R-C03;
- two canonical transaction proofs; and
- forty-eight acceptance criteria, R-A01 through R-A48.

The v0.1 ratification questions are resolved as follows:

1. Original P/Q datasets are sufficient; only hidden technical relationship
   keys are added, never a derived business mart.
2. CORE is the minimum business-analysis profile; complete trace and evidence
   journeys require LINEAGE.
3. P-D15 remains CORE and Q-D12 remains LINEAGE.
4. Parquet byte reproduction is conditional on one exact writer profile;
   DuckDB uses logical reproduction and is non-canonical.
5. Measures are safe only through the expanded grain, currency, version,
   population, and raw-summarization rules now stated.
6. The first flagship Excel consumer uses complete LINEAGE.

Artifact R v0.2 incorporates the complete v0.1 critique, passed the independent
structural and semantic assessment recorded in
`docs/roadmap/milestone-4-artifact-r-v02-assessment.md`, and is ratified through
ADR-038. Phases R1 and R2 and their mandatory cohesion audits now pass; ADR-039
and ADR-041 record those implementation decisions. The exact P+Q package now
materializes into verified, byte-reproducible Parquet and shared catalogues.
DuckDB and every presentation-specific consumer remain outside the implemented
boundary pending a separately authorised phase or consumer artifact.
