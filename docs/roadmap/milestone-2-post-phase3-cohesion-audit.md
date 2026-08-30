# Milestone 2 Post-Phase 3 Cohesion Audit

Status: Passed 2026-08-05 - Phase 4 may begin

## 1. Audit Question

Does the SQLite adapter implement Artifact K's transactional, restart, and
rebuild semantics without changing Artifacts C through N, creating a second
owner, weakening the event firewall, or adding a hidden persistence path?

Verdict: yes, after five implementation findings were corrected before
ratification.

## 2. Findings Resolved During the Audit

### F1 - Direct baseline seeding created a seventh mutation path

The first draft exposed a convenience method that accepted `InMemoryState`
directly. That bypassed the ratified baseline manifest and made the six-mode
root untrue.

Resolution: removed. Baselines now enter only through
`RuntimeBaselineAdmissionUnitOfWork`, with manifest, descriptor, record,
projection, hash, owner, and replay validation.

### F2 - Rebuild initially depended on a saved baseline projection

Copying a saved projection is recovery, not deterministic rebuild from declared
authority.

Resolution: schema migration 3 binds the baseline checkpoint to an immutable
baseline J-AR02 module product. Rebuild resolves and verifies that authoritative
record, then folds committed accepted closures. The checkpoint itself is not a
rebuild input.

### F3 - Administrative modes were initially too generic

Family allowlists alone did not prove semantic ownership or mode-specific
context binding.

Resolution: every admission validates mode-specific record and projection
families, permitted owners, canonical bytes and hashes, required record sets,
context identities, prerequisite fields, and the J-AR17 to G-13 source/hash
binding. Baseline J-AR02 resolves through one finite descriptor whose flags are
`baseline_eligible = true` and `command_output_eligible = false`.

### F4 - A committed constructor could have produced an unrebuildable view

The current transition closure does not itself contain every constructor input.
Allowing the write and discovering the gap only during maintenance would violate
Artifact J.

Resolution: every durable ordinary commit rebuilds the proposed projection from
declared authority before opening the SQLite transaction. Missing constructor
authority fails the commit. Phase 4 must persist the Artifact I/L treatment
version that makes the constructor replayable.

### F5 - Separate process views needed durable revision arbitration

An in-process lock cannot serialize two independently opened adapter instances.

Resolution: ordinary commands and administrative admissions execute a durable
revision compare under `BEGIN IMMEDIATE`. A stale process view cannot overwrite
or obscure a committed result.

## 3. Invariant Reconciliation

| Invariant or boundary | Audit result |
|---|---|
| Business-event/accounting-event firewall | Unchanged; persistence never invokes posting-rule evaluation. |
| Balanced, immutable accounting | Existing planner/store checks remain mandatory before durable commit; database identities are unique. |
| Four truth layers | Administrative records retain family and semantic owner; SQLite acquires no domain ownership. |
| Purpose-specific reliability | No readiness inference or new data-product use is introduced in Phase 3. |
| Reproducible evidence | Canonical bytes, exact hashes, type registry, source refs, and tamper failure remain explicit. |
| J-AR14 command closure | Ordinary commands only; administrative admissions remain outside J-AR14. |
| J-AR15 effect independence | Dedicated unique registry survives restart and remains separate from command deduplication. |
| J-AR17/G-13 non-authorship | Source bytes and hash are admitted and exposed without creating a J-AR08 journal. |
| Projection disposability | Current checkpoint can be deleted; rebuild uses declared authority and promotes atomically. |
| Runtime/validation dependency | No runtime module imports `finance_assurance.validation`. |

## 4. Stale-Documentation Reconciliation

The Phase 2 statement that five Artifact K modes were not executable is retained
as historical Phase 2 scope. Current-status surfaces now identify Phase 3 as
complete and point to the durable adapter record.

The duplicated trailing ADR-026/ADR-027 text in the decision log was an exact
editorial duplication. It was removed without altering either accepted
decision. ADR-028 is the next unique decision.

## 5. Scope Guard

The audit found no API, UI, authentication, tenancy, broker, background worker,
outbox, second database, external effect, or new business process. SQLite is one
shared substrate behind the ratified port, not a module-owned database.

## 6. Residual Phase 4 Obligations

These are entry conditions, not Phase 3 defects:

- parameterised constructors must publish their complete authoritative
  treatment/version inputs before their projections can commit;
- Artifact L module-product descriptors must be populated only as their Phase 4
  command families become executable;
- globally unique command IDs remain the current executable convention even
  though retry identity also binds semantic owner; and
- no application service may bypass the six-mode root or depend directly on
  SQLite tables.

## 7. Gate

The persistence, migration, transaction, restart, admission, query, rebuild,
event-firewall, and ownership models agree at the implemented boundary. Phase 4
may begin.
