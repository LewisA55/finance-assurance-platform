# Milestone 2 Phase 2: Persistence Port and In-Memory Parity

Status: Complete 2026-08-05

## 1. Objective

Phase 2 proves the Artifact K ordinary-command persistence boundary before a
database product can shape it. Every existing planner command now executes
through one typed command unit of work rather than mutating validation-owned
`HarnessState` directly.

## 2. Implemented Boundary

The runtime now defines database-independent semantic types for:

- command context and version-bound retry identity;
- authoritative references and semantic state expectations;
- accepted and rejection-only staged write sets;
- effect claims and G-14 dispositions;
- validated plans, final conflict snapshots, and commit plans; and
- semantic commit receipts without adapter-local transaction identity.

`CommandUnitOfWork` exposes only the ordered Artifact K operations:

```text
context -> prior result -> stable reads -> stage -> validate
        -> arbitrate -> commit / rollback
```

The root boundary exposes no generic append and no independent commit method.
Only a plan validated by the same open unit can commit.

## 3. In-Memory Adapter

`InMemoryPersistenceBoundary` provides one shared serializable state boundary.
Its command unit:

- captures one immutable read view;
- resolves command deduplication before planner execution;
- validates closure against the exact transition outputs and effect;
- compares semantic state tokens and effect keys at final arbitration;
- holds one transaction lock from arbitration through commit or rollback;
- converts an exact stale/effect snapshot into an application-owned rejection;
- commits accepted or rejection-only records atomically;
- returns the original result for an identical retry; and
- leaves state and revision unchanged after rollback or identity conflict.

The runtime-owned state is now named `InMemoryState`. The historical
`HarnessState` name remains only as a compatibility alias for the independent
H0 through H7 suite.

## 4. Existing Command Parity

The former dispatcher compatibility entry point now creates an in-memory
persistence boundary and invokes the same runtime `execute` path used by direct
adapter consumers. Accepted and rejected planner paths no longer construct a
replacement state in the validation layer.

Canonical behavior remains unchanged for:

- all eighteen Artifact E guard cases;
- accepted proposal, period, posting, restatement, and publication transitions;
- command and effect idempotency;
- rejection-only G-14 disposition commits;
- C-001 and CT-1 event sequences and terminal digests; and
- the deterministic H7 report.

## 5. Phase 2 Conformance Proofs

Eight new tests prove:

- typed boundary execution and semantic receipt contents;
- identical retry before new domain execution;
- contract-version participation in command retry identity;
- injected pre-commit rollback;
- effect uniqueness across different command identities;
- final effect-race arbitration into a rejection-only commit;
- atomic G-14 result and disposition persistence; and
- absence of root-level generic append or commit methods.

The complete repository passes:

- seventy-eight Pytest tests;
- Ruff;
- H0 7/7;
- H1 14/14;
- H2 11/11;
- H3 18/18;
- H4 7/7;
- H5 2/2;
- H6 17/17;
- H7 4/4; and
- H3-GUARD 18/18.

## 6. Scope Boundary

This phase implements and proves Artifact K's ordinary `CommandUnitOfWork`
mode, which is the Phase 2 roadmap requirement. It does not claim that the
runtime-baseline, pre-scope-import, referenced-journal-admission, query, or
rebuild modes have executable adapters yet. Those modes remain ratified by
Artifact K and must be implemented and tested before a later adapter can claim
full Artifact K conformance.

Phase 2 introduces no database, ORM, physical schema, migration, API,
authentication system, broker, outbox, external side effect, or UI.

## 7. Exit Gate

Phase 2 is complete. Phase 3 may select one storage engine through an ADR and
implement the transactional persistent adapter, exact uniqueness constraints,
restart/reload behavior, projection checkpoints, and rebuild proofs. Full
Artifact K adapter conformance remains a Phase 3 exit requirement.
