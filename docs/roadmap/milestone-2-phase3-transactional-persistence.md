# Milestone 2 Phase 3 - Transactional Persistent Adapter

Status: Complete 2026-08-05

## 1. Outcome

Phase 3 implements one durable Artifact K persistence boundary using SQLite.
The pure planner and runtime contracts remain database-independent. SQLite is
confined to the persistence adapter and is not visible to module, command, or
payload contracts.

The adapter now proves:

- ordered schema migrations through schema version 3;
- one atomic local transaction for command records, effects, command closure,
  and the promoted projection checkpoint;
- database-enforced uniqueness for authoritative identities, command contexts,
  effects, and admission identities;
- compare-and-swap revision arbitration across separate process views;
- same-command retry and independent effect idempotency after restart;
- sealed runtime-baseline, pre-scope-reporting, and referenced-journal
  admission modes outside J-AR14;
- immutable exact/current query sessions;
- isolated projection rebuild generations and atomic promotion;
- tamper detection for authoritative state, command contexts, projection
  checkpoints, and baseline authority; and
- refusal to commit a projection that cannot be rebuilt from declared
  authority.

No HTTP surface, UI, authentication system, message broker, background worker,
outbox, database-per-module split, or new finance workflow was introduced.

## 2. Storage Decision

SQLite is the one Milestone 2 storage engine. The adapter uses Python's standard
`sqlite3` module, explicit `BEGIN IMMEDIATE` transactions, explicit commit or
rollback, foreign-key enforcement, and `synchronous = FULL`.

This choice fits the milestone because the runtime is one in-process modular
monolith with one writer boundary and no production continuity or distributed
delivery requirement. It adds durable transactions and exact constraints
without adding a server, deployment dependency, ORM, or second persistence
model.

The decision is recorded in ADR-028. A future deployment may implement the same
ports over another engine, but storage selection is not a domain decision and
does not weaken the SQLite adapter's conformance obligations.

## 3. Physical Boundary

Three schema migrations create and evolve:

- schema and runtime metadata;
- canonical authoritative-state storage;
- an authority-bound baseline source;
- disposable projection checkpoints;
- immutable authoritative record envelopes;
- exact command contexts;
- independent effect claims;
- sealed admission receipts and projection replacements; and
- the explicit binding from a baseline projection to its authoritative module
  product.

Authoritative state and current projections are stored separately. Restart may
load both after verifying their hashes and revision binding. Rebuild does not
copy the prior checkpoint: it loads the admitted authoritative baseline product
and folds committed accepted transition closures in order.

## 4. Closed Durable Codec

The adapter codec is deterministic canonical JSON with explicit runtime type
tags. Its decoder uses a closed registry of runtime-owned dataclasses, enums,
and Pydantic models. Persisted bytes cannot request an arbitrary Python import.

Every decoded value must:

1. use a registered type;
2. satisfy its frozen runtime model;
3. match the caller's expected top-level type; and
4. re-encode to byte-identical canonical content.

Float values are not admitted by the durable codec. Money remains integer minor
units under the ratified Artifact F contracts.

## 5. Six Artifact K Modes

The durable root exposes exactly:

1. `CommandUnitOfWork`;
2. `RuntimeBaselineAdmissionUnitOfWork`;
3. `PreScopeReportingImportUnitOfWork`;
4. `ReferencedJournalAdmissionUnitOfWork`;
5. `QuerySession`; and
6. `RebuildSession`.

The temporary direct state-seeding path found during the Phase 3 audit was
removed. A runtime baseline now requires an exact manifest J-AR04 record, a
finite baseline-eligible J-AR02 descriptor, canonical authoritative state
facts, declared predecessor evidence, and a permitted J-P04 replacement.

Administrative admission uses mode-specific record-family and projection-family
allowlists, semantic-owner checks, canonical byte/hash verification, exact
context binding, replay/conflict handling, and one atomic transaction. These
modes do not create J-AR14, claim an effect, execute the planner, or acquire
authorship over referenced state.

## 6. Commit and Recovery Ordering

An ordinary accepted or rejected command follows the Phase 2 unit-of-work path.
After final validation, the SQLite adapter:

1. verifies the durable revision still matches the unit's base revision;
2. proves the proposed projection remains rebuildable;
3. inserts immutable authoritative deltas and effect claims;
4. stores the exact command context;
5. replaces authoritative-state and projection-checkpoint rows;
6. invokes the sole fault-injection point;
7. commits SQLite; and only then
8. publishes the new in-process state.

If any database operation or injected fault fails, SQLite rolls back and the
in-process state remains unchanged. If acknowledgement is lost after the
database commit, restart and same-command retry resolve the committed J-AR14
closure rather than repeating the effect.

## 7. Projection Rebuild

Rebuild uses a generation lifecycle:

```text
begin_generation
-> rebuild candidate
-> validate semantic parity
-> promote atomically
```

The candidate is not query-visible before promotion. Abort or failure leaves
the prior in-process generation unchanged. The promoted checkpoint is bound to
the current authoritative-state hash and revision.

The current Phase 3 authoritative vocabulary reconstructs transitions whose
base treatment already exists in the admitted authoritative baseline. A
constructor lacking a declared authoritative treatment/version fails before
commit. Phase 4 must add the appropriate Artifact I/L authoritative outputs;
the adapter will not preserve an unrebuildable projection merely to allow a
workflow to proceed.

## 8. Verification

The Phase 3 test catalog covers:

- schema migration and idempotent reopen;
- baseline restart parity;
- command retry and effect identity after restart;
- command and administrative pre-commit failure rollback;
- cross-process stale-revision rejection;
- database uniqueness enforcement;
- G-14 rejection/disposition recovery;
- exact read-only query sessions;
- all three sealed admission modes;
- projection deletion, rebuild, validation, promotion, and restart;
- checkpoint tamper detection; and
- pre-commit refusal of unrebuildable constructor state.

The unchanged Milestone 1 suite and H0 through H7 remain the canonical semantic
regression gate.

## 9. Exit

Phase 3 is complete. The post-Phase-3 cohesion audit passes. Phase 4 may begin
parameterised application services, provided every new command output supplies
the authoritative values required by persistence and rebuild rather than
introducing a workflow-private repository or projection seed.
