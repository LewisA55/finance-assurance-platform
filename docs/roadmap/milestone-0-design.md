# Milestone 0: Design Baseline

Status: Complete 2026-07-24

Milestone 0 is complete when the platform can explain C-001 and CT-1 without contradiction.

## Required Artifacts

- Product thesis.
- Canonical transaction C-001.
- Canonical transaction CT-1.
- Artifact C: accounting object model.
- Artifact E v0.2.1: accounting state machines and command/event matrix (resolved baseline).
- Artifact G v0.2: module ownership and publish/consume contract map (ratified).
- Artifact F v0.2.1: minimum payload contracts, canonical fixtures, and referenced-state proof projection for C-001 and CT-1 (ratified contract boundary; reporting proof fixtures revised).
- Artifact H v0.3.1: first executable validation specification (v0.3 ratified;
  corpus-role wording clarified without changing acceptance scope).

## Acceptance Criteria

- C-001 proves restatement without reopening a hard-closed period.
- CT-1 proves reversal and replacement for an incorrect posted journal.
- Accounting events never re-enter the posting engine.
- Submitted but unposted proposals remain identifiable.
- Deferred close exceptions are explicit proposal dispositions rather than hidden metadata.
- Reporting versions preserve as-published and as-restated views.
- Restatement explicitly bridges correction-period ledger effects to prior-period presentation effects.
- The model distinguishes mechanical balance from accounting correctness.

Executable follow-ups that do not block design ratification are tracked in `docs/roadmap/executable-schema-backlog.md`.
