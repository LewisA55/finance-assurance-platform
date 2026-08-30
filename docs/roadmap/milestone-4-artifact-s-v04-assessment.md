# Artifact S v0.4 Structural and Semantic Reassessment

Status: NOT RATIFIABLE - bounded v0.5 correction required

Date: 2026-08-19

## 1. Scope and method

This independent reassessment tests
`docs/product/local-analytical-handoff.md` v0.4 against:

- the five blocking findings in the v0.3 reassessment;
- the implemented and audited Artifact R Phase R3 cache boundary;
- the exact P-plus-Q and R `LINEAGE@1` inventories;
- package, digest, XLSX, metadata, validation, operation, failure, and fixture
  closure;
- C-001 and CT-1 source semantics; and
- the rule that S must stop before React, an Excel analytical model, or a
  Power BI semantic model.

The result is mixed. Artifact S v0.4 preserves the right product boundary and
closes the external R3 prerequisite. Its declared structure is internally
consistent, and its C-001/CT-1 intent remains faithful. Four bounded
executable-contract blockers remain. No blocker requires new domain data, a
dashboard, a financial model, DAX, TMDL, or a paid dependency.

## 2. Mechanical and implementation evidence

The declared v0.4 inventory is mechanically consistent:

```text
32 rulings                    S-R01 through S-R32
1 package tree                one embedded complete R model
2 path classes                canonical and noncanonical
3 verification claims        canonical bytes, same-build binary, logical
4 representations            R CSV, R Parquet, R DuckDB, S XLSX
8 metadata files              including the validation registry
12 validation checks          S-V01 through S-V12
29 declared assertions        1+1+1+1+1+6+2+2+2+2+6+4
3 operations                  S-C01 through S-C03
20 failure codes              one closed lexical list
22 negative fixtures          S-NF01 through S-NF22
58 acceptance criteria        S-A01 through S-A58
```

The document is ASCII, uses LF line endings, and has no trailing whitespace.
The package tree contains no React, Power BI, dashboard, report, forecast,
valuation, or financial-model output.

The exact path arithmetic also reconciles:

```text
99 R canonical files, including the R ledger and detached digest
+ 13 S-owned canonical payload files
= 112 S canonical-ledger paths
+ 4 noncanonical paths: 2 R cache files and 2 S workbook files
+ 2 S detached-integrity files
= 118 physical files
```

The focused R3 suite independently passed all six cache tests. It proves the
strict cache manifest, read-only cache, domain-divergence rejection, unknown-
object rejection, binary/manifest tamper rejection, atomic writer failure, and
R-C03 reproduction behavior required by S.

The three literal profile hashes also match the values printed in v0.4 when
computed from the apparent intended profile bodies:

```text
XLSX-TYPE-MAP@v1
sha256:41b42f86d6620e042e1137b352fee44018ecfa34b980fb4bca4f33eeb71e48dd

XLSXWRITER-3.2.9@v1
sha256:1a7dc795c0f09c22db462051c1190cf8b86dea7f03c6e79b4990fa1637c15f76

S-GRID-RENDERER-PILLOW-12.3.0@v1
sha256:fb2c4d41ea4ec9baa0c0eae9abe69cdb5ab606123b1ff3249a949c928e9c0fd6
```

This proves the printed hash arithmetic under that inferred representation. It
does not close the missing serialized preimage contracts recorded in S4-B01.

## 3. v0.3 blocker closure

| v0.3 blocker | v0.4 result | Judgment |
|---|---|---|
| S3-B01 - required R3 source contract absent | R3 is implemented and audited. S resolves the database path through verified `duckdb-cache-manifest@v1` and delegates build, verification, and reproduction to R. | CLOSED |
| S3-B02 - XLSX writer and renderer not pinned | Literal type-map, writer, and external renderer coordinates now exist. Render evidence is correctly external, and naming/capacity rules are substantially closed. The exact serialized profile and logical-workbook preimages remain unstated. | PARTIAL |
| S3-B03 - metadata provenance and nested schemas open | Field-level value/array-order provenance and several strict nested models now exist. Row-value provenance cannot use the JSON-only source pointer, and the consumer-suitability registry and some nested payload content remain unenumerated. | PARTIAL |
| S3-B04 - validation schema cannot encode the registry | Ordered discriminated assertions can now represent field, set, and graph proofs. The actual twenty-nine assertion instances are not defined or validated; they are deferred to the future output that they are meant to govern. | PARTIAL |
| S3-B05 - operations not strict serialized contracts | Top-level request/result fields, versions, counts, claims, failure vocabulary, and fixture IDs are much stronger. Success results, failed results, serialized operation failures, and reproduction statuses still have no one closed dispatch and mapping. | PARTIAL |

R3 is therefore no longer a blocker. The other four v0.3 blockers improved but
are not yet executable end to end.

## 4. Blocking findings

### S4-B01 - Profile and logical-workbook digest preimages are not closed

Sections 6.3, 6.4, and 6.6 publish literal hashes and enough prose to infer the
three bodies used above. They do not define those bodies as strict serialized
models with exact keys, nesting, ordering, canonicalization, and hash-exclusion
rules. For example, the type-map preimage is described as the mapping plus
three values, while the writer table uses descriptive rows such as
`storage-mode widths` rather than one exact JSON field shape. The renderer has
the same issue.

More importantly, `logical_workbook_digest` names an ASCII JSON preimage and
describes its content, but does not define:

- an exact contract version and complete field list for the preimage;
- the discriminated typed-cell representation;
- the exact typed-row preimage and digest function;
- metadata-sheet row contracts and canonical row order; or
- whether data-sheet row digests reuse one exact R digest or construct a new S
  digest over source plus technical columns.

Two implementations can therefore emit different valid-looking profile or
workbook logical digests from the same R model. S-C02 and S-C03 cannot
independently reconstruct one uniquely governed logical claim.

Required repair:

1. define strict `XlsxTypeMapProfile@v1`, `XlsxWriterProfile@v1`, and
   `AuditRendererProfile@v1` serialized bodies;
2. state the exact canonical hash function and excluded hash field for each;
3. define `LogicalWorkbookDigestPreimage@v1`, typed-cell variants, sheet-entry
   variants, typed-row preimages, and their exact ordering; and
4. add positive hash vectors and one mutation vector per hashed field family.

### S4-B02 - Metadata provenance cannot bind governed row values

`SourcePointer@v1` can address only a JSON document through an RFC 6901 pointer.
That is sufficient for the R manifest and catalogues. It cannot address a value
in canonical CSV, typed Parquet, or DuckDB.

`validation-checks.json` nevertheless contains upstream selectors and expected
row values. The shared envelope requires exactly one provenance entry for every
scalar payload leaf. Those governed values cannot truthfully be marked as an R
copy or projection through the JSON-only source pointer. Marking them as
`S_GUIDANCE` would incorrectly make S the authority for P/Q row values.

The same section names a closed `S-CONSUMER-SUITABILITY@v1` registry but never
enumerates its permitted use IDs, required-expansion IDs, or exact four consumer
entries. Some source-binding payload items, including `table_entries[]`, are
also named without a complete strict item model. Two builders can therefore
emit different payloads while claiming the same contract and algorithm.

Required repair:

1. add a strict source-cell pointer variant containing exact dataset
   coordinate, typed selector, source field, and bound source file/digest;
2. require governed expected values to use that row-addressable R projection,
   never `S_GUIDANCE`;
3. enumerate the complete consumer-suitability registry and four exact entries;
4. define every remaining payload item as one strict versioned model; and
5. add missing, extra, overlapping, unresolved, and wrong-authority provenance
   fixtures.

### S4-B03 - The twenty-nine validation assertions do not exist as a contract

Section 8 defines a materially better assertion union and gives twelve IDs,
counts, and prose summaries. It then says the exact selectors, evidence refs,
relationship IDs, result schemas, and ordering are fixture-bound in
`validation-checks.json`.

That file is a future S output, not an independent design input or checked-in
contract fixture. It cannot govern its own derivation. The v0.4 text does not
enumerate the twenty-nine assertion IDs, assertion kinds, selectors, typed
expected values, currency bindings, measure IDs, relationship IDs, evidence
refs, result columns, result order, or query IDs. The statement that all
twenty-nine assertions validate against the union is therefore an assertion,
not a reproduced proof.

This blocks deterministic metadata generation, finite SQL generation, S-A42,
and independent validation that composite checks do not calculate or upgrade a
governance conclusion.

Required repair:

1. place the complete twenty-nine-instance registry in the design or one
   checked-in pre-implementation contract fixture;
2. validate every instance against the discriminated schema before S1;
3. publish exact expected canonical registry bytes and digest;
4. generate the twelve SQL queries and exact result schemas from that registry;
   and
5. prove each query selects registered authorities rather than recomputing a
   substitute conclusion.

### S4-B04 - Operation failure signaling has competing models

S-C01 says failure raises serialized `HandoffOperationFailure@v1`. S-C02
instead returns a `FAILED` verification result. S-C03 returns one of several
domain statuses plus a failure code. Section 10 then defines one operation-
failure model for S-C01, S-C02, and S-C03 without saying which condition is
returned and which is raised.

There is also no exact status/code/phase matrix. For example, S-C03 has status
`WRITER_PROFILE_UNAVAILABLE`, while the shared failure code is
`XLSX_PROFILE_UNAVAILABLE`; source-handoff verification can fail for inventory,
metadata, SQL, or XLSX reasons without a corresponding reproduction-status
mapping. The general rule that every non-success status has one code does not
select that code or settle nullability and cleanup for each branch.

An implementation must therefore invent its public failure channel and parts
of its status mapping, contrary to the strict operation requirement.

Required repair:

1. choose one explicit outcome union or one exception boundary per operation;
2. define the exhaustive status/failure-code/phase/final-path-state matrix;
3. close nullable digest, count, claim, message, and cleanup rules per branch;
4. align reproduction status names with the shared failure vocabulary; and
5. bind every negative fixture to the exact serialized outcome or exception.

## 5. Semantic scenario reassessment

### 5.1 C-001

The semantic claims remain correct:

- P-D06 preserves June v1 at `0` and June v2 at `1000000` minor GBP as separate
  reporting-version rows;
- P-D07/R-M02 remains the `1000000` minor GBP bridge authority;
- P-D04/R-M03 and P-D08/R-M04 retain their exact difference fields without
  becoming a finding, issue, or approval;
- P-D10 readiness remains purpose, version, and scope specific and stays bound
  to P-D15 bases and P-D20 limitations; and
- P-D11/R-M05 retains the `650000` minor GBP deferred-hire monthly effect and
  exact readiness reference.

S adds no DCF, three-statement model, forecast, executive KPI, or new readiness
conclusion. C-001 semantic intent passes. Its executable S proof remains blocked
by S4-B02 and S4-B03.

### 5.2 CT-1

The semantic claims also remain correct:

- P-D13/R-M06 retains zero control-account net movement and
  `BOUND_BEFORE_COMPARE`;
- Q-D04/R-M07/R-M08 retains J-011 and J-012 as separate authored journals with
  `12000000` minor GBP debit and credit totals each;
- Q-D08/Q-D09 retains J-010 only as referenced pre-scope state; and
- P-D16/P-D17 preserves directed node, edge, terminal, and evidence-status
  semantics.

S does not infer issue closure from balanced journals, verified remediation, or
package integrity. CT-1 semantic intent passes. Its executable S proof remains
blocked by S4-B02 and S4-B03.

### 5.3 Authority and consumer boundary

No new domain value, truth level, relationship, measure, status, or consumer
calculation has leaked into v0.4. CSV, Parquet, and DuckDB remain R-owned; XLSX
is a reversible S projection; metadata remains intended as guidance and
projection; and React, Excel modelling, and Power BI modelling remain later
independently governed workstreams.

The remaining authority risk is mechanical, not conceptual: unresolved
provenance and self-defining validation fixtures could let an implementation
mistake S-authored constants for governed upstream facts.

## 6. Bounded v0.5 correction sequence

The correction order is:

1. close the three profile bodies and logical-workbook digest preimages;
2. add row-addressable upstream provenance and enumerate every remaining
   metadata registry/item;
3. publish and schema-validate all twenty-nine concrete assertion instances;
4. generate and inspect all twelve exact SQL/result contracts from that finite
   registry;
5. unify operation failure channels and publish the exhaustive status matrix;
6. add the required positive, mutation, provenance, registry, and operation
   fixtures; and
7. repeat the structural and semantic reassessment before ratification.

R3 must not be redesigned or moved into S. The package tree, product boundary,
Excel naming/capacity rules, external render-evidence role, C-001/CT-1 values,
and no-consumer-output boundary should survive unchanged.

## 7. Verdict

Artifact S v0.4 is not ratifiable as written.

The structural inventory, path arithmetic, R3 binding, product boundary,
literal profile coordinates, Excel naming/capacity rules, external visual-audit
role, negative-fixture catalogue, and C-001/CT-1 semantic intent are sound.

Four bounded blockers remain:

1. profile and logical-workbook digest preimages are not strict serialized
   contracts;
2. metadata provenance cannot address governed row values and some finite
   registries remain unenumerated;
3. the claimed twenty-nine validation instances are absent and self-deferred to
   the future output; and
4. the three operations expose competing, unmapped failure channels.

No Artifact S implementation, handoff, XLSX data pack, or ratification ADR is
authorised until a bounded v0.5 closes all four and passes another independent
reassessment.
