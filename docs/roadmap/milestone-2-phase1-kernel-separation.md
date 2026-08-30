# Milestone 2 Phase 1: Runtime Kernel Separation

Status: Complete 2026-08-05

## 1. Objective

Phase 1 changes dependency direction without changing domain behavior. It moves
the reusable contract and transition semantics out of the Artifact H validation
harness and proves exact equivalence against the Milestone 1 baseline.

## 2. Runtime Boundary

`finance_assurance.runtime` now owns:

- canonical JSON serialization and deterministic value hashing;
- the strict Artifact F payload models;
- stable semantic rejection values;
- the admitted non-authored referenced-journal projection model; and
- the single pure Artifact E transition planner, its commands, states, and
  transition plans.

The runtime package imports no module under `finance_assurance.validation`.

`finance_assurance.validation` continues to own:

- fixture loading and the raw and validated corpus indices;
- validation-library error translation;
- H0 through H7 assertions and reports;
- scenario-local C-001 and CT-1 replay;
- the immutable Milestone 1 harness stores and dispatcher; and
- compatibility facades for the import paths used by the ratified harness.

This leaves the conformance harness as a consumer of the runtime kernel rather
than the owner of reusable domain behavior.

## 3. Black-Box Characterization

The Phase 1 characterization locks the complete pure-planner vector set:

- twenty rejected guard command executions;
- thirteen accepted transition controls;
- exact result structure, rejection codes, reasons, transitions, event bodies,
  immutable creations, and effect keys; and
- one combined deterministic digest over both sets.

The locked digests are:

```text
guards   sha256:bf8241b979f20e626f7d14e471a14ad90f93195f7d610f28e21663da6b8fcb49
accepted sha256:e493dd70f0a83b12c0a8e50f4e6f876d004e9cf713c8935feca171de55c33773
combined sha256:a8cb0dc06380a815febd301d1edba461803330607e016af73ae7ab7a686d4168
```

The tests also prove that the validation facades resolve to the runtime-owned
planner, rejection types, and Artifact F adapters rather than parallel copies.

## 4. Validation Result

Phase 1 passes:

- seventy Pytest tests, including three new runtime-kernel tests;
- Ruff over the complete repository;
- H0 7/7;
- H1 14/14;
- H2 11/11;
- H3 18/18;
- H4 7/7;
- H5 2/2;
- H6 17/17;
- H7 4/4; and
- H3-GUARD 18/18.

The canonical fixture files, seventeen accounting-event instances, C-001 and
CT-1 replay semantics, terminal digests, and machine-readable report behavior
remain unchanged.

## 5. Scope Boundary

Phase 1 introduces no repository port, unit of work, persistent adapter,
database, schema, migration, public API, authentication, module workflow, or UI.
The Milestone 1 `HarnessState` and dispatcher remain validation-owned until
Phase 2 proves a database-independent persistence port and in-memory parity.

## 6. Exit Gate

Phase 1 is complete. Phase 2 may implement the ratified Artifact K persistence
ports and an in-memory adapter while preserving the locked planner vectors and
all existing H0 through H7 behavior.
