# Milestone 2 Phase 4: Parameterised Application Services

Status: Complete 2026-08-05

## 1. Outcome

The runtime now executes the finite accounting portions of the C-001 and CT-1
families through one parameterised application service. Runtime code no longer
depends on the validation scenario drivers, canonical fixture loader, H-layer
dispatcher, or literal canonical command/event identities.

Phase 4 deliberately stops at the accounting application boundary. Hermes,
Argus, Aegis, Pythia, and source-domain Artifact G publications remain Phase 5
work; this phase does not simulate those handoffs or manufacture a manual G
trace.

## 2. Runtime Boundary

`AccountingWorkflow` admits exactly two closed lifecycle shapes:

- C-001: eleven ratified accounting-event types in their declared order, one
  admitted recognition business event, one automated proposal treatment, and
  one restatement-adjustment treatment;
- CT-1: six ratified accounting-event types in their declared order, one
  reversal treatment, one replacement treatment, and no business-event input.

Any missing, additional, reordered, or undeclared lifecycle event is rejected
before execution. The service translates the finite workflow into the existing
pure planner commands and commits exclusively through the Artifact K
persistence boundary.

## 3. Deterministic Ports

Clock and identity allocation are injected through small protocols. The
executable deterministic adapters bind:

- accounting-event identity;
- application-command identity;
- constructor-command identity;
- correlation identity; and
- separate occurrence and recording timestamps.

Canonical identity and time scripts reproduce the ratified event payloads.
Alternative scripts execute a non-canonical family instance without changing
domain logic or branching on C-001/CT-1 literal IDs.

## 4. Authoritative Constructor Basis

Phase 3 correctly refused to persist constructor projections that could not be
rebuilt. Phase 4 closes that boundary with `ProposalTreatmentVersion`, the
runtime representation of Artifact J J-AR05:

- immutable proposal family/version identity;
- origin and exact derivation basis;
- target period and effective date;
- currency, ordered balanced lines, and totals;
- preparer, creation time, and evidence; and
- canonical treatment hash.

Lifecycle status and submission time are not part of J-AR05. Draft state derives
from the accepted constructor plus treatment; later status derives from the
ordered J-AR06 accounting events.

SQLite rebuild now reconstructs proposal constructors from exact J-AR05 input,
restatement constructors from `restatement.proposed`, and linked-journal plus
manifest state from the corresponding accounting events. A constructor without
its exact treatment still fails before commit.

## 5. Authoritative-Family Reconciliation

The Phase 4 cohesion pass found one stale Phase 2/3 implementation label:
ordinary accounting events were reported and stored as J-AR05, while generic
objects were always labelled J-AR02. Artifact J requires a semantic split.

The ordinary command path now classifies outputs as:

- J-AR03: admitted business event;
- J-AR05: proposal treatment version;
- J-AR06: accounting event;
- J-AR08: posted journal and lines;
- J-AR10: reporting version; or
- J-AR02: finite module-owned product only.

This correction changes internal authoritative-family metadata, not Artifact F
payload bytes, planner semantics, event counts, or canonical terminal states.

## 6. CT-1 Ordering

Before the reversal constructor can run, the service resolves the referenced
J-010 projection and proves its `source_hash` equals the reversal treatment's
first declared input hash. Only after that binding may the existing planner
derive and later compare equal-and-opposite lines. A mismatch commits nothing.

Neither CT-1 constructor invokes `EvaluatePostingRule`. C-001 invokes it only
for the admitted business-event-backed automated treatment. The event-stream
firewall therefore remains structural.

## 7. Executable Proofs

The Phase 4 suite proves:

- canonical C-001 executes thirteen ordinary commands, including two eventless
  constructors, and appends exactly eleven accounting events;
- canonical CT-1 executes eight ordinary commands, including two correction
  constructors, and appends exactly six accounting events;
- both terminal projections equal the independent Milestone 1 scenario oracle;
- both survive projection deletion, deterministic rebuild, process restart,
  and exact proposal query;
- J-AR05 treatment bytes remain independently retrievable;
- C-001 and CT-1 instances with remapped IDs, correlations, and dual timestamps
  execute through the same service;
- undeclared lifecycle shapes fail before execution; and
- reversal source-hash mismatch fails before the first constructor commit.

Ruff passes. All 98 tests pass. The unchanged H0 through H7 harness remains
green with all 17 canonical accounting events and the same report semantics.

## 8. Scope Guard and Phase 5 Entry

Phase 4 introduces no API, UI, authentication, tenant model, broker, worker,
outbox, second database, new event type, new lifecycle, or speculative workflow
framework. The deterministic scripted ports are reproducibility tools, not a
production scheduler or identity service.

Phase 5 may now execute the ratified Artifact L G-01 through G-14 bodies through
in-process contract ports. It must retain this accounting service and ordinary
unit-of-work path rather than building module-specific persistence or assembling
expected traces after execution.
