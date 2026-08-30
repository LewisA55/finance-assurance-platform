# Finance & Assurance Platform Instructions

This repository is the durable source of truth for the Finance & Assurance Platform.

## Product Thesis

Build a synthetic finance and assurance operating environment. The platform models how enterprise business events become accounting records, management information, forecasts, controls, audit evidence, and governed decisions.

This is not five separate applications. It is one process-led platform with a shared substrate and several product lenses.

## Module Lenses

- Hermes observes source integrity, reconciliation, lineage, and data operations.
- Atlas owns accounting records, ledger integrity, reporting versions, and financial performance.
- Argus runs assurance tests and produces machine observations, exceptions, and evidence.
- Aegis governs reviewed findings, issues, remediation, readiness, and sign-off.
- Pythia consumes governed actuals for planning, scenarios, forecasts, and decisions.

## Invariants

1. Events preserve business causality.
2. Accounting is derived, balanced, and independently reconciled.
3. Business-event truth, source-system truth, accounting truth, and governed truth remain distinct.
4. Reliability is purpose-specific and travels with every published data product.
5. Every claim is traceable to reproducible evidence, exact rule versions, and source inputs.

## Architecture Rules

- `business_event` is the only object class permitted to drive posting-rule evaluation.
- `accounting_event` records accounting lifecycle transitions and must never re-enter the business-event posting engine.
- Proposed journals are derived records, not causal events.
- Posting, reversal, restatement, and publication actions are first-class accounting events because they have governance significance.
- Journal headers and lines are immutable records once posted.
- A hard-closed period must not be silently reopened to correct history.
- Reversal corrects posted journals in an open correction path.
- Restatement republishes a reporting period version when the original reporting state must remain preserved.

## Working Practice

- Design before implementation during Milestone 0.
- Keep docs ASCII unless a file already uses another character set.
- Use append-only decision logging for material architecture choices.
- Preserve the distinction between exception, finding, issue, remediation, readiness, and decision.
- Test every architecture artifact against C-001 and CT-1 before expanding scope.
