# Artifact E: Accounting State Machines and Command/Event Matrix

Design sequence artifact E. This document makes the accounting object model executable by defining permitted commands, state transitions, event emissions, immutable record creation, and rejected alternatives.

Status: Design v0.2.1 - resolved baseline before payload contracts

Binds:

- Artifact C: Accounting Object Model.
- The hybrid accounting ontology.
- Canonical transaction C-001.
- Canonical transaction CT-1.

## 0. Rulings Settled by This Artifact

### 0.1 `accounting_event` records actions and transitions

`accounting_event` is immutable and has no state machine. Every state transition is evidenced by exactly one accounting event.

An accounting event may also:

- create an immutable record;
- append a governed relationship;
- freeze a manifest; or
- update a read projection without changing another object's lifecycle state.

Therefore, the relationship is deliberately not a strict one-event-to-one-edge bijection. Every transition has one event, but not every valid event must represent a state transition.

### 0.2 `restatement_case` is the ninth accounting object

`restatement_case` has durable identity, affected periods, linked adjustment journals, approval, evidence, a frozen presentation-adjustment manifest, and publication state. Those responsibilities cannot safely live in an event payload.

Minimum fields:

| Field | Meaning |
|---|---|
| `restatement_case_id` | Permanent identity. |
| `scope_period_ids` | Periods that may be re-presented. |
| `trigger_ref` | Finding, issue, or directive that initiated the case. |
| `linked_journal_ids` | Correction journals included in the case. |
| `adjustment_manifest` | Frozen value records mapping ledger effects to presented periods. |
| `manifest_hash` | Integrity hash of the frozen manifest. |
| `status` | Current lifecycle state. |
| `evidence_refs` | Reproducible approval and publication basis. |
| `published_version_refs` | Reporting versions produced by the case. |

The entries inside `adjustment_manifest` are owned value records, not independently stateful accounting objects. This preserves the nine-object model.

### 0.3 `reporting_version` is immutable, not stateful

A reporting version is created only when published. Draft preparation belongs to the `restatement_case`; publication creates a terminal immutable `reporting_version`.

### 0.4 Restatement is not an `accounting_period` state

A period can remain `HARD_CLOSED` while a later reporting version re-presents it. Restatement changes publication history, not the original ledger-period state.

## 1. Structural Firewall and Proposal Origins

The posting-rule evaluator accepts only `business_event`:

```text
business_event
-> posting_rule
-> journal_proposal
```

Accounting correction workflows may also construct journal proposals, but they use separate typed constructors and never invoke the business-event posting engine:

| `origin_type` | Required origin | Derivation authority |
|---|---|---|
| `AUTOMATED_POSTING` | `business_event_ref` and `posting_rule_version` | Versioned posting rule. |
| `REVERSAL` | `reverses_journal_id` | Versioned reversal policy; lines are mechanically equal and opposite. |
| `REPLACEMENT` | `corrects_journal_id` and remediation directive | Versioned correction policy. |
| `RESTATEMENT_ADJUSTMENT` | `restatement_case_id` and remediation directive | Versioned restatement policy. |

The posting engine interface rejects every origin other than `business_event`. Correction constructors reject `accounting_event` as an input. Registry-set checks supplement this type boundary:

```text
posting_rule.trigger_event_types
INTERSECT
accounting_event.event_types
= empty set
```

## 2. State Machine: `journal_proposal`

The state belongs to a specific `proposal_id@version`. A successor version never overwrites the history or terminal state of its predecessor.

```text
DRAFT -> SUBMITTED -> APPROVED -> POSTED
  |          |            |
  |          |            +-> APPROVAL_REVOKED
  |          +-> REJECTED
  |          +-> SUPERSEDED
  |          +-> DEFERRED
  +-> VOIDED
```

| ID | Command | Current state | Authority | Guards | Event emitted | Result |
|---|---|---|---|---|---|---|
| P1 | `regenerate_draft` | `DRAFT` | Proposal constructor | Derivation authority remains effective; lines balance. | None | Draft content or draft version changes before governance begins. |
| P2 | `submit_proposal` | `DRAFT` | Preparer or authorised system policy | Balanced; required dimensions resolved; target period is not `HARD_CLOSED`; origin basis complete. | `proposal.submitted` | `SUBMITTED`; submitted version is frozen. |
| P3 | `approve_proposal` | `SUBMITTED` | Controller role or authorised system policy | Target period accepts approval; evidence complete; segregation-of-duties policy passes. | `proposal.approved` | `APPROVED`. |
| P4 | `post_proposal` | `APPROVED` | Posting service | Approval remains valid; target period accepts posting; lines remain balanced; idempotency key unused. | `journal.posted` | `POSTED`; immutable journal and lines are created. |
| P5 | `reject_proposal` | `SUBMITTED` | Approver | Reason and evidence recorded. | `proposal.rejected` | `REJECTED`. |
| P6 | `supersede_proposal` | `SUBMITTED` | Preparer or proposal constructor | A frozen successor version for the same proposal family exists. | `proposal.superseded` | `SUPERSEDED`. |
| P7 | `defer_at_close` | `SUBMITTED` | Controller under close-exception policy | Reason, owner, target treatment, expiry, and evidence recorded. | `proposal.deferred` | `DEFERRED`; remains historically submitted and unposted. |
| P8 | `void_draft` | `DRAFT` | Preparer | Proposal has never been submitted. | `proposal.voided` | `VOIDED`. |
| P9 | `revoke_approval` | `APPROVED` | Controller or higher authority | Proposal is unposted; reason and evidence recorded. | `proposal.approval_revoked` | `APPROVAL_REVOKED`; a new version is required for later posting. |

Terminal states are `POSTED`, `REJECTED`, `SUPERSEDED`, `DEFERRED`, `VOIDED`, and `APPROVAL_REVOKED`.

`DEFERRED` is explicit close treatment, not hidden metadata. A later restatement proposal references the deferred proposal as its predecessor but does not mutate it.

### Period guards for approval and posting

- `OPEN`: permitted under ordinary policy.
- `SOFT_CLOSED`: permitted before the adjustment cut-off under late-posting policy.
- `REOPENED`: permitted only within the approved reopen scope and directive.
- `HARD_CLOSED`: prohibited. Use the restatement path or an authorised exceptional reopen.

## 3. State Machine: `accounting_period`

```text
OPEN -> SOFT_CLOSED -> HARD_CLOSED
  ^          |
  |          +-> OPEN              (cancel soft close)
  |
  +---- REOPENED <- HARD_CLOSED    (exceptional)
            |
            +-> HARD_CLOSED        (re-close)
```

| ID | Command | Current state | Authority | Guards | Event emitted | Result |
|---|---|---|---|---|---|---|
| A1 | `soft_close_period` | `OPEN` | Controller | Required soft-close checklist items complete. | `period.soft_closed` | `SOFT_CLOSED`. |
| A2 | `cancel_soft_close` | `SOFT_CLOSED` | Controller | Reason recorded; hard close has not occurred. | `period.soft_close_cancelled` | `OPEN`. |
| A3 | `hard_close_period` | `SOFT_CLOSED` | Controller and close policy | Trial balance balances; required reconciliations pass or carry authorised disposition; no unresolved `SUBMITTED` or `APPROVED` proposal targets the period. | `period.hard_closed` | `HARD_CLOSED`. |
| A4 | `reopen_period` | `HARD_CLOSED` | CFO and governance policy | Approved directive identifies the period, permitted accounts, permitted proposal origins, time limit, and evidence. | `period.reopened_exceptionally` | `REOPENED`. |
| A5 | `reclose_period` | `REOPENED` | Controller and CFO | Scoped corrections complete; ledger and reconciliations revalidated; no unresolved proposal remains in scope. | `period.reclosed` | `HARD_CLOSED`. |

An approved `restatement_case` may support A4, but it does not automatically authorise reopening. C-001 does not use A4 or A5.

## 4. State Machine: `restatement_case`

```text
PROPOSED -> ADJUSTMENTS_READY -> APPROVED -> PUBLISHED
    |              |                |
    +--------------+----------------+-> WITHDRAWN
```

| ID | Command | Current state | Authority | Guards | Event emitted | Result |
|---|---|---|---|---|---|---|
| RS1 | `propose_restatement` | None | Aegis directive and Controller | Trigger, scope periods, owner, and initial evidence exist. | `restatement.proposed` | Creates case in `PROPOSED`. |
| RS2 | `link_adjustment` | `PROPOSED` | Controller | Journal is posted; entry class is `RESTATEMENT_ADJUSTMENT`; journal references this case. | `restatement.adjustment_linked` | Appends a governed relationship; state remains `PROPOSED`. |
| RS3 | `freeze_adjustment_manifest` | `PROPOSED` | Controller | At least one linked adjustment; each manifest entry reconciles to referenced journal lines; presented periods are within scope. | `restatement.adjustments_ready` | `ADJUSTMENTS_READY`; manifest and hash are frozen. |
| RS4 | `approve_restatement` | `ADJUSTMENTS_READY` | CFO | Materiality, evidence, manifest, disclosure basis, and publication impact reviewed. | `restatement.approved` | `APPROVED`. |
| RS5 | `publish_restatement` | `APPROVED` | Reporting publication service under approved policy | Manifest hash unchanged; predecessor reporting version exists; publication is idempotent. | `reporting_version.published` | `PUBLISHED`; creates immutable successor reporting version. |
| RS6 | `withdraw_restatement` | `PROPOSED`, `ADJUSTMENTS_READY`, or `APPROVED` | Controller before approval; CFO after approval | Reason and evidence recorded; no reporting version has been published. | `restatement.withdrawn` | `WITHDRAWN`. |

Additional adjustment links require a new manifest freeze. Once `ADJUSTMENTS_READY`, the case must be withdrawn and replaced if the adjustment set changes. It is never silently returned to preparation.

## 5. Restatement Presentation Bridge

A current-period ledger journal cannot directly rewrite a prior hard-closed ledger period. C-001 therefore separates ledger effect from presentation effect.

Each frozen adjustment-manifest entry contains:

| Field | Meaning |
|---|---|
| `journal_line_ref` | Exact immutable ledger line providing the adjustment. |
| `ledger_period_id` | Open correction period in which the line was posted. |
| `presented_period_id` | Prior period being re-presented. |
| `account_id` | Financial statement account affected in the re-presented view. |
| `debit_minor` / `credit_minor` | Signed presentation effect as integer minor units in ledger currency. |
| `currency` | Ledger currency. |
| `basis_ref` | Restatement policy, issue, and evidence basis. |

Publication derives the successor reporting version as:

```text
predecessor reporting version
+ frozen presentation-adjustment manifest
= successor reporting version
```

The correction-period ledger remains unchanged, the original reporting version remains retrievable, and the successor version is reproducible from exact journal lines and the frozen manifest.

## 6. Immutable Journal Creation Rules

A `journal_entry` and its `journal_line` records are created only by `journal.posted`. The event records the proposal and entry class used. Posting is rejected unless all applicable rules pass.

1. Debits equal credits within the journal in ledger currency, subject only to an explicit controlled rounding line.
2. The source is an approved `proposal_id@version` and the posting event is recorded.
3. The target period is `OPEN`, eligible `SOFT_CLOSED`, or authorised `REOPENED`; never `HARD_CLOSED`.
4. The proposal's derivation authority was effective for its accounting effective date.
5. Every line contains the dimensions required by its account role.
6. The journal header and lines are immutable after creation.
7. Entry-class conditional references are enforced:
   - `REVERSAL` requires `reverses_journal_id` and mechanically equal-and-opposite lines.
   - `REPLACEMENT` requires `corrects_journal_id`.
   - `RESTATEMENT_ADJUSTMENT` requires `restatement_case_id`; no prior journal is required.
   - `AUTOMATED_POSTING` requires `business_event_ref` and `posting_rule_version`.
8. Posting is idempotent for the proposal version and posting command key.

## 7. Event Authority and Evidence by Family

Every accounting event requires:

- event identity and timestamp;
- subject type and subject identity;
- actor or system-policy identity;
- authorisation context;
- event-family-appropriate basis;
- evidence or input references needed to reproduce the action; and
- idempotency or correlation identity where the command can be retried.

Additional family requirements:

| Event family | Additional required basis |
|---|---|
| Proposal derivation and submission | Origin type, input hashes, and posting-rule or correction-policy version. |
| Approval or rejection | Decision-maker, segregation-of-duties result, reason, and evidence. |
| Journal posting | Approved proposal version, period guard result, balance validation, and idempotency key. |
| Period close or reopen | Checklist or directive version, reconciliation results, exceptions, and authority. |
| Restatement | Case, scope, materiality assessment, adjustment-manifest hash, and evidence. |
| Reporting publication | Predecessor version, approved restatement case, manifest hash, and publication policy. |

Human approval is not mandatory for every event. Explicit authorisation is mandatory for every event. Automated actions cite the system policy that authorised them.

## 8. Canonical Proof: CT-1 Reverse and Replace

CT-1 concerns the GBP 120,000 July 2026 cash receipt from Orion Manufacturing Ltd that was incorrectly applied to Vega Industrial Ltd while July remained open.

| Step | Command and event | Result |
|---|---|---|
| CT1-1 | Aegis issues a remediation directive. | Governance authority exists outside the accounting-event stream. |
| CT1-2 | Reversal constructor derives and submits `P-REV-010@v1`; `proposal.submitted`. | Frozen equal-and-opposite proposal references J-010. |
| CT1-3 | Controller approves; `proposal.approved`. | Reversal proposal becomes `APPROVED`. |
| CT1-4 | Posting service posts; `journal.posted`. | J-011 is created as `REVERSAL`, debiting AR/Vega and crediting unapplied cash for GBP 120,000. |
| CT1-5 | Correction constructor derives and submits `P-REP-010@v1`; `proposal.submitted`. | Frozen replacement proposal references J-010 and the directive. |
| CT1-6 | Controller approves and posting service posts; `proposal.approved`, then `journal.posted`. | J-012 is created as `REPLACEMENT`, debiting unapplied cash and crediting AR/Orion for GBP 120,000. |

J-010 is never changed. J-011 and J-012 have zero net effect on the GL control-account total while correcting the customer allocation.

No accounting event enters the business-event posting engine.

## 9. Canonical Proof: C-001 Restate and Publish

C-001 concerns the missing GBP 10,000 June 2026 recognition for Orion's annual GBP 120,000 SaaS contract.

| Step | Command and event | Result |
|---|---|---|
| C1 | `accounting.recognition.due` enters `PR-O2C-RECOG`. | `P-551@v1` is derived. |
| C2 | Submit; `proposal.submitted`. | `P-551@v1` is frozen in `SUBMITTED`. |
| C3 | Controller applies a documented close exception; `proposal.deferred`. | `P-551@v1` becomes `DEFERRED`, historically submitted and unposted. |
| C4 | June hard-closes; `period.hard_closed`. | No unresolved submitted or approved proposal remains. |
| C5 | Argus runs the completeness control. | Expected 1; posted 0; submitted-unposted 1; deferred 1; difference GBP 10,000. |
| C6 | Aegis confirms the issue and directs restatement; `restatement.proposed`. | `RC-001` becomes `PROPOSED`, scoped to 2026-06. |
| C7 | Restatement constructor derives `P-551@v2`; proposal is submitted, approved, and posted in the open July 2026 correction period. | J-560 is created as `RESTATEMENT_ADJUSTMENT`, linked to RC-001, with ledger period `2026-07`. June is not reopened. |
| C8 | Link J-560; `restatement.adjustment_linked`. | RC-001 records the governed journal relationship. |
| C9 | Freeze the June presentation allocation; `restatement.adjustments_ready`. | Manifest maps J-560's GBP 10,000 effect from its ledger period to presented period 2026-06. |
| C10 | CFO approves; `restatement.approved`. | RC-001 becomes `APPROVED`. |
| C11 | Publish; `reporting_version.published`. | Immutable 2026-06 v2 supersedes v1; RC-001 becomes `PUBLISHED`. |

The original June ledger period remains `HARD_CLOSED`. June v1 and v2 remain independently retrievable and reproducible.

## 10. Invalid-Transition and Integrity Tests

### Preventive platform invariants

These commands must be rejected before state or ledger mutation:

| Test | Illegal attempt |
|---|---|
| PI-01 | Post a proposal that is not `APPROVED`. |
| PI-02 | Approve a terminal proposal version. |
| PI-03 | Mutate a posted journal header or line. |
| PI-04 | Post into a `HARD_CLOSED` period. |
| PI-05 | Hard-close with any unresolved `SUBMITTED` or `APPROVED` proposal. |
| PI-06 | Defer a proposal without close-exception authority, reason, owner, and evidence. |
| PI-07 | Self-approve where segregation-of-duties policy prohibits it. |
| PI-08 | Invoke the posting-rule engine with an `accounting_event`. |
| PI-09 | Reopen without an approved, bounded directive. |
| PI-10 | Approve or post outside an authorised reopen scope. |
| PI-11 | Publish from a restatement case that is not `APPROVED`. |
| PI-12 | Post a reversal whose lines are not equal and opposite to the referenced journal. |
| PI-13 | Post a replacement without `corrects_journal_id`. |
| PI-14 | Post a restatement adjustment without `restatement_case_id`. |
| PI-15 | Freeze a manifest that does not reconcile exactly to linked journal lines. |
| PI-16 | Change a frozen manifest, posted journal, or published reporting version. |
| PI-17 | Let a current-period journal directly overwrite a prior published reporting version. |
| PI-18 | Repeat a successful posting or publication command under the same idempotency key. |

### Independent Argus integrity controls

Argus independently detects bypass, imported corruption, and assurance failures even where the application normally prevents them:

- journal imbalance;
- orphan journal lines;
- duplicate posting keys;
- posted journals without approved proposal versions;
- proposal-to-period state incompatibility;
- reversal mismatch;
- restatement manifest-to-journal mismatch;
- reporting-version lineage breaks;
- unresolved or deferred proposal completeness gaps; and
- any overlap between registered business-event triggers and accounting-event types.

Preventive enforcement and detective assurance intentionally overlap but remain separate responsibilities.

## 11. Completion and Next Design Target

Artifact E is complete when implementations can derive both canonical lifecycles from these tables and reject every preventive-invariant test without special-case mutation.

The next design target is Artifact F: minimum payload contracts for only the object and event types instantiated by C-001 and CT-1. No speculative event taxonomy should be added before those contracts pass the canonical proofs above.
