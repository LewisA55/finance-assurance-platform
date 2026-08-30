# Milestone 4 Post-Evidence-Package Cohesion Audit

Status: PASS - implementation cohesion closed under ADR-036

Date: 2026-08-13

## 1. Scope

This audit reviews the implemented `P-EVIDENCE@v1` package after Artifact P
Phases 1 through 3 and before any governed analytical registry, Excel workbook,
Power BI model, or wider synthetic population is authorised.

The audit covers:

- P-Q00 discovery and its fifteen-query Artifact O plan;
- the one-session/fresh-reader snapshot boundary;
- P-D01 through P-D21 field provenance and semantic ownership;
- canonical JSON, canonical CSV, manifest, checksums, and package digest;
- standard, conditional, polymorphic, and directed-graph relationships;
- offline verification, failure atomicity, and exact reproduction;
- C-001 and CT-1 semantic parity;
- dependency direction and absence of direct persistence access; and
- inherited Milestone 1 through 3 behavior.

## 2. Implemented Boundary

The implementation is confined to:

```text
governed_outputs.py
src/finance_assurance/exports/
tests/exports/
```

One narrow addition to Artifact O permits a caller-owned immutable query
session while still creating a fresh `_PinnedReader` for every invocation.
Artifact P does not import SQLite, validation fixtures, HTTP adapters, web code,
or module command services. SQLite appears only in the local composition root
that materialises the already-ratified synthetic demo.

## 3. Contract Inventory

The executable registry contains exactly:

- one `P-EVIDENCE@v1` registry;
- twenty-one datasets, P-D01 through P-D21;
- sixteen query-execution rows: P-Q00 plus fifteen Artifact O invocations;
- one manifest and one relationship registry;
- twenty-one strict schema documents;
- twenty-one canonical CSV datasets;
- one checksum ledger and detached package digest; and
- no analytical registry or unregistered file.

Every schema column declares its type, nullability, enum where applicable,
value origin, exact source path where applicable, and transformation. Composite
views retain multiple semantic owners and one export steward.

## 4. Semantic Findings

### 4.1 Snapshot and source closure - PASS

P-C01 opens one query session. P-Q00 binds the exact session revision and
semantic time. Every O invocation uses a fresh reader, so P-D19 contains only
that invocation's authoritative sources. P-Q00 has no P-D19 rows and claims no
semantic authority.

### 4.2 Reporting and readiness - PASS

June v1 and v2 remain separate P-D05 rows. P-D06 retains exact integer-minor
values and verification status. P-D07 copies the GBP 10,000 restatement bridge
from O-V04. P-D10 preserves purpose-specific readiness, P-D15 preserves its
bases, and P-D20 preserves its limitations. The Pythia decision retains the
exact readiness and reporting-version bindings.

### 4.3 Evidence and traceability - PASS

Content verification status is copied without promotion. P-D16 and P-D17 retain
the exact J-P11 node identity, nullable semantic hash, edge direction, and
relationship. The verifier checks both directed endpoints and does not infer a
reverse edge.

### 4.4 CT-1 correction integrity - PASS

CT-1 exposes the referenced-state correction case without inventing readiness
or Pythia rows. The package retains `BOUND_BEFORE_COMPARE`, distinct reversal
and replacement journal summaries, corrected customer identity, balanced
journals, and GBP 0 control-account net movement.

### 4.5 Dependency direction - PASS

The export implementation depends on public Artifact O contracts and the
abstract persistence query port only. It contains no direct state, SQL, SQLite,
fixture, HTTP, web, credential, paid API, or runtime network access. The local
launcher owns the SQLite composition decision and does not move it into the
package boundary.

## 5. Failure and Attack Proofs

The executable suite proves:

- missing declared file -> `MISSING_FILE`;
- unregistered file -> `UNREGISTERED_FILE`;
- one-byte mutation -> `HASH_MISMATCH`;
- resealed broken trace relationship -> `RELATIONSHIP_VIOLATION`;
- resealed revision divergence -> `SNAPSHOT_MISMATCH`;
- existing final path -> rejection without overwrite;
- P-Q00/O-V01 membership mismatch -> rejection and staging cleanup; and
- successful reproduction -> identical package digest.

## 6. Audit Finding Closed During Review

The inherited runtime application package eagerly imported service modules.
When the in-memory persistence adapter was imported first in a fresh process,
that package initialization recursed through application contracts back into
the partially initialized adapter. Test import order had hidden the defect.

The package root now lazily resolves the same public compatibility names. A
fresh-interpreter test imports `InMemoryPersistenceBoundary` directly. This is
a dependency-cycle repair, not an Artifact P semantic change.

## 7. Evidence

Final evidence:

```text
Artifact P criteria     PASS 45/45
Focused Artifact P      PASS 11/11
Complete Python suite   PASS 215/215
Ruff                     PASS
H0-H7                    PASS
Web typecheck            PASS
Web lint                 PASS
Rendered web tests       PASS
Deterministic web build  PASS
Local public startup     PASS
Manual browser evidence  PASS at current recorded revision
Offline package verify   VERIFIED
Exact reproduction       REPRODUCED
```

Package digest:

```text
sha256:62f824ddab4b515045c2bfa773f1bd75420a47fbca308d317ad91be74c9f42e3
```

The legacy M2 and M3 report runners reserve their final criterion for an
actually clean Git checkout. Because this implementation and its ratification
documents remain intentionally uncommitted, those report-level cleanliness
criteria are not claimed here. M2 reports 18/19 with only `clean_checkout`
blocked; M3's two non-pass criteria are that same M2/cleanliness dependency.
All substantive runtime, Python, web, public-build, and manual-review gates pass.

## 8. Verdict and Next Gate

No semantic, accounting, assurance, governance, readiness, traceability,
dependency, determinism, or package-integrity blocker remains in
`P-EVIDENCE@v1`.

The next authorised work is not an Excel workbook or Power BI model. It is the
finite governed analytical-read artifact and registry that will add only the
exact journal, reporting-fact, account, source-object, and stable-dimension
grains required by those first local consumers. Both consumers must then import
that registry through the verified Artifact P package.
