# Milestone 1 Post-Phase 7 Cohesion Audit

Status: Passed 2026-08-02 - Milestone 1 complete

## 1. Purpose

This is the mandatory hard audit after Phase 7 and before Milestone 1 closure.
It reconciles:

- the five platform invariants and `AGENTS.md`;
- Artifacts C, E v0.2.1, F v0.2.1, G v0.2, and H v0.3.1;
- canonical transactions C-001 and CT-1;
- all six canonical fixture files and both reporting proof bodies;
- ADR-012 through ADR-017;
- the executable-schema backlog and Milestone 1 roadmap;
- implementation and tests through H7; and
- the README's public claims and clean-checkout command.

The committed implementation baseline reviewed before the Phase 7 candidate was
`26b733d`, which completed canonical scenario replay and H5.

## 2. Audit Method

The review traced every H6 and H7 assertion to Artifact G or H, re-ran all lower
layers, inspected prohibited boundary edges, compared the recorder port with its
Phase 0 compatibility tests, and challenged the machine report's inventory and
reproducibility claims. It separately searched documentation for stale phase,
backlog, artifact-version, path, and public-status wording.

The audit specifically tested whether Phase 7 had:

- made the observational recorder participate in a transition;
- broken subject-free G-14 representation;
- allowed J-010 to appear as authored G-04 or G-05 state;
- accepted a non-business event through G-01;
- allowed Argus, Aegis, or Pythia to write Atlas accounting state;
- permitted unversioned, implicit-latest, missing-readiness, or stale-readiness
  consumption;
- omitted required downstream consumers from either canonical G trace;
- added a G payload schema rather than proof metadata;
- hashed contract labels while claiming to digest the executable contracts;
- omitted required test-result fields or mutation digests from the report;
- treated `BLOCKED` as an overall pass;
- included environment paths or elapsed time in reproducibility; or
- expanded Milestone 1 into a database, service, UI, or speculative taxonomy.

None of those prohibited outcomes remains.

## 3. Findings Resolved During the Audit

Five implementation or documentation gaps were found and closed.

1. The first Phase 7 recorder model made `contract_version` and `subject_ref`
   mandatory. That regressed the Phase 0 port, where a G-14 pre-construction
   rejection can exist with only a command identity. The port remains backward
   compatible; Phase 7 traces add version, subject, outcome, lineage, and
   evidence metadata without making a domain subject mandatory.
2. The initial happy-path traces proved the presence of G-11 and G-12 but did
   not separately observe both Argus and Aegis consuming both Pythia proof
   products. CT-1 also omitted Atlas as a reader of the verified issue state.
   The traces now reproduce those directions explicitly, and the prohibited
   Aegis/Argus/Pythia accounting-write cases have direct negative tests.
3. The first H7 contract inventory digest covered contract names and event
   discriminants only. It now hashes the complete strict Pydantic JSON schemas
   and the deterministic Artifact G publisher/consumer/version registry, so a
   material executable contract change changes the digest.
4. README and roadmap status still stopped at Phase 6. Current-status documents
   now reflect the executable result. Similarly phrased pre-implementation text
   in ADR-014 is historical decision context and remains unchanged.
5. The initial report value checked only that status counts totalled the number
   of rows. It now reconciles each PASS/FAIL/BLOCKED count to the actual rows and
   rejects any overall status inconsistent with those rows.

These corrections implement existing ratified obligations. They do not change
an Artifact F field, event type, fixture byte, state transition, owner, G
contract meaning, or scope decision. No new ADR is required.

## 4. Cohesion Results

### 4.1 Event, object, and ownership boundaries

- Artifact F remains nine object types, ten accounting-event types, and
  seventeen accounting-event instances.
- Only the one C-001 business event reaches the posting-rule evaluator.
- Accounting events, governance outputs, forecasts, and G-14 dispositions
  cannot enter G-01.
- Atlas remains the sole writer of the eight Atlas-owned Artifact F types.
- Hermes preserves source meaning; Argus publishes machine exceptions; Aegis
  publishes governance and readiness; Pythia publishes planning and decisions.
- J-010 remains immutable non-authored state consumed only through G-13.

### 4.2 Canonical boundary proofs

- C-001 records every G contract from G-01 through G-12 in permitted
  directions.
- Pythia receives exact `RV-2026-06@v2` and `READY-C001-V2@v1` references before
  publishing its frozen inputs and decision products.
- Argus and Aegis both receive the Pythia proof outputs.
- The approved hiring decision returns only as a G-01 candidate.
- CT-1 records G-03, G-04, G-05, G-07, G-08, G-09, and G-13, while G-10 through
  G-12 remain absent because CT-1 has no controlled planning use.
- G-14 proves one rejected command disposition without an Artifact F object or
  accounting event.

### 4.3 Assertion report and reproducibility

- H7 accounts for 80 unique H0-H7 assertions: 80 pass, zero fail, zero blocked.
- Every report row carries the complete stable result shape; H3 rows retain
  before and after store digests where mutation is relevant.
- Fixture inventory, executable contract inventory, C-001 state, and CT-1 state
  are content-addressed.
- The report excludes elapsed time and environment-specific filesystem paths.
- Two fresh complete runs produce byte-identical canonical JSON at the same
  repository revision.
- Failure and blocked overall results both return non-zero.

### 4.4 Scope discipline

- No fixture, object contract, accounting-event variant, posting rule, or
  canonical transaction was added.
- The G recorder contains proof metadata only and is not a domain payload.
- No database, API, authentication system, UI, event bus, distributed-delivery
  claim, or module deployment was introduced.
- F-EXE-001 and F-EXE-002 remain closed by their existing H2 and H4 proofs.

## 5. Executable Gate

The final gate requires all of the following from the locked repository:

```text
uv run --locked python -m finance_assurance.validation
uv run --locked pytest
uv run --locked ruff check .
```

The harness output must report:

```text
H0 PASS (7/7)
H1 PASS (14/14)
H2 PASS (11/11)
H3 PASS (18/18)
H4 PASS (7/7)
H5 PASS (2/2)
H6 PASS (17/17)
H7 PASS (4/4)
OVERALL PASS
```

The generated canonical machine report is written to
`build/validation-report.json`; generated output remains ignored by Git.

## 6. Verdict

No architecture, contract, fixture, ownership, accounting, temporal, evidence,
or scope contradiction blocks closure. Milestone 1 is complete and provides a
cohesive executable baseline for designing the next explicitly bounded
milestone.
