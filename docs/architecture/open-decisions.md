# Resolved Design Questions

Status: Closed - no unresolved Milestone 0 architecture decisions

This file preserves the questions resolved during the Artifact E/F design
sequence. `decision-log.md` is the authoritative append-only decision record.
New unresolved implementation findings belong in the active milestone roadmap,
not in this historical register.

## Resolved: `restatement_case` Is the Ninth Object

Resolved by Artifact E v0.2.1.

Restatement has identity, scope, linked adjustments, affected periods, approval, evidence, a frozen presentation-adjustment manifest, and publication state.

## Resolved: Artifact E State Machine Scope

Artifact E v0.2.1 covers:

- `journal_proposal`
- `accounting_period`
- correction lifecycle for CT-1
- restatement and publication lifecycle for C-001

`accounting_event` itself has no state machine. It records governed actions and evidences transitions for stateful objects.

## Resolved: Artifact F Design Boundary

Artifact F is a closed payload-contract set for the nine accounting objects and ten distinct accounting-event types instantiated across seventeen event instances: eleven in C-001 and six in CT-1.

The following conventions are settled before drafting:

- Integer minor units plus ISO 4217 currency; no floating-point money.
- `debit_minor` and `credit_minor` are used consistently for journal lines and restatement-manifest entries.
- Every event carries `event_id` and `command_id`; only posting and publication additionally require an `idempotency_key`.
- `AUTOMATED_POSTING` is exercised as a proposal origin but not as a posted-journal entry class.
- Reporting versions carry an immutable content reference, content hash, and content schema version rather than defining statement structure.
- Aegis issues and directives remain opaque typed references.
- C-001 uses ledger correction period `2026-07` and presented period `2026-06` as canonical scenario data, not as a platform rule.
- Object and event contracts reject fields not listed by their declared contract version.

## Resolved: Artifact F v0.2 and v0.2.1 Critique

- J-010 is admitted only as a non-authored read-only projection so CT-1 can prove equal-and-opposite reversal.
- June v1-to-v2 statement-body arithmetic is explicitly deferred to runtime content resolution.
- `reporting_version.published` uses RC-001 as its transitioning subject and carries the created reporting version in its payload.
- Logical command identity is stable across retries; effect idempotency remains separately enforced for posting and publication.
- Proposal submission uses one discriminated `derivation_authority` shape.
- All exercised RC-001 lifecycle states have fixture snapshots.
- Hard-close proposal counts, segregation of duties, and reversal integrity have explicit negative tests.
