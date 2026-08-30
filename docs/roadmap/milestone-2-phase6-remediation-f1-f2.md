# Milestone 2 Phase 6 Remediation: F1 and F2

Status: Complete 2026-08-09 - final Phase 6 gate subsequently passed

## 1. Scope

This bounded pass resolves only the first two blockers from the post-Phase-6
cohesion audit:

- F1: semantic availability was recorded but not enforced on reads; and
- F2: pre-scope import did not validate its exact hard-close and temporal
  prerequisites.

It does not address directed J-P11 traversal, the incomplete exact/as-of query
catalog, J-AR01 candidate receipt production, or mandatory Artifact G
publication closure.

## 2. F1 Resolution - Semantic Availability

Every exact runtime record now carries an `available_from` value. Query
sessions pin both revision and semantic time, then exclude unavailable records
before any exact lookup, collection read, current projection, reporting query,
controlled planning read, or trace can consume them.

Current J-P02/J-P04/J-P06 state is rebuilt from the baseline plus only accepted
command closures visible at the pinned semantic time. It is not copied from the
latest live checkpoint. The baseline itself has an availability boundary and
is absent from an earlier semantic view.

SQLite schema version 4 persists availability for authoritative records and
effect claims. A deterministic migration backfills version-3 rows from exact
command contexts or embedded semantic fields; records with no later semantic
time are classified as baseline-available rather than left nullable.

Ordinary accounting command contexts now use the accounting event's
`recorded_at`. Constructor-only commands use the latest declared creation time
instead of the former epoch placeholder.

## 3. F2 Resolution - Pre-Scope Import

The import validator now requires one exact current `HARD_CLOSED` period view,
the named `period.hard_closed` J-AR06 event for that period, and the exact
declared J-P04 view hash.

The validator also binds:

- reporting-version identity, period, publication origin, and original
  publication time;
- the complete J-AR11 minimum attestation body;
- canonical reporting-core hash;
- verified J-AR12 content bytes and content hash;
- imported G-06 identity, payload hash, basis, authority, and source;
- original publication, import, hard-close, and availability ordering; and
- the import context's actor, semantic time, candidate hash, and identities.

The C-001 runtime proof now executes as one validated workflow in two
contiguous segments. I-S01 through I-S06 run through the ordinary service,
then the sealed import transaction runs, then I-S08 onward resumes through the
same service. No partial `AccountingWorkflow` object or direct store mutation is
used.

## 4. Executable Proofs

The tests prove:

- in-memory and SQLite current period state is `SOFT_CLOSED` immediately before
  the hard-close event's recorded time and `HARD_CLOSED` at that time;
- the hard-close event itself follows the same visibility boundary;
- baseline authority is absent before baseline availability;
- pre-scope import is rejected while the period is soft-closed;
- a wrong exact close-view hash is rejected;
- availability before attested import time is rejected;
- every rejected import leaves predecessor J-AR10/G-06 absent;
- a valid import remains invisible before `available_from` and becomes visible
  exactly at that time;
- the imported predecessor remains independently queryable after the successor
  workflow, restart, and rebuild; and
- a schema-v3 database upgrades to schema v4 with deterministic non-null
  availability metadata.

Ruff passes. All 114 tests pass, including unchanged H0 through H7 coverage.

## 5. Scope Guard and Next Gate

This pass adds no API, UI, authentication, workflow framework, second
dispatcher, second repository, or process taxonomy. The workflow segment
operation accepts only a contiguous range of an already validated canonical
workflow and still uses the ordinary planner, dispatcher, and unit of work.

F6 mandatory Artifact G publication
closure was subsequently resolved in
`docs/roadmap/milestone-2-phase6-remediation-f6.md`; F3/F4 query and trace work
was then resolved in `docs/roadmap/milestone-2-phase6-remediation-f3-f4.md`.
F5 was resolved in `docs/roadmap/milestone-2-phase6-remediation-f5.md`, and the
follow-up audit passes.
