# Artifact C: Accounting Object Model

Design sequence artifact C. This is the minimum nine-object model supporting the full posting lifecycle:

- `business_event`
- `posting_rule`
- `journal_proposal`
- `accounting_event`
- `journal_entry`
- `journal_line`
- `accounting_period`
- `reporting_version`
- `restatement_case`

## Structural Firewall

The platform has two separate event streams:

```text
business_event  -> posting-rule engine
accounting_event -> governance, period, ledger, and reporting lifecycles only
```

`business_event` is the only object class accepted by the posting-rule evaluator. `accounting_event` can never be passed to that interface and can never trigger posting-rule evaluation.

This makes recursive posting impossible by construction:

```text
Business event
-> proposed journal
-> journal approved event
-> journal posted event
-> immutable journal records
```

The posted journal records do not become new business events.

## Objects

### `business_event`

Captures a material business state transition with causal significance.

Required examples:

- `accounting.recognition.due`
- `o2c.cash.received`
- `o2c.cash.applied`

Only this object class can trigger posting-rule evaluation.

### `posting_rule`

Versioned accounting logic that derives proposed journals from eligible business events.

Posting rules create journal proposals. They do not post directly.

### `journal_proposal`

A derived, versioned, frozen candidate accounting treatment.

Submitted proposals must remain identifiable even if they are never approved or posted.

### `accounting_event`

Immutable record of an accounting lifecycle action.

Examples:

- `proposal.submitted`
- `proposal.approved`
- `proposal.deferred`
- `journal.posted`
- `period.hard_closed`
- `restatement.adjustment_linked`
- `restatement.approved`
- `reporting_version.published`

Accounting events can affect governance, period, ledger, and reporting lifecycles. They cannot trigger posting-rule evaluation.

### `journal_entry`

Immutable posted journal header.

### `journal_line`

Immutable posted debit or credit line belonging to one journal entry.

### `accounting_period`

Controls ledger-period state, including open, soft-closed, hard-closed, and exceptionally reopened. Restatement is not a period state: a hard-closed period can be re-presented through a later reporting version without reopening its ledger.

### `reporting_version`

Immutable record preserving a published view of a reporting period.

Examples:

- June 2026 v1 as originally closed.
- June 2026 v2 as restated.

### `restatement_case`

Coordinates a governed restatement under one identity. It owns the affected-period scope, linked adjustment journals, frozen presentation-adjustment manifest, approval evidence, and published reporting-version references.

The manifest bridges a correction journal posted in an eligible open ledger period to the prior period re-presented in the successor reporting version. Its entries are owned value records rather than a tenth independently stateful accounting object.

## Correction Lifecycles

### Reversal Arm

Used when an incorrect journal was posted and correction policy requires an equal-and-opposite entry plus a replacement.

CT-1 exercises this lifecycle.

### Restatement Arm

Used when a hard-closed reporting period must be republished without pretending the original version never existed.

C-001 exercises this lifecycle.

## C-001 Proof

C-001 starts with one `business_event`, `accounting.recognition.due`, for the June 2026 service obligation.

`PR-O2C-RECOG` produces proposal `P-551@v1`.

`accounting_event: proposal.submitted` freezes the proposal.

The Controller explicitly defers the submitted proposal under close-exception policy, after which June hard-closes. The proposal remains historically submitted and unposted but has a visible terminal disposition.

Argus finds that the recognition schedule expected one June recognition journal, but Atlas has zero posted journals and one submitted unposted proposal.

Aegis confirms the issue and publishes the remediation directive. Atlas
validates that authority and opens `restatement_case` RC-001 through
`accounting_event: restatement.proposed`.

Atlas creates `P-551@v2` under restatement policy, posts the approved restatement-adjustment journal in an eligible correction period, freezes a presentation-adjustment manifest for June, and publishes June 2026 v2.

No accounting event re-enters the posting-rule engine.

## CT-1 Proof

CT-1 starts with a cash application posted to the wrong customer.

The incorrect posted journal is corrected through a frozen equal-and-opposite reversal proposal and journal, followed by a frozen replacement proposal and journal.

This proves the reversal arm without forcing C-001 to demonstrate both correction lifecycles.

## Bound Downstream Baseline

- Artifact E v0.2.1 defines the accounting state machines and command/event
  matrix.
- Artifact F v0.2.1 defines the minimum payload contracts and canonical
  fixtures instantiated by C-001 and CT-1.
- Artifact G v0.2 fixes module ownership and publish/consume boundaries.
- Artifact H v0.3.1 defines the finite executable validation boundary.

Milestone 1 implements that baseline without expanding this object model.
