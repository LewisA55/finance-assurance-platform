# Artifact R v0.1 Hard Critique

Status: NOT RATIFIABLE - bounded v0.2 correction required

Date: 2026-08-13

## 1. Scope

This critique tests Artifact R v0.1 against the implemented
`P-EVIDENCE@v1` and `Q-ANALYTICS@v1` package rather than only against R's
internal prose and counts.

The review covers:

- all thirty-seven implemented P/Q dataset schemas;
- all 427 source columns, their types, nullability, value origins, and
  transformations;
- all sixty-four serialized relationship entries in relationship contract v2;
- the actual 706-row canonical analytical package;
- CORE, LINEAGE, and DIAGNOSTIC profile closure;
- CSV-to-Parquet and Parquet-to-DuckDB materialization claims;
- exact reproduction and offline verification;
- Excel Data Model and Power BI import-model relationship constraints;
- raw numeric-column and registered-measure behavior;
- C-001 and CT-1 consumer proofs; and
- continued separation of domain values, source-package metadata, and
  R-owned model metadata.

Artifact R's direction is correct. The blockers are consumer-contract and
physical-reproducibility gaps. None requires reopening Artifact P, Artifact Q,
the runtime, the event model, or the project thesis.

## 2. Structural and Field Audit Results

R's stated structural inventory is internally correct:

```text
28 rulings                    R-R01 through R-R28
3 cumulative profiles        CORE, LINEAGE, DIAGNOSTIC
37 dataset classifications   26 CORE, 5 LINEAGE, 6 DIAGNOSTIC
3 physical formats           CSV, PARQUET, DUCKDB
12 measures                  R-M01 through R-M12
3 operations                 R-C01 through R-C03
34 acceptance criteria       R-A01 through R-A34
```

The dataset classification is exact: all P-D01 through P-D21 and Q-D01
through Q-D16 occur once, with no gap or duplicate. The cumulative profiles
contain 26, 31, and 37 datasets respectively.

Every profile is closed over the current upstream
`CONSUMER_RELATIONSHIP` endpoints:

```text
CORE         unresolved required targets = 0
LINEAGE      unresolved required targets = 0
DIAGNOSTIC   unresolved required targets = 0
```

The source field inventory is:

```text
P-EVIDENCE columns       231
Q-ANALYTICS columns      196
total                    427

boolean                    5
date                       12
enum                       32
hash                       27
integer                    50
text                      288
timestamp                  13
```

The document is ASCII-clean and has no trailing whitespace. These checks
establish coverage and hygiene only. They do not close the eight blockers
below.

## 3. Strengths That Should Survive v0.2

The following decisions are sound and should not be reopened:

- one verified P-plus-Q package is the sole domain source;
- R remains a disposable projection and cannot feed authority upstream;
- all thirty-seven source dataset identities remain registry-qualified;
- no replacement fact, dimension, or aggregate mart is created in v1;
- CSV, Parquet, semantic metadata, and DuckDB have distinct intended roles;
- authored journals and referenced pre-scope journals remain separate;
- reporting history, readiness, evidence status, and trace direction survive
  materialization;
- the baseline remains local, deterministic in intent, synthetic, and free of
  paid services; and
- C-001 and CT-1 remain the bounded proof depth rather than an excuse to invent
  decorative volume.

The 26/5/6 classification also has a defensible shape. P-D15 belongs in CORE
because controlled readiness use requires its exact references. Q-D15 belongs
in CORE because Q-D01 through Q-D03 have required consumer relationships to
the exact ledger-semantics catalogue. Q-D11 and Q-D12 correctly remain
lineage-oriented rather than ordinary reporting tables.

## 4. Blocking Findings

### R-B01 - The field-role model does not close the 427-column boundary

R-R13 says domain values and R-owned model metadata remain separate, while
SemanticCatalogue v1 records only a `domain-or-metadata classification`.
That binary vocabulary does not represent the implemented source boundary.

P/Q already distinguish at least:

```text
governed domain and evidence values
O query and envelope coordinates
P discovery values
P transport metadata
P/Q structural metadata
R model metadata
```

The schemas expose six P value-origin families and two Q families. For
example, P-D01 contains finance-facing context beside `export_ref`,
`producer_release`, `query_revision`, and discovery hashes. Every P/Q table
also contains a source-owned `row_key`. Those fields are not R model metadata,
but neither should all be exposed as business attributes.

Consequences:

- R-A13 is not mechanically testable;
- a consumer adapter cannot know which technical fields to hide;
- source-package metadata could be presented as a module-owned domain value;
- an R-owned relationship key could be confused with a governed key; and
- R cannot honestly claim a field-by-field semantic boundary.

Recommended repair:

- retain each column's exact P/Q `value_origin` and `transformation` in the R
  semantic catalogue;
- define a closed R column-role vocabulary, at minimum
  `DOMAIN_ATTRIBUTE`, `DOMAIN_MEASURE_INPUT`, `EVIDENCE_ATTRIBUTE`,
  `SOURCE_TECHNICAL`, and `R_TECHNICAL`;
- define a deterministic mapping or a finite generated registry covering all
  427 source columns;
- require every R-added field to use a reserved namespace and
  `R_TECHNICAL`; and
- add a field-coverage acceptance test proving exactly one role and one
  default-visibility decision per source column.

This does not require hand-authoring 427 prose rows. The registry may be
generated from the ratified schemas plus a small explicit override table, but
its output must be finite and auditable.

### R-B02 - The physical type map omits all thirty-two enum columns

Section 6.2 maps `text`, `integer`, `boolean`, `date`, `timestamp`, and `hash`.
The implemented P registry also contains thirty-two `enum` columns, including
compatibility mode, module, reconciliation type/status, publication origin,
readiness status, correction role, and evidence status.

R mentions enums later only by saying the semantic catalogue cannot override
them. It never defines their Parquet or DuckDB representation or requires the
closed allowed-value set to survive materialization.

The same section overstates empty-string semantics. Artifact P's canonical CSV
uses an empty field only for null and prohibits a non-null empty string. R-R16's
claim that `empty text remains empty text` therefore describes a source value
the package cannot encode.

Consequences:

- valid P datasets have fields with no legal R physical mapping;
- a Parquet writer could silently widen an enum to unconstrained text;
- R-C02 cannot validate enum-domain preservation; and
- null and empty-string behavior is stated differently from the canonical
  source serializer.

Recommended repair:

- add `enum -> UTF-8 string / VARCHAR` to the physical type map;
- require the exact source `enum_values[]` in the semantic and physical schema
  fingerprints;
- reject values outside that source set during build and verification;
- state that a canonical empty CSV field represents null only on a nullable
  column;
- state that non-null empty text is prohibited by the source contract; and
- keep absent fields as schema failures.

### R-B03 - Composite consumer relationships cannot be materialized under R's current rules

Relationship contract v2 contains eight required composite
`CONSUMER_RELATIONSHIP` entries. They cover reporting values and versions,
restatement predecessor/successor versions, readiness, decisions, and
limitations.

R-R18 says an unsupported relationship must remain inactive and prohibits an
invented concatenated authoritative key. R-R06 and R-R13 also prohibit derived
tables and R metadata inside a domain table. Together, those rules leave no
way for the first Excel or Power BI import model to implement the composite
relationships.

This is a real consumer constraint, not a style preference. Excel Data Models
cannot use composite keys, and Power BI import-model relationships relate one
column in one table to one column in another. Microsoft explicitly recommends
a surrogate or combined technical key where a single unique column is absent.

Consequences:

- P-D06 cannot filter through its exact P-D05 reporting version;
- P-D11 cannot bind simultaneously to its exact reporting version and
  readiness assessment through model relationships;
- P-D12 cannot relate to its exact decision through the registered composite
  key;
- P-D20 cannot relate to its readiness parent; and
- the shared semantic relationship promise is not implementable in the named
  consumers.

Recommended repair:

- define a finite `RelationshipKeyProjection@v1` for composite
  `CONSUMER_RELATIONSHIP` entries;
- derive hidden, R-owned technical primary and foreign keys from the exact
  registry-qualified relationship ID and a canonical length-prefixed tuple;
- specify null handling, type tags, Unicode encoding, hash algorithm, collision
  behavior, and verification;
- retain the original source columns unchanged;
- classify projected keys as `R_TECHNICAL`, hidden, non-authoritative, and
  unusable as business identifiers; and
- require Excel and Power BI adapters to use the same projection rather than
  inventing their own concatenation.

The projection may be generated in the consumer import adapter instead of
being appended to canonical Parquet, but the exact algorithm and relationship
identity must remain owned by R.

Primary references:

- [Excel relationships and composite-key limitation](https://support.microsoft.com/en-us/excel/relationships-between-tables-in-a-data-model)
- [Power BI relationship column rules](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand)
- [Power BI surrogate-key guidance](https://learn.microsoft.com/en-ie/power-bi/guidance/star-schema)

### R-B04 - Permitted relationships are not an executable activation topology

Artifact Q defines which joins are semantically permitted. It does not decide
which relationships a tabular consumer can activate simultaneously. R must do
that second job, but section 7.4 provides only a possible
`load_disposition` value and no closed relationship plan.

The current graph contains at least twenty-three direct-versus-two-hop
alternate paths. Examples include:

```text
P-D02 -> P-D06
P-D02 -> P-D05 -> P-D06

P-D02 -> P-D11
P-D02 -> P-D05 -> P-D11
P-D02 -> P-D10 -> P-D11

P-D02 -> Q-D05
P-D02 -> Q-D04 -> Q-D05
```

P-D07 also has two different registered relationships to P-D05: predecessor
and successor. Only one relationship between the same pair can be active by
default in the Excel Data Model, and loops or multiple active paths are not
permitted.

Consequences:

- two conforming adapters can choose different active paths;
- filter propagation can become ambiguous or tool-rejected;
- Excel and Power BI no longer share one semantic model; and
- R-C02 has no exact expected activation state to verify.

Recommended repair:

- define one finite `RelationshipPlan@v1` over every relationship relevant to
  each profile;
- record exact `ACTIVE`, `INACTIVE_ROLE_PLAYING`, `NAVIGATION_ONLY`, or
  `VALIDATION_ONLY` disposition;
- record relationship role, projected key ID, cardinality, and single filter
  direction;
- select one acyclic active filter topology;
- keep alternate scenario and role-playing paths inactive but addressable by
  named consumer calculations; and
- prove the active graph has no cycle or ambiguous path.

Microsoft's current Excel documentation confirms both the single-active-
relationship rule between a table pair and the prohibition on loops in the
workbook Data Model.

### R-B05 - The profile contract contradicts its own consumer guidance

R-R07 says a consumer selects one whole cumulative profile and may hide tables
but cannot import an undeclared subset. Section 9.2 then says the Excel
consumer should use CORE plus `selected LINEAGE` tables. That selection is not
one of the three declared profiles.

CORE is also described as directly supporting all four ratified consumer
journeys. It does not contain P-D16/P-D17, while R's own C-001 proof requires
LINEAGE to preserve the O-J01 directed reporting trace. CORE supports business
summaries and governed values; it does not independently reproduce the full
flagship trace journey.

Consequences:

- the first Excel baseline is not a valid R profile;
- the profile completeness rule and adapter guidance disagree;
- CORE's capability claim is overstated; and
- R-A08 and R-A31 can be interpreted incompatibly.

Recommended repair:

- describe CORE as the minimum business-analysis profile, not the complete
  flagship-journey profile;
- require LINEAGE for the complete C-001 and CT-1 trace/evidence proofs;
- replace `CORE plus selected LINEAGE tables` with one exact declared profile;
- allow a consumer to hide tables from presentation without omitting them from
  the imported R model; and
- leave the Excel artifact to choose CORE or LINEAGE explicitly, or settle
  LINEAGE as the first flagship workbook baseline in R v0.2.

### R-B06 - R-C02 cannot prove source parity from the model package as specified

R-C02 has no request or result contract. It says verification is offline and
checks exact source-to-model rows, values, schemas, and keys, but it does not
say whether the verified P-plus-Q source package is an input.

That omission matters because CSV is optional. A Parquet-only R model retains
source CSV hashes and row counts but does not contain the source CSV bytes.
Without the exact source package, a verifier can confirm the R package's own
checksums, but it cannot independently prove that its Parquet values equal the
committed P/Q rows.

Section 6.3 also says R copies canonical CSV files `and their schemas`, while
the canonical directory layout contains no schema directory. The schemas are
needed for strict source parsing and for independent physical-schema
comparison.

Consequences:

- `VERIFIED` has two possible meanings: internally intact or source-equivalent;
- a resealed model can be internally self-consistent without proving P/Q
  parity;
- R-A09, R-A10, R-A15, R-A28, and R-A29 are not fully executable; and
- a self-contained CSV bundle cannot contain the promised source schemas.

Recommended repair:

- define strict `VerifyConsumerModelRequest@v1` and result/status contracts;
- require `model_path`, exact `source_package_path`, expected model digest, and
  expected source package digest for full verification;
- rerun P-C02 against that source package before comparing any R table;
- distinguish full `VERIFIED` from any optional internal-integrity-only result;
- add byte-identical selected schema files to the R layout, or explicitly make
  the source package mandatory and remove the schema-copy claim; and
- retain the exact P-C02 verification receipt or its reproducible coordinates
  in the R manifest.

Offline should mean no runtime, database, or network dependency. It should not
mean that source bytes are unnecessary for a source-equivalence claim.

### R-B07 - Byte-exact Parquet and DuckDB reproduction is underspecified and internally inconsistent

R-R28 and R-C03 require the same model digest and every file byte. No Parquet
writer profile is defined. Parquet bytes depend on implementation and settings
including compression, compression level, row-group sizing, dictionary use,
statistics, data-page version, timestamp coercion, schema metadata, and writer
version. `producer_release` does not specify those choices.

The repository currently has no Parquet or DuckDB dependency declared. That is
appropriate before implementation, but it proves the exact physical writer is
not yet part of the contract.

DuckDB is a sharper contradiction. R-R11 calls the database disposable
acceleration, yet R-C03 requires exact reproduction of every file byte. DuckDB
storage has an explicit storage-format compatibility version; logical equality
does not imply byte-identical database files across engine versions or
storage settings.

Consequences:

- two valid writers can produce semantically identical but byte-different
  Parquet files;
- a dependency upgrade can break reproduction without changing one domain
  value;
- DuckDB's rebuildable-cache role conflicts with canonical-byte status; and
- R-A10, R-A11, and R-A29 cannot all be satisfied as written.

Recommended repair:

- define `ParquetWriterProfile@v1` with exact implementation/version and every
  byte-affecting setting;
- pin the implementation in the project lock when R is implemented;
- store the writer profile coordinate and hash in the manifest;
- define a logical table digest over exact typed rows independently of Parquet
  bytes;
- retain byte-exact Parquet reproduction only under the same writer profile;
- classify DuckDB as a non-canonical cache excluded from the detached semantic
  model digest and byte-reproduction claim;
- checksum DuckDB for tamper detection within one build, but verify its tables
  logically against Parquet; and
- record DuckDB engine and storage-compatibility versions.

Primary reference:

- [DuckDB storage versions and format](https://duckdb.org/docs/current/internals/storage)

### R-B08 - The measure contract does not prevent accidental or misleading aggregation

The source package contains fifty integer columns. Only twelve measures are
registered, and only four are additive. R does not define the default
summarization behavior of the remaining raw integers.

That is unsafe for the named consumers. Power BI and Excel can automatically
sum raw numeric columns such as:

```text
reporting-value amounts across both reporting versions
journal header totals across multiple journals
versions, ordinals, and query revisions
exception expected/actual/difference variants
```

R-M01 through R-M08 are labelled `EXACT_VALUE`, but they do not define the
required single-row context or what happens when multiple source rows are in
scope. R-M09 through R-M12 do not define mandatory grouping dimensions,
single-currency context, or machine-readable population separation. Their
English labels say authored and referenced values are separate, but R-A23 has
no executable registry fields that enforce that distinction.

The closure rule also says consumers are `unable to create` competing
authoritative calculations. Excel, Power BI, React, and SQL can always create
new formulas. R can govern labels and default behavior; it cannot make analysis
technically impossible.

Consequences:

- a default visual can double-count June v1 and v2 reporting values;
- gross posted activity can be mistaken for a trial-balance or statement
  amount;
- currencies can be summed without a declared conversion basis in future
  packages;
- authored and referenced populations can be combined by an unlabelled
  consumer formula; and
- R's authority claim is stronger than it can enforce.

Recommended repair:

- set every raw integer column to `DO_NOT_SUMMARIZE` by default;
- require an explicit registered measure for every permitted aggregation;
- add `required_grain`, `aggregation`, `grouping_dimensions`,
  `currency_policy`, `population_class`, `blank_or_error_on_multirow`, and
  `non_combinable_with[]` to the measure contract;
- make exact-value measures require a single exact row or return blank/error;
- bind additive journal-line measures to either `AUTHORED` or `REFERENCED`,
  never both;
- label debit/credit sums as gross activity, not balances or financial
  statement values;
- classify all other formulas as consumer-owned and visibly
  non-authoritative; and
- replace `unable to create` with the enforceable rule that a consumer may not
  present its own calculation as a governed platform value.

## 5. Non-Blocking Tightening Items

### R-N01 - Empty format sets are not rejected

R-C01 orders and deduplicates `formats[]` but does not require at least one
format. Require a non-empty set. Retain `DUCKDB -> PARQUET` as an exact
dependency.

### R-N02 - Parquet row ordering should name the exact source rule

The package CSV is already sorted by `row_key`. Replace the generic
`deterministic row-order key` with exact `row_key ASC` source order for every
v1 table. Consumer query results remain unordered unless a query orders them.

### R-N03 - Atomic publication should require a same-parent staging directory

Require staging beneath the final output parent so publication is a same-
filesystem rename. All Parquet and DuckDB handles must be closed, and no
DuckDB WAL or temporary file may remain before verification and publication.

### R-N04 - DuckDB read-only status is an adapter mode, not a database fact

DuckDB base tables are not intrinsically immutable. Require consumer adapters
to open the database read-only. Any write invalidates its build checksum and
requires rebuild or reverification.

### R-N05 - Friendly physical names need a deterministic collision rule

The DuckDB aliases derived from dataset names need exact normalization,
reserved-word handling, maximum length, and collision rejection. The same
applies to later Excel and Power BI table aliases.

### R-N06 - Q text fields must not be strengthened into enums by R

Several Q semantic discriminators are intentionally typed as text. R may copy
their observed values and labels, but only the thirty-two source columns whose
P/Q type is `enum` may receive enum enforcement without a later Q revision.

### R-N07 - Direct SQL must preserve verification honesty

State explicitly that arbitrary DuckDB queries are consumer analysis. Saved
views and modified caches are no longer the exact verified R output even when
their source remains governed.

## 6. Answers to R's Six Ratification Questions

### 6.1 Are the original P/Q datasets sufficient?

Yes for v1 domain facts. No derived business mart is required for the first
Excel or Power BI journey.

A bounded technical relationship-key projection is required by the consumer
engines. That is not a new fact or dimension and must not be represented as
one.

### 6.2 Is CORE the minimum useful set?

CORE is relationship-closed and sufficient for module summaries and governed
values. It is not sufficient for the full directed trace/evidence journey.
The latter requires LINEAGE.

### 6.3 Is P-D15 core while Q-D12 is lineage defensible?

Yes. P-D15 is required by Artifact Q's controlled-readiness rule. Q-D12 is
needed for analytical evidence inspection but is not required for ordinary
reporting-value use. Both remain non-business-facing by default.

### 6.4 Is Parquet reproduction specified tightly enough?

No. A finite writer profile and logical table digest are required. DuckDB
should not be subject to canonical byte reproduction.

### 6.5 Is the measure registry safe enough?

No. It needs default summarization, grain, currency, population, and
multi-row behavior before any BI model is authorised.

### 6.6 Which profile should the first Excel consumer use?

The first flagship workbook should use LINEAGE if it is expected to demonstrate
the platform's auditability and value trace. A smaller management-reporting
workbook could use CORE, but that choice belongs in its consumer artifact.
Artifact R must prohibit an undeclared CORE-plus-selected-lineage hybrid.

## 7. Required v0.2 Correction Sequence

The cleanest correction order is:

1. close the column-role vocabulary and exact enum/null physical mapping;
2. define technical composite-key projection and the finite relationship
   activation plan together;
3. reconcile CORE/LINEAGE capability claims and consumer profile rules;
4. define full R-C02 request/result and source-package requirements;
5. add canonical schema placement and exact file inventory;
6. define Parquet writer profile, logical table digests, and non-canonical
   DuckDB treatment;
7. close raw-column summarization and measure semantics; and
8. add negative acceptance cases for every boundary above.

After that correction pass, rerun:

- the 427-column role and physical-type audit;
- the 37-dataset classification proof;
- relationship endpoint, composite-key, acyclic-active-path, and role-playing
  tests for all profiles;
- C-001 and CT-1 consumer proofs;
- Parquet semantic and byte reproduction under the exact writer profile;
- DuckDB logical parity; and
- all existing P/Q verification and acceptance suites.

## 8. Verdict

Artifact R v0.1 is not ratifiable as written.

Eight blocking issues remain:

1. incomplete field-role classification;
2. missing enum and incorrect empty-string physical semantics;
3. no executable composite-key strategy;
4. no finite relationship activation topology;
5. contradictory profile capability and Excel-selection rules;
6. incomplete source-equivalence verification contract;
7. underspecified Parquet and contradictory DuckDB reproduction; and
8. unsafe and partly unenforceable measure semantics.

These findings do not weaken the product direction. They identify the exact
work Artifact R exists to settle before Excel, Power BI, or a broader React
analytical surface is allowed to define its own workaround. A bounded v0.2
revision can close them without a new runtime query, domain dataset, or
authoritative finance calculation.
