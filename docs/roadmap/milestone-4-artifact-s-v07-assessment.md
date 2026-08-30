# Artifact S v0.7 Structural and Semantic Reassessment

Status: RATIFIABLE - no blocking findings

Date: 2026-08-20

## 1. Scope and method

This independent reassessment tests
`docs/product/local-analytical-handoff.md` v0.7 against:

- S6-B01 and the bounded v0.7 correction sequence;
- every checked-in canonical, validation, workbook-vector, failure-state,
  mutation-recipe, and negative-fixture authority;
- the implemented and audited Artifact R Phase R3 boundary;
- a fresh P-plus-Q package and `LINEAGE@1` model with CSV, Parquet, and the
  R-owned DuckDB cache;
- all five starter queries, twelve reconciliation queries, and twenty-nine
  registered assertions; and
- C-001, CT-1, R3 ownership, and the no-consumer-implementation boundary.

No implementation code was added while reaching this verdict.

## 2. Independent mechanical evidence

The complete v0.7 authority reconciles:

```text
32 rulings                         S-R01 through S-R32
58 acceptance criteria            S-A01 through S-A58
9 checked-in authority files      exact ASCII/LF file hashes reproduce
6 parsed-object hashes            all reproduce
3 pinned profile hashes           type map, writer, and audit renderer
8 workbook digests                2 positive plus 6 mutation vectors
90 checkpoints                    unique ordinals 1 through 90
28 state vectors                  unique and fully referenced
10 digest-presence vectors        unique and fully referenced
80 admissions                     unique six-field tuples
80 human-matrix triples           exact machine-authority projection
41 negative fixtures              S-NF01 through S-NF41
34 fixture-covered admissions     explicit tested subset
20 failure codes                  all directly fixture-covered
41 executable mutation recipes    one per fixture reference
19 mutation operators             exact operator-contract closure
```

Every admission resolves one checkpoint whose operation and phase match the
admission, one complete state vector, and one complete digest-presence vector.
Every fixture resolves exactly one admission and one recipe. Fixture claim,
cleanup, source-path, and output-path states equal the admitted vector. Recipe
operation, request mutation, and first-failure checkpoint equal the fixture,
and every application checkpoint precedes the expected failure checkpoint.

The serializer rule is closed by exact six-field membership. Every registered
tuple is admitted; substitutions outside any closed field vocabulary are not
members and therefore fail. The Markdown matrix projects exactly the same
eighty code, operation, and phase triples and is not a second authority.

The external Arial asset is present at the declared ratification-environment
path and reproduces its pinned hash:

```text
sha256:b3658eadae55e682b5f69eb64c439c1ecc8f196c0bb8d4756d145d13bc86476a
```

Both positive workbook preimages and all six value, type, order, count,
source-digest, and storage-mode mutations reproduce their expected digests.
The count and storage-mode mutations retain their declared contract-rejection
outcomes.

## 3. Fresh upstream and SQL evidence

A fresh governed P-plus-Q package and 31-table `LINEAGE@1` model were built
through the ordinary services. The model included canonical CSV and Parquet
plus the R-owned DuckDB cache. R-C02 `FULL_SOURCE_EQUIVALENCE` returned
`VERIFIED` with:

```text
31 tables
189 source rows
99 canonical R files
2 noncanonical R cache files
```

All fixed SQL authorities executed read-only against that cache:

```text
S-QS01 rows  4
S-QS02 rows  1
S-QS03 rows  1
S-QS04 rows  2
S-QS05 rows 58

S-QV01 through S-QV12       PASS
registered assertion columns 29
true assertion columns        29
```

The complete R2/R3 service regression also passed: 19 tests in 52.01 seconds.

## 4. S6-B01 closure

S6-B01 is closed.

The checkpoint registry removes phase-level timing ambiguity. The state and
digest-presence registries determine every public failure field for all eighty
admissions rather than only the fixture-covered subset. The executable recipe
authority fixes target resolution, before-state, mutation, resealing, request
change, earliest failure, and cleanup for all forty-one negative fixtures.
No operation implementation must invent an admission, state, or recipe.

## 5. Semantic and ownership reassessment

C-001 passes unchanged: June v1 remains GBP 0; the gap, bridge, exception, and
June v2 remain GBP 10,000; readiness remains purpose-specific with its exact
basis and empty limitation set; and the decision retains the GBP 6,500 monthly
effect without becoming a new planning or valuation conclusion.

CT-1 passes unchanged: J-010 remains referenced-only; J-011 and J-012 remain
distinct authored, balanced GBP 120,000 journals; the control-account net
movement remains GBP 0; and verified remediation is not treated as issue
closure.

R remains the only CSV, Parquet, and DuckDB materializer. S has no DuckDB
writer. XLSX remains a data-only S projection. Measures remain specifications,
and no React dashboard, Excel financial model, Power BI semantic model, DAX,
TMDL, report, forecast, or valuation has entered source or tests.

## 6. Verdict

Artifact S v0.7 is ratifiable as written. No blocking or advisory correction
is required before implementation.

Ratification may authorize Phase S1 only: strict operation and metadata
contracts, exact profiles and digests, fixed-authority loaders, the complete
failure-admission validator, executable mutation operators, and all negative
fixtures. It does not authorize handoff publication, XLSX emission, or any
consumer implementation; those remain gated by the later S phases and S4
cohesion audit.
