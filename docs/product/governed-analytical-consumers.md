# Artifact S - Governed Analytical Consumers and Cross-Tool Parity

Status: Design v0.1 - draft for critique

## 0. Purpose and hard constraint

Artifact S defines the first presentation-specific consumers of the verified
`LINEAGE@v1` model produced by Artifact R:

1. a portable Excel analytical workbook;
2. a source-controlled Power BI semantic project; and
3. a cross-tool parity proof over the governed claims both consumers expose.

Its hard constraint is:

> Excel and Power BI may present, navigate, and calculate over one exact
> Artifact R model, but neither may author a second semantic truth.

Artifact S is not permission to widen the synthetic population, derive a new
mart, infer a readiness result, collapse reporting history, blend authored and
referenced journals, or replace an Artifact R relationship or measure rule.

The first consumer pack is intentionally bounded to C-001 and CT-1. It proves
the complete governed journeys before wider synthetic populations make the
visual layer more impressive but harder to validate.

## 1. Binding sources

Artifact S is bound by:

- Artifact O v0.2.1, the public-product journey and view boundary;
- Artifact P v0.2.1, the governed evidence-package contract;
- Artifact Q v0.2, the governed analytical registry;
- Artifact R v0.2, the model-digestion and consumer-dataset contract;
- ADR-033, ADR-035, ADR-037, ADR-038, ADR-039, and ADR-041; and
- the implemented `consumer-model@v1` verifier.

Where Artifact S conflicts with the exact R manifest, semantic catalogue,
relationship catalogue, column-role registry, or measure registry, Artifact S
is wrong.

Current Microsoft Power BI project guidance is treated as an adapter-format
dependency, not as platform authority. The implementation targets a PBIP
semantic-model definition using TMDL and a version 4.0-or-later
`definition.pbism`. Any later project-format migration must preserve this
artifact's source identity and parity rules.

## 2. Product position

```text
P-EVIDENCE@v1 + Q-ANALYTICS@v1
                |
                v
          R-LINEAGE@v1
                |
        +-------+-------+
        |               |
        v               v
   Excel snapshot   Power BI model
        |               |
        +-------+-------+
                |
                v
       Cross-tool parity proof
                |
                v
      Later analytical React pages
```

The later React layer consumes Artifact R plus the parity catalogue. It does
not scrape either Excel or Power BI and is outside Artifact S implementation.

## 3. Rulings

### S-R01 - One exact R model is the consumer source

Every consumer pack binds one exact:

```text
model_ref
model_digest
profile_id = LINEAGE
profile_version = 1
source_package_ref
source_package_digest
source_query_revision
source_semantic_as_of
source_scenario_set_digest
source_compatibility_mode = EXACT_ORIGINAL
```

The complete R-C02 full-source-equivalence verification must pass before any
consumer file is authored.

### S-R02 - LINEAGE is imported whole

The first Excel and Power BI consumers admit all thirty-one `LINEAGE@v1`
tables. A consumer may hide a table from ordinary navigation, but the pack may
not silently reduce LINEAGE to a convenient subset.

### S-R03 - The consumer pack is a snapshot, not a live authority

The consumer pack is an immutable analytical snapshot of one verified R
model. It never writes to the runtime, persistence database, P/Q package, or R
model. Refresh means building a new pack from a newly verified R model.

### S-R04 - Consumer files carry source identity visibly

Excel cover/check sheets, Power BI annotations, and the consumer manifest all
show the exact R model digest, source package digest, query revision, semantic
as-of timestamp, compatibility mode, synthetic-data notice, and profile.

### S-R05 - Physical format may vary; semantics may not

Excel embeds exact canonical R CSV rows because they are portable and
inspectable. Power BI imports exact R Parquet tables because they preserve the
physical type map efficiently. Cross-tool parity is assessed against logical
R rows and registered measures, not against identical file formats.

### S-R06 - Domain rows remain unchanged

Neither adapter adds presentation, refresh, worksheet, report-page, visual,
or consumer-measure fields to a governed table. Consumer metadata lives only
in workbook sheets, TMDL metadata, annotations, or the S manifest.

### S-R07 - Major units are visibly consumer calculations

Money remains integer minor units in imported data and governed measures.
Division by 100 is an adapter calculation labelled `Consumer calculation`.
No major-unit value is described as an additional governed fact.

### S-R08 - Raw numerics never auto-summarize

Every raw integer column uses `SummarizeBy = None` in Power BI and is not used
as an implicit Excel total. Amounts, counts, ordinals, versions, and revisions
may be aggregated only through an R measure or an explicitly labelled
consumer calculation.

### S-R09 - R measures are translated, not reinterpreted

R-M01 through R-M12 retain their identifiers, source fields, classification,
aggregation, required grain, grouping, currency, reporting-version,
population, multirow, and non-combination rules. Adapter syntax may differ;
measure meaning may not.

### S-R10 - Exact-value measures fail closed

R-M01 through R-M08 return blank or an explicit error state unless one exact
registered source row remains at the required grain. They never sum multiple
reporting versions, statement fields, exceptions, decisions, cases, or
journals.

### S-R11 - Additive measures retain population firewalls

R-M09/R-M10 aggregate only authored journal lines. R-M11/R-M12 aggregate only
referenced journal lines. No measure, visual, pivot, or worksheet total may
combine those populations or label their gross activity as a balance,
statement value, revenue, or expense.

### S-R12 - Relationship topology is copied exactly

Power BI creates only R relationships whose disposition is `ACTIVE` or
`INACTIVE_ROLE_PLAYING`. It preserves single-direction filtering,
cardinality, projected technical keys, and inactive state exactly.
`NAVIGATION_ONLY` and `VALIDATION_ONLY` entries remain catalogue metadata.

Excel does not invent a relational model. Formula and navigation blocks use
exact keys and are checked against the same relationship catalogue.

### S-R13 - Technical keys remain hidden and non-business

Every `_r_*` technical key remains hidden from Excel presentation sheets and
Power BI report navigation. It may support relationships and checks only and
is never exposed as a customer, account, journal, scenario, or evidence ID.

### S-R14 - Reporting history stays simultaneous

Excel and Power BI retain June v1, June v2, and the governed restatement bridge
as separate rows and measures. A default selection may highlight v2, but no
consumer overwrites, drops, or recalculates v1.

### S-R15 - Readiness always travels with controlled use

Any visual or workbook output presented as decision-usable must retain the
exact reporting version, readiness reference, purpose, scope, status,
limitations, and decision-input binding. Corrected, posted, balanced, or
content-verified never implies approved.

### S-R16 - Evidence wording remains exact

`CONTENT_BYTES_VERIFIED` and `DECLARED_HASH_ONLY` remain distinct labels.
Neither adapter uses generic wording such as `verified evidence` when only a
declared hash exists.

### S-R17 - Directed trace remains directed

Trace nodes and edges preserve exact source and target identity and edge
direction. Excel may show an ordered trace table; Power BI may expose a drill
path. Neither may infer a missing edge or reverse an edge for visual
convenience.

### S-R18 - Excel is portable and inspectable

The workbook contains the complete admitted snapshot, requires no paid API,
credential, external workbook link, macro, add-in, Power Pivot dependency, or
network access, and remains usable in ordinary desktop Excel.

### S-R19 - Excel calculation zones are explicit

The workbook separates:

```text
governed imported rows
registered R measure translations
consumer calculations
presentation-only cells
checks and source metadata
```

Formula cells are black, cross-sheet links green, editable consumer controls
blue, and external links are absent. Governed imported constants are not
styled as editable assumptions.

### S-R20 - Power BI is source controlled and local

The first Power BI artifact is a PBIP-compatible semantic-model project using
TMDL. It requires no Power BI Service, Fabric workspace, gateway, credential,
or online refresh. A local `ModelRootPath` parameter points to one verified R
model and is machine configuration rather than governed metadata.

### S-R21 - Machine-local Power BI bindings are noncanonical

The canonical project contains the parameter definition and exact relative
Parquet paths, but no user-specific absolute path. A machine-local binding may
be generated or entered for refresh and is excluded from canonical checksums.

### S-R22 - Power BI report visuals are a later bounded phase

Artifact S first proves the semantic model, relationships, measures, DAX
queries, and Desktop load boundary. Hand-authored PBIR visual JSON is
prohibited. Report pages are added only after Power BI Desktop has opened and
saved the generated semantic project, or a separately verified PBIR generator
is introduced.

### S-R23 - Cross-tool parity is claim-based

Parity compares the same exact R source rows and registered measure results.
It does not require identical layouts, chart types, colors, filter controls, or
adapter file bytes.

### S-R24 - Reproduction claims are format-specific

Canonical manifests, Power BI text, formula maps, mapping catalogues, and
parity fixtures reproduce byte-for-byte. The `.xlsx` file must reproduce
logically: the same sheets, cells, values, formulas, formats, tables, charts,
and source rows. Byte identity is claimed only if the pinned workbook writer is
proved deterministic.

### S-R25 - Publication is atomic and non-overwriting

The complete consumer pack builds in a same-parent staging directory, verifies
all canonical and consumer files, and publishes through one same-filesystem
rename to a previously absent final directory. Failure leaves no partial pack.

### S-R26 - Later React analysis reuses this boundary

Artifact S publishes a consumer-neutral parity catalogue containing measure
IDs, calculation IDs, source coordinates, labels, formats, and claim fixtures.
Later React analysis must translate that catalogue and may not import workbook
formulas, DAX text, or presentation-specific metadata as semantic authority.

## 4. Exact first consumer pack

The first pack coordinate is:

```text
consumer_pack_ref = S-LINEAGE-DEMO
contract_version = governed-analytical-consumer-pack@v1
source_model_ref = R-LINEAGE-DEMO
source_profile = LINEAGE@v1
scenario_set = C-001 + CT-1
```

The pack contains:

```text
S-LINEAGE-DEMO/
|-- consumer-manifest.json
|-- parity-catalogue.json
|-- parity-results.json
|-- checksums.json
|-- pack.digest
|-- excel/
|   `-- finance-assurance-lineage.xlsx
`-- powerbi/
    |-- README.md
    |-- FinanceAssurance.SemanticModel/
    |   |-- definition.pbism
    |   `-- definition/
    |-- DAXQueries/
    `-- local-binding.example.json
```

The Power BI report folder and `.pbip` shortcut are introduced only by the
later Desktop-owned report phase described by S-R22.

## 5. Excel workbook contract

### 5.1 Visible sheets

| Order | Sheet | Purpose |
|---:|---|---|
| 1 | `Cover` | Product thesis, exact snapshot identity, instructions, model status |
| 2 | `Executive` | C-001 governed reporting, assurance, readiness, and decision summary |
| 3 | `Reporting` | June v1/v2 values and the governed restatement bridge |
| 4 | `Assurance` | Hermes reconciliation and Argus exception, kept distinct |
| 5 | `Governance` | Review, finding, issue, remediation, verification, readiness |
| 6 | `Decision` | Exact Pythia input/readiness pairing and deferred-hire effect |
| 7 | `Correction` | CT-1 source, reversal, replacement, and zero-net proof |
| 8 | `Trace` | Directed C-001 authority nodes, edges, and evidence status |
| 9 | `Checks` | Source, formula, relationship, measure, and parity checks |
| 10 | `Sources` | R/P/Q coordinates, hashes, owners, refresh metadata, limitations |
| 11 | `Data_Map` | Dataset ID to physical alias, worksheet alias, class, row count |
| 12 | `Measure_Map` | R-M01 through R-M12 and consumer-calculation register |

### 5.2 Imported data sheets

All thirty-one LINEAGE tables are embedded as exact source rows on dedicated
data sheets. Worksheet aliases are deterministic, unique, at most thirty-one
characters, and recorded in `Data_Map`. Their tables retain exact R column
order and typed values.

Imported data sheets:

- are hidden from ordinary navigation where the writer supports it;
- retain filters and frozen headers;
- use no formulas in governed columns;
- expose dataset ID, version, and registry coordinate in the map rather than
  appending them to domain rows; and
- remain inspectable by unhiding the sheet.

### 5.3 Workbook-owned calculations

The first workbook defines only these consumer calculations:

| ID | Label | Rule |
|---|---|---|
| S-XM01 | Reporting value major units | Exact R-M01 divided by 100 |
| S-XM02 | Restatement adjustment major units | Exact R-M02 divided by 100 |
| S-XM03 | Exception difference major units | Exact R-M04 divided by 100 |
| S-XM04 | Decision monthly cost major units | Exact R-M05 divided by 100 |
| S-XM05 | Correction net movement major units | Exact R-M06 divided by 100 |
| S-XM06 | Machine exception count | Count of exact P-D08 rows in selected scenario |
| S-XM07 | Directed trace node count | Count of exact P-D16 rows at selected reporting-value grain |
| S-XM08 | Directed trace edge count | Count of exact P-D17 rows at selected reporting-value grain |

Every calculation is formula-driven, visible in `Measure_Map`, and labelled
`Consumer calculation` in presentation sheets.

### 5.4 Workbook checks

The `Checks` sheet contains one row per assertion with:

```text
check_id
actual
expected
difference
tolerance
status
where_to_fix
notes
```

At minimum it proves:

- source model digest and profile match;
- thirty-one datasets and their row counts match the R manifest;
- all twelve R measures are represented;
- June v1 subscription revenue is GBP 0;
- June v2 subscription revenue is GBP 10,000;
- the governed bridge is GBP 10,000;
- v1 plus bridge equals v2 for the same statement field;
- the reconciliation and exception differences agree at GBP 10,000 without
  treating that agreement as a governance conclusion;
- readiness is `APPROVED` only for the exact hiring-forecast purpose and scope;
- the deferred-hire monthly cost is GBP 6,500;
- CT-1 reversal and replacement are individually balanced;
- CT-1 control-account net movement is GBP 0;
- authored and referenced journal populations remain separate; and
- all presentation formulas are free of formula errors.

## 6. Power BI semantic-model contract

### 6.1 Project structure

The canonical semantic project uses:

```text
FinanceAssurance.SemanticModel/
|-- definition.pbism
`-- definition/
    |-- database.tmdl
    |-- model.tmdl
    |-- expressions.tmdl
    |-- relationships.tmdl
    `-- tables/
        `-- one .tmdl file per R table
```

`definition.pbism` uses semantic-model definition version 4.0 or later and
selects TMDL. Power BI local cache and local settings remain ignored.

### 6.2 Partitions

Each table has one import-mode Power Query M partition. It reads only:

```text
ModelRootPath
+ exact R manifest parquet_path
```

The query applies no row filter, rename, type inference, join, fill, grouping,
or business calculation. TMDL columns retain the R display name separately
from `sourceColumn` where a friendlier label is used.

### 6.3 Columns

All 388 LINEAGE catalogue columns are present. Power BI data types derive only
from the R physical schema. Raw numeric columns use `summarizeBy: none`.
Technical columns and fields with R role `OMIT` are hidden. Keys, attributes,
metrics, enums, nullability, formats, and sorting remain aligned to Artifact R.

### 6.4 Relationships

The semantic model materializes the R load plan exactly:

- `ACTIVE` entries become active relationships;
- the one `INACTIVE_ROLE_PLAYING` entry remains inactive;
- `NAVIGATION_ONLY` and `VALIDATION_ONLY` entries are not model
  relationships; and
- every relationship uses single-direction filtering from the registered one
  side to the many side.

The model contains no bidirectional filter and no inferred same-name join.

### 6.5 Measures

R-M01 through R-M12 are model measures with their exact R IDs in annotations.
Each measure fails closed according to S-R10/S-R11.

S-XM01 through S-XM08 may also be present in a separate display folder named
`Consumer calculations`. Their descriptions state the source R measure or
dataset and the calculation rule.

### 6.6 DAX query proofs

The project includes source-controlled DAX queries that produce the same
claim rows used by Excel checks and `parity-results.json`. They cover C-001
reporting/restatement/readiness/decision and CT-1 correction integrity.

## 7. Cross-tool parity catalogue

Each parity claim contains:

```text
claim_id
scenario_ref
source_registry_id
source_dataset_id
source_row_key_or_filter
source_field_or_measure_id
currency
reporting_version_ref?
readiness_ref?
expected_typed_value
excel_location
power_bi_measure_or_query
classification = GOVERNED_SOURCE | REGISTERED_MEASURE | CONSUMER_CALCULATION
```

The v1 claims are:

| Claim | Expected result |
|---|---|
| S-PC01 | June v1 subscription revenue = GBP 0 |
| S-PC02 | June v2 subscription revenue = GBP 10,000 |
| S-PC03 | Governed restatement bridge = GBP 10,000 |
| S-PC04 | Recognition reconciliation difference = GBP 10,000 |
| S-PC05 | Recognition exception difference = GBP 10,000 |
| S-PC06 | Hiring readiness = APPROVED for exact purpose and scope |
| S-PC07 | Deferred-hire monthly cost = GBP 6,500 |
| S-PC08 | CT-1 correction net movement = GBP 0 |
| S-PC09 | J-011 debits equal credits at GBP 120,000 |
| S-PC10 | J-012 debits equal credits at GBP 120,000 |
| S-PC11 | Authored and referenced journal totals remain separate |
| S-PC12 | Trace terminates at exact evidence/reporting-content nodes |

## 8. Operations

### S-C01 - `BuildAnalyticalConsumerPack`

Request:

```text
contract_version = build-analytical-consumer-pack-request@v1
consumer_pack_ref
source_model_path
expected_model_digest
output_path
producer_release
built_at
excel_writer_profile_ref
power_bi_project_profile_ref
```

Rules:

1. source path and output path pass the Artifact R source/output firewall;
2. R-C02 verifies the exact source before consumer parsing;
3. the source is exactly `LINEAGE@v1` and `EXACT_ORIGINAL`;
4. the Excel and Power BI adapters consume the same in-memory verified model
   inventory;
5. each adapter is fully verified in staging;
6. parity claims are evaluated from source, Excel, and Power BI definitions;
7. the canonical checksum ledger and detached digest are written last; and
8. the verified directory is atomically renamed to a previously absent output.

### S-C02 - `VerifyAnalyticalConsumerPack`

Verification reruns R-C02 and proves:

- exact source and pack identity;
- closed file scope and checksum integrity;
- complete LINEAGE table/column/row admission;
- Excel logical workbook equivalence;
- Power BI TMDL structure, partitions, types, relationships, visibility, and
  measures;
- all parity claims;
- absence of external links, paid services, credentials, and runtime writes;
  and
- exact synthetic and bounded-depth disclosures.

### S-C03 - `ReproduceAnalyticalConsumerPack`

Reproduction requires the exact R model, writer profiles, producer release,
and build time. It reproduces every canonical text/JSON/checksum byte and
proves Excel logical equivalence. It never treats a changed source model as a
refresh of the same pack.

## 9. Canonical proofs

### 9.1 C-001

The consumer pack must show, without recomputation:

```text
June v1 subscription revenue GBP 0
-> reconciliation difference GBP 10,000
-> exception difference GBP 10,000
-> reviewed governance path
-> June v2 subscription revenue GBP 10,000
-> purpose-specific readiness APPROVED
-> exact decision input binding
-> deferred hire monthly cost GBP 6,500
```

The reporting, assurance, governance, readiness, and decision records remain
separate objects even when presented on one page.

### 9.2 CT-1

The consumer pack must show:

```text
wrong-customer source projection J-010
-> exact hash binding before comparison
-> reversal J-011, GBP 120,000 debit = credit
-> replacement J-012, GBP 120,000 debit = credit
-> control-account net movement GBP 0
-> remediation verified, not silently closed
```

J-010 stays referenced-only and is never unioned into the authored-journal
population.

## 10. Implementation phases

### Phase S1 - Shared consumer contracts

- strict S manifest, parity, writer-profile, request/result contracts;
- finite workbook sheet/table/formula map;
- finite Power BI table/partition/relationship/measure map;
- negative fixtures; and
- no `.xlsx` or TMDL output yet.

### Phase S2 - Excel workbook

- build the complete embedded LINEAGE workbook;
- formula-driven presentation and checks;
- workbook inspect, formula-error scan, finance audit, and visual render of
  every visible sheet; and
- logical reproduction proof.

### Phase S3 - Power BI semantic project

- build canonical TMDL and DAX query files;
- structural and semantic verification;
- machine-local path binding remains noncanonical; and
- manual Power BI Desktop open/refresh evidence where Desktop is available.

### Phase S4 - Cross-tool parity and cohesion audit

- evaluate S-PC01 through S-PC12;
- compare exact source, Excel result, and Power BI query/measure definitions;
- rerun P/Q/R verification and prior milestone gates; and
- ratify the implemented consumer pack before analytical React expansion.

### Phase S5 - Analytical React expansion

Separately define analytical pages that consume Artifact R and the S parity
catalogue. The web product must not depend on Excel, Power BI Desktop, or DAX.

## 11. Acceptance criteria

- S-A01: R-C02 passes before either adapter reads source rows.
- S-A02: the pack binds one exact LINEAGE@v1 model and exact source snapshot.
- S-A03: all thirty-one LINEAGE tables are admitted by both consumers.
- S-A04: all 388 LINEAGE catalogue columns retain exact source identity.
- S-A05: no governed row gains a consumer metadata field.
- S-A06: every raw integer column defaults to no summarization.
- S-A07: every amount retains integer minor units and exact currency.
- S-A08: major-unit presentation is labelled consumer calculation.
- S-A09: R-M01 through R-M12 retain exact semantic contracts.
- S-A10: exact-value measures fail closed outside one exact grain.
- S-A11: authored and referenced additive measures remain non-combinable.
- S-A12: Power BI relationships equal the R activation plan exactly.
- S-A13: Excel key usage is validated against the R relationship catalogue.
- S-A14: no bidirectional or inferred relationship exists.
- S-A15: technical keys remain hidden and non-business.
- S-A16: June v1, June v2, and the bridge remain simultaneous.
- S-A17: readiness retains exact purpose, scope, status, and limitations.
- S-A18: decision output retains exact reporting/readiness input binding.
- S-A19: evidence verification wording remains exact.
- S-A20: trace nodes and edges preserve direction and identity.
- S-A21: the Excel workbook has exactly the twelve visible sheets in section 5.
- S-A22: Excel embeds every admitted table with exact row and column order.
- S-A23: Excel presentation values are formulas, not copied constants.
- S-A24: Excel contains no macro, external workbook link, credential, or network
  dependency.
- S-A25: every required workbook check is visible and passes.
- S-A26: every visible workbook sheet is rendered and visually inspected.
- S-A27: the workbook contains no formula error in populated formula ranges.
- S-A28: Power BI contains one import partition per admitted table.
- S-A29: every Power BI partition reads only its exact R Parquet path.
- S-A30: Power BI applies no source-row transformation or filtering.
- S-A31: all Power BI columns have explicit type, source column, summarization,
  visibility, and formatting metadata.
- S-A32: the canonical Power BI project contains no machine-specific path.
- S-A33: local Power BI binding is excluded from canonical digests.
- S-A34: S-PC01 through S-PC12 pass against source and both adapters.
- S-A35: parity compares logical claims, not presentation equivalence.
- S-A36: the consumer manifest and checksum ledger have closed file scope.
- S-A37: build failure leaves no partial final pack.
- S-A38: an existing output is never overwritten.
- S-A39: exact canonical files reproduce byte-for-byte.
- S-A40: Excel reproduces logically; byte identity is claimed only if proved.
- S-A41: C-001 completes through reporting, assurance, governance, readiness,
  and decision without collapsing object classes.
- S-A42: CT-1 preserves referenced-only J-010 and exact reversal/replacement
  integrity.
- S-A43: no paid API, cloud service, secret, account, or network dependency is
  required.
- S-A44: all outputs disclose synthetic data and the bounded C-001/CT-1 depth.
- S-A45: existing P/Q/R verification and prior milestone gates remain green.
- S-A46: analytical React remains unimplemented until S1 through S4 pass.

## 12. Structural inventory and critique gate

Artifact S v0.1 contains exactly:

- twenty-six rulings, S-R01 through S-R26;
- one complete LINEAGE source coordinate;
- one Excel workbook contract;
- twelve visible workbook sheets;
- thirty-one embedded governed data tables;
- one Power BI TMDL semantic-model contract;
- twelve R measures and eight consumer calculations;
- twelve parity claims, S-PC01 through S-PC12;
- three operations, S-C01 through S-C03;
- five implementation phases; and
- forty-six acceptance criteria, S-A01 through S-A46.

Before ratification, critique must test:

1. whether the workbook can embed all LINEAGE tables without becoming an
   unusable thirty-plus-tab artifact;
2. whether every Excel formula can fail closed at the exact registered grain;
3. whether the Power BI relationship plan is mechanically derivable without
   introducing a second topology;
4. whether the TMDL project can remain portable while local Parquet paths are
   machine configuration;
5. whether all R measures have executable Excel and DAX translations;
6. whether S-PC01 through S-PC12 are sufficient to catch cross-tool semantic
   drift;
7. whether `.xlsx` logical reproduction is defined strongly enough; and
8. whether any consumer-owned calculation is presented too close to a governed
   source value.

No Excel workbook, Power BI project, or analytical React page is implemented
until this artifact is critiqued, corrected, and ratified.
