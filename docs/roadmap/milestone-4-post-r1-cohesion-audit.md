# Milestone 4 Post-Phase-R1 Cohesion Audit

Status: PASSED - no unresolved blocker

Date: 2026-08-13

## 1. Scope

This audit tests the bounded Artifact R Phase R1 implementation against:

- Artifact R v0.2 and ADR-038;
- the implemented `P-EVIDENCE@v1` and `Q-ANALYTICS@v1` registries;
- relationship contract v2;
- the complete 37-dataset and 427-source-column inventory;
- the exact composite-key, relationship-topology, and measure rulings;
- the pinned Parquet writer-profile contract; and
- the requirement that R1 remain metadata-only.

It does not assess Parquet bytes, model publication, DuckDB, Excel, Power BI,
or analytical React behavior because none is implemented in Phase R1.

## 2. Implemented Boundary

Phase R1 adds `finance_assurance.digestion` with:

- strict immutable build, verify, reproduce, manifest, table-binding,
  catalogue, relationship, measure, and writer-profile contracts;
- cumulative CORE, LINEAGE, and DIAGNOSTIC profile registries;
- a derived but closed role and visibility entry for every P/Q source column;
- the exact physical type map;
- eight deterministic composite relationship-key definitions;
- one finite relationship-disposition plan per profile;
- twelve measure definitions with grain, currency, version, population, and
  non-combination guards;
- Artifact P canonical JSON relationship-key hashing and collision detection;
- a dependency-locked PyArrow writer profile; and
- positive and negative fixtures.

No build service or adapter exists. R1 imports metadata definitions only and
does not read a governed package, runtime repository, database, or source row.

## 3. Structural Results

```text
source registries             2 (P-EVIDENCE@v1, Q-ANALYTICS@v1)
source datasets               37
CORE datasets                 26
LINEAGE datasets              31 cumulative
DIAGNOSTIC datasets           37 cumulative
source columns                427
source physical types         7
enum columns                  32
raw integer columns           50, all default summarization NONE
R technical placements        16 (8 relationships x 2 endpoints)
composite key definitions     8
shared measures               12
DIAGNOSTIC relationships      64
active relationships          33
inactive role-playing         1
navigation-only               18
validation-only               12
active cycles                 0
duplicate active paths        0
```

The source-role distribution is:

```text
DOMAIN_ATTRIBUTE       201
DOMAIN_KEY              87
DOMAIN_MEASURE_INPUT    12
EVIDENCE_ATTRIBUTE      35
SOURCE_TECHNICAL        92
```

The sixteen endpoint placements are separately classified `R_TECHNICAL` and
hidden. They do not enter the 427-source-column count.

## 4. Profile and Relationship Closure

| Profile | Total relationships | Active | Inactive role | Navigation | Validation |
|---|---:|---:|---:|---:|---:|
| CORE | 49 | 27 | 1 | 17 | 4 |
| LINEAGE | 57 | 30 | 1 | 18 | 8 |
| DIAGNOSTIC | 64 | 33 | 1 | 18 | 12 |

Every relationship is copied from P/Q metadata and receives one disposition
only when both required endpoints are present. The active graph is checked in
the one-to-many filter direction. Positive tests prove the ratified plan;
negative tests prove rejection of cycles and duplicate directed paths.

All eight composite definitions resolve exact source endpoint types and widths.
The technical key is SHA-256 over Artifact P canonical JSON including its
terminating LF. Tests reject null, absent-width, mistyped, and collision cases.

## 5. Semantic and Measure Closure

All 427 source fields preserve their P/Q type, nullability, enum values,
origin, and transformation and receive exactly one R role, visibility, and
`NONE` summarization setting. No source field is classified `NOT_LOADED`.

The twelve measures resolve exact existing dataset fields. R-M01 through R-M08
use `SELECT_EXACT` and reject ambiguous row context. R-M09 through R-M12 require
scenario and currency grouping, identify themselves as gross activity, and
keep authored and referenced journal populations mutually non-combinable.

No derived statement, balance, KPI, ratio, signed net, or major-unit value is
introduced.

## 6. Writer Binding

PyArrow 25.0.0 is exact in `pyproject.toml` and `uv.lock`. Runtime validation
checks the installed version and confirms every option in the 26-entry preset
is accepted by `pyarrow.parquet.write_table`.

```text
writer profile  PYARROW-25@v1
profile hash    sha256:2702aa8812844e508d5b303c50b52e30ab9f20cf7b65c42c2d59f39171b85cb1
options hash    sha256:2642b3ea3f71badfff44760005b01ed1f80f9a571d823dc99fa6ef78f432b862
```

The profile-hash preimage includes the complete option-preset hash. A
byte-affecting option therefore cannot change while retaining the advertised
profile hash. No canonical Parquet fixture or Parquet file is written in R1.

## 7. Audit Findings and Remediation

### Finding R1-F01 - Writer profile did not initially bind its option preset

The first implementation hashed the visible profile fields and tested the
writer options separately. An option change could therefore have retained the
same profile hash.

Resolution: the complete option preset now has its own fixed hash, and that
hash participates in the profile-hash preimage. Runtime validation checks both.

### Finding R1-F02 - Metadata import crossed the public-product package root

The first implementation inherited R's base contract from Artifact O and P's
package root eagerly imported its public surface. This did not mutate state,
but it made a metadata-only R import load unnecessary product-layer modules.

Resolution: R owns a local strict Pydantic base. Artifact P retains the same
public names through lazy package exports. A fresh-process regression test
proves importing `finance_assurance.digestion` loads neither
`finance_assurance.product` nor runtime persistence.

### Finding R1-F03 - Revision-bound product review exposed tablet overflow

The post-commit connected-browser review found that the Atlas reporting-version
screen could exceed the 768-pixel tablet viewport. The data contract and value
trace remained correct; the shared screen stack allowed a child grid's minimum
content width to escape its container.

Resolution: the shared screen stack and its direct children now permit bounded
shrinkage with `min-width: 0`. A static regression assertion protects the
shared rule, and all ten public routes now pass the connected review at desktop,
tablet, and mobile widths without root-level horizontal overflow.

All three findings are closed. None changed an Artifact R business contract.

## 8. Regression Evidence

```text
R1 focused tests                         25 passed
R/P/Q focused compatibility tests        38 passed
complete Python inventory               248 tests collected and passed
Ruff                                      PASS
P package build                           PASS
P offline verification                    VERIFIED
P byte reproduction                       REPRODUCED
Q analytical package build                PASS
Q offline verification                    VERIFIED
Q byte reproduction                       REPRODUCED
frontend ESLint                           PASS
frontend TypeScript                       PASS
frontend deterministic build              PASS
rendered public-route tests               10 passed
connected route/viewport combinations     30 passed
```

The governed-output acceptance command returned `overall_status = PASS`.
Artifact R introduced no paid API, credential, hosted dependency, network
runtime, DuckDB dependency, or public route.

## 9. Judgment

Phase R1 passes its cohesion audit with no unresolved blocker.

The implementation lays a safe foundation for Excel and Power BI because both
will receive the same profile, field, relationship, key, and measure semantics.
It does not yet claim that any consumer model exists.

The next authorised work is Phase R2 only:

1. verify and bind one exact P-plus-Q source package;
2. parse source CSV strictly from P/Q schemas;
3. materialize deterministic Parquet and tool-neutral catalogues;
4. publish atomically; and
5. complete the mandatory post-R2 cohesion audit.

DuckDB remains Phase R3. Excel, Power BI, and analytical React remain blocked
until the separately ratified consumer boundary after R2.
