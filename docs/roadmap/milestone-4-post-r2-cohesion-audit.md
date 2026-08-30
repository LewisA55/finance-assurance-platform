# Milestone 4 Post-Phase-R2 Cohesion Audit

Status: passed 2026-08-13

## 1. Scope

This audit evaluates the bounded Artifact R Phase R2 implementation against
Artifact R v0.2, ADR-038, the Phase R1 registries, one exact verified
`P-EVIDENCE@v1` plus `Q-ANALYTICS@v1` package, and the unchanged C-001 and CT-1
reference cases.

Phase R2 implements only R-C01 staged model construction, R-C02 full source-
equivalence verification, R-C03 deterministic reproduction, byte-identical
selected schema and optional CSV copies, deterministic Parquet, tool-neutral
catalogues, and the three ratified profiles. DuckDB, Excel, Power BI, and
analytical React remain outside this phase.

## 2. Exact Source and Snapshot Binding

The builder invokes P-C02 before reading a CSV and rejects anything other than
an exact verified two-registry package using relationship contract v2 and
`EXACT_ORIGINAL` compatibility. The model manifest binds the source digest,
export reference, query revision, semantic-as-of time, scenario-set digest,
registry coordinates, relationship version, verification contract, and
synthetic-data notice.

R-C02 reruns P-C02 and compares all coordinates to the source manifest. The
package may move to another local directory without changing identity; path text
is not a semantic coordinate.

## 3. Physical and Semantic Closure

All three cumulative profiles build and verify:

```text
CORE        26 tables
LINEAGE     31 tables
DIAGNOSTIC  37 tables
```

Every selected source schema is copied byte-for-byte. CSV is copied only when
requested. Parquet retains source columns in exact P/Q order, adds only
applicable hidden `_r_hk_*` columns in relationship-ID order, preserves
`row_key ASC`, and maps amounts to signed `int64` without float conversion.

The semantic catalogue carries source coordinates, deterministic portable
aliases, owners, profile classes, exact column order, all source and technical
column semantics, the relationship plan, and all in-profile guarded measures.
Domain rows contain no worksheet, Power BI, React route, refresh, or model-build
metadata.

## 4. Relationship and Measure Safety

The R1 registries remain the only executable source. R2 projects all eight
composite keys where endpoints exist, retains original components, checks
collision absence, and publishes no inferred relationship. Every profile plan
passes cycle and duplicate-path rejection. Raw integer summarization remains
`NONE`; authored and referenced journal measures remain non-combinable.

Readiness, limitations, evidence status, reporting history, directed trace, and
authored-versus-referenced journal separation remain in their original P/Q
datasets and are related rather than duplicated.

## 5. Reproduction and Atomicity

The checksum ledger binds every selected schema, optional CSV, Parquet table,
catalogue, manifest, and README. The detached model digest binds that ledger.
Reproduction rebuilds through R-C01 and proves every canonical file byte is
identical.

Builds use a unique staging directory under the final parent, run R-C02 before
publication, reject overwrite, and publish by one same-filesystem rename.
Writer failure removes staging and leaves no final model.

## 6. Findings and Remediation

### R2-F01 - Semantic tables lacked the required portable alias

The first implementation reused R1's coordinate-only placeholder for
`SemanticCatalogue.tables[]`. That was insufficient for R-R24 because future
consumers would have been forced to derive their own physical aliases.

Resolution: `SemanticTable@v1` now carries the source coordinate, portable
alias, display label, profile class, owners, row ordering, and exact source-plus-
technical column order. R-C02 reconstructs and compares the catalogue.

### R2-F02 - Full verification needed stronger coordinate closure

The first R-C02 pass verified source digest and file equality but did not
explicitly compare every snapshot coordinate or reconstruct every expected
table path and binding field.

Resolution: R-C02 now compares the source export reference, query revision,
semantic-as-of time, scenario digest, synthetic notice, canonical file scope,
table paths, identities, owners, classes, keys, hashes, and profile membership.
A resealed Parquet domain-value mutation still fails source equivalence.

### R2-F03 - Windows retained Parquet resources across publication

Workspace-drive validation found that filesystem-backed Parquet reads could
leave a transient Windows handle after staged verification. Verification passed,
but the atomic directory rename was intermittently denied.

Resolution: R-C02 reads Parquet from owned bytes and the publisher retries only
the same atomic rename on bounded `PermissionError`, with collection and a short
increasing delay. No copy/delete fallback or partial publication is permitted.

### R2-F04 - Output location needed an explicit source-package firewall

The initial application service resolved the input and output paths but did not
reject a final output nested inside the governed source package. Such a request
could have created staging content under P+Q before later verification failed.

Resolution: R-C01 resolves both paths before creating any directory and rejects
an output equal to or below the source-package root. A regression test proves no
staging or final path appears inside the governed package.

All four findings are closed. None changes an upstream P/Q domain contract.

## 7. Evidence

```text
Artifact R tests                         41 passed
R/P/Q compatibility tests               59 passed
complete Python inventory               263 passed
Milestone 4 acceptance                  PASS
P package verification                  VERIFIED
P package reproduction                  REPRODUCED
Q package verification                  VERIFIED
Q package reproduction                  REPRODUCED
LINEAGE model verification              VERIFIED
LINEAGE model reproduction              REPRODUCED
local LINEAGE tables                    31
local LINEAGE source rows               189
local LINEAGE catalogue columns         388
local LINEAGE relationships             57
local canonical files                   99
local model digest                      sha256:0dd800d079bb1e9d6f68667614e12057763c52aa190ff7c1619623dc1809fef4
```

The acceptance report carries R-A01 through R-A48 beside the existing P and Q
catalogues.

## 8. Judgment

Phase R2 passes its cohesion audit with no unresolved blocker.

The model-digestion boundary is now ready for a separately designed consumer:
one exact governed package, one shared typed table set, one relationship plan,
one measure registry, and one reproducible local materialization.

The next authorised work is Phase R3 optional DuckDB acceleration or a new
consumer-design artifact. Excel, Power BI, and analytical React still require
their own bounded design decision.
