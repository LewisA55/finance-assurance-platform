# Milestone 2 Phase 6 Remediation: F6

Status: Complete 2026-08-09 - final Phase 6 gate subsequently passed

## 1. Scope

This bounded pass resolves F6 from the post-Phase-6 cohesion audit: required
Artifact G publication closure was caller-optional on ordinary Atlas accounting
commands.

It does not address directed J-P11 traversal, the incomplete exact/as-of query
catalog, or J-AR01 candidate-receipt production.

## 2. Mandatory Publication Matrix

The application service now owns the closed Artifact I publication matrix.
Constructor-only commands I-S03 and I-S13 still publish nothing because they
create treatments without an accounting event. Every accounting-event command
has the following exact closure:

| Transition | Mandatory atomic publications |
|---|---|
| Proposal submit, defer, or approve | exact proposal G-04 and event G-05 |
| Journal post | exact posted-proposal G-04, immutable journal G-04, and event G-05 |
| Period hard close | exact period G-04 and event G-05 |
| Restatement propose, link, manifest-ready, or approve | exact case G-04 and event G-05 |
| Successor reporting publication | exact published-case G-04, event G-05, and successor G-06 |

The exact Artifact F payload, product identity, lifecycle token where required,
command publication basis, evidence references, semantic availability time,
and G contract discriminator are materialized deterministically from the
owning command's event, treatment, and authoritative creations.

## 3. Enforcement

`AccountingApplicationService` always has a `ModuleContractService`. Omitting an
observation sink no longer disables contract validation. Callers cannot inject
J-AR13 records into an accounting event bundle; the owning command service
constructs and validates the entire set before entering the unit of work.

Validation rejects:

- a missing exact Artifact F object required to publish a G-04 view;
- an extra caller-authored publication;
- a product, subject, lifecycle, event, timestamp, manifest, journal, or
  reporting-version mismatch; and
- a missing, extra, reordered, or payload-mismatched publication relative to
  the closed matrix.

Only after that validation are the publications added to the planner command's
immutable creations. The accounting event, object versions, journal or
reporting version where applicable, J-AR13 publications, effect claim, and
durable command result therefore share one Artifact K commit. Post-commit
boundary observations remain removable and non-authoritative.

The module publication binder now recognizes Artifact F's canonical
`restatement_case_id`; it no longer expects the non-contract alias `case_id`.

## 4. Exact Replay and Persistence Proof

The ordinary parameterised paths now commit:

- C-001: eleven accounting events, twelve G-04 records, eleven G-05 records,
  and one G-06 record - twenty-four publications in total; and
- CT-1: six accounting events, eight G-04 records, and six G-05 records -
  fourteen publications in total.

The proof also covers non-canonical event identities and dual timestamps. Exact
period, journal, restatement, and reporting bodies remap their causal event
references and action times with the parameterised workflow rather than
retaining canonical fixture literals.

Missing, extra, and mismatched hard-close inputs are each rejected before the
target command changes either the full state digest or persistence revision.
The complete publication identity set survives projection deletion, rebuild,
database close, and process restart unchanged.

## 5. Verification and Next Gate

Ruff passes. All 117 tests pass. The independent H0 through H7 validation
harness also passes without modification.

This pass adds no new command, query, event taxonomy, dispatcher, repository,
workflow framework, API, UI, or distributed infrastructure. It implements the
already-ratified Artifact G, I, J, K, and L closure.

F3/F4 exact query and directed trace work
was subsequently resolved in
`docs/roadmap/milestone-2-phase6-remediation-f3-f4.md`. F5 was resolved in
`docs/roadmap/milestone-2-phase6-remediation-f5.md`, and the follow-up audit
passes.
